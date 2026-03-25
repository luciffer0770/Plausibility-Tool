# PRÜF — Plausibility Check Tool

Desktop Python application for Bosch engine test bed plausibility checks against PUMA measurement exports (Excel/CSV).

## Requirements

- Python 3.10+
- Windows 10/11 (primary target; runs on Linux for development)

## Run (local)

```bash
pip install -r requirements.txt
python3 main.py
```

Use **Python 3.10+** (on Windows, `py -3 main.py` if `python` is still 2.x).

## Run in GitHub Codespaces

PRÜF is a **desktop (Tk) app**. The dev container runs **Xvfb + Fluxbox + x11vnc + websockify** and serves **noVNC** on port **6080** (replaces the older `desktop-lite` setup, which often failed to connect).

### One-time after pulling these changes

1. **Rebuild the container** so the new Dockerfile runs: Command Palette (`Ctrl+Shift+P`) → **Dev Containers: Rebuild Container** (or recreate the Codespace).

### Every session

1. Create or open a Codespace on a branch that includes `.devcontainer/`.
2. Wait until the environment is ready ( **`pip install -r requirements.txt`** runs on create).
3. Open the **Ports** tab → find **6080** → set visibility to **Public** (needed for the browser tab to load reliably).
4. Click the **globe / Open in browser** link for port **6080**.
5. You should see the **noVNC** page. Click **Connect** (this setup uses **no VNC password** — dev-only).
6. **Right‑click the desktop → Terminal** (or open a terminal in Fluxbox) and run:

   ```bash
   cd /workspaces/Plausibility-Tool
   python3 main.py
   ```

   The integrated VS Code terminal also has `DISPLAY=:99`, so **`python3 main.py` in VS Code** can show the window **if** Xvfb is running (same display as noVNC).

**If the UI looks “cut off” or has odd scrollbars**

The remote desktop has a fixed pixel size. If it was smaller than the app window, the window was clipped. The dev container now uses a **1920×1080** virtual screen and sets **`PRUF_GEOMETRY=1280x720`** so the app fits better in the browser. After rebuild, you should see the full window.

In noVNC, try **full screen** (toolbar) or open with scaling, e.g. append to the path:

`vnc.html?autoconnect=true&resize=scale`

(Exact query options depend on the noVNC version; the toolbar **Settings** may offer “Scaling”.)

**Troubleshooting**

```bash
./scripts/check_novnc.sh
tail -50 /tmp/pruf-desktop.log
```

If port 6080 is closed, restart the stack: `nohup /usr/local/bin/start-pruf-desktop.sh &` (then wait a few seconds and refresh the browser).

**Headless smoke test** (no GUI):

```bash
./scripts/run_headless.sh
```

Modal dialogs use a deferred `grab_set` so they work on **noVNC / remote X** where “window not viewable” errors can occur.

## Packaging

Install PyInstaller, then:

```bash
pyinstaller build.spec
```

Place `assets/bosch_logo.png` in the repository for the header and PDF (corporate logo from your internal brand kit).

## Features (Phase 1)

- **Tabbed UI** (reference-style): **PROJECTS** | **LIMITS CONFIG** | **UPLOAD & EVALUATE** | **RESULTS** (+ Export/Settings in header)
- Projects: create + list/select; header shows `ACTIVE: …`
- **LIMITS CONFIG**: scrollable **table** (#, label, type, description, lower/upper, unit, root cause, **ON** checkbox). Category filter, **SAVE ALL LIMITS**, JSON/Excel import, clone. Disabled rows are skipped in plausibility checks.
- SQLite (`pruf_data.db`); schema v2 adds `is_enabled` on limit profiles (auto-migrated)
- PUMA upload with mapping preview; analysis (first data row vs limits); results table + export

## Tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```
