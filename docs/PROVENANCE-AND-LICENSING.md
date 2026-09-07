# Provenance & licensing — the "why it's worth building" case

This is the non-technical half of the project's justification. Keep it precise; the strength of the
pitch depends on **not overclaiming**.

## Licensing (the strongest, cleanest argument) — VERIFIED 2026-09-02

Surya splits its licence (confirmed from the repo LICENSE + README):
- **Surya code: Apache-2.0.**
- **Surya model weights: modified AI Pubs OpenRAIL-M** — README verbatim: *"free for research,
  personal use, and startups under $5M funding/revenue. For broader commercial licensing of the
  model weights, visit our pricing page."* The HF weight repos (`datalab-to/surya-ocr-2`, `-gguf`)
  are tagged `openrail`.
- This weight licence covers **both** Surya models — so even the **detection/segmentation** weights
  (the only part a segmentation-only user touches) are:
  1. **Revenue-gated** — free only below $5M funding-or-revenue; commercial licence required above.
  2. **Use-restricted** — OpenRAIL ("Responsible AI Licence") imposes behavioural use restrictions,
     which makes it **not OSI-approved open source**. Some organisations and Linux distros reject
     OpenRAIL outright, independent of the revenue question.

- **Kraken: Apache-2.0 code + a permissively-distributed default segmentation model** — **no revenue
  gate, no use restrictions, OSI-open.**

- **Consequence:** organisations that can't accept a revenue-gated *or* use-restricted weight licence
  currently have no GPU-fast, fully-permissive page segmenter with Kraken-quality crops. That gap
  alone justifies the work, independent of any China question. The clean framing:
  **Apache-2.0 vs OpenRAIL-M (revenue-gated + use-restricted) weights** — and it applies to the
  *segmentation* model, not just Surya's OCR.

*(Terms can change across Surya versions — re-verify at github.com/datalab-to/surya and
datalab.to/pricing before publishing.)*

## Supply-chain / provenance (real, but state it carefully)
- Surya has **two** models. **Detection** (what a segmentation-only user touches) is
  `EfficientViTForSemanticSegmentation` — an academic vision architecture, weights trained by Datalab
  (US). **Recognition** (`surya-ocr-2`) is **Qwen3.5-based** (Alibaba). So a *segmentation-only*
  Surya pipeline is already Qwen-free.
- **But** the Surya *package* still bundles / can pull the Qwen recognition model. For institutions
  with procurement or policy rules, "the dependency ships a Chinese-origin model at all" is a
  dealbreaker regardless of which component is called. A tool with **zero Surya in its dependency
  tree** is a materially cleaner story to certify.
- Kraken's own segmentation model is **already Apache-2.0 and has no Chinese-vendor provenance** — so
  the cleanest path (speed up Kraken's existing model) introduces **no** new provenance questions at
  all.

## The principled line (protects the project from bad-faith readings)
Frame the motivation as **supply chain + licensing**, never nationality.
- **Defensible line:** organisational provenance of the *weights* and the *shipping package* — who
  trained it (e.g. Alibaba), who distributes it, under what licence.
- **Not a line:** the birthplace/ethnicity of an architecture's academic authors. (EfficientViT's
  lead author is MIT faculty; chasing that thread is arbitrary and makes the project indefensible.)
- Sticking to "we want an Apache-2.0 tool whose entire dependency tree we can vouch for" is
  unimpeachable and is also just **good engineering hygiene** — reproducible, auditable, licence-clean
  supply chains are a mainstream requirement, not a fringe one.

## Who benefits
- Public-sector / government / defence-adjacent archives with vendor-provenance rules.
- Commercial users above Surya's revenue gate who want permissive licensing.
- The Kraken/eScriptorium community generally (tier 1 speeds up everyone).
- Anyone who values a single, auditable, Apache-licensed toolchain over stitching in a second
  vendor's models.

## Positioning (how to talk about it)
"**Same trusted Kraken, now GPU-fast.**" A speed contribution to a beloved Apache-2.0 tool — not an
anti-anything crusade. The licence and clean-supply-chain benefits sell themselves; let them.
