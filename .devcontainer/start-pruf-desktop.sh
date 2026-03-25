#!/usr/bin/env bash
# Virtual desktop for PRÜF in headless environments (GitHub Codespaces).
# Serves noVNC on 0.0.0.0:6080 → VNC on 127.0.0.1:5900 → Xvfb :99

set -euo pipefail

LOG=/tmp/pruf-desktop.log
exec >>"$LOG" 2>&1
echo "=== start-pruf-desktop $(date) ==="

export DISPLAY=:99

pkill -f "[X]vfb :99" 2>/dev/null || true
pkill -f "[x]11vnc" 2>/dev/null || true
pkill -f "[w]ebsockify" 2>/dev/null || true
sleep 1

# Virtual framebuffer
Xvfb :99 -screen 0 1280x800x24 -ac +extension RENDER -noreset &
sleep 1

# Minimal window manager (required for Tk placement)
fluxbox &
sleep 1

# VNC without password — dev container only; do not expose publicly outside Codespaces
x11vnc -display :99 -nopw -forever -shared -listen 127.0.0.1 -rfbport 5900 -bg
sleep 1

NOVNC_WEB=""
for d in /usr/share/novnc /usr/share/novnc_core; do
  if [[ -f "$d/vnc.html" ]]; then
    NOVNC_WEB="$d"
    break
  fi
done
if [[ -z "$NOVNC_WEB" ]]; then
  echo "ERROR: noVNC web (vnc.html) not found under /usr/share"
  exit 1
fi
echo "Using noVNC web root: $NOVNC_WEB"

# Bind all interfaces so GitHub port forwarding can reach the proxy
exec python3 -m websockify --web="$NOVNC_WEB" 0.0.0.0:6080 127.0.0.1:5900
