#!/usr/bin/env bash
# Virtual desktop for Bosch Plausibility Check in headless environments (GitHub Codespaces).
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

# Virtual framebuffer — must be >= app geometry (1400x850) + window borders / taskbar
Xvfb :99 -screen 0 1920x1080x24 -ac +extension RENDER -noreset &
sleep 1

# Minimal window manager (required for Tk placement)
fluxbox &
sleep 1

# Auto-open a terminal so users are not stuck with an empty desktop
(
  sleep 2
  export DISPLAY=:99
  cat >/tmp/pruf-xterm.sh <<'EOS'
#!/bin/bash
echo "======== Bosch Plausibility Check — desktop terminal ========"
echo "GUI:  cd to your repo, then:  python3 main.py"
echo "CLI:  python3 scripts/cli_plausibility.py list-projects"
echo "      python3 scripts/cli_plausibility.py run --project-id ID --file file.xlsx"
echo "========================================="
for d in /workspaces/*/ /workspace; do
  if [ -f "$d/main.py" ]; then cd "$d" 2>/dev/null && break; fi
done
pwd
exec bash -l
EOS
  chmod +x /tmp/pruf-xterm.sh
  xterm -geometry 110x26+40+80 -bg '#FFFFFF' -fg '#333333' -title 'Bosch Plausibility — python3 main.py' -e /tmp/pruf-xterm.sh &
) &

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

# Copy tree + add index.html — otherwise websockify shows "Directory listing for /"
WEBDIR=/tmp/pruf-novnc-web
rm -rf "$WEBDIR"
mkdir -p "$WEBDIR"
cp -a "${NOVNC_WEB}/." "${WEBDIR}/"
cat > "${WEBDIR}/index.html" <<'HTMLEOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta http-equiv="refresh" content="0;url=vnc.html" />
  <title>Bosch Plausibility Check — noVNC</title>
</head>
<body>
  <p>Opening noVNC… <a href="vnc.html">Open vnc.html</a> if this page does not redirect.</p>
</body>
</html>
HTMLEOF

# Bind all interfaces so GitHub port forwarding can reach the proxy
exec python3 -m websockify --web="$WEBDIR" 0.0.0.0:6080 127.0.0.1:5900
