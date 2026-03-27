"""PUMA file upload, ZEIT-based preview table, run analysis."""

from __future__ import annotations

import logging
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, List, Optional, Tuple

import customtkinter as ctk
import pandas as pd

from core.data_loader import (
    build_canonical_numeric_df,
    detect_column_mapping,
    load_puma_file,
    preview_parameters_detailed_table,
)
from core.user_settings import load_settings, save_settings
from ui.components.file_drop_zone import FileDropZone
from ui.pages.base_page import BasePage
from ui.ttk_style import neutral_ctk_entry_focus
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

logger = logging.getLogger(__name__)


class UploadPage(BasePage):
    """Select file, preview parameters × ZEIT, run check."""

    def __init__(self, parent: ctk.CTkFrame, controller: Any) -> None:
        super().__init__(parent, controller)
        self._path: Optional[Path] = None
        self._df_raw: Optional[pd.DataFrame] = None
        self._mapping: dict[str, Any] = {}
        self._meta: dict[str, Any] = {}
        self._busy = False
        self._preview_tree: Optional[ttk.Treeview] = None
        self._preview_wrap: Optional[tk.Frame] = None
        self._preview_cols: List[str] = []
        self.setup_ui()

    def setup_ui(self) -> None:
        self.configure(fg_color=BOSCH_LIGHT_GRAY)

        top_card = ctk.CTkFrame(
            self,
            fg_color=BOSCH_WHITE,
            corner_radius=8,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
        )
        top_card.pack(fill="x", padx=GRID, pady=(GRID // 2, GRID))
        top_card.grid_columnconfigure(0, weight=1, uniform="upload_top")
        top_card.grid_columnconfigure(1, weight=1, uniform="upload_top")

        left_col = ctk.CTkFrame(top_card, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(GRID, GRID // 2), pady=GRID)

        hdr = ctk.CTkFrame(left_col, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(hdr, text="Upload PUMA export", font=font_body(), text_color=BOSCH_DARK_GRAY).pack(anchor="w")
        ctk.CTkLabel(
            hdr,
            text="Formats: .xlsx · .xls (TSV) · .csv",
            font=font_small(),
            text_color=BOSCH_DARK_GRAY,
        ).pack(anchor="w", pady=(2, 0))

        self.drop = FileDropZone(left_col, self._on_file, compact=True)
        self.drop.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(left_col, text="Session note (optional)", font=font_small(), text_color=BOSCH_DARK_GRAY).pack(
            anchor="w"
        )
        self.note_var = ctk.StringVar()
        self.note_entry = ctk.CTkEntry(
            left_col,
            textvariable=self.note_var,
            placeholder_text="e.g. Cold start, Map 2",
            font=font_small(),
            height=30,
            border_color=BOSCH_MID_GRAY,
            fg_color=BOSCH_WHITE,
        )
        self.note_entry.pack(fill="x", pady=(4, 10))
        self.after_idle(neutral_ctk_entry_focus, self.note_entry)
        self.note_entry.bind("<Return>", self._on_enter_run)

        btn_row = ctk.CTkFrame(left_col, fg_color="transparent")
        btn_row.pack(fill="x")
        _bh = 36
        self.run_btn = ctk.CTkButton(
            btn_row,
            text="Run plausibility check",
            height=_bh,
            corner_radius=4,
            fg_color=BOSCH_RED,
            hover_color="#C40007",
            font=font_body(),
            command=self._run_analysis,
            state="disabled",
        )
        self.run_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.rerun_btn = ctk.CTkButton(
            btn_row,
            text="Re-run last file",
            width=132,
            height=_bh,
            corner_radius=4,
            fg_color=BOSCH_WHITE,
            text_color=BOSCH_DARK_GRAY,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
            hover_color="#EEEEEE",
            font=font_small(),
            command=self._rerun_last,
            state="disabled",
        )
        self.rerun_btn.pack(side="right")

        right = ctk.CTkFrame(top_card, fg_color="#FAFAFA", corner_radius=6, border_width=1, border_color=BOSCH_MID_GRAY)
        right.grid(row=0, column=1, sticky="nsew", padx=(GRID // 2, GRID), pady=GRID)

        ctk.CTkLabel(right, text="File metadata", font=font_body(), text_color=BOSCH_DARK_GRAY).pack(
            anchor="w", padx=GRID, pady=(GRID, 4)
        )
        self.meta_box = ctk.CTkTextbox(right, height=92, font=font_small(), border_color=BOSCH_MID_GRAY)
        self.meta_box.pack(fill="x", padx=GRID, pady=(0, 4))

        ctk.CTkLabel(right, text="Mapping summary", font=font_body(), text_color=BOSCH_DARK_GRAY).pack(
            anchor="w", padx=GRID, pady=(4, 4)
        )
        self.summary = ctk.CTkTextbox(right, height=88, font=font_small(), border_color=BOSCH_MID_GRAY)
        self.summary.pack(fill="x", padx=GRID, pady=(0, GRID))

        prev_wrap = ctk.CTkFrame(self, fg_color=BOSCH_WHITE, corner_radius=8, border_width=1, border_color=BOSCH_MID_GRAY)
        prev_wrap.pack(fill="both", expand=True, padx=GRID, pady=(0, GRID))

        ctk.CTkLabel(
            prev_wrap,
            text="Data preview — parameters × ZEIT (time); Unit, Min, Max, Avg across loaded rows",
            font=font_small(),
            text_color=BOSCH_DARK_GRAY,
        ).pack(anchor="w", padx=GRID, pady=(GRID, 4))

        self._preview_wrap = tk.Frame(prev_wrap, bg=BOSCH_WHITE, highlightthickness=0)
        self._preview_wrap.pack(fill="both", expand=True, padx=GRID, pady=(0, GRID))
        self._build_preview_tree_empty()

    def _build_preview_tree_empty(self) -> None:
        if self._preview_wrap is None:
            return
        for w in self._preview_wrap.winfo_children():
            w.destroy()
        self._preview_tree = None
        self._preview_cols = []
        lbl = tk.Label(
            self._preview_wrap,
            text="Browse a file to load preview.",
            bg=BOSCH_WHITE,
            fg=BOSCH_DARK_GRAY,
            font=("Segoe UI", 10),
        )
        lbl.pack(expand=True, pady=GRID * 4)

    def _ensure_preview_tree(self, col_ids: List[str]) -> ttk.Treeview:
        assert self._preview_wrap is not None
        for w in self._preview_wrap.winfo_children():
            w.destroy()

        style = ttk.Style(self._preview_wrap)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "UploadPreview.Treeview",
            rowheight=22,
            fieldbackground=BOSCH_WHITE,
            background=BOSCH_WHITE,
            foreground=BOSCH_DARK_GRAY,
        )
        style.configure(
            "UploadPreview.Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#E8E8E8",
            foreground=BOSCH_DARK_GRAY,
        )
        style.map(
            "UploadPreview.Treeview",
            background=[("selected", "#F5D5D5")],
            foreground=[("selected", BOSCH_DARK_GRAY)],
        )

        tree = ttk.Treeview(
            self._preview_wrap,
            columns=col_ids,
            show="headings",
            style="UploadPreview.Treeview",
            height=14,
        )
        wmap = {
            "Parameter": 120,
            "Unit": 48,
            "Min": 56,
            "Max": 56,
            "Avg": 56,
        }
        for cid in col_ids:
            if cid.startswith("ZEIT "):
                h = cid[5:].strip() or cid
            else:
                h = cid
            tree.heading(cid, text=h, anchor="w")
            w = wmap.get(cid, 88)
            stretch = cid not in ("Parameter", "Unit", "Min", "Max", "Avg")
            tree.column(cid, width=w, minwidth=40, anchor="w", stretch=stretch)

        vsb = ttk.Scrollbar(self._preview_wrap, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(self._preview_wrap, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self._preview_wrap.grid_rowconfigure(0, weight=1)
        self._preview_wrap.grid_columnconfigure(0, weight=1)

        tree.tag_configure("odd", background=BOSCH_WHITE)
        tree.tag_configure("even", background="#F5F5F5")

        self._preview_tree = tree
        self._preview_cols = col_ids
        return tree

    def _fill_preview(self, col_ids: List[str], rows: List[Tuple[str, str, str, str, str, List[str]]]) -> None:
        tree = self._ensure_preview_tree(col_ids)
        tree.delete(*tree.get_children())
        for i, row in enumerate(rows):
            param, unit, mn, mx, av, cells = row
            vals = (param, unit, mn, mx, av) + tuple(cells)
            tag = "even" if i % 2 else "odd"
            tree.insert("", "end", values=vals, tags=(tag,))

    def _on_enter_run(self, _event: object) -> str:
        if not self._busy and str(self.run_btn.cget("state")) == "normal":
            self._run_analysis()
        return "break"

    def on_show(self) -> None:
        s = load_settings()
        lp = s.get("last_puma_path") or ""
        if lp and Path(lp).is_file() and self._path is None:
            self._on_file(Path(lp))

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        if self._path and self._df_raw is not None and not busy:
            self.run_btn.configure(state="normal", text="Run plausibility check")
        elif busy:
            self.run_btn.configure(state="disabled", text="Working…")
        else:
            self.run_btn.configure(state="disabled", text="Run plausibility check")
        self.rerun_btn.configure(state="disabled" if busy else ("normal" if self._path else "disabled"))

    def _on_file(self, path: Path) -> None:
        self._path = path
        try:
            df, self._meta = load_puma_file(path)
            self._df_raw = df
            self._mapping = detect_column_mapping(df)
            canon, _ = build_canonical_numeric_df(df)
            nlim = 0
            proj = self.controller.current_project
            if proj:
                lims = self.controller.db.get_limit_profile(proj.engine_type_key())
                enabled = {d.parameter_name for d in lims if d.is_enabled}
                nlim = sum(1 for c in canon.columns if c in enabled)
        except Exception as e:
            logger.exception("Load failed")
            messagebox.showerror("Bosch Plausibility Check", f"Could not load file:\n{e}")
            self._df_raw = None
            self.run_btn.configure(state="disabled")
            self.rerun_btn.configure(state="disabled")
            self._build_preview_tree_empty()
            return

        save_settings({"last_puma_path": str(path.resolve())})
        self.rerun_btn.configure(state="normal")

        rpm = self._meta.get("rpm_sample", "—")
        pcount = self._meta.get("parameter_column_count", len(df.columns))
        meta_lines = [
            f"File: {path.name}",
            f"DATUM: {self._meta.get('datum', '—')}  |  VERSIONT: {self._meta.get('versiont', '—')}",
            f"PRNAME: {self._meta.get('prname', '—')}  |  N (1st): {rpm}",
            f"Rows: {len(df)}  |  Cols: {len(df.columns)}  |  Params: {pcount}  |  {self._meta.get('file_type', '')}",
        ]
        self.meta_box.delete("1.0", "end")
        self.meta_box.insert("1.0", "\n".join(meta_lines))

        lines = [
            f"Numeric columns: {len(canon.columns)}  |  Match enabled limits: {nlim}",
            "Sample:",
        ]
        skip = {"PRNAME", "DATUM", "ZEIT", "VERSIONT", "AVL_INDEP_TIME"}
        extra = [c for c in df.columns if str(c).strip().upper() not in {s.upper() for s in skip}][:12]
        lines.extend(f"  {c}" for c in extra)
        self.summary.delete("1.0", "end")
        self.summary.insert("1.0", "\n".join(lines))

        col_ids, prow = preview_parameters_detailed_table(df, max_runs=12, max_parameters=60)
        if not col_ids or not prow:
            self._build_preview_tree_empty()
        else:
            self._fill_preview(col_ids, prow)

        if not self._busy:
            self.run_btn.configure(state="normal", text="Run plausibility check")

    def _rerun_last(self) -> None:
        s = load_settings()
        lp = s.get("last_puma_path") or ""
        if not lp or not Path(lp).is_file():
            messagebox.showinfo("Bosch Plausibility Check", "No saved file path. Browse for a file first.")
            return
        self._on_file(Path(lp))
        self._run_analysis()

    def _run_analysis(self) -> None:
        if self._busy:
            return
        if not self._path:
            messagebox.showwarning("Bosch Plausibility Check", "Select a file first.")
            return
        if self._df_raw is None or self._df_raw.empty:
            messagebox.showwarning("Bosch Plausibility Check", "No data loaded.")
            return
        proj = self.controller.current_project
        if not proj or proj.id is None:
            messagebox.showwarning("Bosch Plausibility Check", "Select or create a project on the PROJECTS tab first.")
            return
        self._set_busy(True)
        self.update_idletasks()
        try:
            from core.analysis_service import run_plausibility_for_file

            sid = run_plausibility_for_file(
                self.controller.db,
                proj.id,
                proj.engine_type_key(),
                self._path,
                self._mapping.get("timestamp_col"),
                None,
                file_name=self._path.name,
                session_note=self.note_var.get().strip() or None,
            )
            self.controller.set_current_session(sid)
            rows = self.controller.db.get_measurements_for_session(sid)
            n_warn = sum(1 for r in rows if str(r.get("status", "")).upper() == "WARNING")
            msg = f"Analysis complete. Session id {sid}."
            if n_warn > 0:
                msg += (
                    f"\n\nWarning: {n_warn} column(s) in the file have no limit configured for this engine profile. "
                    "They appear as WARNING at the bottom of Results — add limits in LIMITS CONFIG if needed."
                )
            messagebox.showinfo("Bosch Plausibility Check", msg)
            self.controller.show_page("analysis")
        except Exception as e:
            logger.exception("Analysis failed")
            messagebox.showerror("Bosch Plausibility Check", str(e))
        finally:
            self._set_busy(False)
