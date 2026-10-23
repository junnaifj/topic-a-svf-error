# Topic A: elevation and 3D geometry effects on sky view factor

## Research question

How do elevation-grid resolution and 3D city-model geometry or
level-of-detail differences affect sky view factor (SVF), and potentially shade?

SVF describes how much of the sky is visible from a location.
Buildings, terrain and vegetation can obstruct that view.

## Current stage

**Round 2 (data acquisition) complete as of 23 Oct 2026.**
Study area fixed (Mong Kok); CEDD 2020 DSM/DTM 0.5 m tiles acquired (held off this Mac until iCloud space allows); LandsD 3D-BIT00 blocked at OneStopSystem.
No SVF results have been produced yet — that is Round 3+.

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

These are provisional geographic rectangles.
Visual inspection, data coverage and exact metric dimensions remain to be checked.
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
Software setup is pending.

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

Inspect the acquired raster and prepare:
notebooks/01_dem_resample_compare.ipynb

This first notebook will compare elevation grids.
It will not yet calculate SVF.

## Data licensing

Source data retain their providers' terms.
Check redistribution permission before publishing any data sample.
