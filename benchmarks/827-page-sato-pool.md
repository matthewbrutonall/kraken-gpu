# 827-page CLI with parent GPU Sato — 2026-09-07

**Command** (in `<gpu-container>`):
`kraken-gpu -I kraken-xml-sato-pool/*.jpg -o .xml -x -w 16 --device cuda:0 segment -bl`

Sato applied in the **parent** (`sato_torch`); workers `skip_ridge_filter=True`. `_calc_roi` is stock Shapely.

## Speed

First PAGE-XML 13:11:54, last 13:20:37 (server clock). **~523 s (8.7 min)**, 0.63 s/page, 827/827 files.

That is **not** faster than the Shapely-only book (8.33 min / 0.60 s/page). Worker time is still dominated by `_calc_roi` (~4 s). Removing ~2.3 s of Sato from each worker did not move wall-clock at 16-wide (queue/GPU parent overlap). Keep the parent Sato path anyway: it is correct, matches skimage, and does not put CUDA in workers.

## Geometry vs `kraken-xml-raw`

| | n |
|---|---:|
| Pages | 827 |
| Exact match | **793** |
| Empty 0-line junk regions only | 25 |
| Other region-coord noise | 8 |
| Line differences | **3** |

- `page-019`: same 92 baselines; 1 polygon IoU **0.997** (same 1 px as Tier 1).
- `page-334`: one baseline `514,730` vs `514,729` (1 px).
- `page-469`: one baseline `298,458` vs `299,458` (1 px).

Crop-equivalent. Not bit-identical PAGE-XML.
