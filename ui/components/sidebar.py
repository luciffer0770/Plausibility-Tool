"""Left navigation sidebar."""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from ui.theme import BOSCH_DARK_BLUE, BOSCH_WHITE, GRID, SIDEBAR_WIDTH, font_body


class Sidebar(ctk.CTkFrame):
    """Dark blue sidebar with nav buttons."""

    def __init__(
        self,
        master: object,
        on_nav: Callable[[str], None],
    ) -> None:
        super().__init__(
            master,
            width=SIDEBAR_WIDTH,
            fg_color=BOSCH_DARK_BLUE,
            corner_radius=0,
        )
        self.on_nav = on_nav
        self._buttons: dict[str, ctk.CTkButton] = {}
        self.pack_propagate(False)

        pad = GRID
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=pad, pady=pad * 2)

        for key, label in [
            ("dashboard", "Dashboard"),
            ("upload", "Upload"),
            ("analysis", "Analysis"),
            ("profiles", "Limit profiles"),
            ("history", "History"),
            ("reports", "Reports"),
            ("settings", "Settings"),
        ]:
            btn = ctk.CTkButton(
                inner,
                text=label,
                anchor="w",
                fg_color="transparent",
                text_color=BOSCH_WHITE,
                hover_color="#003d7a",
                corner_radius=4,
                height=36,
                font=font_body(),
                command=lambda k=key: self._click(k),
            )
            btn.pack(fill="x", pady=4)
            self._buttons[key] = btn

        self._active: Optional[str] = None

    def _click(self, key: str) -> None:
        self.set_active(key)
        self.on_nav(key)

    def set_active(self, key: str) -> None:
        """Highlight active nav item."""
        self._active = key
        for k, btn in self._buttons.items():
            if k == key:
                btn.configure(fg_color="#003d7a")
            else:
                btn.configure(fg_color="transparent")
