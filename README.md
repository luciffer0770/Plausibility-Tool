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

## Run in GitHub Codespaces (see the GUI)

Tk apps have no window in the browser by themselves. You must open **noVNC** (virtual desktop) on port **6080**, then start the app **inside that desktop** (or use the VS Code terminal with `DISPLAY=:99` — same screen).

### A — First time on this branch

1. Push/pull branch **`cursor/plausibility-check-tool-e9d7`** (or merge to `main`) so `.devcontainer/` is on GitHub.
2. **Code → Codespaces → Create codespace** on that branch.
3. Wait for build to finish (`postCreateCommand` installs Python deps; `postStartCommand` starts the desktop).
4. **Rebuild if the container was created before** `.devcontainer/Dockerfile` existed: `Ctrl+Shift+P` → **Dev Containers: Rebuild Container**.

### B — Every time you want the GUI

1. In Codespace, open the **Ports** tab (bottom panel).
2. Find port **6080** → set **Visibility** to **Public** → click the **globe** “open in browser”.
3. In the noVNC tab you should land on the viewer (or click **Connect** if prompted).  
   **If you see “Directory listing for /”** instead, click **`vnc.html`** in the list — or **rebuild the container** so the updated startup script adds an automatic redirect.
4. **Inside the grey desktop**, right‑click → **Terminal** (Fluxbox menu), **or** use the VS Code terminal and run:

   ```bash
   ./scripts/codespace_run_gui.sh
   ```

   If the path differs, use:

   ```bash
   cd /workspaces/<YOUR-REPO-NAME>
   python3 main.py
   ```

5. The PRÜF window should appear on the **virtual desktop** (the noVNC tab). If you only look at VS Code with no noVNC open, you will not see it.

**Tip:** Keep the **6080** browser tab visible; drag the app window if it opens off-screen.

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
