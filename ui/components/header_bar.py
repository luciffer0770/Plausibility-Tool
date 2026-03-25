"""Top header: logo, title, project, actions."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk
from PIL import Image

from ui.theme import (
    BOSCH_DARK_GRAY,
    BOSCH_MID_GRAY,
    BOSCH_WHITE,
    GRID,
    HEADER_HEIGHT,
    font_body,
    font_h3,
)


class HeaderBar(ctk.CTkFrame):
    """White header strip."""

    def __init__(
        self,
        master: object,
        on_export: Optional[Callable[[], None]] = None,
        on_settings: Optional[Callable[[], None]] = None,
        logo_path: Optional[Path] = None,
    ) -> None:
        super().__init__(
            master,
            height=HEADER_HEIGHT,
            fg_color=BOSCH_WHITE,
            corner_radius=0,
        )
        self.pack_propagate(False)
        self._project_label: Optional[ctk.CTkLabel] = None
        self._title_label: Optional[ctk.CTkLabel] = None
        self.on_export = on_export
        self.on_settings = on_settings

        border = ctk.CTkFrame(self, height=1, fg_color=BOSCH_MID_GRAY)
        border.pack(side="bottom", fill="x")

        row = ctk.CTkFrame(self, fg_color=BOSCH_WHITE)
        row.pack(fill="both", expand=True, padx=GRID * 2, pady=GRID)

        if logo_path and Path(logo_path).is_file():
            try:
                img = Image.open(logo_path)
                img_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(80, 22))
                ctk.CTkLabel(row, image=img_ctk, text="").pack(side="left", padx=(0, GRID))
            except OSError:
                ctk.CTkLabel(row, text="BOSCH", font=font_h3(), text_color=BOSCH_DARK_GRAY).pack(
                    side="left"
                )
        else:
            ctk.CTkLabel(row, text="BOSCH", font=font_h3(), text_color=BOSCH_DARK_GRAY).pack(
                side="left"
            )

        self._title_label = ctk.CTkLabel(
            row,
            text="PRÜF — Plausibility Check Tool",
            font=font_h3(),
            text_color=BOSCH_DARK_GRAY,
        )
        self._title_label.pack(side="left", padx=GRID * 2)

        self._project_label = ctk.CTkLabel(
            row,
            text="",
            font=font_body(),
            text_color=BOSCH_DARK_GRAY,
        )
        self._project_label.pack(side="left", expand=True)

        if on_export:
            ctk.CTkButton(
                row,
                text="Export",
                width=88,
                height=32,
                corner_radius=4,
                command=on_export,
            ).pack(side="right", padx=4)
        if on_settings:
            ctk.CTkButton(
                row,
                text="Settings",
                width=88,
                height=32,
                corner_radius=4,
                fg_color="#E8E8E8",
                text_color=BOSCH_DARK_GRAY,
                command=on_settings,
            ).pack(side="right", padx=4)

    def set_title(self, text: str) -> None:
        """Set main title next to logo."""
        if self._title_label:
            self._title_label.configure(text=text)

    def set_project_text(self, text: str) -> None:
        """Show current project in header."""
        if self._project_label:
            self._project_label.configure(text=text)
