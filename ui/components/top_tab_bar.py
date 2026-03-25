"""Horizontal tab strip (reference-style main navigation)."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

import customtkinter as ctk

from ui.theme import BOSCH_RED, BOSCH_WHITE, GRID, font_body

TabCallback = Callable[[str], None]


class TopTabBar(ctk.CTkFrame):
    """PROJECTS | LIMITS CONFIG | UPLOAD | RESULTS style tabs."""

    def __init__(
        self,
        master: object,
        tabs: List[tuple[str, str]],
        on_select: TabCallback,
    ) -> None:
        super().__init__(master, fg_color=BOSCH_WHITE, corner_radius=0)
        self._on_select = on_select
        self._keys: List[str] = []
        self._buttons: Dict[str, ctk.CTkButton] = {}
        inner = ctk.CTkFrame(self, fg_color=BOSCH_WHITE)
        inner.pack(fill="x", padx=GRID * 2, pady=(0, GRID))

        for key, label in tabs:
            self._keys.append(key)
            btn = ctk.CTkButton(
                inner,
                text=label,
                width=148,
                height=42,
                corner_radius=4,
                font=font_body(),
                fg_color=BOSCH_WHITE,
                text_color="#333333",
                border_width=1,
                border_color="#D9D9D9",
                hover_color="#F2F2F2",
                command=lambda k=key: self._click(k),
            )
            btn.pack(side="left", padx=(0, 8), pady=4)
            self._buttons[key] = btn

        self._active: Optional[str] = None

    def _click(self, key: str) -> None:
        self.set_active(key)
        self._on_select(key)

    def set_active(self, key: str) -> None:
        """Highlight active tab (red fill, white text)."""
        self._active = key
        for k, btn in self._buttons.items():
            if k == key:
                btn.configure(
                    fg_color=BOSCH_RED,
                    text_color=BOSCH_WHITE,
                    border_width=0,
                    hover_color="#C40007",
                )
            else:
                btn.configure(
                    fg_color=BOSCH_WHITE,
                    text_color="#333333",
                    border_width=1,
                    border_color="#D9D9D9",
                    hover_color="#F2F2F2",
                )
