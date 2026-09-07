# kraken-gpu

Faster **page segmentation** with the same default BLLA line crops. Apache-2.0.

This is an independent fork, published as `kraken-gpu`. It is not the upstream
Kraken project and should not be presented as such.

This is **crops on N CPU cores**, not a GPU geometry engine. The neural net
(and parent-only Sato) run on GPU; polygons are still stock Shapely.

## What shipped

1. Many pages at once (`-w` workers) inside `kraken-gpu segment`.
2. Skimage-matching Sato on the GPU in the **parent** process; workers skip
   the ridge filter. No CUDA in workers.
3. `_calc_roi` left as stock Shapely
   (`unary_union(...).buffer(1).boundary`).

`-w > 1` is the **default single-model BLLA path** (one segmentation model,
polygonal reading order). Multiple segmentation models or a neural
reading-order model stay on `-w 1`.

On an 827-page book (RTX 5070 Ti, Ryzen 9 9950X, 16 cores):

| Run | wall | notes |
|---|---:|---|
| Serial BLLA | ~114 min | GPU ~0 % util |
| This project `-w 16` | **8.33 min** | Shapely-only pool |
| This project + parent Sato | **8.7 min** | `_calc_roi` still dominates |
| Surya detect (same pages) | ~95 s | different crops; OpenRAIL-M weights |

Geometry vs serial PAGE-XML is **crop-equivalent, not bit-identical**
(793/827 exact on the Sato run; the rest are empty junk regions or 1 px).
Receipts are under `benchmarks/`.

Why not just use Surya: this stack is Apache-2.0 (code + default seg model);
Surya's **segmentation weights** are OpenRAIL-M. See
`docs/PROVENANCE-AND-LICENSING.md`.

## Install

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -e . --no-deps   # when torch / shapely / skimage are already there
# otherwise: pip install -e .
```

The installed commands are `kraken-gpu` and `ketos-gpu`. The Python import
namespace remains `kraken` for compatibility with the existing code and
model/plugin metadata.

On a box with a **custom** PyTorch wheel, never `pip install torch`. Use
`--system-site-packages` and `--no-deps`. One such layout: `INSTALL.md`.

## Segment a book

Write PAGE-XML next to **copies or symlinks** of the page images, not into a
live `images/` directory.

```bash
kraken-gpu -I "*.jpg" -o .xml -x -w 16 --device cuda:0 segment -bl
```

- `-w` is process workers. `--threads` is OpenMP per worker; leave it at 1.
- The pool runs only when there is more than one input file and `-w` > 1.

## Remaining work

The remaining cost is `_calc_roi` (~4 s/page). Do not revive the rejected
approaches in `DEV_NOTES.md`. Any geometry change must match serial crops
(p.297 55/55, then the book dump).

## Licence

Apache-2.0. This fork derives from Kraken by Benjamin Kiessling and
contributors. See `LICENSE`.

## Docs

- `INSTALL.md` — GPU-worker bind-mount recipe
- `DEV_NOTES.md` — profile, rejected approaches, remaining work
- `docs/BENCHMARKS.md` — measured numbers
- `docs/TECHNICAL-BACKGROUND.md` — why it is slow
- `docs/ROADMAP.md` — tiers
- `benchmarks/` — p.297 profile and 827-page receipts
