#!/usr/bin/env bash
# Quick check that the Codespace desktop + noVNC stack is up.
set -e
echo "=== Processes (Xvfb, fluxbox, x11vnc, websockify) ==="
ps aux | grep -E '[X]vfb|[f]luxbox|[x]11vnc|[w]ebsockify' || true
echo ""
echo "=== Port 6080 ==="
ss -tlnp 2>/dev/null | grep 6080 || netstat -tlnp 2>/dev/null | grep 6080 || echo "(ss/netstat not available)"
echo ""
echo "=== HTTP localhost:6080 ==="
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:6080/ || echo "curl failed"
echo ""
echo "=== Last lines of /tmp/bosch-plausibility-desktop.log ==="
tail -20 /tmp/bosch-plausibility-desktop.log 2>/dev/null || echo "(no log yet)"
