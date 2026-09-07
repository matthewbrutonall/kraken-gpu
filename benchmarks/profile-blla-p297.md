# Profile note — Hibernia Dominicana printed p.297

**When:** 2026-09-07. **Where:** `<gpu-container>`, Kraken 7.0.1, RTX 5070 Ti.
**Page:** `<benchmark-image>` — 1310×1730 RGB, 55 lines, 3 regions.
**Raw dump:** `benchmarks/profile-blla-p297.txt`.

## Wall-clock split (after GPU warmup, serial)

| Stage | Seconds | Share |
|---|---:|---:|
| GPU `compute_segmentation_map` | 0.093 | 1.3% |
| CPU `vec_regions` | 0.137 | 1.9% |
| CPU `vec_lines` | 7.036 | 96.8% |
| CPU reading order | 0.004 | ~0% |
| **Total** | **7.270** | 100% |

GPU is not the bottleneck. VRAM after warmup: 5 MB allocated / 1.4 GB reserved. Full `blla.segment` with cProfile overhead: 9.05 s (55 lines).

## Inside `vec_lines` (cProfile cumulative)

The old assumption that `calculate_polygonal_environment` (seam-carve) dominates is **only half true**.

| Function | Cum. s | What it is |
|---|---:|---|
| `vec_lines` | 8.76 | whole CPU geometry |
| `calculate_polygonal_environment` (55×) | 4.82 | per-line polygons |
| `_calc_roi` | 4.00 | Shapely ray-cast vs other baselines |
| `_calc_seam` | 0.75 | seam-carve DP (the thing we thought was the cost) |
| `vectorize_lines` | 3.90 | heatmap → baselines |
| `skimage.filters.sato` / `gaussian_filter` | 2.31 | ridge filter on the whole page |
| `boundary_tracing` + `_extend_boundaries` | ~1.5 + 1.4 | skeleton trace |

So on this page:

- **~53%** of `vec_lines` is polygonisation, almost all of it `_calc_roi` (Shapely), not `_calc_seam`.
- **~43%** is `vectorize_lines` (Sato + tracing), which is **whole-page sequential**, not per-line.

## Consequence for Tier 1

Threading only the per-baseline loop in `vec_lines` can attack the ~4.8 s polygon part. It cannot touch the ~3.9 s Sato/trace. Best case on this page: ~7.3 s → ~4 s (~1.8×), not ~10×.

A **page-level** pool still gets the full ~10× on a book, because both halves are independent across pages. Intra-page threads are a bonus on top, not a substitute.

## Consequence for Tier 2

Do not start by CUDA-porting the seam-carve DP. On this page it is 0.75 s. The GPU-worthy CPU costs are Sato/gaussian (`vectorize_lines`) and Shapely `_calc_roi`.
