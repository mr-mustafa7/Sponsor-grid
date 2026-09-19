#!/bin/sh
set -e
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/modal ]; then
  CBOR2_BUILD_C_EXTENSION=0 .venv/bin/pip install 'cbor2<5.7' 'modal>=0.73'
fi
echo "This needs a Modal account. Run modal setup once if you have not."
if .venv/bin/modal skills --help >/dev/null 2>&1; then
  .venv/bin/modal skills install --global --yes --no-docs || true
fi
exec .venv/bin/modal deploy modal_app/serve_model.py
