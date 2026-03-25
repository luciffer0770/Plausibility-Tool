"""RESULTS tab: summary + table + charts."""

from __future__ import annotations

from typing import Any, Optional

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from core.analysis_service import measurements_to_summary_counts, sort_measurement_results
from database.db_manager import DatabaseManager
from ui.components.data_table import DataTable
from ui.components.filter_bar import FilterBar
from ui.pages.base_page import BasePage
from ui.pages.parameter_detail import ParameterDetailPanel
from ui.theme import (
    BOSCH_LIGHT_GRAY,
    BOSCH_MID_GRAY,
    BOSCH_RED,
    BOSCH_WHITE,
    GRID,
    STATUS_FAIL,
    STATUS_OK,
    font_body,
    font_small,
)


class AnalysisPage(BasePage):
    """Plausibility results."""

    def __init__(self, parent: ctk.CTkFrame, controller: Any) -> None:
        super().__init__(parent, controller)
        self._all_rows: list[dict[str, Any]] = []
        self._canvas: Any = None
        self.setup_ui()

    def setup_ui(self) -> None:
        self.configure(fg_color=BOSCH_LIGHT_GRAY)

        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="x", padx=GRID, pady=GRID)

        self.card_total = self._mk_card(cards, "TOTAL CHECKED", "0", "#E8E8E8")
        self.card_pass = self._mk_card(cards, "PASSED", "0", "#E8F5E9")
        self.card_high = self._mk_card(cards, "ABOVE", "0", "#FDE8E8")
        self.card_low = self._mk_card(cards, "BELOW LOW", "0", "#FDE8E8")

        bar = ctk.CTkFrame(self, fg_color=BOSCH_LIGHT_GRAY)
        bar.pack(fill="x", padx=GRID, pady=(0, GRID))
        self.filter_bar = FilterBar(bar, self._on_filter)
        self.filter_bar.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            bar,
            text="EXPORT EXCEL REPORT",
            width=180,
            height=34,
            corner_radius=4,
            fg_color=BOSCH_RED,
            hover_color="#C40007",
            font=font_body(),
            command=lambda: self.controller.show_page("reports"),
        ).pack(side="right", padx=8)

        split = ctk.CTkFrame(self, fg_color="transparent")
        split.pack(fill="both", expand=True, padx=GRID, pady=0)

        self.table = DataTable(split, on_row_click=self._on_row)
        self.table.pack(side="left", fill="both", expand=True)

        self.detail = ParameterDetailPanel(split)
        self.detail.pack(side="right", fill="y", padx=(GRID, 0))

        charts = ctk.CTkFrame(
            self,
            fg_color=BOSCH_WHITE,
            corner_radius=6,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
        )
        charts.pack(fill="x", padx=GRID, pady=GRID)

        left = ctk.CTkFrame(charts, fg_color=BOSCH_WHITE)
        left.pack(side="left", fill="both", expand=True, padx=GRID, pady=GRID)
        ctk.CTkLabel(left, text="Failure distribution by type", font=font_body()).pack(anchor="w")
        self.fig = Figure(figsize=(4, 2.2), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self.fig, master=left)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        right = ctk.CTkFrame(charts, fg_color=BOSCH_WHITE, width=260)
        right.pack(side="right", fill="y", padx=GRID, pady=GRID)
        right.pack_propagate(False)
        ctk.CTkLabel(right, text="Top failed parameters", font=font_body()).pack(anchor="w")
        self.top_fail_box = ctk.CTkTextbox(right, height=120, font=font_small(), border_color=BOSCH_MID_GRAY)
        self.top_fail_box.pack(fill="both", expand=True)

    def _mk_card(self, parent: ctk.CTkFrame, title: str, val: str, accent: str) -> ctk.CTkLabel:
        f = ctk.CTkFrame(
            parent,
            fg_color=BOSCH_WHITE,
            corner_radius=6,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
            width=140,
            height=72,
        )
        f.pack(side="left", padx=6, pady=2)
        f.pack_propagate(False)
        top = ctk.CTkFrame(f, fg_color=accent, height=4, corner_radius=0)
        top.pack(fill="x")
        ctk.CTkLabel(f, text=title, font=font_small(), text_color="#333333").pack(anchor="w", padx=8, pady=(4, 0))
        lbl = ctk.CTkLabel(f, text=val, font=("Segoe UI", 18, "bold"), text_color="#333333")
        lbl.pack(anchor="w", padx=8)
        return lbl

    def on_show(self) -> None:
        self._reload()

    def _reload(self) -> None:
        proj = self.controller.current_project
        if proj is None or proj.id is None:
            self._all_rows = []
            self.table.set_rows([])
            self._set_cards(0, 0, 0, 0)
            return

        sid = self.controller.current_session_id
        db: DatabaseManager = self.controller.db
        if sid is None:
            sessions = db.list_upload_sessions(proj.id, limit=1)
            if sessions:
                self.controller.set_current_session(sessions[0]["id"])
                sid = sessions[0]["id"]
        if sid is None:
            self._all_rows = []
            self.table.set_rows([])
            self._set_cards(0, 0, 0, 0)
            return

        rows = db.get_measurements_for_session(sid)
        self._all_rows = sort_measurement_results(rows)
        self._apply_filters()
        self._update_charts()

    def _set_cards(self, total: int, ok: int, high: int, low: int) -> None:
        self.card_total.configure(text=str(total))
        self.card_pass.configure(text=str(ok), text_color=STATUS_OK)
        self.card_high.configure(text=str(high), text_color=STATUS_FAIL if high else "#333333")
        self.card_low.configure(text=str(low), text_color=STATUS_FAIL if low else "#333333")

    def _on_filter(self, show: str, ptype: str) -> None:
        self._apply_filters(show, ptype)

    def _apply_filters(self, show: Optional[str] = None, ptype: Optional[str] = None) -> None:
        show = show or self.filter_bar.show_var.get()
        ptype = ptype or self.filter_bar.type_var.get()
        q = self.filter_bar.get_search()

        filtered: list[dict[str, Any]] = []
        for r in self._all_rows:
            st = str(r.get("status", ""))
            if show == "Failed only" and st in ("OK",):
                continue
            if show == "Passed only" and st not in ("OK",):
                continue
            pt = str(r.get("param_type", r.get("parameter_type", ""))).lower()
            if ptype != "All" and ptype not in pt:
                continue
            if q and q not in str(r.get("parameter_name", "")).lower() and q not in str(
                r.get("description", "")
            ).lower():
                continue
            filtered.append(r)

        self.table.set_rows(filtered)

        c = measurements_to_summary_counts(self._all_rows)
        total = c.get("TOTAL", len(self._all_rows))
        self._set_cards(
            total,
            c.get("OK", 0),
            c.get("HIGH", 0),
            c.get("LOW", 0),
        )

    def _update_charts(self) -> None:
        by_cat: dict[str, int] = {}
        fails: list[tuple[str, int]] = []
        for r in self._all_rows:
            st = str(r.get("status", ""))
            if st not in ("HIGH", "LOW", "FAIL"):
                continue
            cat = str(r.get("category") or "Other")
            by_cat[cat] = by_cat.get(cat, 0) + 1
            name = str(r.get("parameter_name", ""))
            fails.append((name, 1))

        self.ax.clear()
        if by_cat:
            names = list(by_cat.keys())
            vals = [by_cat[k] for k in names]
            self.ax.barh(names, vals, color=BOSCH_RED)
            self.ax.set_xlabel("Count")
        else:
            self.ax.text(0.5, 0.5, "No failures", ha="center", va="center")
        self.fig.tight_layout()
        if self._canvas:
            self._canvas.draw()

        agg: dict[str, int] = {}
        for r in self._all_rows:
            if str(r.get("status", "")) in ("HIGH", "LOW", "FAIL"):
                n = str(r.get("parameter_name", ""))
                agg[n] = agg.get(n, 0) + 1
        top = sorted(agg.items(), key=lambda x: -x[1])[:5]
        self.top_fail_box.delete("1.0", "end")
        for name, cnt in top:
            self.top_fail_box.insert("end", f"{name}:  {cnt}\n")

    def _on_row(self, m: dict[str, Any]) -> None:
        self.detail.show_measurement(m)
