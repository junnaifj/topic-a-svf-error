# Processing status: waiting for local rasters

Original project: `/Users/junnai/Documents/phd-topic-a-svf-error`

Working root: `/Users/junnai/Downloads/phd-topic-a-svf-working-20261024`

The source project contains CEDD download records, SHA-256 hashes and tile indexes,
but no ZIP/TIFF raster files. Its DSM and DTM folders contain only .gitkeep.
All 23 original non-Git files match the initial hash baseline. No original
files were edited, moved or deleted. A duplicate is under source_snapshot/.

The preprocessing script and isolated Python dependencies are ready. Local-only
preflight correctly stops when the 18 required archives are absent. No full
mosaics or clips have been produced. One recovered DSM archive and its extracted
TIFF are retained separately from the original project; its metadata was verified
as EPSG:2326, 0.5 m resolution and NoData -9999. Incomplete recovery files and
package-download caches were removed. No original raw data were deleted.

## Continue once actual tile archives are available

Put **copies** of all 9 DSM and 9 DTM archives into the corresponding folders in
source_snapshot/data/raw/cedd/. Keep the original files in their existing location.
Then run from this working root, choosing a new analysis-output folder:

```bash
/private/tmp/svf-preprocess-env/bin/python scripts/prepare_cedd_rasters.py --source-project source_snapshot --work-dir analysis
```

The temporary Python environment is retained for continuation, not deleted as cache.
Its path is machine-specific. requirements-svf.txt documents how to rebuild it.

The script will write two mosaics and four clips into analysis/data/processed/.
It reports CRS, resolution, NoData, exact snapped extents and coverage, and requires
full valid coverage in both clips. DSM and DTM remain separate and grid-aligned.
Use acquisition rasters for SVF computation, then crop the SVF result to the core.

## Visual

figures/processing_overview.png shows actual indexed tile footprints and the
configured analysis boxes. It is a coverage/workflow illustration, not an
elevation map or computed pilot figure.
