# Technical background — why Kraken segmentation is slow

## The two stages of Kraken `blla`

Kraken's baseline-layout-analysis (`blla`) segmentation is two very different stages:

### Stage 1 — neural inference (GPU, already fast)
A fully-convolutional model (U-Net-style, defined in Kraken's VGSL spec; default `blla.mlmodel`)
takes the page image and outputs dense **heatmaps**: one channel bundle for baselines, others for
region classes. This runs on the GPU in a burst. On the test box it holds ~2.8 GB VRAM and finishes
a page in a fraction of a second.

**This stage is not the problem.** During a full-book run the GPU sits at **0 % utilisation** almost
the whole time — the bursts are tiny relative to stage 2.

### Stage 2 — geometry post-processing (CPU, the bottleneck)
Turning heatmaps into usable line geometry is pure CPU work (NumPy / SciPy / scikit-image / Shapely),
largely **sequential per line**, and it dominates runtime (~8.3 s/page on the test book).

Key functions in `kraken/lib/segmentation.py` (Kraken 7.0.1):

| Function (approx line) | What it does | Cost |
|---|---|---|
| `vectorize_lines` (313) | threshold + skeletonise + trace the baseline heatmap into polylines | moderate |
| **`calculate_polygonal_environment` (744)** | for **each** baseline, seam-carve a tight boundary polygon (distance transforms, cost maps, path finding) | **dominant** |
| `compute_polygon_section` (1158) | slice/refine polygon sections along a baseline | moderate |
| `scale_polygonal_lines` (1066) | rescale geometry back to image coords | cheap |
| `_bevelled_warping_envelope` (1331) | envelope used for line dewarping/extraction | moderate |

Entry point that orchestrates both stages: `kraken/blla.py` → `segment()`.

## Why the polygon step is what makes Kraken *good*

`calculate_polygonal_environment` is exactly why Kraken's line crops are **tight and precise** — each
line gets a boundary polygon that hugs its ink and excludes neighbours. That precision is what made
Kraken beat Surya on crop cleanliness in the 12-page pre-test (`Waræo` vs Surya's `Ivaræo`; Surya's
bbox→baseline crops pulled in neighbouring ink and even the `Diuzed oy Coogle` watermark).

**So Kraken's slowness and Kraken's crop quality are the same feature.** Surya is fast because its
detector emits bounding boxes straight off the GPU with almost no post-processing — cheaper, but
looser. Any speed-up plan must preserve the precise polygons, or it stops being Kraken.

## Why this parallelises well (tier 1)

Stage 2 is **per-page independent** and **per-line independent within a page**. There is no
cross-page state. So the cheapest large win is data-parallelism: run many pages at once across the
16-core / 32-thread CPU. Expected ~10× (≈2 hrs → ≈10–15 min) with no algorithmic change and no
quality change.

**Gotcha:** each Kraken/torch worker will try to use all cores for its own NumPy/torch ops. Running
16 workers each spawning 32 threads oversubscribes badly. Pin threads per worker
(`OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, `torch.set_num_threads(1)`) and let the pool provide the
parallelism. Also: stage-1 neural inference wants the GPU — either (a) run stage 1 batched on GPU
once, then fan out stage 2 across CPU workers (cleanest), or (b) share the GPU carefully if workers
each do their own inference (risk of VRAM contention).

## Why the GPU port is hard (tier 2)

Moving stage 2 to the GPU is uneven:
- **Tractable:** distance transforms, morphology, thresholding, connected components — all have
  CuPy / Torch equivalents and vectorise across the whole page.
- **Hard:** the per-line seam-carving / path-finding in `calculate_polygonal_environment` is
  sequential and data-dependent. Options: batch it across all lines of a page as independent
  problems on the GPU; or reformulate the boundary as a differentiable/parallel operation. This is
  the genuine research risk and the part that, done well, is the real gift to the community.

## Measure before building
Before writing any code, run `cProfile` on `blla.segment` for one representative page on the box to
confirm the breakdown above and get real percentages. The functions listed are the strong suspects,
but a profile removes all guesswork and gives a baseline to beat. See `ROADMAP.md` step 1.
