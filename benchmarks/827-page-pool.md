# 827-page Tier 1 pool run — 2026-09-07

**Where:** `<gpu-container>`, Kraken 7.0.1 `blla.mlmodel`, `-w 16`.
**Out:** `<benchmark-output-dir>` (827 PAGE-XML, 33 MB, same as `kraken-xml-raw`).
**Full compare log:** `benchmarks/827-page-pool-compare.txt`.

## Speed

XML flush burst at 10:51:53–10:51:58 (server clock). Parent pid 4723 started ~14:43 (container clock, UTC). Watcher measured the last **307 s**; first look already had workers at ~80 s CPU. **Whole-book wall-clock ~8 minutes.**

Serial baseline on this book was **~114 min** (~8.3 s/page).  
**~14×** with 16 pinned CPU workers. Target was ≤15 min.

GPU: ~2.8 GB reserved, **0% util** during the run (CPU geometry). Idle afterwards (15 MiB).

## Geometry vs `kraken-xml-raw`

| | n |
|---|---:|
| Pages | 827 |
| Exact match (baselines + polygons + regions) | **794** (96.0%) |
| Region-only mismatch | 33 |
| … of which empty 0-line junk regions only | 26 |
| Text-line mismatch | **1** (`page-019.xml`) |

`page-019`: 92/92 lines, **same baseline** `171,31 222,32`. One polygon differs by 1 px (`171,4`/`175,2` vs `171,5`/`176,2`). Not a crop regression.

`page-294` (and the other empty-region diffs): 0-line corner artefacts, same class as the 10-page note. Text lines match.

## Caveats

- XML is written only after the GPU producer finishes queueing; a crash would have lost the book. Next revision should write each page as it completes.
- Leftover defunct python3 workers and `<tmp-prefix>*` remain in the celery-gpu container.
- Compare ignores reading-order element IDs (UUIDs). Baselines+polygons are what matter for crops.
