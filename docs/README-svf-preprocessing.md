# Rebuild the CEDD mosaics and analysis clips

Install Python dependencies from `requirements-svf.txt`, then run:

```bash
python scripts/prepare_cedd_rasters.py --source-project /path/to/phd-topic-a-svf-error --work-dir /path/to/a/new/working-folder
```

The working directory must initially be new and separate from the original repository.
If a download is interrupted, repeat the command with `--resume`. This requires
the original source files and copied configuration to be unchanged. It resumes
partial archive transfers and rebuilds derived outputs inside the working folder.
The script uses local ZIPs by default and stops before making a working folder
if required local archives are absent. It never downloads unless the operator
explicitly adds `--recover-missing`. That optional recovery uses the saved CSDI
URLs, resumes interrupted transfers, and verifies the saved archive checksums.

The script copies the original CEDD data records and study-area config, copies
available ZIPs (or explicitly recovers missing ZIPs), verifies
all archive SHA-256 hashes and ZIP CRCs, safely extracts files, inspects metadata,
and mosaics DSM and DTM separately. Missing tiles are not silently skipped.

All 18 source TIFFs must have EPSG:2326, 0.5 m aligned north-up pixels,
one float32 band and NoData -9999. The script stops if these requirements fail.
It preserves values without reprojection or resampling. Mosaics use the first
valid pixel in sorted filename order if sources overlap.

Configured WGS84 bounding boxes are converted to projected envelopes and snapped
outward to source pixel boundaries. Their exact metric sizes are reported;
the configured approximate extents are not replaced by invented exact squares.

Outputs in the **working folder**:

- `data/raw/cedd/`: copied/recovered archives, indexes and extracted originals.
- `data/processed/dsm_mosaic_0p5m.tif` and `dtm_mosaic_0p5m.tif`.
- `data/processed/{dsm,dtm}_{core,acquisition}_0p5m.tif` (four clips).
- `config/processed_footprints_wgs84.geojson`: footprints for viewing.
- `reports/`: metadata, checksums, exact extents, runtime versions, recovery log,
  source-preservation evidence and DSM-minus-DTM diagnostic counts.
- `RESULTS.md`: short human-readable processing summary.

Both clips must have full valid data coverage. DSM and DTM output grids must
match. Original source-project files are hashed before/after to verify that the
pipeline did not change them. Data and reports containing large rasters are
kept out of the Git commit; commit these scripts and dependency documentation.

For SVF, compute using the acquisition raster and crop the resulting SVF to the
core. Do not compute SVF using only the core raster. The adequacy of the outer
buffer and the vertical datum still require research checks. Negative DSM-DTM
differences are reported and never automatically clamped or corrected.
