#!/usr/bin/env python3
"""Prepare native-grid CEDD rasters; never write to data/raw.

Run from any directory with the repository's .venv Python. Failed acceptance
QA still produces diagnostic artifacts and exits 1; structural errors stop.
"""
import argparse
import hashlib
import json
import math
import os
import shutil
import sys
import tempfile
from contextlib import ExitStack
from pathlib import Path

import numpy as np
import pyproj
import rasterio
from rasterio.crs import CRS
from rasterio.merge import merge
from rasterio.windows import Window, from_bounds, bounds as window_bounds

TILES = {'11NW14C','11NW14D','11NW15C','11NW19A','11NW19B',
         '11NW19C','11NW19D','11NW20A','11NW20C'}
CRS_EXPECTED = CRS.from_epsg(2326)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def record(path, root, statistics=False):
    with rasterio.open(path) as ds:
        r = dict(path=path.relative_to(root).as_posix(), crs=ds.crs.to_string() if ds.crs else None,
                 resolution=list(ds.res), shape=[ds.height, ds.width], dtype=ds.dtypes[0],
                 nodata=ds.nodata, bounds=list(ds.bounds), transform=list(ds.transform),
                 bands=ds.count, size_bytes=path.stat().st_size,
                 tiled=ds.profile.get('tiled', False), compression=ds.profile.get('compress'))
        if statistics:
            count, total, lo, hi = 0, 0., math.inf, -math.inf
            for _, w in ds.block_windows(1):
                v = ds.read(1, window=w, masked=True).compressed()
                if v.size:
                    if not np.isfinite(v).all():
                        raise ValueError(f'Nonfinite valid elevations in {path.name}')
                    count += int(v.size)
                    total += float(v.sum(dtype=np.float64))
                    lo, hi = min(lo, float(v.min())), max(hi, float(v.max()))
            r.update(valid_pixels=count, nodata_percent=100*(1-count/(ds.width*ds.height)),
                     elevation_min_m=lo if count else None, elevation_max_m=hi if count else None,
                     elevation_mean_m=total/count if count else None)
        return r


def write_raster(path, array, transform, nodata):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp.tif')
    try:
        with rasterio.open(temporary, 'w', driver='GTiff', height=array.shape[0], width=array.shape[1],
                           count=1, dtype=array.dtype, crs=CRS_EXPECTED, transform=transform,
                           nodata=nodata, compress='LZW', tiled=True, blockxsize=256,
                           blockysize=256, predictor=3 if array.dtype.kind == 'f' else 2) as ds:
            ds.write(array, 1)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def snap_window(envelope, ds):
    w = from_bounds(*envelope, transform=ds.transform)
    # Outward snapping uses integer pixel edges in the mosaic's own grid.
    c, r = math.floor(w.col_off), math.floor(w.row_off)
    right, bottom = math.ceil(w.col_off+w.width), math.ceil(w.row_off+w.height)
    if c < 0 or r < 0 or right > ds.width or bottom > ds.height:
        raise ValueError('Requested envelope extends beyond mosaic coverage')
    return Window(c, r, right-c, bottom-r)


def pair_check(dsm, dtm):
    with rasterio.open(dsm) as a, rasterio.open(dtm) as b:
        matched = a.transform == b.transform and a.shape == b.shape and a.bounds == b.bounds and a.crs == b.crs
        if not matched:
            raise ValueError('DSM/DTM grids do not match')
        x, y = a.read(1, masked=True), b.read(1, masked=True)
        valid = ~(np.ma.getmaskarray(x) | np.ma.getmaskarray(y))
        if not valid.any():
            raise ValueError('No jointly valid pixels')
        delta = x.data[valid].astype(np.float64)-y.data[valid].astype(np.float64)
        negative = delta[delta < 0]
        return dict(grid_match=matched, valid_pixels=int(valid.sum()),
                    dsm_ge_dtm_percent=100*float(np.mean(delta >= 0)),
                    passes_strictly_over_99_percent=bool(np.mean(delta >= 0) > .99),
                    tolerance_m=0.3, dsm_ge_dtm_minus_0p3_percent=100*float(np.mean(delta >= -.3)),
                    passes_core_tolerance=bool(np.mean(delta >= -.3) > .99),
                    below_minus_0p3_pixels=int(np.sum(delta < -.3)),
                    below_minus_0p3_percent=100*float(np.mean(delta < -.3)),
                    negative_percentiles_m={str(q):float(np.percentile(negative,q)) for q in (0,1,5,25,50,75,95,99,100)} if negative.size else {},
                    negative_pixels=int(negative.size), delta_min_m=float(delta.min()),
                    delta_max_m=float(delta.max()), negative_mean_m=float(negative.mean()) if negative.size else None,
                    negative_pixels_below_minus_0p1m=int(np.sum(delta < -.1)),
                    negative_pixels_below_minus_1m=int(np.sum(delta < -1)))


def overview(root, inventory, outputs, pairs):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import LightSource, TwoSlopeNorm
    from matplotlib.patches import Rectangle
    from matplotlib.ticker import ScalarFormatter
    fig, axes = plt.subplots(2, 2, figsize=(14, 12), constrained_layout=True)
    axes=axes.ravel()
    outline = dict(acq='#0086a8', core='#ffb000')
    for ax, extent in zip(axes[:2], ('acq','core')):
        with rasterio.open(root/outputs[f'dsm_{extent}']['path']) as ds:
            z, bb = ds.read(1, masked=True), ds.bounds
            shade = LightSource(azdeg=315, altdeg=45).hillshade(z.filled(np.nan), vert_exag=1, dx=.5, dy=.5)
            ax.imshow(shade, extent=[bb.left,bb.right,bb.bottom,bb.top], cmap='gray', origin='upper', vmin=0, vmax=1)
        for tag in ('acq','core'):
            box = outputs[f'dsm_{tag}']['bounds']
            ax.add_patch(Rectangle((box[0],box[1]),box[2]-box[0],box[3]-box[1],
                                   fill=False, edgecolor=outline[tag], linewidth=2, label=f'{tag} grid bounds'))
        for item in inventory:
            if item['layer'] != 'dsm': continue
            b = item['bounds']
            ax.add_patch(Rectangle((b[0],b[1]),b[2]-b[0],b[3]-b[1],fill=False,
                                   edgecolor='#d75685', linewidth=1, linestyle='--'))
        ax.set_xlim(bb.left,bb.right); ax.set_ylim(bb.bottom,bb.top)
        ax.set_title('Acquisition context / tile boundaries' if extent == 'acq' else 'Core DSM hillshade / tile boundaries')
        if extent == 'acq': ax.legend(loc='upper left', fontsize=8)
    with rasterio.open(root/outputs['dsm_core']['path']) as a, rasterio.open(root/outputs['dtm_core']['path']) as b:
        delta = a.read(1,masked=True)-b.read(1,masked=True)
        # Nonlinear clipping for display only; data and strict QA remain unchanged.
        vmax = max(1.,float(np.percentile(delta.compressed(),99)))
        im = axes[2].imshow(delta, extent=[a.bounds.left,a.bounds.right,a.bounds.bottom,a.bounds.top],
                            cmap='RdBu_r', norm=TwoSlopeNorm(vmin=-2.,vcenter=0.,vmax=vmax), origin='upper')
        fig.colorbar(im,ax=axes[2],label='DSM − DTM (m), display range −2 to 99th percentile',shrink=.73,extend='both')
    axes[2].set_title('Core elevation diagnostic / original DSM − DTM')
    from matplotlib.colors import ListedColormap
    breach=np.ma.array((delta.data < -.3).astype(float),mask=np.ma.getmaskarray(delta))
    axes[3].imshow(breach,extent=[a.bounds.left,a.bounds.right,a.bounds.bottom,a.bounds.top],
                   origin='upper',cmap=ListedColormap(['#eeeeee','#c0005a']),vmin=0,vmax=1)
    yy,xx=np.where((delta.data < -.3)&~np.ma.getmaskarray(delta))
    axes[3].scatter(a.bounds.left+(xx+.5)*.5,a.bounds.top-(yy+.5)*.5,s=12,facecolors='none',edgecolors='#c0005a',linewidths=.7)
    axes[3].set_title(f"Core pixels below −0.3 m / magenta markers\n{pairs['core']['below_minus_0p3_pixels']} pixels ({pairs['core']['below_minus_0p3_percent']:.5f}%), markers enlarged")
    for ax in axes:
        ax.set_xlabel('Easting (m, EPSG:2326)'); ax.set_ylabel('Northing (m)')
        ax.tick_params(axis='x',labelrotation=35)
        formatter=ScalarFormatter(useOffset=False); formatter.set_scientific(False)
        ax.xaxis.set_major_formatter(formatter)
        formatter=ScalarFormatter(useOffset=False); formatter.set_scientific(False)
        ax.yaxis.set_major_formatter(formatter)
        ax.set_aspect('equal')
    fig.suptitle('CEDD 2020 / Mong Kok / native 0.5 m grid\nPink dashed lines: CEDD tile boundaries; hillshade is a QA preview, not SVF',fontsize=14)
    path=root/'figures/qa_overview.png'; path.parent.mkdir(exist_ok=True)
    fig.savefig(path,dpi=180); plt.close(fig)


def save_reports(root, report):
    (root/'reports').mkdir(exist_ok=True); (root/'docs').mkdir(exist_ok=True)
    (root/'reports/raster_qa.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    lines=['# CEDD 2020 raster QA','',f"Overall status: **{report['status']}**.",'',
           'Reproduce: `.venv/bin/python scripts/prepare_cedd_rasters.py`.',
           'Exit code 1 means an acceptance check failed; negative DSM−DTM values alone do not cause failure.','',
           '## Decisions and interpretation','']
    lines += ['- '+x for x in report['notes']]
    lines += ['', '## Output rasters','',
              '| Output | CRS | Pixel m | Shape (rows × columns) | NoData % | Elevation min / max / mean (m) | MiB |',
              '|---|---|---|---|---:|---|---:|']
    for k, r in report.get('outputs',{}).items():
        lines.append(f"| {k} | {r['crs']} | {r['resolution'][0]} × {r['resolution'][1]} | {r['shape'][0]} × {r['shape'][1]} | {r['nodata_percent']:.6f} | {r['elevation_min_m']:.3f} / {r['elevation_max_m']:.3f} / {r['elevation_mean_m']:.3f} | {r['size_bytes']/2**20:.3f} |")
    lines += ['', '## DSM/DTM checks','', '| Extent | Same grid | DSM ≥ DTM % (informational) | DSM ≥ DTM − 0.3 m % | Below −0.3 m % | Negative pixels / nDSM clamp count |', '|---|---|---:|---:|---:|---:|']
    for k,p in report.get('pairs',{}).items():
        lines.append(f"| {k} | {p['grid_match']} | {p['dsm_ge_dtm_percent']:.6f} | {p['dsm_ge_dtm_minus_0p3_percent']:.6f} | {p['below_minus_0p3_percent']:.6f} | {p['negative_pixels']} |")
    lines += ['', 'Only the core tolerant check is an acceptance gate. Mosaic has no nDSM output; its negative count is informational.', '', '## Negative difference distribution', '', 'Percentiles are conditional on DSM − DTM < 0; units are metres.', '', '| Extent | p0 | p1 | p5 | p25 | p50 | p75 | p95 | p99 | p100 |', '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for k,p in report.get('pairs',{}).items():
        lines.append('| '+k+' | '+' | '.join(f'{p["negative_percentiles_m"][str(q)]:.6f}' for q in (0,1,5,25,50,75,95,99,100))+' |')
    lines += ['', '## Automated checks','', '| Check | Result |', '|---|---|']
    lines += [f"| {k} | {'PASS' if v else 'FAIL'} |" for k,v in report.get('checks',{}).items()]
    lines += ['', '## Snapped envelopes (EPSG:2326)','', 'Order: [minx, miny, maxx, maxy].','']
    for k,v in report.get('envelopes',{}).items():
        lines += [f"- {k}: requested `{v['requested']}`; snapped `{v['snapped']}`; dimensions `{v['width_m']} × {v['height_m']} m`."]
    lines += ['', '## Input inventory','', '| Layer / tile | CRS | Pixel m | Shape | Dtype | NoData | Bounds [minx, miny, maxx, maxy] |', '|---|---|---|---|---|---|---|']
    for r in report.get('inventory',[]):
        lines.append(f"| {r['layer']} / {r['tile']} | {r['crs']} | {r['resolution']} | {r['shape']} | {r['dtype']} | {r['nodata']} | {r['bounds']} |")
    lines += ['', '## Samples','']
    lines += [f"- `{r['path']}`: {r['size_bytes']/2**20:.3f} MiB ({r['selection']})." for r in report.get('samples',[])]
    lines += ['', '## Failures',''] + (['- '+s for s in report.get('failures',[])] or ['None.'])
    if report.get('error'): lines += ['', report['error']]
    (root/'docs/RASTER_QA.md').write_text('\n'.join(lines)+'\n')


def prepare(root, report):
    config=json.loads((root/'config/study_area.json').read_text())
    envelopes=config['analysis_envelopes_epsg2326']
    files={k:sorted((root/f'data/raw/cedd/extracted/{k}').rglob('*.tif')) for k in ('dsm','dtm')}
    hashes={p.relative_to(root).as_posix():digest(p) for paths in files.values() for p in paths}
    inventory=report['inventory']=[]
    for kind, paths in files.items():
        if len(paths)!=9 or {p.name.split('(')[0] for p in paths} != TILES:
            raise ValueError(f'{kind}: expected exactly the specified nine tiles')
        for path in paths:
            r=record(path,root); r.update(layer=kind,tile=path.name.split('(')[0],sha256=hashes[path.relative_to(root).as_posix()]); inventory.append(r)
    baseline=inventory[0]
    for r in inventory:
        for key in ('crs','resolution','shape','dtype','nodata','bands'):
            if r[key]!=baseline[key]: raise ValueError(f"Input metadata differs: {r['path']}: {key}")
        if r['crs']!='EPSG:2326' or r['resolution']!=[.5,.5] or r['bands']!=1:
            raise ValueError(f"Unexpected CRS/resolution/bands: {r['path']}")
        t=r['transform']; first=baseline['transform']
        if t[0]!=.5 or t[4]!=-.5 or t[1]!=0 or t[3]!=0 or any(abs((t[i]-first[i])/.5-round((t[i]-first[i])/.5))>1e-8 for i in (2,5)):
            raise ValueError('Inputs have inconsistent pixel-grid alignment')
    for tile in TILES:
        a,b=[r for r in inventory if r['tile']==tile]
        if a['bounds']!=b['bounds'] or a['transform']!=b['transform']:
            raise ValueError(f'DSM/DTM bounds differ for {tile}')
    nodata=baseline['nodata']
    if nodata is None:
        nodata=-9999
        if not np.can_cast(np.min_scalar_type(nodata),np.dtype(baseline['dtype']),casting='safe'):
            raise ValueError('Fallback -9999 cannot be represented without changing original dtype')
        report['notes'].append('Source NoData absent; output NoData explicitly set to -9999.')
    else: report['notes'].append(f'Source NoData retained unchanged: {nodata}.')
    report['checks']['input_metadata_consistent']=True
    out=root/'data/processed'; out.mkdir(parents=True,exist_ok=True)
    outputs=report['outputs']={}
    for kind,paths in files.items():
        print(f'Mosaicking {kind}: 9 native-grid tiles',flush=True)
        with ExitStack() as stack:
            datasets=[stack.enter_context(rasterio.open(p)) for p in paths]
            mosaic, transform=merge(datasets,nodata=nodata,method='first',dtype=baseline['dtype'])
        path=out/f'cedd2020_{kind}_mosaic_0p5m.tif'
        write_raster(path,mosaic[0],transform,nodata); del mosaic
        outputs[f'{kind}_mosaic']=record(path,root,True)
        with rasterio.open(path) as ds:
            for extent,config_key in [('acq','acquisition'),('core','core')]:
                window=snap_window(envelopes[config_key],ds)
                target=out/f'cedd2020_{kind}_{extent}_0p5m.tif'
                write_raster(target,ds.read(1,window=window),ds.window_transform(window),nodata)
                outputs[f'{kind}_{extent}']=record(target,root,True)
                bb=list(window_bounds(window,ds.transform))
                report['envelopes'][extent]=dict(requested=envelopes[config_key],snapped=bb,width_m=bb[2]-bb[0],height_m=bb[3]-bb[1])
    pairs=report['pairs']={}
    for extent in ('mosaic','acq','core'):
        pairs[extent]=pair_check(root/outputs[f'dsm_{extent}']['path'],root/outputs[f'dtm_{extent}']['path'])
        report['checks'][f'{extent}_grid_match']=pairs[extent]['grid_match']
        if extent=='core':
            passed=pairs[extent]['passes_core_tolerance']
            report['checks']['core_dsm_ge_dtm_minus_0p3_over_99_percent']=passed
            if not passed: report['failures'].append(f"Core: DSM ≥ DTM − 0.3 m in {pairs[extent]['dsm_ge_dtm_minus_0p3_percent']:.6f}%; required strictly >99%.")
        if extent=='mosaic': continue
        with rasterio.open(root/outputs[f'dsm_{extent}']['path']) as a, rasterio.open(root/outputs[f'dtm_{extent}']['path']) as b:
            x,y=a.read(1,masked=True),b.read(1,masked=True)
            valid=~(np.ma.getmaskarray(x)|np.ma.getmaskarray(y))
            ndsm=np.full(a.shape,nodata,dtype='float32')
            ndsm[valid]=np.maximum(x.data[valid]-y.data[valid],0)
            path=out/f'cedd2020_ndsm_{extent}_0p5m.tif'
            write_raster(path,ndsm,a.transform,nodata)
        outputs[f'ndsm_{extent}']=record(path,root,True)
        outputs[f'ndsm_{extent}']['negative_pixels_clamped_to_zero']=pairs[extent]['negative_pixels']
    for key,r in outputs.items():
        passed=(r['crs']=='EPSG:2326' and r['resolution']==[.5,.5] and r['nodata']==nodata
                and r['dtype']==baseline['dtype'] and r['tiled'] and r['compression']=='lzw' and r['valid_pixels']>0)
        report['checks'][key+'_raster_metadata']=passed
        if not passed: raise ValueError(f'Output metadata validation failed: {key}')
        if not key.endswith('mosaic'):
            report['checks'][key+'_complete_coverage']=r['nodata_percent']==0
            if r['nodata_percent']!=0: report['failures'].append(f'{key}: expected zero NoData in analysis extent')
    samples=root/'data/sample'; samples.mkdir(parents=True,exist_ok=True)
    report['samples']=[]
    for kind in ('dsm','dtm'):
        source=root/outputs[f'{kind}_core']['path']; target=samples/source.name
        if source.stat().st_size < 10_000_000:
            shutil.copy2(source,target); selection='copy of full core (<10 MB decimal)'
        else:
            target=samples/f'cedd2020_{kind}_sample250m_0p5m.tif'
            with rasterio.open(source) as ds:
                w=Window((ds.width-500)//2,(ds.height-500)//2,500,500)
                write_raster(target,ds.read(1,window=w),ds.window_transform(w),nodata)
            selection='centered 250 m × 250 m subset'
        r=record(target,root,True); r['selection']=selection; report['samples'].append(r)
    overview(root,inventory,outputs,pairs)
    report['checks']['raw_tiff_sha256_unchanged']=all(digest(root/p)==h for p,h in hashes.items())
    if not report['checks']['raw_tiff_sha256_unchanged']: raise ValueError('Raw input integrity changed')
    report['status']='PASS' if all(report['checks'].values()) else 'FAIL'
    return report['status']=='PASS'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args(); root=args.root.resolve()
    report=dict(status='FAIL',inventory=[],outputs={},pairs={},envelopes={},checks={},failures=[],
                software=dict(python=sys.version.split()[0],rasterio=rasterio.__version__,gdal=rasterio.__gdal_version__,numpy=np.__version__,pyproj=pyproj.__version__),
                notes=['Input tile bounds differ by location; metadata, dimensions and pixel-grid alignment must match. Corresponding DSM/DTM tile bounds must be identical.',
                       'No reprojection or resolution change is performed. rasterio.merge combines matching native grids; clips use outward-rounded integer pixel windows.',
                       'Projected envelopes in config are authoritative; retained WGS84 boxes document the original approximate selection.',
                       'nDSM is DSM − DTM with negative valid values clamped to zero. Original DSM/DTM and strict sanity checks remain unchanged.',
                       'Acceptance threshold: DSM ≥ DTM − 0.3 m for strictly >99% of jointly valid core pixels. Strict DSM ≥ DTM is informational only. Negative percentiles are conditional on negative differences; percentages below −0.3 m use all jointly valid pixels.',
                       'Vertical datum and accuracy have not been independently verified; matching horizontal grids do not establish either.'])
    try:
        with tempfile.TemporaryDirectory(prefix='svf-matplotlib-') as cache:
            os.environ['MPLCONFIGDIR']=cache
            passed=prepare(root,report)
    except Exception as exc:
        report['error']=f'{type(exc).__name__}: {exc}'
        report['failures'].append(report['error']); passed=False
    save_reports(root,report)
    print(json.dumps(dict(status=report['status'],failures=report['failures'],checks=report['checks']),indent=2),flush=True)
    return 0 if passed else 1

if __name__=='__main__':
    sys.exit(main())
