# Benchmarks — the motivating measurement

All from the OCR-model-evaluation run on **de Burgo, *Hibernia Dominicana* (1762)**, 827 pages,
200 DPI JPEGs, on the test box: RTX 5070 Ti 16 GB, Ryzen 9 9950X 16c/32t.

## Surya detection (the target to match)
From `surya_detect.log` on the server:
```
Detecting bboxes: 100%|██████████| 46/46 [01:34<00:00, 2.06s/it]
```
- **46 GPU batches × ~2.06 s ≈ 95 s** for all 827 pages (~0.11 s/page).
- Plus a few seconds model load/startup. Call it **~2–3 min wall-clock** end to end.
- Model: `EfficientViTForSemanticSegmentation` (Segformer image processor, 1200×1200). GPU-batched.

## Kraken `blla` segmentation (the thing to speed up)
From the full-book `book_segment.py` run (measured from output-file timestamps):
- **~8.3 s/page → ~114 min** for 827 pages.
- During the run: GPU held **~2.8 GB** VRAM but **0 % utilisation** — i.e. CPU-bound, GPU idle.
- Process ran ~232 % CPU (a few cores), single pipeline over pages.

## The gap
- **~60–80× slower** than Surya on the same hardware and pages.
- Cause is **not** the GPU or the model — it's stage-2 CPU geometry post-processing
  (`calculate_polygonal_environment` et al.). See `TECHNICAL-BACKGROUND.md`.

## Quality context (why we don't "just use Surya")
12-page pre-test, same recogniser (fine-tuned CATMuS-Print HD-v1) on both segmentations
(from `kraken-experiment/seg-ocr/FINDINGS.md`):
- **Coverage tied** (~0.3%; Surya +198 chars / 12 pages — not a real recall win).
- **Kraken crops cleaner** on the sample: `Waræo`/`sunt` vs Surya's `Ivaræo`/`funt`, and Surya
  pulled in the `Diuzed oy Coogle` watermark. (Caveat: 12-page sample, not a book-level verdict —
  the full-book OCR comparison was still running when this project was spun out.)
- **Reading order:** Surya looked better natively, but the same left-then-right sort fixes Kraken
  too → it was blla's serialiser, not missing lines.

Takeaway for this project: the precise-crop advantage is exactly the expensive geometry we must
**keep** while making it fast.

## Targets
- **Tier 1 (parallelise):** ≤ 15 min for 827 pages (≈10× on 16 cores), identical geometry.
- **Tier 2 (GPU geometry):** approach Surya's order of magnitude (single-digit minutes or better)
  with crop parity to CPU Kraken.

## To (re)produce the baseline
Run `cProfile` on `kraken.blla.segment` for one dense page (printed p.297) on the box — see
`ROADMAP.md` Step 1. Save under `benchmarks/`.
