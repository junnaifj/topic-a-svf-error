# Topic A pilot — data folder

**Updated:** 2026-10-23 (Asia/Shanghai)

## Status summary

| Layer | Status | Verified resolution | Survey | Notes |
|---|---|---|---|---|
| CEDD DSM 2020 | Downloaded (9 tiles) — **files held off this Mac** | **0.5 m** | 2019–2020 helicopter LiDAR | EPSG:2326; see `raw/cedd/DOWNLOAD_RECORD.md` |
| CEDD DTM 2020 | Downloaded (9 tiles) — **files held off this Mac** | **0.5 m** | 2019–2020 helicopter LiDAR | Same tile set as DSM |
| LandsD 3D-BIT00 | Blocked / partial probe | — | — | OneStopSystem; Cesium tileset probe only |

Tile names: `11NW14C`, `11NW14D`, `11NW15C`, `11NW19A`, `11NW19B`, `11NW19C`, `11NW19D`, `11NW20A`, `11NW20C`.

## Why rasters are not in this folder yet

iCloud Drive storage for `Documents` is full. Large ZIPs (~101 MB) stay with the research assistant until copied into a **non-iCloud** path (or after iCloud space is freed). Indexes + SHA-256 lists are committed; original ZIPs must **not** go to GitHub.

## Layout

```text
data/
  acquisition_log.csv
  README.md
  raw/
    cedd/          # DOWNLOAD_RECORD, SHA256SUMS, indexes; dsm/ dtm/ for local ZIPs
    landsd/        # DOWNLOAD_RECORD + tileset probe JSON
  processed/       # derived clips later
  sample/          # small shareable clip pending
```

## Pending (not Round 2 blockers)

- Local ZIP copy into `raw/cedd/dsm` and `dtm`
- Small clipped sample
- Resampling notebook
- Analysis-ready buildings
