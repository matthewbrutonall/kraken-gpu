# Roadmap

Ordered by value-per-effort. Do them in order; each de-risks the next.

## Step 0 — decide the deliverable shape (Decision Made)
This project (`kraken-gpu`) owns the tree and can rewrite `segmentation.py`
for speed (gated on crop identity). It is a separate product, not a
contribution back to anyone else's repo.

## Step 1 — PROFILE (DONE 2026-09-07)
Serial `cProfile` of `kraken.blla.segment` on printed p.297 inside `<gpu-container>`
(Kraken 7.0.1, cuda:0). See `benchmarks/profile-blla-p297.md`.

Headline: 7.27 s/page; GPU 0.093 s (1.3%); `vec_lines` 96.8%. Polygonisation is **4.8 s**
(`_calc_roi` 4.0 s, `_calc_seam` only 0.75 s). `vectorize_lines` (Sato + trace) is **3.9 s**
and is whole-page sequential. Intra-page threads cannot 10x this page; page-level parallelism can.

## Step 2 — TIER 1: parallelise stage 2 (DONE 2026-09-07)
- **Result:** Designed and shipped a drop-in multiprocess pool natively integrated into the `kraken segment` CLI.
- **Speed:** Scaled the 827-page book from ~114 min (serial) down to 8.33 min (0.60 s/page).
- **Quality:** Crop-equivalent geometry verified. 794/827 pages matched identically. The rest were sub-pixel or 0-line junk region variations.
- **Output:** Working parallel engine + receipts in `benchmarks/`. The 8-minute run is verified as:
  `kraken-gpu -I ... -o .xml -x -w 16 --device cuda:0 segment -bl`

## Step 3 — TIER 2: GPU-port the geometry
- **Sato (parent only, 2026-09-07):** `sato_torch` in `batch_segmenter` matches skimage
  Sato on p.297 (max abs 3e-7, identical baselines+polygons vs `kraken-xml-raw`).
  Workers skip the ridge filter. Not done: `_calc_roi` is still Shapely.
- Gate every change on: **same crops** vs `kraken-xml-raw`. No CUDA in worker processes.

## Step 4 — package, document, publish
- **Container install (2026-09-07):** durable bind-mount install, CLI documented
  in `INSTALL.md`. Product is 16-core CPU geometry + GPU net/Sato, Kraken crops.
  Not published; not a GPU geometry engine.
- Still open: PyPI/name, benchmark reproducer for other machines.
- Emphasise the pitch: **Apache-2.0, faster Kraken crops, clean supply chain.**

## Guardrails (do not violate)
- **Never trade crop quality for speed silently.** Kraken's value is precise polygons; a fast path
  that loosens them is just a worse Surya. Always show quality parity.
- **Keep it Apache-clean.** No dependency whose licence or provenance reintroduces the very problems
  this project exists to avoid. (CuPy = MIT, fine. Vet anything new.)
- **Measure everything** against the Step-1 baseline. No "feels faster."
