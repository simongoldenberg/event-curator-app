#!/usr/bin/env bash
set -euo pipefail
: "${EVENT_CURATOR_PYTHON:?Absoluten Python-Pfad in EVENT_CURATOR_PYTHON setzen}"
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
exec "$EVENT_CURATOR_PYTHON" main.py --live --monthly "$@"

