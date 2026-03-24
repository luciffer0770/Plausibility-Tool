"""Main plausibility results table."""

from __future__ import annotations

from typing import Any, Optional

import customtkinter as ctk

from core.analysis_service import measurements_to_summary_counts, sort_measurement_results
from database.db_manager import DatabaseManager
from ui.components.data_table import DataTable
from ui.components.filter_bar import FilterBar
from ui.pages.base_page import BasePage
from ui.pages.parameter_detail import ParameterDetailPanel
from ui.theme import BOSCH_LIGHT_GRAY, BOSCH_WHITE, GRID, font_h3


class AnalysisPage(BasePage):
    """Filtered sortable-style results (status sort fixed)."""

    def __init__(self, parent: ctk.CTkFrame, controller: Any) -> None:
        super().__init__(parent, controller)
        self._all_rows: list[dict[str, Any]] = []
        self._param_types: dict[str, str] = {}
        self.setup_ui()

    def setup_ui(self) -> None:
        self.configure(fg_color=BOSCH_LIGHT_GRAY)
        self.summary_bar = ctk.CTkFrame(
            self,
            fg_color=BOSCH_WHITE,
            corner_radius=8,
            border_width=1,
            border_color="#D9D9D9",
        )
        self.summary_bar.pack(fill="x", padx=GRID, pady=GRID)
        self.summary_label = ctk.CTkLabel(
            self.summary_bar,
            text="",
            font=font_h3(),
            text_color="#333333",
        )
        self.summary_label.pack(padx=GRID * 2, pady=GRID)

        self.filter_bar = FilterBar(self, self._on_filter)
        self.filter_bar.pack(fill="x", padx=GRID, pady=(0, GRID))

        split = ctk.CTkFrame(self, fg_color="transparent")
        split.pack(fill="both", expand=True, padx=GRID, pady=0)

        self.table = DataTable(split, on_row_click=self._on_row)
        self.table.pack(side="left", fill="both", expand=True)

        self.detail = ParameterDetailPanel(split)
        self.detail.pack(side="right", fill="y", padx=(GRID, 0))

    def on_show(self) -> None:
        self._reload()

    def _reload(self) -> None:
        sid = self.controller.current_session_id
        db: DatabaseManager = self.controller.db
        if sid is None:
            sessions = db.list_upload_sessions(self.controller.current_project.id or 0, limit=1)
            if sessions:
                self.controller.set_current_session(sessions[0]["id"])
                sid = sessions[0]["id"]
        if sid is None:
            self._all_rows = []
            self._param_types = {}
            self.table.set_rows([])
            self.summary_label.configure(text="No upload session — use Upload.")
            return

        rows = db.get_measurements_for_session(sid)
        proj = self.controller.current_project
        defs = db.get_limit_profile(proj.engine_type.value) if proj else []
        desc = {d.parameter_name: d for d in defs}
        ptype = {d.parameter_name: d.parameter_type.value for d in defs}

        enriched: list[dict[str, Any]] = []
        for m in rows:
            d = desc.get(m["parameter_name"])
            row = dict(m)
            row["description"] = d.description if d else ""
            row["parameter_type"] = ptype.get(m["parameter_name"], "Other")
            enriched.append(row)

        self._all_rows = sort_measurement_results(enriched)
        self._param_types = {r["parameter_name"]: r.get("parameter_type", "Other") for r in enriched}
        self._apply_filters()

    def _on_filter(self, status: str, ptype: str) -> None:
        self._apply_filters(status, ptype)

    def _apply_filters(self, status: Optional[str] = None, ptype: Optional[str] = None) -> None:
        status = status or self.filter_bar.status_var.get()
        ptype = ptype or self.filter_bar.type_var.get()
        q = self.filter_bar.get_search()
        filtered: list[dict[str, Any]] = []
        for r in self._all_rows:
            if status != "All" and str(r.get("status")) != status:
                continue
            if ptype != "All" and str(r.get("parameter_type")) != ptype:
                continue
            if q and q not in str(r.get("parameter_name", "")).lower() and q not in str(
                r.get("description", "")
            ).lower():
                continue
            filtered.append(r)
        self.table.set_rows(filtered)
        counts = measurements_to_summary_counts(self._all_rows)
        txt = (
            f"OK: {counts['OK']}  |  WARNING: {counts['WARNING']}  |  "
            f"FAIL: {counts['FAIL']}  |  NO DATA: {counts['NO_DATA']}"
        )
        self.summary_label.configure(text=txt)

    def _on_row(self, m: dict[str, Any]) -> None:
        self.detail.show_measurement(m)
