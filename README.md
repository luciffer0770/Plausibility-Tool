# Bosch Plausibility Check Tool

Desktop Python application for Bosch engine test bed plausibility checks against PUMA measurement exports (Excel/CSV).

## Requirements

- Python 3.9+ (3.10+ recommended)
- Windows 10/11 (primary target; runs on Linux for development)

## Run (local)

```bash
pip install -r requirements.txt
python3 main.py
```

Use **Python 3.9+** (on Windows, `py -3 main.py` if `python` is still 2.x). For new envs, prefer **3.10+**.

## Run in GitHub Codespaces

### Option 1 — No GUI (recommended if noVNC is painful)

Use the **CLI** from the normal VS Code terminal (no browser, no VNC):

```bash
cd /workspaces/<YOUR-REPO-NAME>
pip install -r requirements.txt   # if not already done
python3 scripts/cli_plausibility.py create-project --name "MyTest" --test-bed TB-03
python3 scripts/cli_plausibility.py list-projects
python3 scripts/cli_plausibility.py run --project-id 1 --file ./your_data.xlsx
```

`create-project` seeds limits for the chosen engine type; no GUI required.

### Option 2 — GUI via noVNC

Tk apps have no window in the browser by themselves. Open **noVNC** on port **6080**, then start the app **in the auto-opened xterm** on the grey desktop **or** in VS Code terminal (`DISPLAY=:99` is set in the dev container).

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
4. You should see a **white xterm window** on the desktop with instructions — run **`python3 main.py`** there. **Or** use the VS Code terminal and run:

   ```bash
   ./scripts/codespace_run_gui.sh
   ```

   If the path differs, use:

   ```bash
   cd /workspaces/<YOUR-REPO-NAME>
   python3 main.py
   ```

5. The application window should appear on the **virtual desktop** (the noVNC tab). If you only look at VS Code with no noVNC open, you will not see it.

**Tip:** Keep the **6080** browser tab visible; drag the app window if it opens off-screen.

**If the UI looks “cut off” or has odd scrollbars**

The remote desktop has a fixed pixel size. If it was smaller than the app window, the window was clipped. The dev container uses a **1920×1080** virtual screen and sets **`BOSCH_PLAUS_GEOMETRY=1280x720`** (or legacy `PRUF_GEOMETRY`) so the app fits better in the browser. After rebuild, you should see the full window.

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
- SQLite (`bosch_plausibility_data.db`; legacy `pruf_data.db` is copied on first run); schema adds `is_enabled` on limit profiles (auto-migrated)
- PUMA upload with mapping preview; analysis (first data row vs limits); results table + export

## Tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```
