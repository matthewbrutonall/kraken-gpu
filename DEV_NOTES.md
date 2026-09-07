# Development notes

Technical record for this project. Local machine layout and session pickup
live in untracked `MEMORY.md` (gitignored).

## What this is

Faster **page segmentation** with the same default BLLA crops. The neural net
already runs on GPU; the wait is CPU geometry after the heatmap.

Shipped:

1. Page-level process pool in `kraken-gpu segment` (`-w` workers; `--threads` is OpenMP).
2. Parent-only GPU Sato (`sato_torch` matches skimage). Workers skip the ridge
   filter. No CUDA in worker processes.
3. `_calc_roi` is still stock Shapely: `unary_union(...).buffer(1).boundary`.

`-w > 1` is the **default single-model BLLA path only** (one segmentation
model, polygonal reading order). Multiple segmentation models or a neural
reading-order model require `-w 1`.

## Profile (printed p.297, 1310×1730, 55 lines)

Serial: **7.27 s**. GPU map 0.093 s (1.3%). `vec_lines` 7.0 s.

| Function | Cum. s |
|---|---:|
| `calculate_polygonal_environment` | 4.82 |
| `_calc_roi` | 4.00 |
| `_calc_seam` | 0.75 |
| `vectorize_lines` (Sato + skeleton) | 3.90 |
| skimage Sato / gaussian | 2.31 |

Full dump: `benchmarks/profile-blla-p297.md`.

## 827-page book

| Run | wall |
|---|---:|
| Serial | ~114 min |
| `-w 16` | **8.33 min** |
| `-w 16` + parent Sato | **8.7 min** |

Crop-equivalent vs serial PAGE-XML, not bit-identical (793/827 exact on the
Sato run; remaining diffs empty junk regions or 1 px). Receipts in
`benchmarks/`.

Parent Sato did not move book wall-clock: `_calc_roi` still dominates.

## Remaining work

`_calc_roi`. Keep union-then-buffer or prove 1.0 IoU / 55/55 on p.297. No
CUDA in workers.

## Rejected approaches (do not revive)

- **Numpy/linspace hit-test `_calc_roi`:** 7.27s → 4.86s; 29/55 polygons moved
  (min IoU 0.86). 4-neighbour hit test is not Shapely `buffer(1)`.
- **`sato_pytorch` inside `vectorize_lines`:** faster, 12/55 baselines drifted,
  CUDA from the worker pool.
- **STRtree + per-line `buffer(1)`:** 7.27s → 8.81s (`_calc_roi` 4.0s → 7.2s),
  54/55 polygons. Closest-point must be on the **union** boundary.
- **Numpy argmin for MultiPoint closest-point:** 7.26s → 8.11s.
- **Seam-carve CUDA first:** `_calc_seam` is 0.75 s. Not the bottleneck.
- **Watershed / Voronoi rewrite of ROI:** different shape; will fail crop identity.
