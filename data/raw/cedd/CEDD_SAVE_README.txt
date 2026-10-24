CEDD 2020 LiDAR DSM/DTM tiles for Topic A (Mong Kok pilot)

Save location (outside iCloud):
  ~/Downloads/phd-topic-a-svf-working-20261024/data/raw/cedd/

Put DSM ZIPs in:  .../cedd/dsm/
Put DTM ZIPs in:  .../cedd/dtm/
Checksums:        .../cedd/SHA256SUMS.txt  (already there; overwrite with this copy if needed)

Filenames must match SHA256SUMS exactly, e.g.
  11NW14C(e834n820,e835n821).zip

Then unzip each into:
  .../cedd/extracted/dsm/<stem>/
  .../cedd/extracted/dtm/<stem>/

Verify:  shasum -a 256 -c SHA256SUMS.txt
