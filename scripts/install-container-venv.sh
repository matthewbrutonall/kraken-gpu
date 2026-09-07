#!/bin/sh
# Recreate the kraken-gpu virtual environment inside a GPU-capable container.
# The venv can live on a host bind-mount so it
# survives a celery-gpu recreate. It uses --system-site-packages so torch,
# shapely, and skimage come from the image. NEVER pip install torch.
set -eu
# uid 1000 in celery-gpu has no homedir; keep pip off /.cache
export HOME="${HOME:-/tmp}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/tmp/kraken-gpu-pip-cache}"
SRC="${KRAKEN_GPU_SRC:-/opt/kraken-gpu}"
VENV="${KRAKEN_GPU_VENV:-/opt/kraken-gpu-venv}"

if [ ! -f "$SRC/pyproject.toml" ]; then
    echo "missing $SRC/pyproject.toml (bind-mount the fork first)" >&2
    exit 1
fi

python3 -m venv --system-site-packages --clear "$VENV"
# --no-deps: do not resolve pyproject torch pins; the image already has torch.
"$VENV/bin/pip" install --disable-pip-version-check -e "$SRC" --no-deps

"$VENV/bin/python" - "$SRC" <<'PY'
import sys
import kraken, torch, shapely
src = sys.argv[1].rstrip("/") + "/"
print("kraken", kraken.__file__)
print("torch", torch.__version__, torch.__file__)
print("shapely", shapely.__version__, shapely.__file__)
if not kraken.__file__.startswith(src):
    raise SystemExit(f"fork did not shadow site-packages kraken: {kraken.__file__}")
if not torch.__file__.startswith("/usr/local/"):
    raise SystemExit(f"torch is not the image copy (do not pip install torch): {torch.__file__}")
PY

"$VENV/bin/kraken-gpu" --help >/dev/null
echo "ok: $VENV/bin/kraken-gpu"
