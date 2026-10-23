# LandsD 3D-BIT00 — download / blocker record

**Attempt date:** 2026-10-23 (Asia/Shanghai)  
**Target:** Building geometry for Mong Kok acquisition bbox (same as CEDD tiles)

## What was attempted

1. **CSDI dataset page** — https://portal.csdi.gov.hk/csdi-webpage/dataset/landsd_rcd_1637306559892_42396  
   Describes Building (Level 1/2/3), Infrastructure, and Terrain TIN products.

2. **data.gov.hk listing** — https://data.gov.hk/en-data/dataset/hk-landsd-openmap-development-hkms-digital-3d-bit00  
   Lists native formats Max / 3ds / FBX / VRML. Resource links point to **HK Map Service OneStopSystem** (`product=OSSCatB&series=3D-BIT00`), not a direct open ZIP of Mong Kok tiles.

3. **3D Spatial Data API** (Cesium 3D Tiles, WGS84) — documented at https://portal.csdi.gov.hk/csdi-webpage/apidoc/3d-spatial-data-api  
   - Example URL pattern requires `?key=...`.
   - On 2026-10-23, `building/tileset.json` returned **HTTP 200** both with the documented example key and without a key.
   - Saved probe file: `tileset_building_examplekey.json` (17 383 bytes).
   - A sample child content URI (`Data/F_Tile_+4_4_0/...json`) also returned HTTP 200 without a key.
   - **However:** this API serves **streaming Cesium 3D Tiles** (meshes), not analysis-ready extruded footprints / LoD1–3 GeoPackages. `tileset.json` alone is **not** complete building geometry for the SVF pilot.

## Status (honest)

| Product | Status |
|---|---|
| Native 3D-BIT00 packages (Max/3ds/FBX/VRML) | **Blocked for CLI open download** — routed through HK Map Service OneStopSystem (account / product request). |
| Cesium 3D Tiles API | **Reachable** (tileset + sample child JSON). Full Mong Kok tile tree **not** bulk-downloaded; format not yet converted to analysis-ready LoD layers. |
| Analysis-ready Level 1 footprints for Mong Kok | **Not obtained** tonight. |

## Next actions (for parent / user)

- Option A: Register on HK Map Service and request 3D-BIT00 sheets covering Mong Kok (OSS Cat B).
- Option B: Write a Cesium 3D Tiles → footprint/height extractor for the building tileset (non-trivial; Week 2+).
- Option C: Use building footprints from another open LandsD product (e.g. B1000 / building outline open data) plus DSM heights as an interim LoD1 proxy — document clearly if used.

## Checksum

See `SHA256SUMS.txt` for `tileset_building_examplekey.json`.
