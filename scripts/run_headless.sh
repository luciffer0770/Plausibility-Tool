#!/usr/bin/env bash
# Smoke-test PRÜF without a visible display (CI / quick check).
set -euo pipefail
cd "$(dirname "$0")/.."
xvfb-run -a python3 main.py
