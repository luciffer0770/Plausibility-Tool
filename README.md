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

PRÜF is a **desktop (Tk) app**. Codespaces are Linux and headless, so the repo includes a **Dev Container** with a small virtual desktop you open in the browser.

1. On GitHub: **Code → Codespaces → Create codespace** on your branch (uses `.devcontainer/devcontainer.json`).
2. Wait for **post-create** (installs `python3-tk`, **Xvfb**, and `pip install -r requirements.txt`).
3. Open the **Ports** tab → port **6080** → open the **noVNC** URL (or use the “Desktop” / forwarded link when notified).
4. Log in to noVNC with password **`vscode`** (default for `desktop-lite`).
5. In the **desktop’s terminal** (inside noVNC), run:

   ```bash
   cd /workspaces/Plausibility-Tool
   python3 main.py
   ```

   The PRÜF window appears **inside that browser desktop**, not in VS Code’s own UI.

**Headless smoke test only** (no window; useful to see if the app starts):

```bash
./scripts/run_headless.sh
```

If your organisation disables the **desktop-lite** feature, ask them to allow it for this repo, or develop on a **local Windows** machine instead.

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
