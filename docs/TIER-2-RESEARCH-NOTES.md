# Tier 2 research notes (historical)

**As of 2026-09-07:** parent GPU Sato is done and matches skimage. It did not
move 827-page wall-clock. The remaining cost is `_calc_roi` (stock Shapely
`unary_union(...).buffer(1).boundary`). Do **not** start with seam-carve CUDA
(`_calc_seam` is 0.75 s on p.297) or a watershed/Voronoi rewrite (it will not
match Kraken crops). Rejected attempts: `MEMORY.md`.

The notes below are the original analysis of `calculate_polygonal_environment`
and its helpers (`_calc_roi`, `_extract_patch`, `_calc_seam`).

## Why it is CPU-bound and slow

For **every single baseline** (which means hundreds of times per page), the code does:
1. **Ray casting (Shapely):** `_calc_roi` casts orthogonal rays from sampled points along the baseline and intersects them against all other baselines to find upper and lower bounding limits. This uses Shapely `intersects` heavily in a python loop.
2. **Patch Extraction & Rotation:** `_calc_seam` extracts the region of interest (ROI) from the feature map (`im_feats`, basically a gaussian-blurred Sobel map), applies a distance transform (`distance_transform_cdt`) from the baseline to bias the features, and then rotates the patch using `skimage.transform.warp` so the baseline is horizontal.
3. **Seam Carving (Dynamic Programming):** A python `for` loop calculates the minimum energy path (seam) from left to right through the rotated patch using dynamic programming (`A[i].min(1, T)`, `B[i] += T`).

## Tier 2 Strategies (GPU)

### 1. The Seam Carving DP
Dynamic programming is inherently sequential along the sequence dimension (x-axis), making it hard to parallelize *within* a single line. However:
- **Batching across lines:** We can extract and rotate all patches for all lines, pad them to a maximum width/height, and process the DP across all lines simultaneously as a tensor batch `(N, C, R)`.
- **Custom CUDA kernel:** A CuPy `RawKernel` or a Numba CUDA kernel can do the DP extremely fast. Each GPU block/thread can handle one line independently.

### 2. Reformulating `_calc_roi` (Ray Casting)
Instead of using Shapely to intersect polygons line-by-line:
- **Global Watershed / Voronoi:** Draw all baselines onto a blank GPU tensor. Use a GPU-accelerated Distance Transform (`cupyx.scipy.ndimage.distance_transform_edt`) and Watershed to partition the image into N regions (one per baseline). The watershed boundaries naturally define the non-overlapping ROIs for all lines simultaneously without any ray casting.

### 3. Alternative: Global Cost Volume
Instead of rotating individual patches and doing 1D seam carving, we can compute the cost of assigning each pixel to each baseline using a distance metric, and resolve the boundary globally. If we must match Kraken's exact crops (the guardrail), we should implement the batched DP approach or ensure the watershed approach produces an identical IoU.

**Next Steps for Tier 2:**
- Write a CuPy prototype for the batched seam carving DP to see the speedup.
- Test if a whole-page distance transform + watershed yields the same boundaries as the Shapely ray-casting `_calc_roi`.
