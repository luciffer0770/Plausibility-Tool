#!/usr/bin/env bash
# Run Bosch Plausibility Check GUI in GitHub Codespaces (needs noVNC on port 6080 + Xvfb).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export DISPLAY="${DISPLAY:-:99}"
echo "DISPLAY=$DISPLAY"
echo "Starting Bosch Plausibility Check from $ROOT ..."
exec python3 main.py
