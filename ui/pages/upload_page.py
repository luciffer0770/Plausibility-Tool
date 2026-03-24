"""PUMA file upload and column mapping preview."""

from __future__ import annotations

import logging
from pathlib import Path
from tkinter import messagebox
from typing import Any, Optional

import customtkinter as ctk
import pandas as pd

from core.data_loader import detect_column_mapping, load_dataframe, preview_dataframe
from ui.components.file_drop_zone import FileDropZone
from ui.pages.base_page import BasePage
from ui.theme import BOSCH_DARK_GRAY, BOSCH_LIGHT_GRAY, BOSCH_MID_GRAY, BOSCH_WHITE, GRID, font_body, font_small

logger = logging.getLogger(__name__)


class UploadPage(BasePage):
    """Select file, show mapping summary, confirm import."""

    def __init__(self, parent: ctk.CTkFrame, controller: Any) -> None:
        super().__init__(parent, controller)
        self._path: Optional[Path] = None
        self._mapping: dict[str, Any] = {}
        self._df_preview: Optional[pd.DataFrame] = None
        self.setup_ui()

    def setup_ui(self) -> None:
        self.configure(fg_color=BOSCH_LIGHT_GRAY)
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=GRID, pady=GRID)

        self.drop = FileDropZone(left, self._on_file)
        self.drop.pack(fill="both", expand=True)

        right = ctk.CTkFrame(
            self,
            fg_color=BOSCH_WHITE,
            corner_radius=8,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
            width=420,
        )
        right.pack(side="right", fill="y", padx=GRID, pady=GRID)
        right.pack_propagate(False)

        ctk.CTkLabel(right, text="Mapping summary", font=font_body(), text_color=BOSCH_DARK_GRAY).pack(
            anchor="w", padx=GRID, pady=GRID
        )
        self.summary = ctk.CTkTextbox(right, height=200, font=font_small(), border_color=BOSCH_MID_GRAY)
        self.summary.pack(fill="x", padx=GRID, pady=4)

        ctk.CTkLabel(right, text="Preview (first rows)", font=font_body(), text_color=BOSCH_DARK_GRAY).pack(
            anchor="w", padx=GRID, pady=(GRID, 0)
        )
        self.preview = ctk.CTkTextbox(right, height=280, font=font_small(), border_color=BOSCH_MID_GRAY)
        self.preview.pack(fill="both", expand=True, padx=GRID, pady=GRID)

        ctk.CTkButton(
            right,
            text="Run plausibility check",
            height=36,
            corner_radius=4,
            command=self._run_analysis,
            font=font_body(),
        ).pack(fill="x", padx=GRID, pady=GRID)

    def _on_file(self, path: Path) -> None:
        self._path = path
        try:
            df = load_dataframe(path)
            self._mapping = detect_column_mapping(df)
            self._df_preview = preview_dataframe(df, 12)
        except Exception as e:
            logger.exception("Load failed")
            messagebox.showerror("PRÜF", f"Could not load file:\n{e}")
            return

        lines = [
            f"Rows: {len(df)}",
            f"Parameters detected: {len({m['parameter'] for m in self._mapping['mappings']})}",
            f"Mapped columns: {len(self._mapping['mappings'])}",
            f"Timestamp column: {self._mapping.get('timestamp_col') or '—'}",
            "",
            "Unmapped columns:",
        ]
        lines.extend(f"  • {c}" for c in self._mapping.get("unmapped_columns", []))
        self.summary.delete("1.0", "end")
        self.summary.insert("1.0", "\n".join(lines))

        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", self._df_preview.to_string() if self._df_preview is not None else "")

    def _run_analysis(self) -> None:
        if not self._path:
            messagebox.showwarning("PRÜF", "Select a file first.")
            return
        proj = self.controller.current_project
        if not proj or proj.id is None:
            messagebox.showwarning("PRÜF", "No active project.")
            return
        if not self._mapping.get("mappings"):
            messagebox.showwarning("PRÜF", "No parameter columns mapped.")
            return
        try:
            from core.analysis_service import run_plausibility_for_file

            sid = run_plausibility_for_file(
                self.controller.db,
                proj.id,
                proj.engine_type.value,
                self._path,
                self._mapping.get("timestamp_col"),
                self._mapping["mappings"],
            )
            self.controller.set_current_session(sid)
            messagebox.showinfo("PRÜF", f"Analysis complete. Session id {sid}.")
            self.controller.show_page("analysis")
        except Exception as e:
            logger.exception("Analysis failed")
            messagebox.showerror("PRÜF", str(e))
