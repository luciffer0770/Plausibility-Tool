# PRÜF — Plausibility Check Tool

Desktop Python application for Bosch engine test bed plausibility checks against PUMA measurement exports (Excel/CSV).

## Requirements

- Python 3.10+
- Windows 10/11 (primary target; runs on Linux for development)

## Run

```bash
pip install -r requirements.txt
python3 main.py
```

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
