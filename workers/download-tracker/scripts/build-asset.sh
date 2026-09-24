#!/usr/bin/env bash
# Build the counted download from this repository. Version is pyproject.toml.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
NAME="amoe-spectrallock-1.3.0"
OUT="$ROOT/workers/download-tracker/public/${NAME}.tar.gz"
VERSION="$(python3 - << PY
import pathlib, re
text = pathlib.Path("$ROOT/pyproject.toml").read_text()
m = re.search(r'^version = "([^"]+)"', text, re.M)
if not m or m.group(1) != "1.3.0":
    raise SystemExit(f"refusing to pack version {m.group(1) if m else 'missing'}")
print(m.group(1))
PY
)"
TMP="$(mktemp -d)"
STAGE="$TMP/$NAME"
mkdir -p "$STAGE"
tar -C "$ROOT" \
  --exclude=.git \
  --exclude=__pycache__ \
  --exclude=.pytest_cache \
  --exclude='*.egg-info' \
  --exclude=.venv \
  --exclude=dist \
  --exclude=build \
  --exclude=node_modules \
  --exclude='*.tar.gz' \
  -cf - . | tar -C "$STAGE" -xf -
find "$STAGE" -depth -type d -name '__pycache__' -exec rm -rf {} + || true
find "$STAGE" -type f -name '*.pyc' -delete || true
rm -f "$OUT"
tar -C "$TMP" -czf "$OUT" "$NAME"
echo "wrote $OUT (AMOE ${VERSION})"
