"""Scrollable results table with row tinting."""

from __future__ import annotations

from typing import Any, Callable, Optional

import customtkinter as ctk

from ui.components.status_badge import StatusBadge
from ui.theme import (
    BOSCH_DARK_GRAY,
    BOSCH_MID_GRAY,
    BOSCH_WHITE,
    GRID,
    ROW_FAIL_BG,
    ROW_WARN_BG,
    ROW_ALT_A,
    ROW_ALT_B,
    font_mono,
    font_small,
)

COL_WIDTHS = (36, 88, 200, 72, 64, 64, 64, 72, 72, 80, 160)


class DataTable(ctk.CTkFrame):
    """Parameter results grid."""

    def __init__(
        self,
        master: object,
        on_row_click: Optional[Callable[[dict[str, Any]], None]] = None,
    ) -> None:
        super().__init__(master, fg_color=BOSCH_WHITE)
        self.on_row_click = on_row_click
        self._rows: list[dict[str, Any]] = []
        self._row_widgets: list[ctk.CTkFrame] = []

        headers = (
            "St",
            "Parameter",
            "Description",
            "Value",
            "Min",
            "Max",
            "Avg",
            "Lo",
            "Hi",
            "Dev %",
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
        """Render measurement dicts."""
        for w in self._row_widgets:
            w.destroy()
        self._row_widgets.clear()
        self._rows = rows

        for idx, m in enumerate(rows):
            bg = ROW_ALT_A if idx % 2 == 0 else ROW_ALT_B
            st = str(m.get("status", ""))
            if st == "FAIL":
                bg = ROW_FAIL_BG
            elif st == "WARNING":
                bg = ROW_WARN_BG

            row_f = ctk.CTkFrame(self.body, fg_color=bg, corner_radius=0)
            row_f.pack(fill="x", pady=1)
            self._row_widgets.append(row_f)

            badge_fr = ctk.CTkFrame(row_f, fg_color=bg, width=COL_WIDTHS[0])
            badge_fr.grid(row=0, column=0, padx=2, pady=2, sticky="nw")
            StatusBadge(badge_fr, st, size=12).pack(padx=4, pady=4)

            def _fmt(v: Any) -> str:
                if v is None:
                    return "—"
                if isinstance(v, float):
                    return f"{v:.4g}"
                return str(v)

            vals = [
                str(m.get("parameter_name", "")),
                str(m.get("description", ""))[:48],
                _fmt(m.get("measured_value")),
                _fmt(m.get("value_min")),
                _fmt(m.get("value_max")),
                _fmt(m.get("value_avg")),
                _fmt(m.get("limit_lower")),
                _fmt(m.get("limit_upper")),
                _fmt(m.get("deviation")),
                str(m.get("root_cause", ""))[:60],
            ]
            for col, (txt, w) in enumerate(zip(vals, COL_WIDTHS[1:]), start=1):
                ctk.CTkLabel(
                    row_f,
                    text=txt,
                    width=w,
                    font=font_mono() if col in (3, 4, 5, 6, 7, 8, 9) else font_small(),
                    text_color=BOSCH_DARK_GRAY,
                    anchor="w",
                ).grid(row=0, column=col, padx=2, pady=2, sticky="w")

            if self.on_row_click:

                def _click(_e: object, mm: dict[str, Any] = m) -> None:
                    self.on_row_click(mm)

                row_f.bind("<Button-1>", _click)
                for child in row_f.winfo_children():
                    child.bind("<Button-1>", _click)
