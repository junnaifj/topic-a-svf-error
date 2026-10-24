# Topic A: elevation and 3D geometry effects on sky view factor

## Research question

How do elevation-grid resolution and 3D city-model geometry or
level-of-detail differences affect sky view factor (SVF), and potentially shade?

SVF describes how much of the sky is visible from a location.
Buildings, terrain and vegetation can obstruct that view.

## Status

Round 3 data are prepared: local CEDD 2020 DSM/DTM mosaics, acquisition/core
clips, nDSM and small samples have been generated. All acceptance checks pass.
DSM ≥ DTM − 0.3 m for **99.99520%** of valid core pixels (required >99%).
There are **48 core pixels below −0.3 m**, mapped in the QA figure. Strict
DSM ≥ DTM and the full negative-difference distribution are reported without
being acceptance gates. nDSM negatives alone are clamped to zero and counted.
No SVF has been calculated.

Reproduce rasters, reports and the figure with one command from this repo:

```bash
.venv/bin/python scripts/prepare_cedd_rasters.py
```

The command exits 0 if acceptance checks pass, or 1 on failure. See
[raster QA](docs/RASTER_QA.md), [machine-readable QA](reports/raster_qa.json)
and [overview figure](figures/qa_overview.png).

For a fresh checkout, place the 18 extracted source GeoTIFFs under
`data/raw/cedd/extracted/{dsm,dtm}/<tile>/`, then create the environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-svf.txt
```

Raw data, processed rasters and sample TIFFs stay local under the publishing
safeguard that excludes all ZIP and TIFF files. The script never writes to
`data/raw`; it verifies source TIFF SHA-256 hashes before and after processing.

## Pilot target

Prepare a reproducible pilot figure by 13 November 2026:

- a: reference SVF map
- b: SVF difference map for one degraded input
- c: SVF error against input resolution
- d: changes in membership of the lowest-SVF 10% of street points

If progress is behind on 6 November, reduce the scope to one area,
SVF only, three inputs and panels a–c.

## Proposed study area

Mong Kok, Hong Kong.

Coordinate system: WGS84, EPSG:4326.
Bounding-box order: [west longitude, south latitude, east longitude, north latitude].

Acquisition area, approximately 1 km × 1 km:

[114.16464, 22.31480, 114.17436, 22.32380]

Core analysis area, approximately 500 m × 500 m:

[114.16707, 22.31705, 114.17193, 22.32155]

These geographic rectangles record the original approximate selection.
The authoritative EPSG:2326 envelopes are in `config/study_area.json`;
processing snaps them outward to native pixel edges (see the QA report).
The surrounding acquisition area supplies context for buildings outside the core.
The final SVF buffer distance will require checking.

## Proposed data

- CEDD LiDAR-derived DSM: candidate surface reference
- DTM / terrain: ground elevations
- LandsD 3D-BIT00: candidate building geometry and terrain
- Optional coarse elevation product for comparison

Native resolution, survey dates, coordinate systems, vertical datums,
geometry classes and licences must be verified before analysis.

## Planned tools

Python, Jupyter, pandas, matplotlib, rasterio/GDAL and QGIS/UMEP.
The raster-preparation Python environment is installed in `.venv/`.

## Data sources

- CEDD LiDAR information:
  https://www.ginfo.cedd.gov.hk/geoopendata/eng/LIDAR.aspx
- CEDD Spatial Data Portal:
  https://sdportal.cedd.gov.hk/
- LandsD open geospatial data:
  https://www.landsd.gov.hk/en/spatial-data/open-data.html
- CSDI Portal:
  https://portal.csdi.gov.hk/
- 3D Spatial Data API documentation:
  https://portal.csdi.gov.hk/csdi-webpage/apidoc/3d-spatial-data-api

## Project folders

- data/raw/: original downloads, stored locally
- data/processed/: derived datasets, stored locally
- data/sample/: small examples only if redistribution is permitted
- notebooks/: analysis notebooks
- figures/: exported figures

See data/README.md for acquisition status and licence notes.

## Method notes

A terrain-only elevation model omits the buildings needed for street-canyon SVF.

A DSM includes above-ground surfaces such as roofs and vegetation.
A DTM represents terrain, subject to the provider's product definition.

Resampling one DSM tests resolution sensitivity.
Comparing separate products may also introduce differences in survey date,
vegetation, geometry and processing.

Upsampling a coarse raster does not restore missing fine detail.
The reference DSM is not error-free ground truth.

## Next step

Review the mapped 48 core outliers before interpreting local height differences.
Then prepare `notebooks/01_dem_resample_compare.ipynb`.

This first notebook will compare elevation grids.
It will not yet calculate SVF.

## Data licensing

Source data retain their providers' terms.
Check redistribution permission before publishing any data sample.
