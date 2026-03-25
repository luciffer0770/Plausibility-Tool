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

- Projects with engine type and test bed ID
- SQLite storage (`pruf_data.db` in the working directory)
- Limit profile editor: edit all fields, JSON import/export, Excel import for extra parameters, clone profile, **Required** toggled via clickable button
- PUMA upload with auto column mapping and preview
- Plausibility analysis (first data row vs limits)
- Analysis table with filters and detail panel
- Dashboard charts and upload history
- Annotated Excel export and PDF summary

## Tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```
