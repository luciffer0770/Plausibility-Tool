"""RESULTS tab: summary, ttk table, filters, session note, export/copy."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Optional

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from core.analysis_service import measurements_to_summary_counts, sort_measurement_results
from core.results_export import export_measurements_excel
from core.user_settings import load_settings, save_settings
from database.db_manager import DatabaseManager
from ui.components.filter_bar import FilterBar
from ui.components.results_treeview import ResultsTreeview
from ui.pages.base_page import BasePage
from ui.pages.parameter_detail import ParameterDetailPanel
from ui.theme import (
    BOSCH_DARK_GRAY,
    BOSCH_LIGHT_GRAY,
    BOSCH_MID_GRAY,
    BOSCH_RED,
    BOSCH_WHITE,
    GRID,
    font_body,
    font_small,
)


class AnalysisPage(BasePage):
    """Plausibility results."""

    def __init__(self, parent: ctk.CTkFrame, controller: Any) -> None:
        super().__init__(parent, controller)
        self._all_rows: list[dict[str, Any]] = []
        self._last_selected: Optional[dict[str, Any]] = None
        self._mpl_canvas: Any = None
        self._charts_expanded = ctk.BooleanVar(value=True)
        self._empty_frame: Optional[ctk.CTkFrame] = None
        self._content_frame: Optional[ctk.CTkFrame] = None
        self.setup_ui()

    def setup_ui(self) -> None:
        self.configure(fg_color=BOSCH_LIGHT_GRAY)

        self.session_banner = ctk.CTkLabel(
            self,
            text="",
            font=font_small(),
            text_color="#333333",
            anchor="w",
        )
        self.session_banner.pack(fill="x", padx=GRID, pady=(GRID, 0))

        self.compare_label = ctk.CTkLabel(
            self,
            text="",
            font=font_small(),
            text_color="#666666",
            anchor="w",
        )
        self.compare_label.pack(fill="x", padx=GRID, pady=(2, 0))

        self._empty_frame = ctk.CTkFrame(self, fg_color=BOSCH_LIGHT_GRAY)
        self._build_empty_state(self._empty_frame)

        self._content_frame = ctk.CTkFrame(self, fg_color=BOSCH_LIGHT_GRAY)

        cards = ctk.CTkFrame(self._content_frame, fg_color="transparent")
        cards.pack(fill="x", padx=GRID, pady=GRID)

        self.card_total = self._mk_card(cards, "TOTAL CHECKED", "0", "#EEEEEE", "#333333")
        self.card_pass = self._mk_card(cards, "WITHIN LIMITS", "0", "#E8F5E9", "#1B5E20")
        self.card_high = self._mk_card(cards, "ABOVE UPPER", "0", "#FFEBEE", "#C62828")
        self.card_low = self._mk_card(cards, "BELOW LOWER", "0", "#FFF9C4", "#F57F17")

        toolbar = ctk.CTkFrame(self._content_frame, fg_color="transparent")
        toolbar.pack(fill="x", padx=GRID, pady=(0, GRID))
        toolbar.grid_columnconfigure(0, weight=1)

        self.filter_bar = FilterBar(toolbar, self._on_filter)
        self.filter_bar.grid(row=0, column=0, sticky="ew", padx=(0, GRID))

        actions = ctk.CTkFrame(toolbar, fg_color="transparent")
        actions.grid(row=0, column=1, sticky="e")
        _bh = 36
        ctk.CTkButton(
            actions,
            text="Copy row",
            width=96,
            height=_bh,
            corner_radius=4,
            fg_color=BOSCH_WHITE,
            text_color=BOSCH_DARK_GRAY,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
            hover_color="#EEEEEE",
            font=font_small(),
            command=self._copy_selected_row,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            actions,
            text="Export failed",
            width=118,
            height=_bh,
            corner_radius=4,
            fg_color=BOSCH_WHITE,
            text_color=BOSCH_DARK_GRAY,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
            hover_color="#EEEEEE",
            font=font_small(),
            command=self._export_failed,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            actions,
            text="Excel report…",
            width=124,
            height=_bh,
            corner_radius=4,
            fg_color=BOSCH_RED,
            hover_color="#C40007",
            font=font_small(),
            command=lambda: self.controller.show_page("reports"),
        ).pack(side="left", padx=0)

        main_card = ctk.CTkFrame(
            self._content_frame,
            fg_color=BOSCH_WHITE,
            corner_radius=8,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
        )
        main_card.pack(fill="both", expand=True, padx=GRID, pady=(0, GRID))

        split = ctk.CTkFrame(main_card, fg_color="transparent")
        split.pack(fill="both", expand=True, padx=GRID, pady=GRID)

        tk_host = tk.Frame(split, bg=BOSCH_WHITE, highlightthickness=0)
        tk_host.pack(side="left", fill="both", expand=True, padx=(0, GRID))

        self.table = ResultsTreeview(tk_host, on_row_select=self._on_row)
        self.table.pack(fill="both", expand=True)

        self.detail = ParameterDetailPanel(split)
        self.detail.pack(side="right", fill="y")

        self._charts_frame = ctk.CTkFrame(self._content_frame, fg_color="transparent")
        self._charts_frame.pack(fill="x", padx=GRID, pady=(0, GRID))

        toggle_row = ctk.CTkFrame(self._charts_frame, fg_color="transparent")
        toggle_row.pack(fill="x", pady=(0, 4))
        ctk.CTkCheckBox(
            toggle_row,
            text="Show failure charts",
            variable=self._charts_expanded,
            command=self._toggle_charts,
            font=font_small(),
        ).pack(side="left")

        self._charts_inner = ctk.CTkFrame(
            self._charts_frame,
            fg_color=BOSCH_WHITE,
            corner_radius=6,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
        )

        left = ctk.CTkFrame(self._charts_inner, fg_color=BOSCH_WHITE)
        left.pack(side="left", fill="both", expand=True, padx=GRID, pady=GRID)
        ctk.CTkLabel(left, text="Failure distribution by type", font=font_body()).pack(anchor="w")
        self.fig = Figure(figsize=(4, 2.0), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self._mpl_canvas = FigureCanvasTkAgg(self.fig, master=left)
        self._mpl_canvas.get_tk_widget().pack(fill="both", expand=True)

        right = ctk.CTkFrame(self._charts_inner, fg_color=BOSCH_WHITE, width=240)
        right.pack(side="right", fill="y", padx=GRID, pady=GRID)
        right.pack_propagate(False)
        ctk.CTkLabel(right, text="Top failed parameters", font=font_body()).pack(anchor="w")
        self.top_fail_box = ctk.CTkTextbox(right, height=100, font=font_small(), border_color=BOSCH_MID_GRAY)
        self.top_fail_box.pack(fill="both", expand=True)

        self._charts_inner.pack(fill="x", pady=0)

        self._apply_results_visibility(False)

    def _build_empty_state(self, parent: ctk.CTkFrame) -> None:
        box = ctk.CTkFrame(parent, fg_color=BOSCH_WHITE, corner_radius=8, border_width=1, border_color=BOSCH_MID_GRAY)
        box.pack(fill="both", expand=True, padx=GRID, pady=GRID)
        ctk.CTkLabel(
            box,
            text="No results yet",
            font=font_body(),
            text_color="#333333",
        ).pack(pady=(GRID * 2, 8))
        ctk.CTkLabel(
            box,
            text="Run a plausibility check from Upload & Evaluate to see results here.",
            font=font_small(),
            text_color="#666666",
        ).pack(pady=(0, GRID))
        ctk.CTkButton(
            box,
            text="Go to UPLOAD & EVALUATE",
            width=220,
            height=40,
            fg_color=BOSCH_RED,
            font=font_body(),
            command=lambda: self.controller.show_page("upload"),
        ).pack(pady=GRID)

    def _apply_results_visibility(self, has_session: bool) -> None:
        if self._empty_frame is None or self._content_frame is None:
            return
        if has_session:
            self._empty_frame.pack_forget()
            self._content_frame.pack(fill="both", expand=True)
        else:
            self._content_frame.pack_forget()
            self._empty_frame.pack(fill="both", expand=True)

    def _toggle_charts(self) -> None:
        if self._charts_expanded.get():
            self._charts_inner.pack(fill="x", pady=0)
        else:
            self._charts_inner.pack_forget()

    def _mk_card(
        self,
        parent: ctk.CTkFrame,
        title: str,
        val: str,
        bg: str,
        value_color: str,
    ) -> ctk.CTkLabel:
        """Summary tile: large value on top, label below (reference layout)."""
        f = ctk.CTkFrame(
            parent,
            fg_color=bg,
            corner_radius=8,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
            width=160,
            height=96,
        )
        f.pack(side="left", padx=(0, 8), pady=0)
        f.pack_propagate(False)
        inner = ctk.CTkFrame(f, fg_color="transparent")
        inner.pack(expand=True, fill="both", padx=12, pady=12)
        lbl = ctk.CTkLabel(
            inner,
            text=val,
            font=("Segoe UI", 28, "bold"),
            text_color=value_color,
        )
        lbl.pack(anchor="center", pady=(0, 4))
        ctk.CTkLabel(
            inner,
            text=title.upper(),
            font=("Segoe UI", 9),
            text_color=BOSCH_DARK_GRAY,
        ).pack(anchor="center")
        return lbl

    def on_show(self) -> None:
        s = load_settings()
        self.filter_bar.apply_saved(s)
        self._reload()

    def _reload(self) -> None:
        proj = self.controller.current_project
        if proj is None or proj.id is None:
            self._all_rows = []
            self._apply_results_visibility(False)
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
            self._apply_results_visibility(False)
            self.session_banner.configure(text="")
            self.compare_label.configure(text="")
            return

        self._apply_results_visibility(True)
        sess = db.get_upload_session(sid)
        if sess:
            note = (sess.get("session_note") or "").strip()
            fn = sess.get("file_name", "")
            ts = sess.get("upload_date") or ""
            self.session_banner.configure(
                text=f"Session #{sid}  ·  {fn}"
                + (f"  ·  {ts}" if ts else "")
                + (f"  ·  Note: {note}" if note else "")
            )
            prev_list = db.list_upload_sessions(proj.id, limit=10)
            prev = None
            for srow in prev_list:
                if srow["id"] != sid:
                    prev = srow
                    break
            if prev:
                pc = measurements_to_summary_counts(
                    db.get_measurements_for_session(int(prev["id"]))
                )
                cc = measurements_to_summary_counts(db.get_measurements_for_session(sid))
                self.compare_label.configure(
                    text=(
                        f"vs previous run ({prev.get('file_name', '')}): "
                        f"OK {pc.get('OK', 0)}→{cc.get('OK', 0)}  "
                        f"HIGH {pc.get('HIGH', 0)}→{cc.get('HIGH', 0)}  "
                        f"LOW {pc.get('LOW', 0)}→{cc.get('LOW', 0)}"
                    )
                )
            else:
                self.compare_label.configure(text="")
        else:
            self.session_banner.configure(text="")

        rows = db.get_measurements_for_session(sid)
        self._all_rows = sort_measurement_results(rows)
        self._apply_filters()
        self._update_charts()

    def _set_cards(self, total: int, ok: int, high: int, low: int) -> None:
        self.card_total.configure(text=str(total))
        self.card_pass.configure(text=str(ok))
        self.card_high.configure(text=str(high))
        self.card_low.configure(text=str(low))

    def _on_filter(self, show: str, ptype: str) -> None:
        save_settings(self.filter_bar.snapshot())
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

    def _export_failed(self) -> None:
        failed = [
            r
            for r in self._all_rows
            if str(r.get("status", "")) in ("HIGH", "LOW", "FAIL")
        ]
        if not failed:
            messagebox.showinfo("Bosch Plausibility Check", "No failed rows in this session.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="failed_parameters.xlsx",
        )
        if not path:
            return
        try:
            export_measurements_excel(Path(path), failed, title="Failed")
            messagebox.showinfo("Bosch Plausibility Check", f"Saved:\n{path}")
        except Exception as e:
            messagebox.showerror("Bosch Plausibility Check", str(e))

    def _copy_selected_row(self) -> None:
        m = self._last_selected
        if not m:
            messagebox.showinfo("Bosch Plausibility Check", "Click a row in the table first.")
            return
        zt = str(m.get("timestamp") or "").strip()
        line = (
            f"{m.get('parameter_name')}\t"
            f"min={m.get('value_min')}\tmax={m.get('value_max')}\tavg={m.get('value_avg')}\t"
            f"zeit_out_of_range={zt or '—'}\t"
            f"status={m.get('status')}"
        )
        root = self.winfo_toplevel()
        root.clipboard_clear()
        root.clipboard_append(line)
        root.update()

    def _update_charts(self) -> None:
        by_cat: dict[str, int] = {}
        for r in self._all_rows:
            st = str(r.get("status", ""))
            if st not in ("HIGH", "LOW", "FAIL"):
                continue
            cat = str(r.get("category") or "Other")
            by_cat[cat] = by_cat.get(cat, 0) + 1

        self.ax.clear()
        if by_cat:
            names = list(by_cat.keys())
            vals = [by_cat[k] for k in names]
            self.ax.barh(names, vals, color=BOSCH_RED)
            self.ax.set_xlabel("Count")
        else:
            self.ax.text(0.5, 0.5, "No failures", ha="center", va="center", fontsize=10, color="#888888")
            self.ax.set_axis_off()
        self.fig.tight_layout()
        if self._mpl_canvas:
            self._mpl_canvas.draw()

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
        self._last_selected = m
        self.detail.show_measurement(m)
