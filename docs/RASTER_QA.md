# CEDD 2020 raster QA

Overall status: **PASS**.

Reproduce: `.venv/bin/python scripts/prepare_cedd_rasters.py`.
Exit code 1 means an acceptance check failed; negative DSM−DTM values alone do not cause failure.

## Decisions and interpretation

- Input tile bounds differ by location; metadata, dimensions and pixel-grid alignment must match. Corresponding DSM/DTM tile bounds must be identical.
- No reprojection or resolution change is performed. rasterio.merge combines matching native grids; clips use outward-rounded integer pixel windows.
- Projected envelopes in config are authoritative; retained WGS84 boxes document the original approximate selection.
- nDSM is DSM − DTM with negative valid values clamped to zero. Original DSM/DTM and strict sanity checks remain unchanged.
- Acceptance threshold: DSM ≥ DTM − 0.3 m for strictly >99% of jointly valid core pixels. Strict DSM ≥ DTM is informational only. Negative percentiles are conditional on negative differences; percentages below −0.3 m use all jointly valid pixels.
- Vertical datum and accuracy have not been independently verified; matching horizontal grids do not establish either.
- Source NoData retained unchanged: -9999.0.

## Output rasters

| Output | CRS | Pixel m | Shape (rows × columns) | NoData % | Elevation min / max / mean (m) | MiB |
|---|---|---|---|---:|---|---:|
| dsm_mosaic | EPSG:2326 | 0.5 × 0.5 | 3600 × 4500 | 0.223630 | -7.044 / 260.316 / 25.601 | 56.046 |
| dsm_acq | EPSG:2326 | 0.5 × 0.5 | 1994 × 2004 | 0.000000 | -7.044 / 260.316 / 23.679 | 14.087 |
| dsm_core | EPSG:2326 | 0.5 × 0.5 | 998 × 1003 | 0.000000 | 3.426 / 260.316 / 25.551 | 3.560 |
| dtm_mosaic | EPSG:2326 | 0.5 × 0.5 | 3600 × 4500 | 0.223630 | -2.669 / 69.206 / 13.356 | 42.935 |
| dtm_acq | EPSG:2326 | 0.5 × 0.5 | 1994 × 2004 | 0.000000 | -2.383 / 40.304 / 7.622 | 10.178 |
| dtm_core | EPSG:2326 | 0.5 × 0.5 | 998 × 1003 | 0.000000 | 3.351 / 7.364 / 5.127 | 2.426 |
| ndsm_acq | EPSG:2326 | 0.5 × 0.5 | 1994 × 2004 | 0.000000 | 0.000 / 255.323 / 16.059 | 13.904 |
| ndsm_core | EPSG:2326 | 0.5 × 0.5 | 998 × 1003 | 0.000000 | 0.000 / 255.323 / 20.427 | 3.670 |

## DSM/DTM checks

| Extent | Same grid | DSM ≥ DTM % (informational) | DSM ≥ DTM − 0.3 m % | Below −0.3 m % | Negative pixels / nDSM clamp count |
|---|---|---:|---:|---:|---:|
| mosaic | True | 88.960256 | 99.951818 | 0.048182 | 1784439 |
| acq | True | 91.686136 | 99.983133 | 0.016867 | 332220 |
| core | True | 88.318811 | 99.995205 | 0.004795 | 116928 |

Only the core tolerant check is an acceptance gate. Mosaic has no nDSM output; its negative count is informational.

## Negative difference distribution

Percentiles are conditional on DSM − DTM < 0; units are metres.

| Extent | p0 | p1 | p5 | p25 | p50 | p75 | p95 | p99 | p100 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| mosaic | -48.549149 | -0.082888 | -0.049849 | -0.025211 | -0.013262 | -0.005580 | -0.000950 | -0.000174 | -0.000000 |
| acq | -13.104218 | -0.075456 | -0.050214 | -0.025709 | -0.013447 | -0.005548 | -0.000909 | -0.000164 | -0.000000 |
| core | -1.532138 | -0.070790 | -0.050388 | -0.026566 | -0.014022 | -0.005851 | -0.000995 | -0.000186 | -0.000000 |

## Automated checks

| Check | Result |
|---|---|
| input_metadata_consistent | PASS |
| mosaic_grid_match | PASS |
| acq_grid_match | PASS |
| core_grid_match | PASS |
| core_dsm_ge_dtm_minus_0p3_over_99_percent | PASS |
| dsm_mosaic_raster_metadata | PASS |
| dsm_acq_raster_metadata | PASS |
| dsm_acq_complete_coverage | PASS |
| dsm_core_raster_metadata | PASS |
| dsm_core_complete_coverage | PASS |
| dtm_mosaic_raster_metadata | PASS |
| dtm_acq_raster_metadata | PASS |
| dtm_acq_complete_coverage | PASS |
| dtm_core_raster_metadata | PASS |
| dtm_core_complete_coverage | PASS |
| ndsm_acq_raster_metadata | PASS |
| ndsm_acq_complete_coverage | PASS |
| ndsm_core_raster_metadata | PASS |
| ndsm_core_complete_coverage | PASS |
| raw_tiff_sha256_unchanged | PASS |

## Snapped envelopes (EPSG:2326)

Order: [minx, miny, maxx, maxy].

- acq: requested `[835007.46, 819534.61, 836008.96, 820531.27]`; snapped `[835007.0, 819534.5, 836009.0, 820531.5]`; dimensions `1002.0 × 997.0 m`.
- core: requested `[835257.85, 819783.77, 835758.59, 820282.1]`; snapped `[835257.5, 819783.5, 835759.0, 820282.5]`; dimensions `501.5 × 499.0 m`.

## Input inventory

| Layer / tile | CRS | Pixel m | Shape | Dtype | NoData | Bounds [minx, miny, maxx, maxy] |
|---|---|---|---|---|---|---|
| dsm / 11NW14C | EPSG:2326 | [0.5, 0.5] | [1200, 1500] | float32 | -9999.0 | [834500.0, 820400.0, 835250.0, 821000.0] |
| dsm / 11NW14D | EPSG:2326 | [0.5, 0.5] | [1200, 1500] | float32 | -9999.0 | [835250.0, 820400.0, 836000.0, 821000.0] |
| dsm / 11NW15C | EPSG:2326 | [0.5, 0.5] | [1200, 1500] | float32 | -9999.0 | [836000.0, 820400.0, 836750.0, 821000.0] |
| dsm / 11NW19A | EPSG:2326 | [0.5, 0.5] | [1200, 1500] | float32 | -9999.0 | [834500.0, 819800.0, 835250.0, 820400.0] |
| dsm / 11NW19B | EPSG:2326 | [0.5, 0.5] | [1200, 1500] | float32 | -9999.0 | [835250.0, 819800.0, 836000.0, 820400.0] |
| dsm / 11NW19C | EPSG:2326 | [0.5, 0.5] | [1200, 1500] | float32 | -9999.0 | [834500.0, 819200.0, 835250.0, 819800.0] |
| dsm / 11NW19D | EPSG:2326 | [0.5, 0.5] | [1200, 1500] | float32 | -9999.0 | [835250.0, 819200.0, 836000.0, 819800.0] |
| dsm / 11NW20A | EPSG:2326 | [0.5, 0.5] | [1200, 1500] | float32 | -9999.0 | [836000.0, 819800.0, 836750.0, 820400.0] |
| dsm / 11NW20C | EPSG:2326 | [0.5, 0.5] | [1200, 1500] | float32 | -9999.0 | [836000.0, 819200.0, 836750.0, 819800.0] |
| dtm / 11NW14C | EPSG:2326 | [0.5, 0.5] | [1200, 1500] | float32 | -9999.0 | [834500.0, 820400.0, 835250.0, 821000.0] |
| dtm / 11NW14D | EPSG:2326 | [0.5, 0.5] | [1200, 1500] | float32 | -9999.0 | [835250.0, 820400.0, 836000.0, 821000.0] |
| dtm / 11NW15C | EPSG:2326 | [0.5, 0.5] | [1200, 1500] | float32 | -9999.0 | [836000.0, 820400.0, 836750.0, 821000.0] |
| dtm / 11NW19A | EPSG:2326 | [0.5, 0.5] | [1200, 1500] | float32 | -9999.0 | [834500.0, 819800.0, 835250.0, 820400.0] |
| dtm / 11NW19B | EPSG:2326 | [0.5, 0.5] | [1200, 1500] | float32 | -9999.0 | [835250.0, 819800.0, 836000.0, 820400.0] |
| dtm / 11NW19C | EPSG:2326 | [0.5, 0.5] | [1200, 1500] | float32 | -9999.0 | [834500.0, 819200.0, 835250.0, 819800.0] |
| dtm / 11NW19D | EPSG:2326 | [0.5, 0.5] | [1200, 1500] | float32 | -9999.0 | [835250.0, 819200.0, 836000.0, 819800.0] |
| dtm / 11NW20A | EPSG:2326 | [0.5, 0.5] | [1200, 1500] | float32 | -9999.0 | [836000.0, 819800.0, 836750.0, 820400.0] |
| dtm / 11NW20C | EPSG:2326 | [0.5, 0.5] | [1200, 1500] | float32 | -9999.0 | [836000.0, 819200.0, 836750.0, 819800.0] |

## Samples

- `data/sample/cedd2020_dsm_core_0p5m.tif`: 3.560 MiB (copy of full core (<10 MB decimal)).
- `data/sample/cedd2020_dtm_core_0p5m.tif`: 2.426 MiB (copy of full core (<10 MB decimal)).

## Failures

None.
