# Bosch Plausibility Check Tool

Desktop Python application for Bosch engine test bed **plausibility checks** against PUMA measurement exports (`.xlsx`, tab-separated `.xls`, `.csv`). Compares measured values to configurable limits and reports **OK / HIGH / LOW / NO_DATA**, with optional **ZEIT (time)** when values are out of range.

## Requirements

| Item | Notes |
|------|--------|
| **Python** | **3.9+** (tested with 3.9.7 / Anaconda; 3.10+ also fine) |
| **OS** | Windows 10/11 (primary); Linux for development / Codespaces |
| **Dependencies** | See `requirements.txt` — CustomTkinter, pandas, openpyxl, matplotlib, fpdf2, Pillow, xlrd |

```bash
pip install -r requirements.txt
python3 main.py
```

On Windows, if `python` is still 2.x, use `py -3 main.py` or your Anaconda environment’s `python`.

## Quick start

1. **Install dependencies** (ideally in a venv or conda env).
2. Run **`python3 main.py`**.
3. **PROJECTS** — Create a project and pick an **engine type** (presets + custom types).
4. **LIMITS CONFIG** — Edit limits (table + detail panel), **Save all limits**, or use **OK** on a row to apply and save.
5. **UPLOAD & EVALUATE** — Browse a PUMA file, optional session note, **Run plausibility check**.
6. **RESULTS** — Summary cards, filterable table, **ZEIT (out of range)** when the file has a time column and limits are violated.

Settings such as last project, last file path, and results filters are stored in **`config/settings.json`** (created/updated at runtime).

## Main features

### Projects

- Create projects with **engine type** (enum presets + user-defined via **+** / **−**), test bed, engine code, OEM, emission norm.
- **Duplicate project names** are blocked (case-insensitive).
- Select active project; header shows `ACTIVE: …`.

### Limits configuration

- **Engine profile** matches the active project’s engine type (can be switched to edit another profile).
- **Tree table** + **Edit selected row**: label, type, description, **category** (combobox synced with filter presets), lower/upper, unit, root cause.
- **Include in check**: **Yes / No** control (same as **ON** in the table; double-click **ON** column still toggles).
- **OK** — Apply row and **save full profile to database**. **Apply** — Update row in memory only (then use **Save all limits** if needed).
- **Category filter** with **+** / **−** for user presets (`config/user_limit_categories.json`).
- Import/export JSON, import Excel, **export empty limits template**, clone from another engine type.

### Upload & evaluation

- Compact layout: browse, session note, **Run plausibility check** / **Re-run last file**.
- **Data preview** table: parameters × **ZEIT** columns, with Unit / Min / Max / Avg.
- Last PUMA path remembered for re-run.

### Results

- Summary tiles: **Total checked**, **Within limits**, **Above upper**, **Below lower**.
- Session line includes file name, **upload timestamp**, optional note.
- Table columns include **ZEIT (out of range)** when violations occur and the PUMA file has a **ZEIT** column (see *Data handling* below).
- Copy row, export failed rows (Excel), link to full Excel/PDF reports.
- Optional failure charts (checkbox).

### Reports & CLI

- **Reports** page: Bosch-style Excel report, annotated workbook.
- **CLI** (`scripts/cli_plausibility.py`): create/list projects and run checks without the GUI.

### Packaging

```bash
pip install pyinstaller
pyinstaller build.spec
```

`build.spec` bundles `config/`, `database/schema.sql`, and `assets/` (including `assets/themes/bosch_ctk.json` for UI theming).

## Data handling & plausibility logic

- PUMA files are loaded with **`load_puma_file`**: format detection, optional units row removal, `**` → missing, numeric coercion for **measurement** columns.
- **ZEIT** (and related meta columns) are **not** coerced to numeric so time strings stay available for **violation timestamps**.
- **Canonical dataframe** merges duplicate column names (e.g. `.1` suffix preference).
- For each **enabled** limit with a matching column: all numeric **rows** are evaluated. **HIGH** if any value &gt; upper; **LOW** if any &lt; lower (HIGH wins if both); **OK** if in band; **NO_DATA** if no column or no valid numbers.
- Violation **ZEIT** values are stored in `measurements.timestamp` (comma-separated, capped for display). **Re-run analysis** after updating the app if older sessions show **—** in the ZEIT column.

## Configuration files (runtime)

| Path | Purpose |
|------|---------|
| `config/settings.json` | Last project id, last PUMA path, window geometry, results filter prefs |
| `config/user_engine_types.json` | Extra engine type names (gitignored if you prefer local only) |
| `config/user_limit_categories.json` | Extra category filter presets (gitignored) |
| `bosch_plausibility_data.db` | SQLite database (local; gitignored) |

## UI theming

- CustomTkinter theme: **`assets/themes/bosch_ctk.json`** (Bosch red primary; bundled with PyInstaller).
- Window icon: solid red tile via Pillow; on Windows an `.ico` is also applied for the title bar.

## Run in GitHub Codespaces

### CLI (no GUI)

```bash
cd /workspaces/<YOUR-REPO-NAME>
pip install -r requirements.txt
python3 scripts/cli_plausibility.py create-project --name "MyTest" --test-bed TB-03
python3 scripts/cli_plausibility.py list-projects
python3 scripts/cli_plausibility.py run --project-id 1 --file ./your_data.xlsx
```

### GUI via noVNC

Tk needs a display. The devcontainer starts a virtual desktop on port **6080**.

1. Open **Ports** → port **6080** → **Public** → open in browser.
2. In the desktop **xterm** or VS Code terminal (with `DISPLAY=:99`): `python3 main.py` or `./scripts/codespace_run_gui.sh`.
3. If the UI is clipped, the container sets **`BOSCH_PLAUS_GEOMETRY`** (e.g. `1280x720`). Adjust if needed.

Diagnostics:

```bash
./scripts/check_novnc.sh
tail -50 /tmp/bosch-plausibility-desktop.log
```

Headless smoke test:

```bash
./scripts/run_headless.sh
```

## Tests

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## Project layout (high level)

```
main.py                 # Entry point
core/                   # Plausibility engine, PUMA loading, analysis, reports
database/               # SQLite schema + manager + migrations
ui/                     # CustomTkinter shell, pages, components
assets/themes/          # CustomTkinter Bosch theme JSON
scripts/                # CLI, Codespace helpers
tests/                  # Unit tests
```

## License / branding

Bosch naming and colors follow internal Bosch Engineering usage. Replace or add **`assets/bosch_logo.png`** if your PDF reports should embed a corporate logo (see `core/report_generator.py`).
