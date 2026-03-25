#!/usr/bin/env bash
# Run PRÜF GUI in GitHub Codespaces (needs noVNC on port 6080 + Xvfb).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export DISPLAY="${DISPLAY:-:99}"
echo "DISPLAY=$DISPLAY"
echo "Starting PRÜF from $ROOT ..."
exec python3 main.py
