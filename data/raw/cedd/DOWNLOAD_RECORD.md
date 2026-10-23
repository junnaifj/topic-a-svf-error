# CEDD 2020 LiDAR DSM / DTM — download record

**Retrieval date:** 2026-10-23 (Asia/Shanghai)  
**Site:** Mong Kok, Hong Kong — acquisition bbox WGS84 `[114.16464, 22.31480, 114.17436, 22.32380]`  
**HK1980 (EPSG:2326) envelope used for tile select:** E 835007.5–836009.0, N 819534.7–820531.2

## Datasets

| Field | Value |
|---|---|
| Provider | Civil Engineering and Development Department (CEDD), Geotechnical Engineering Office |
| Product | Airborne LiDAR 2020 — Raster DSM and Raster DTM (by tile) |
| Survey | Helicopter LiDAR, 2019-12-20 to 2020-02-02 (per CSDI dataset abstract) |
| Stated / verified resolution | **0.5 m** (verified on extracted GeoTIFF with rasterio) |
| CRS | **EPSG:2326** (Hong Kong 1980 Grid) — verified |
| Pixel type | float32; nodata −9999 |
| Vertical units / datum | metres (elevation); vertical datum not embedded in sample GeoTIFF tags — treat as HK local orthometric pending official metadata PDF |
| Licence | Open government spatial data; commercial use and modification allowed with attribution (per GPXZ summary of Geodata Store terms; confirm against CEDD/CSDI Terms of Use when publishing) |
| CSDI dataset | https://portal.csdi.gov.hk/csdi-webpage/dataset/cedd_rcd_1629267205233_87895 |

## How tiles were selected (no geodata.gov.hk)

`geodata.gov.hk` DNS/TLS failed from the research box and the user’s Mac on 2026-10-23.

Instead:

1. Queried Esri China (HK) ArcGIS Online **FeatureServer** layers with an EPSG:2326 envelope intersecting the acquisition bbox:
   - DSM: `https://services3.arcgis.com/6j1KwZfY2fZrfNMR/arcgis/rest/services/Digital_Surface_Model_from_2020_LiDAR_Survey/FeatureServer/0`
   - DTM: `https://services3.arcgis.com/6j1KwZfY2fZrfNMR/arcgis/rest/services/Digital_Terrain_Model_from_2020_LiDAR_Survey/FeatureServer/0`
2. Saved filtered GeoJSON indexes under `indexes/dsm_mongkok.geojson` and `indexes/dtm_mongkok.geojson` (9 features each).
3. Downloaded each feature’s `properties.URL` from `https://bulkdata.csdi.gov.hk/cedd/lidar/2020dsm/` and `.../2020dtm/` with a ~3 s delay between requests.

## Tiles downloaded (9 DSM + 9 DTM)

Same TILE_NAME set for DSM and DTM:

| TILE_NAME | Filename pattern |
|---|---|
| 11NW14C | `11NW14C(e834n820,e835n821).zip` |
| 11NW14D | `11NW14D(e835n820,e836n821).zip` |
| 11NW15C | `11NW15C(e836n820,e836n821).zip` |
| 11NW19A | `11NW19A(e834n819,e835n820).zip` |
| 11NW19B | `11NW19B(e835n819,e836n820).zip` |
| 11NW19C | `11NW19C(e834n819,e835n819).zip` |
| 11NW19D | `11NW19D(e835n819,e836n819).zip` |
| 11NW20A | `11NW20A(e836n819,e836n820).zip` |
| 11NW20C | `11NW20C(e836n819,e836n819).zip` |

- Local folders: `dsm/` (~52 MB), `dtm/` (~49 MB)
- Each ZIP contains one GeoTIFF of the same basename (e.g. `11NW19B(e835n819,e836n820).tif`, ~7.9 MB uncompressed for the core tile).
- Sample inspect extract (core tile 11NW19B): 1500×1200 pixels, 0.5 m, bounds E 835250–836000 / N 819800–820400.

## Checksums

See `SHA256SUMS.txt` in this directory (18 ZIP files). Checksums completed on the box on 2026-10-23.

## Do not commit rasters to GitHub

Keep original ZIPs / GeoTIFFs local only. Commit only indexes, this record, and `data/acquisition_log.csv`.
