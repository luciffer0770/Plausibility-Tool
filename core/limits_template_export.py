"""Export empty limits Excel template (openpyxl — already a project dependency)."""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font


def write_limits_template_excel(path: Path) -> Path:
    """One header row; no data rows — OEM fills offline."""
    path = Path(path)
    wb = Workbook()
    ws = wb.active
    ws.title = "Limits"
    headers = (
        "Parameter",
        "Type",
        "Description",
        "Category",
        "Lower",
        "Upper",
        "Unit",
        "Root Cause",
        "Enabled",
    )
    for col, h in enumerate(headers, start=1):
        c = ws.cell(row=1, column=col, value=h)
        c.font = Font(bold=True)
    ws.freeze_panes = "A2"
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(path))
    return path
