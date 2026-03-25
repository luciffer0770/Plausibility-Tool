"""PUMA file upload, ZEIT-based preview, run analysis."""

from __future__ import annotations

import logging
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
            text="Supported: .xlsx, .xls (TSV), .csv",
            font=font_small(),
            text_color=BOSCH_DARK_GRAY,
        ).pack(anchor="w", pady=(0, GRID))

        self.drop = FileDropZone(left, self._on_file)
        self.drop.pack(fill="x", pady=(0, GRID))

        self.run_btn = ctk.CTkButton(
            left,
            text="▶ RUN PLAUSIBILITY CHECK",
            height=40,
            corner_radius=4,
            fg_color=BOSCH_RED,
            hover_color="#C40007",
            font=font_body(),
            command=self._run_analysis,
            state="disabled",
        )
        self.run_btn.pack(fill="x")

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

        self.preview = ctk.CTkTextbox(prev_wrap, font=font_small(), border_color=BOSCH_MID_GRAY)
        self.preview.pack(fill="both", expand=True, padx=GRID, pady=(0, GRID))

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
            messagebox.showerror("PRÜF", f"Could not load file:\n{e}")
            self._df_raw = None
            self.run_btn.configure(state="disabled")
            return

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

        prev_df = preview_parameters_by_zeit(df, max_runs=25, max_parameters=100)
        self.preview.delete("1.0", "end")
        if prev_df.empty:
            self.preview.insert("1.0", "(No parameter columns to preview)")
        else:
            self.preview.insert("1.0", prev_df.to_string(max_cols=30))

        self.run_btn.configure(state="normal")

    def _run_analysis(self) -> None:
        if not self._path:
            messagebox.showwarning("PRÜF", "Select a file first.")
            return
        if self._df_raw is None or self._df_raw.empty:
            messagebox.showwarning("PRÜF", "No data loaded.")
            return
        proj = self.controller.current_project
        if not proj or proj.id is None:
            messagebox.showwarning("PRÜF", "Select or create a project on the PROJECTS tab first.")
            return
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
            )
            self.controller.set_current_session(sid)
            messagebox.showinfo("PRÜF", f"Analysis complete. Session id {sid}.")
            self.controller.show_page("analysis")
        except Exception as e:
            logger.exception("Analysis failed")
            messagebox.showerror("PRÜF", str(e))
