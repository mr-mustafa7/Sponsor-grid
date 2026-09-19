#!/bin/sh
set -e
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/pip install -e .
fi
.venv/bin/pip install -e . >/dev/null
export PYTHONPATH=src
exec .venv/bin/python -m uvicorn enrolbound.app:app --host 127.0.0.1 --port 8000 --reload
