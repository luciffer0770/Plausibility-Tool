"""Scrollable results table (v3 columns)."""

from __future__ import annotations

from typing import Any, Callable, Optional

import customtkinter as ctk

from core.plausibility_engine import limits_display_str
from ui.theme import (
    BOSCH_DARK_GRAY,
    BOSCH_MID_GRAY,
    BOSCH_WHITE,
    GRID,
    ROW_ALT_A,
    ROW_ALT_B,
    STATUS_FAIL,
    STATUS_NO_DATA,
    STATUS_OK,
    font_mono,
    font_small,
)

COL_WIDTHS = (72, 140, 88, 64, 40, 56, 56, 56, 100, 56, 140)


def _status_fg(st: str) -> str:
    s = (st or "").upper()
    if s == "OK":
        return STATUS_OK
    if s in ("HIGH", "LOW", "FAIL"):
        return STATUS_FAIL
    return STATUS_NO_DATA


class DataTable(ctk.CTkFrame):
    """Parameter results grid."""

    def __init__(
        self,
        master: object,
        on_row_click: Optional[Callable[[dict[str, Any]], None]] = None,
    ) -> None:
        super().__init__(master, fg_color=BOSCH_WHITE)
        self.on_row_click = on_row_click
        self._row_widgets: list[ctk.CTkFrame] = []

        headers = (
            "Parameter",
            "Description",
            "Category",
            "Type",
            "Runs",
            "Min",
            "Max",
            "Avg",
            "Limits",
            "Status",
            "Root cause",
        )
        head = ctk.CTkFrame(self, fg_color=BOSCH_WHITE)
        head.pack(fill="x", padx=GRID, pady=(GRID, 0))
        for i, (h, w) in enumerate(zip(headers, COL_WIDTHS)):
            ctk.CTkLabel(
                head,
                text=h,
                width=w,
                font=font_small(),
                text_color=BOSCH_DARK_GRAY,
                anchor="w",
            ).grid(row=0, column=i, padx=2, sticky="w")

        sep = ctk.CTkFrame(self, height=1, fg_color=BOSCH_MID_GRAY)
        sep.pack(fill="x", padx=GRID)

        self.body = ctk.CTkScrollableFrame(self, fg_color=BOSCH_WHITE)
        self.body.pack(fill="both", expand=True, padx=GRID, pady=GRID)

    def set_rows(self, rows: list[dict[str, Any]]) -> None:
        for w in self._row_widgets:
            w.destroy()
        self._row_widgets.clear()

        for idx, m in enumerate(rows):
            bg = ROW_ALT_A if idx % 2 == 0 else ROW_ALT_B
            st = str(m.get("status", ""))
            if st in ("HIGH", "LOW", "FAIL"):
                bg = "#FDE8E8"
            elif st in ("NO_DATA", "N/A"):
                bg = "#F5F5F5"

            row_f = ctk.CTkFrame(self.body, fg_color=bg, corner_radius=0)
            row_f.pack(fill="x", pady=1)
            self._row_widgets.append(row_f)

            def _fmt(v: Any) -> str:
                if v is None:
                    return "—"
                if isinstance(v, float):
                    return f"{v:.2f}"
                return str(v)

            lo = m.get("limit_lower")
            hi = m.get("limit_upper")
            unit = str(m.get("unit") or "")
            lims = limits_display_str(
                float(lo) if lo is not None else None,
                float(hi) if hi is not None else None,
                unit,
            )

            vals: list[Any] = [
                str(m.get("parameter_name", "")),
                str(m.get("description", ""))[:36],
                str(m.get("category", ""))[:22],
                str(m.get("param_type", m.get("parameter_type", "")))[:12],
                str(m.get("num_runs", "")),
                _fmt(m.get("value_min")),
                _fmt(m.get("value_max")),
                _fmt(m.get("value_avg")),
                lims[:28],
                st,
                str(m.get("root_cause", ""))[:48],
            ]
            fam, sz = font_small()
            for col, (txt, w) in enumerate(zip(vals, COL_WIDTHS)):
                fg = _status_fg(st) if col == 9 else BOSCH_DARK_GRAY
                if col in (5, 6, 7, 8):
                    fnt = font_mono()
                elif col == 9 and st not in ("OK", "NO_DATA", "N/A", ""):
                    fnt = (fam, sz, "bold")
                else:
                    fnt = font_small()
                ctk.CTkLabel(
                    row_f,
                    text=txt,
                    width=w,
                    font=fnt,
                    text_color=fg,
                    anchor="w",
                ).grid(row=0, column=col, padx=2, pady=2, sticky="w")

            if self.on_row_click:

                def _click(_e: object, mm: dict[str, Any] = m) -> None:
                    self.on_row_click(mm)

                row_f.bind("<Button-1>", _click)
                for child in row_f.winfo_children():
                    child.bind("<Button-1>", _click)
