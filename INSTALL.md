# Install in a GPU Container

Generic CLI install is in `README.md`. This file is a bind-mount recipe for
running the fork inside a GPU-capable worker container.

This fork is **Kraken crops on 16 CPU cores**, not a GPU geometry engine.
The neural net (and parent-only Sato) run on `cuda:0`. Line polygons still
come from stock Shapely `_calc_roi`. That is why an 827-page book is ~8–9
minutes instead of Surya's ~95 seconds — and why the crops stay Kraken's.

eScriptorium's own Celery worker still uses the image `kraken` 7.0.1. This
install only adds a CLI named `kraken-gpu`.

## Layout

| Host | Inside `<gpu-container>` |
|---|---|
| `<kraken-host-dir>/src` | `/opt/kraken-gpu` |
| `<kraken-host-dir>/venv` | `/opt/kraken-gpu-venv` |

The venv is `--system-site-packages` so **torch / shapely / skimage are the
container image copies**. Do **not** `pip install torch` or upgrade PyTorch in
containers with custom CUDA wheels.

Bind mounts live in `<escriptorium-dir>/docker-compose.override.yml`
on the celery-gpu service:

```yaml
      - <kraken-host-dir>/src:/opt/kraken-gpu
      - <kraken-host-dir>/venv:/opt/kraken-gpu-venv
```

## Recreate the Worker Only

Recreate only the worker service that uses these bind mounts:

```bash
cd <escriptorium-dir>
docker compose -f docker-compose.yml -f docker-compose.override.yml \
  up -d --no-deps --force-recreate <worker-service>
```

Then, if the venv is missing (empty bind-mount after the first recreate):

```bash
docker exec -u 1000:1000 <gpu-container> \
  /opt/kraken-gpu/scripts/install-container-venv.sh
```

`install-container-venv.sh` runs `pip install -e /opt/kraken-gpu --no-deps`.
It must not pull torch.

## The command

Write PAGE-XML next to **copies or symlinks** of the page images, not into
the live `images/` tree.

```bash
docker exec -it -u 1000:1000 -w /path/to/empty-dir-of-jpg-symlinks \
  <gpu-container> \
  kraken-gpu \
    -I "*.jpg" -o .xml -x -w 16 --device cuda:0 segment -bl
```

- `-w 16` is process workers. `--threads` is OpenMP per worker; leave it at 1.
- Pool only runs when there is more than one input file and `-w` > 1.
- Parent applies GPU Sato; workers skip the ridge filter. No CUDA in workers.

## What you should expect (Hibernia Dominicana, 827 pp)

| | wall | vs serial (~114 min) |
|---|---:|---|
| Shapely-only pool (`kraken-xml-pool/`) | **8.33 min** | ~14× |
| Parent GPU Sato + pool (`kraken-xml-sato-pool/`) | **8.7 min** | ~13× |

Geometry vs serial `kraken-xml-raw/`: **crop-equivalent, not bit-identical PAGE-XML**.
Parent-Sato run: 793/827 exact; 25 empty 0-line junk regions; 8 other region-coord
noise; 3 line diffs of 1 px. Receipts: `benchmarks/827-page-pool.md`,
`benchmarks/827-page-sato-pool.md`.

Surya detect on the same book is ~95 s. Closing that gap is `_calc_roi`, which
is still stock Shapely on purpose.

## Guardrails

- Never `pip install torch` / upgrade PyTorch in any eScriptorium container.
- Do not edit `/usr/local/lib/python3.12/site-packages/kraken/` (production 7.0.1).
- Do not call `sato_torch` from worker processes.
- Do not bounce the whole compose stack if a worker-only recreate will do.
