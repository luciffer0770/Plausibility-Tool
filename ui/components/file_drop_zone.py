"""Browse zone for PUMA files (drag-and-drop optional if tkinterdnd2 + root support)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Optional

import customtkinter as ctk

from ui.theme import BOSCH_MID_GRAY, BOSCH_STEEL, GRID, font_body, font_h3

logger = logging.getLogger(__name__)


class FileDropZone(ctk.CTkFrame):
    """Dashed-style bordered area with browse button."""

    def __init__(
        self,
        master: Any,
        on_path_chosen: Callable[[Path], None],
        extensions: tuple[str, ...] = (".xlsx", ".xls", ".csv"),
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.on_path_chosen = on_path_chosen
        self.extensions = extensions
        self._path: Optional[Path] = None

        self.zone = ctk.CTkFrame(
            self,
            fg_color="#FAFAFA",
            border_width=2,
            border_color=BOSCH_MID_GRAY,
            corner_radius=8,
        )
        self.zone.pack(fill="both", expand=True, padx=GRID, pady=GRID)

        inner = ctk.CTkFrame(self.zone, fg_color="transparent")
        inner.pack(expand=True, fill="both", padx=GRID * 3, pady=GRID * 4)

        self.label = ctk.CTkLabel(
            inner,
            text="PUMA export — browse for .xlsx / .xls / .csv",
            font=font_h3(),
            text_color=BOSCH_STEEL,
            justify="center",
        )
        self.label.pack(pady=GRID * 2)

        ctk.CTkButton(
            inner,
            text="Browse file…",
            width=160,
            height=36,
            corner_radius=4,
            command=self._browse,
            font=font_body(),
        ).pack(pady=GRID)

    def _browse(self) -> None:
        from tkinter import filedialog

        fp = filedialog.askopenfilename(
            filetypes=[
                ("Excel/CSV", "*.xlsx *.xls *.csv"),
                ("All", "*.*"),
            ]
        )
        if fp:
            self.set_path(Path(fp))

    def set_path(self, path: Path) -> None:
        """Update display and notify."""
        if path.suffix.lower() not in self.extensions:
            logger.warning("Unexpected extension: %s", path.suffix)
        self._path = path
        self.label.configure(text=f"Selected:\n{path.name}")
        self.on_path_chosen(path)

    def get_path(self) -> Optional[Path]:
        return self._path
