#!/usr/bin/env python3
"""Serial profile of kraken.blla.segment on Hibernia Dominicana printed p.297.

Run inside <gpu-container>. Does not modify Kraken.
"""
from __future__ import annotations

import cProfile
import io
import os
import pstats
import time
from importlib import resources
from pathlib import Path

import torch
from PIL import Image
from kraken import blla
from kraken.containers import BaselineLine, Segmentation
from kraken.lib import vgsl
from kraken.lib.segmentation import (
    is_in_region,
    polygonal_reading_order,
    scale_regions,
)
import shapely.geometry as geom

PAGE = Path(os.environ.get("KRAKEN_GPU_PROFILE_PAGE", "page-297.jpg"))
DEVICE = "cuda:0"
OUT = Path(os.environ.get("KRAKEN_GPU_PROFILE_OUT", "profile-blla-p297.txt"))


def _sync():
    if DEVICE.startswith("cuda") and torch.cuda.is_available():
        torch.cuda.synchronize()


def dump_pstats(pr: cProfile.Profile, n: int = 40) -> str:
    buf = io.StringIO()
    stats = pstats.Stats(pr, stream=buf)
    buf.write("\n===== cProfile by cumulative time =====\n")
    stats.sort_stats("cumtime").print_stats(n)
    buf.write("\n===== cProfile by tottime (self) =====\n")
    stats.sort_stats("tottime").print_stats(n)
    return buf.getvalue()


def main():
    lines_out = []
    def log(msg: str):
        print(msg, flush=True)
        lines_out.append(msg)

    im = Image.open(PAGE).convert("RGB")
    log(f"page={PAGE}")
    log(f"size={im.size} mode={im.mode}")
    log(f"device={DEVICE} cuda={torch.cuda.is_available()}")
    if torch.cuda.is_available():
        log(f"gpu={torch.cuda.get_device_name(0)}")
        log(f"vram_before_mb={torch.cuda.memory_allocated() / 1e6:.1f}")

    t0 = time.perf_counter()
    model = vgsl.TorchVGSLModel.load_model(resources.files("kraken").joinpath("blla.mlmodel"))
    t_load = time.perf_counter() - t0
    log(f"model_load_s={t_load:.3f}")

    # Warmup GPU kernels (not in the measured split)
    _sync()
    t0 = time.perf_counter()
    _ = blla.compute_segmentation_map(im, None, model, DEVICE, autocast=False)
    _sync()
    t_warmup = time.perf_counter() - t0
    log(f"gpu_warmup_s={t_warmup:.3f}")
    if torch.cuda.is_available():
        log(f"vram_after_warmup_mb={torch.cuda.memory_allocated() / 1e6:.1f}")
        log(f"vram_reserved_mb={torch.cuda.memory_reserved() / 1e6:.1f}")

    # ----- staged wall-clock (serial, measured) -----
    _sync()
    t0 = time.perf_counter()
    rets = blla.compute_segmentation_map(im, None, model, DEVICE, autocast=False)
    _sync()
    t_gpu = time.perf_counter() - t0

    t0 = time.perf_counter()
    _regions = blla.vec_regions(**rets)
    t_regions = time.perf_counter() - t0

    line_regs = []
    suppl_obj = []
    for cls, regs in _regions.items():
        line_regs.extend(regs)
        if rets["bounding_regions"] is not None and cls in rets["bounding_regions"]:
            suppl_obj.extend(regs)
    suppl_obj = scale_regions([x.boundary for x in suppl_obj], 1 / rets["scale"])
    line_regs = scale_regions([x.boundary for x in line_regs], 1 / rets["scale"])

    t0 = time.perf_counter()
    _lines = blla.vec_lines(
        **rets,
        regions=line_regs,
        text_direction="horizontal-lr",
        suppl_obj=suppl_obj,
        topline=model.user_metadata["topline"] if "topline" in model.user_metadata else False,
        raise_on_error=False,
    )
    t_lines = time.perf_counter() - t0

    blls = [
        BaselineLine(
            id=f"_{i}",
            baseline=line["baseline"],
            boundary=line["boundary"],
            tags=line["tags"],
        )
        for i, line in enumerate(_lines)
    ]
    t0 = time.perf_counter()
    all_regions = [reg for rgs in _regions.values() for reg in rgs]
    if blls:
        order = polygonal_reading_order(
            lines=blls, regions=all_regions, text_direction="lr"
        )
        blls = [blls[idx] for idx in order]
    t_ro = time.perf_counter() - t0

    n_lines = len(blls)
    n_regs = sum(len(v) for v in _regions.values())
    t_cpu_geom = t_regions + t_lines + t_ro
    t_staged = t_gpu + t_cpu_geom

    log("")
    log("===== staged wall-clock (after warmup, serial) =====")
    log(f"n_lines={n_lines} n_regions={n_regs}")
    log(f"stage1_gpu_compute_segmentation_map_s={t_gpu:.3f}")
    log(f"stage2_vec_regions_s={t_regions:.3f}")
    log(f"stage2_vec_lines_s={t_lines:.3f}")
    log(f"stage2_reading_order_s={t_ro:.3f}")
    log(f"stage2_cpu_geometry_total_s={t_cpu_geom:.3f}")
    log(f"staged_total_s={t_staged:.3f}")
    if t_staged > 0:
        log(f"gpu_pct={100 * t_gpu / t_staged:.1f}")
        log(f"cpu_geom_pct={100 * t_cpu_geom / t_staged:.1f}")
        log(f"vec_lines_pct={100 * t_lines / t_staged:.1f}")

    # ----- full blla.segment under cProfile (model preloaded) -----
    pr = cProfile.Profile()
    t0 = time.perf_counter()
    pr.enable()
    seg = blla.segment(im, model=model, device=DEVICE, raise_on_error=False)
    pr.disable()
    t_full = time.perf_counter() - t0
    log("")
    log("===== full blla.segment (model preloaded, includes cProfile overhead) =====")
    log(f"full_segment_wall_s={t_full:.3f}")
    log(f"full_segment_n_lines={len(seg.lines)}")

    profile_txt = dump_pstats(pr, n=50)
    log(profile_txt)

    OUT.write_text("\n".join(lines_out) + "\n", encoding="utf-8")
    log(f"wrote {OUT}")


if __name__ == "__main__":
    main()
