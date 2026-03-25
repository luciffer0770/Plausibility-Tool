"""Top header: Bosch red bar, title, active project, actions."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk
from PIL import Image

from ui.theme import (
    BOSCH_RED,
    BOSCH_WHITE,
    GRID,
    HEADER_HEIGHT,
    font_body,
    font_h3,
)


class HeaderBar(ctk.CTkFrame):
    """Red header strip (v3 Bosch style)."""

    def __init__(
        self,
        master: object,
        on_export: Optional[Callable[[], None]] = None,
        on_settings: Optional[Callable[[], None]] = None,
        logo_path: Optional[Path] = None,
    ) -> None:
        super().__init__(
            master,
            height=HEADER_HEIGHT + 4,
            fg_color=BOSCH_RED,
            corner_radius=0,
        )
        self.pack_propagate(False)
        self._project_label: Optional[ctk.CTkLabel] = None
        self._title_label: Optional[ctk.CTkLabel] = None

        row = ctk.CTkFrame(self, fg_color=BOSCH_RED)
        row.pack(fill="both", expand=True, padx=GRID * 2, pady=GRID)

        if logo_path and Path(logo_path).is_file():
            try:
                img = Image.open(logo_path)
                img_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(80, 22))
                ctk.CTkLabel(row, image=img_ctk, text="").pack(side="left", padx=(0, GRID))
            except OSError:
                ctk.CTkLabel(row, text="BOSCH", font=font_h3(), text_color=BOSCH_WHITE).pack(side="left")
        else:
            ctk.CTkLabel(row, text="BOSCH", font=font_h3(), text_color=BOSCH_WHITE).pack(side="left")

        self._title_label = ctk.CTkLabel(
            row,
            text="PLAUSIBILITY CHECKER — ENGINE TEST BENCH",
            font=font_h3(),
            text_color=BOSCH_WHITE,
        )
        self._title_label.pack(side="left", padx=GRID * 2)

        self._project_label = ctk.CTkLabel(
            row,
            text="",
            font=font_body(),
            text_color=BOSCH_WHITE,
        )
        self._project_label.pack(side="right", padx=8)

        if on_export:
            ctk.CTkButton(
                row,
                text="Export",
                width=88,
                height=32,
                corner_radius=4,
                fg_color=BOSCH_WHITE,
                text_color=BOSCH_RED,
                hover_color="#F2F2F2",
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
                text_color="#333333",
                command=on_settings,
            ).pack(side="right", padx=4)

    def set_title(self, text: str) -> None:
        if self._title_label:
            self._title_label.configure(text=text)

    def set_project_text(self, text: str) -> None:
        if self._project_label:
            self._project_label.configure(text=text)
