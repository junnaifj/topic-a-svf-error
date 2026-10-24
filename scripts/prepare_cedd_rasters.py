#!/usr/bin/env python3
"""Copy/recover CEDD tiles, verify, extract, mosaic and clip; never edit sources."""
import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
import zipfile
from contextlib import ExitStack
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

def load_geospatial():
    global np, pyproj, rasterio, CRS, merge, transform_bounds, transform, Window, from_bounds
    import numpy as np
    import pyproj
    import rasterio
    from rasterio.crs import CRS
    from rasterio.merge import merge
    from rasterio.warp import transform_bounds, transform
    from rasterio.windows import Window, from_bounds


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def snapshot(root):
    return {str(p.relative_to(root)): sha256(p)
            for p in sorted(root.rglob('*'))
            if p.is_file() and '.git' not in p.relative_to(root).parts}


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')


def info(path):
    with rasterio.open(path) as ds:
        valid = 0
        minimum, maximum = math.inf, -math.inf
        for _, window in ds.block_windows(1):
            a = ds.read(1, window=window, masked=True)
            values = a.compressed()
            if values.size:
                if not np.isfinite(values).all():
                    raise ValueError(f'Nonfinite valid values: {path}')
                valid += int(values.size)
                minimum = min(minimum, float(values.min()))
                maximum = max(maximum, float(values.max()))
        return dict(path=str(path), crs=ds.crs.to_string() if ds.crs else None,
                    resolution=list(ds.res), nodata=ds.nodata, dtype=ds.dtypes[0],
                    count=ds.count, width=ds.width, height=ds.height,
                    bounds=list(ds.bounds), transform=list(ds.transform),
                    valid_pixels=valid, invalid_pixels=ds.width*ds.height-valid,
                    valid_fraction=valid/(ds.width*ds.height),
                    min=minimum if valid else None, max=maximum if valid else None,
                    tags=ds.tags(), units=list(ds.units), sha256=sha256(path))


def recover(job):
    kind, prop, raw, expected, allow_recovery = job
    name = prop['FILENAME']
    if Path(name).name != name:
        raise ValueError('Unsafe index filename')
    target = raw/kind/name
    rel = f'{kind}/{name}'
    if rel not in expected:
        raise ValueError(f'No expected SHA256: {rel}')
    target.parent.mkdir(parents=True, exist_ok=True)
    action = 'copied_existing'
    if not target.exists():
        if not allow_recovery:
            raise FileNotFoundError(f'Missing local archive: {target}. No download was attempted. Supply existing tiles or explicitly use --recover-missing.')
        action = 'recovered_from_saved_url'
        parts = urlsplit(prop['URL'])
        if parts.scheme != 'https' or parts.hostname != 'bulkdata.csdi.gov.hk':
            raise ValueError('Unexpected download host')
        url = urlunsplit((parts.scheme, parts.netloc, quote(parts.path, safe='/()%'), parts.query, ''))
        partial = target.with_name(target.name+'.partial')
        print(f'Downloading {rel}', flush=True)
        for attempt in range(8):
            result = subprocess.run(['curl', '-fsSL', '-C', '-', '--connect-timeout', '30',
                                     '--max-time', '180', url, '-o', str(partial)])
            if result.returncode == 0:
                break
            if result.returncode in (-2, -15, 130, 143):
                raise InterruptedError(f'Download cancelled: {rel}')
            print(f'Resuming interrupted download: {rel}, attempt {attempt+2}', flush=True)
        else:
            raise RuntimeError(f'Download failed after resumable attempts: {rel}')
        partial.rename(target)
    actual = sha256(target)
    if actual != expected[rel]:
        raise ValueError(f'Archive checksum mismatch: {rel}')
    outdir = raw/'extracted'/kind/Path(name).stem
    outdir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target) as archive:
        for member in archive.infolist():
            destination = (outdir/member.filename).resolve()
            if not destination.is_relative_to(outdir.resolve()):
                raise ValueError('Unsafe ZIP entry')
        bad = archive.testzip()
        if bad:
            raise ValueError(f'ZIP CRC failure: {name}: {bad}')
        archive.extractall(outdir)
    rasters = [p for p in outdir.rglob('*') if p.suffix.lower() in ('.tif', '.tiff')]
    if len(rasters) != 1:
        raise ValueError(f'Expected one TIFF per ZIP: {rel}: {rasters}')
    record = dict(layer=kind, filename=name, url=prop['URL'], action=action,
                  sha256=actual, matches_prior_manifest=True)
    print(f'Checksum and ZIP verified: {rel}', flush=True)
    return kind, rasters[0], record


def run(source, work, resume=False, allow_recovery=False):
    if source == work or source in work.parents or work in source.parents:
        raise ValueError('Working folder must be separate from the source project')
    if not (source/'config/study_area.json').is_file():
        raise FileNotFoundError('Missing config/study_area.json')
    if not allow_recovery:
        missing = []
        for kind in ('dsm', 'dtm'):
            index = source/f'data/raw/cedd/indexes/{kind}_mongkok.geojson'
            features = json.loads(index.read_text())['features']
            for feature in features:
                name = feature['properties']['FILENAME']
                original = source/'data/raw/cedd'/kind/name
                copied = work/'data/raw/cedd'/kind/name
                if not original.is_file() and not (resume and copied.is_file()):
                    missing.append(str(original))
        if missing:
            raise FileNotFoundError('Required local ZIPs are absent; no files changed and no downloads attempted:\n'+'\n'.join(missing))
    before = snapshot(source)
    work.mkdir(parents=True, exist_ok=resume)
    reportdir = work/'reports'
    reportdir.mkdir(exist_ok=resume)
    if resume:
        saved_before = json.loads((reportdir/'source_files_before.json').read_text())
        if any(before.get(k) != v for k, v in saved_before.items()):
            raise ValueError('Source project changed since this working copy was created')
        if (work/'config/study_area.json').read_bytes() != (source/'config/study_area.json').read_bytes():
            raise ValueError('Working config differs from original; use a new folder')
    else:
        dump(reportdir/'source_files_before.json', before)
    # Only copy data/config into the working folder; keep original project untouched.
    if not resume:
        shutil.copytree(source/'config', work/'config')
        shutil.copytree(source/'data/raw/cedd', work/'data/raw/cedd')
    scriptsdir = work/'scripts'
    scriptsdir.mkdir(exist_ok=resume)
    shutil.copy2(Path(__file__), scriptsdir/Path(__file__).name)
    for name in ('requirements-svf.txt', 'README-svf-preprocessing.md'):
        candidate = Path(__file__).parent.parent/name
        if candidate.exists():
            shutil.copy2(candidate, work/name)
    raw = work/'data/raw/cedd'
    processed = work/'data/processed'
    processed.mkdir(parents=True, exist_ok=resume)
    expected = {}
    for line in (raw/'SHA256SUMS.txt').read_text().splitlines():
        if line.strip():
            digest, rel = line.split(maxsplit=1)
            expected[rel.lstrip('*')] = digest
    cfg = json.loads((work/'config/study_area.json').read_text())
    if cfg.get('bbox_order') != ['west', 'south', 'east', 'north']:
        raise ValueError('Unexpected bbox order')
    acquisitions, tiles = [], {'dsm': [], 'dtm': []}
    jobs = []
    for kind in ('dsm', 'dtm'):
        features = json.loads((raw/f'indexes/{kind}_mongkok.geojson').read_text())['features']
        if len(features) != 9:
            raise ValueError(f'Expected 9 {kind} tile-index features; got {len(features)}')
        for feature in sorted(features, key=lambda f: f['properties']['FILENAME']):
            jobs.append((kind, feature['properties'], raw, expected, allow_recovery))
    with ThreadPoolExecutor(max_workers=8) as pool:
        for kind, path, record in pool.map(recover, jobs):
            tiles[kind].append(path)
            acquisitions.append(record)
            dump(reportdir/'acquisition_recovery.json', acquisitions)
    load_geospatial()
    dump(reportdir/'runtime_versions.json', dict(python=sys.version, rasterio=rasterio.__version__,
         gdal=rasterio.__gdal_version__, numpy=np.__version__, pyproj=pyproj.__version__,
         proj=pyproj.proj_version_str, utc=datetime.now(timezone.utc).isoformat()))
    inventory = []
    reference_grid = None
    for kind, paths in tiles.items():
        for path in paths:
            record = info(path)
            record['layer'] = kind
            if record['crs'] != 'EPSG:2326' or record['resolution'] != [0.5, 0.5]:
                raise ValueError(f'Unexpected source CRS/resolution: {record}')
            if record['nodata'] != -9999 or record['count'] != 1 or record['dtype'] != 'float32':
                raise ValueError(f'Unexpected source NoData/band count/type: {record}')
            with rasterio.open(path) as ds:
                if ds.transform.b or ds.transform.d or ds.transform.a <= 0 or ds.transform.e >= 0:
                    raise ValueError('Rotated/non-north-up source grid')
                if reference_grid is None:
                    reference_grid = ds.transform
                if not all(abs(v-round(v)) < 1e-6 for v in (
                    (ds.transform.c-reference_grid.c)/0.5,
                    (ds.transform.f-reference_grid.f)/0.5)):
                    raise ValueError('Source pixels are not aligned')
            inventory.append(record)
    dump(reportdir/'source_raster_inventory.json', inventory)
    for kind in ('dsm', 'dtm'):
        with ExitStack() as stack:
            datasets = [stack.enter_context(rasterio.open(p)) for p in tiles[kind]]
            a, affine = merge(datasets, res=0.5, nodata=-9999, method='first', dtype='float32')
            profile = datasets[0].profile.copy()
            profile.update(driver='GTiff', width=a.shape[2], height=a.shape[1], count=1,
                           transform=affine, crs=CRS.from_epsg(2326), dtype='float32',
                           nodata=-9999, compress='deflate', predictor=3,
                           tiled=True, blockxsize=256, blockysize=256, BIGTIFF='IF_SAFER')
            with rasterio.open(processed/f'{kind}_mosaic_0p5m.tif', 'w', **profile) as dst:
                dst.write(a)
                dst.update_tags(PROCESSING='Mosaic; first valid pixel; no reprojection or resampling',
                                VERTICAL_DATUM='Not verified; preserve source heights', SOURCE='CEDD 2020 LiDAR')
        print(f'Mosaic written: {kind}', flush=True)
    extents = {}
    with rasterio.open(processed/'dsm_mosaic_0p5m.tif') as ds, rasterio.open(processed/'dtm_mosaic_0p5m.tif') as dt:
        if ds.transform != dt.transform or ds.shape != dt.shape or ds.crs != dt.crs:
            raise ValueError('DSM and DTM mosaic grids differ')
        for label in ('acquisition', 'core'):
            geographic = cfg[f'{label}_bbox']
            bounds = transform_bounds(cfg['bbox_crs'], ds.crs, *geographic, densify_pts=101)
            floating = from_bounds(*bounds, transform=ds.transform)
            left, top = math.floor(floating.col_off), math.floor(floating.row_off)
            right, bottom = math.ceil(floating.col_off+floating.width), math.ceil(floating.row_off+floating.height)
            if left < 0 or top < 0 or right > ds.width or bottom > ds.height:
                raise ValueError(f'{label} extends beyond mosaic')
            window = Window(left, top, right-left, bottom-top)
            actual = rasterio.windows.bounds(window, ds.transform)
            extents[label] = dict(input_wgs84_bbox=geographic, projected_envelope=list(bounds),
                snapped_epsg2326_bounds=list(actual), width_m=actual[2]-actual[0],
                height_m=actual[3]-actual[1], width_pixels=int(window.width),
                height_pixels=int(window.height), grid_snapping='outward to native 0.5 m pixel edges',
                geometry_note='Rectangular projected envelope of configured WGS84 bbox; exact metric square not imposed')
            for kind in ('dsm', 'dtm'):
                with rasterio.open(processed/f'{kind}_mosaic_0p5m.tif') as src:
                    values = src.read(1, window=window, masked=True)
                    if np.ma.getmaskarray(values).any():
                        raise ValueError(f'NoData inside {kind} {label} clip')
                    p = src.profile.copy()
                    p.update(width=int(window.width), height=int(window.height), transform=src.window_transform(window))
                    with rasterio.open(processed/f'{kind}_{label}_0p5m.tif', 'w', **p) as dst:
                        dst.write(values.filled(src.nodata), 1)
                        dst.update_tags(**src.tags(), EXTENT=label)
                print(f'Clip written: {kind} {label}', flush=True)
    dump(reportdir/'analysis_extents.json', extents)
    footprints = []
    for label, extent in extents.items():
        w, s, e, n = extent['snapped_epsg2326_bounds']
        xs, ys = transform('EPSG:2326', 'EPSG:4326', [w,e,e,w,w], [s,s,n,n,s])
        footprints.append(dict(type='Feature', properties=dict(extent=label, width_m=extent['width_m'], height_m=extent['height_m']),
                               geometry=dict(type='Polygon', coordinates=[list(map(list, zip(xs,ys)))])))
    dump(work/'config/processed_footprints_wgs84.geojson', dict(type='FeatureCollection', features=footprints))
    outputs = [info(p) for p in sorted(processed.glob('*.tif'))]
    # DSM/DTM height differences are diagnostic only: never modify or clamp heights.
    diagnostics = {}
    for label in ('acquisition', 'core'):
        with rasterio.open(processed/f'dsm_{label}_0p5m.tif') as dsm, rasterio.open(processed/f'dtm_{label}_0p5m.tif') as dtm:
            delta = dsm.read(1)-dtm.read(1)
            diagnostics[label] = dict(dsm_below_dtm_pixels=int((delta < 0).sum()),
                dsm_below_dtm_fraction=float((delta < 0).mean()), min_difference_m=float(delta.min()),
                max_difference_m=float(delta.max()), heights_modified=False)
    after = snapshot(source)
    unchanged = before == after
    dump(reportdir/'source_preservation.json', dict(all_original_files_unchanged=unchanged,
         files_checked=len(before), changed=[k for k,v in before.items() if after.get(k) != v],
         added=sorted(set(after)-set(before))))
    if not unchanged:
        raise ValueError('Original project changed during processing; inspect preservation report')
    dump(reportdir/'processing_report.json', dict(status='success', source=str(source), work=str(work),
         inputs=18, outputs=outputs, extents=extents, height_diagnostics=diagnostics,
         original_project_unchanged=True, resampling=False, vertical_datum='not independently verified'))
    with (reportdir/'output_checksums.sha256').open('w') as f:
        for output in outputs:
            f.write(f"{output['sha256']}  {Path(output['path']).relative_to(work)}\n")
    lines = ['# CEDD raster preparation completed', '',
        'DSM and DTM were processed separately, preserving the native EPSG:2326, 0.5 m grid and source heights.',
        'NoData is -9999. No reprojection, interpolation, gap filling or height correction was applied.',
        'The working copy contains recovered ZIPs verified against the original SHA-256 manifest.',
        'The original project was checked before/after processing and was unchanged.', '',
        '| Extent | Width (m) | Height (m) | Raster dimensions |', '|---|---:|---:|---|']
    for label, ex in extents.items():
        lines.append(f"| {label} | {ex['width_m']} | {ex['height_m']} | {ex['width_pixels']} x {ex['height_pixels']} |")
    lines += ['', 'These are approximate analysis extents from the existing config, snapped outward to source pixels.',
        'Use the acquisition raster to compute SVF, then crop results to the core; do not compute street SVF from the core-only raster.',
        'The outer buffer still requires a sensitivity check. Vertical datum and survey/product limitations remain as documented by the provider.',
        'See reports/processing_report.json, source_raster_inventory.json and analysis_extents.json for evidence.']
    (work/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(status='success', work=str(work), extents=extents), indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-project', type=Path, required=True)
    parser.add_argument('--work-dir', type=Path, required=True, help='New folder; existing folders are never overwritten')
    parser.add_argument('--resume', action='store_true', help='Resume an existing working copy after verifying its source snapshot; rebuild derived outputs')
    parser.add_argument('--recover-missing', action='store_true', help='Explicitly allow recovery downloads from saved CSDI URLs; default is local-only')
    args = parser.parse_args()
    run(args.source_project.expanduser().resolve(), args.work_dir.expanduser().resolve(), args.resume, args.recover_missing)
