"""PUMA file upload, ZEIT-based preview, run analysis."""

from __future__ import annotations

import logging
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Any, Optional

import customtkinter as ctk
import pandas as pd

from core.data_loader import (
    build_canonical_numeric_df,
    detect_column_mapping,
    load_puma_file,
    preview_parameters_by_zeit,
)
from core.user_settings import load_settings, save_settings
from ui.components.file_drop_zone import FileDropZone
from ui.pages.base_page import BasePage
from ui.theme import BOSCH_DARK_GRAY, BOSCH_LIGHT_GRAY, BOSCH_MID_GRAY, BOSCH_RED, BOSCH_WHITE, GRID, font_body, font_small

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
        self.setup_ui()

    def setup_ui(self) -> None:
        self.configure(fg_color=BOSCH_LIGHT_GRAY)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=GRID, pady=GRID)

        left = ctk.CTkFrame(top, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=(0, GRID))

        ctk.CTkLabel(left, text="Upload PUMA export", font=font_body(), text_color=BOSCH_DARK_GRAY).pack(
            anchor="w", pady=(0, 4)
        )
        ctk.CTkLabel(
            left,
            text="Supported: .xlsx, .xls (TSV), .csv  ·  Press Enter in the session note field to run check",
            font=font_small(),
            text_color=BOSCH_DARK_GRAY,
        ).pack(anchor="w", pady=(0, GRID))

        self.drop = FileDropZone(left, self._on_file)
        self.drop.pack(fill="x", pady=(0, GRID))

        note_row = ctk.CTkFrame(left, fg_color="transparent")
        note_row.pack(fill="x", pady=(0, GRID))
        ctk.CTkLabel(note_row, text="Session note (optional):", font=font_small(), text_color=BOSCH_DARK_GRAY).pack(
            anchor="w"
        )
        self.note_var = ctk.StringVar()
        self.note_entry = ctk.CTkEntry(
            note_row,
            textvariable=self.note_var,
            placeholder_text="e.g. Cold start, Map 2",
            font=font_small(),
            height=32,
        )
        self.note_entry.pack(fill="x", pady=(4, 0))
        self.note_entry.bind("<Return>", self._on_enter_run)

        btn_row = ctk.CTkFrame(left, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, GRID))
        self.run_btn = ctk.CTkButton(
            btn_row,
            text="▶ RUN PLAUSIBILITY CHECK",
            height=44,
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
            width=160,
            height=44,
            corner_radius=4,
            fg_color=BOSCH_WHITE,
            text_color=BOSCH_DARK_GRAY,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
            font=font_body(),
            command=self._rerun_last,
            state="disabled",
        )
        self.rerun_btn.pack(side="right")

        right = ctk.CTkFrame(
            top,
            fg_color=BOSCH_WHITE,
            corner_radius=6,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
            width=400,
        )
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        ctk.CTkLabel(right, text="File metadata", font=font_body(), text_color=BOSCH_DARK_GRAY).pack(
            anchor="w", padx=GRID, pady=(GRID, 4)
        )
        self.meta_box = ctk.CTkTextbox(right, height=160, font=font_small(), border_color=BOSCH_MID_GRAY)
        self.meta_box.pack(fill="x", padx=GRID, pady=4)

        ctk.CTkLabel(right, text="Mapping summary", font=font_body(), text_color=BOSCH_DARK_GRAY).pack(
            anchor="w", padx=GRID, pady=(GRID, 4)
        )
        self.summary = ctk.CTkTextbox(right, height=120, font=font_small(), border_color=BOSCH_MID_GRAY)
        self.summary.pack(fill="x", padx=GRID, pady=(0, GRID))

        prev_wrap = ctk.CTkFrame(self, fg_color=BOSCH_WHITE, corner_radius=6, border_width=1, border_color=BOSCH_MID_GRAY)
        prev_wrap.pack(fill="both", expand=True, padx=GRID, pady=(0, GRID))

        ctk.CTkLabel(
            prev_wrap,
            text="Data preview — rows = parameters, columns = ZEIT (time) per run",
            font=font_body(),
            text_color=BOSCH_DARK_GRAY,
        ).pack(anchor="w", padx=GRID, pady=(GRID, 4))

        self._preview_host = tk.Frame(prev_wrap, bg=BOSCH_WHITE, highlightthickness=0)
        self._preview_host.pack(fill="both", expand=True, padx=GRID, pady=(0, GRID))
        self.preview = tk.Text(
            self._preview_host,
            height=16,
            wrap="none",
            font=("Consolas", 9),
            bg=BOSCH_WHITE,
            fg=BOSCH_DARK_GRAY,
            relief="flat",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=BOSCH_MID_GRAY,
            selectbackground="#CCE5FF",
        )
        pv_sb_y = tk.Scrollbar(self._preview_host, orient="vertical", command=self.preview.yview)
        pv_sb_x = tk.Scrollbar(self._preview_host, orient="horizontal", command=self.preview.xview)
        self.preview.configure(yscrollcommand=pv_sb_y.set, xscrollcommand=pv_sb_x.set)
        self.preview.grid(row=0, column=0, sticky="nsew")
        pv_sb_y.grid(row=0, column=1, sticky="ns")
        pv_sb_x.grid(row=1, column=0, sticky="ew")
        self._preview_host.grid_rowconfigure(0, weight=1)
        self._preview_host.grid_columnconfigure(0, weight=1)

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
        st = "disabled" if busy else "normal"
        if self._path and self._df_raw is not None and not busy:
            self.run_btn.configure(state="normal", text="▶ RUN PLAUSIBILITY CHECK")
        elif busy:
            self.run_btn.configure(state="disabled", text="Working…")
        else:
            self.run_btn.configure(state="disabled", text="▶ RUN PLAUSIBILITY CHECK")
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
            return

        save_settings({"last_puma_path": str(path.resolve())})
        self.rerun_btn.configure(state="normal")

        rpm = self._meta.get("rpm_sample", "—")
        pcount = self._meta.get("parameter_column_count", len(df.columns))
        meta_lines = [
            f"File: {path.name}",
            f"Date (DATUM): {self._meta.get('datum', '—')}",
            f"Version (VERSIONT): {self._meta.get('versiont', '—')}",
            f"Program (PRNAME): {self._meta.get('prname', '—')}",
            f"Engine speed N (1st row): {rpm}",
            f"Data rows (runs): {len(df)}",
            f"Total columns: {len(df.columns)}",
            f"Parameter columns (excl. meta): {pcount}",
            f"File format: {self._meta.get('file_type', '')}",
        ]
        self.meta_box.delete("1.0", "end")
        self.meta_box.insert("1.0", "\n".join(meta_lines))

        lines = [
            f"Canonical numeric columns: {len(canon.columns)}",
            f"Mapped to configured limits: {nlim}",
            "",
            "Sample column names (non-meta):",
        ]
        skip = {"PRNAME", "DATUM", "ZEIT", "VERSIONT", "AVL_INDEP_TIME"}
        extra = [c for c in df.columns if str(c).strip().upper() not in {s.upper() for s in skip}][:20]
        lines.extend(f"  • {c}" for c in extra)
        self.summary.delete("1.0", "end")
        self.summary.insert("1.0", "\n".join(lines))

        prev_df = preview_parameters_by_zeit(df, max_runs=20, max_parameters=60)
        self.preview.delete("1.0", "end")
        if prev_df.empty:
            self.preview.insert("1.0", "(No parameter columns to preview)")
        else:
            self.preview.insert("1.0", prev_df.to_string(max_cols=24))

        if not self._busy:
            self.run_btn.configure(state="normal", text="▶ RUN PLAUSIBILITY CHECK")

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
            messagebox.showinfo("Bosch Plausibility Check", f"Analysis complete. Session id {sid}.")
            self.controller.show_page("analysis")
        except Exception as e:
            logger.exception("Analysis failed")
            messagebox.showerror("Bosch Plausibility Check", str(e))
        finally:
            self._set_busy(False)
