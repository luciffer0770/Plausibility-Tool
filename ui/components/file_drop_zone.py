"""Browse zone for PUMA files — Bosch-styled (no default green)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Optional

import customtkinter as ctk

from ui.theme import BOSCH_DARK_GRAY, BOSCH_MID_GRAY, BOSCH_RED, BOSCH_STEEL, GRID, font_body, font_small

logger = logging.getLogger(__name__)


class FileDropZone(ctk.CTkFrame):
    """Compact bordered area with browse (explicit Bosch red)."""

    def __init__(
        self,
        master: Any,
        on_path_chosen: Callable[[Path], None],
        extensions: tuple[str, ...] = (".xlsx", ".xls", ".csv"),
        compact: bool = False,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.on_path_chosen = on_path_chosen
        self.extensions = extensions
        self._path: Optional[Path] = None
        self._compact = compact

        self.zone = ctk.CTkFrame(
            self,
            fg_color="#FAFAFA",
            border_width=1,
            border_color=BOSCH_MID_GRAY,
            corner_radius=6,
        )
        py = GRID if compact else GRID * 2
        self.zone.pack(fill="x" if compact else "both", expand=not compact, padx=0, pady=py)

        inner = ctk.CTkFrame(self.zone, fg_color="transparent")
        ipx = GRID * 2 if compact else GRID * 3
        ipy = GRID if compact else GRID * 4
        inner.pack(expand=True, fill="both", padx=ipx, pady=ipy)

        self.label = ctk.CTkLabel(
            inner,
            text="No file selected",
            font=font_small() if compact else font_body(),
            text_color=BOSCH_STEEL,
            justify="left",
            anchor="w",
        )
        self.label.pack(anchor="w", pady=(0, GRID if compact else GRID * 2))

        ctk.CTkButton(
            inner,
            text="Browse file…",
            width=130 if compact else 160,
            height=30 if compact else 34,
            corner_radius=4,
            fg_color=BOSCH_RED,
            hover_color="#C40007",
            text_color="white",
            command=self._browse,
            font=font_small() if compact else font_body(),
        ).pack(anchor="w", pady=0)

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
        self.label.configure(text=f"Selected: {path.name}", text_color=BOSCH_DARK_GRAY)
        self.on_path_chosen(path)

    def get_path(self) -> Optional[Path]:
        return self._path
