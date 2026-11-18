#!/usr/bin/env bash
# Install local kid-face-sort so face features can be extracted and used on-device.
# Downloads public buffalo_l weights once (~280MB). Does NOT ship personal face data.
set -euo pipefail
D="$(cd "$(dirname "$0")" && pwd)"; cd "$D"

echo "== kid-face-sort install =="

command -v python3 >/dev/null || { echo "python3 required (e.g. brew install python@3.12)"; exit 1; }
if [[ "$(uname)" == "Darwin" ]] && ! xcode-select -p >/dev/null 2>&1; then
  echo "Xcode Command Line Tools required: xcode-select --install"
  exit 1
fi

python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -q --upgrade pip wheel setuptools Cython
python -m pip install -q -r requirements.txt
chmod +x kidface.sh

# Local runtime dirs (biometric data stays outside git)
KIDFACE_HOME="${KIDFACE_HOME:-$HOME/.kidface}"
mkdir -p "$KIDFACE_HOME" "$KIDFACE_HOME/backups"
chmod 700 "$KIDFACE_HOME" 2>/dev/null || true

EMPTY_TMPL="$D/templates/embeddings.empty.npz"
DB_PATH="${KIDFACE_DB:-$KIDFACE_HOME/embeddings.npz}"
if [[ ! -f "$DB_PATH" ]]; then
  if [[ -f "$EMPTY_TMPL" ]]; then
    cp "$EMPTY_TMPL" "$DB_PATH"
    echo "Created empty embeddings DB: $DB_PATH"
  else
    python - <<'PY'
import json, os
from pathlib import Path
import numpy as np
db = Path(os.environ.get("KIDFACE_DB", Path.home()/".kidface"/"embeddings.npz"))
db.parent.mkdir(parents=True, exist_ok=True)
np.savez(db, __meta__=np.array(json.dumps({})))
print(f"Created empty embeddings DB: {db}")
PY
  fi
  chmod 600 "$DB_PATH" 2>/dev/null || true
else
  echo "Keeping existing embeddings DB: $DB_PATH"
fi

echo "Downloading InsightFace buffalo_l models if missing (~280MB, once)..."
python - <<'PY'
import os, sys
from pathlib import Path
sys.path.insert(0, "kidface")
import cli
print("loading FaceAnalysis(buffalo_l) ...")
app = cli.get_app()
# verify expected onnx files under ~/.insightface/models/buffalo_l
root = Path.home() / ".insightface" / "models" / os.environ.get("KIDFACE_MODEL", "buffalo_l")
need = ["det_10g.onnx", "w600k_r50.onnx"]
missing = [n for n in need if not (root / n).exists()]
if missing:
    # some layouts nest differently; search
    found = {n: False for n in need}
    if root.exists():
        for p in root.rglob("*.onnx"):
            for n in need:
                if p.name == n:
                    found[n] = True
    missing = [n for n, ok in found.items() if not ok]
if missing:
    raise SystemExit(f"model files still missing under {root}: {missing}")
print(f"models ok: {root}")
print("providers ready")
PY

echo
echo "Smoke check:"
./kidface.sh list || true
echo
echo "Install complete. Next:"
echo "  1) Put 3-10 solo reference photos in a folder"
echo "  2) ./kidface.sh enroll <label> /path/to/refs/"
echo "  3) ./kidface.sh sort /path/to/photos -o /tmp/out --mode dry -t 0.55 --margin 0.10"
echo "Models: ~/.insightface/models/buffalo_l"
echo "DB:     $DB_PATH"
echo "Cache:  ${KIDFACE_CACHE:-$HOME/.kidface/scan_cache.sqlite}"
