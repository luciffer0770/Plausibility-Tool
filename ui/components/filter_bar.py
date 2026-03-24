"""Filter controls for analysis table."""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from ui.theme import BOSCH_LIGHT_GRAY, BOSCH_MID_GRAY, GRID, font_body


class FilterBar(ctk.CTkFrame):
    """Status and parameter type filters."""

    def __init__(
        self,
        master: object,
        on_change: Callable[[str, str], None],
    ) -> None:
        super().__init__(master, fg_color=BOSCH_LIGHT_GRAY, corner_radius=8)
        self.on_change = on_change

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=GRID, pady=GRID)

        ctk.CTkLabel(inner, text="Status:", font=font_body()).pack(side="left", padx=(0, 4))
        self.status_var = ctk.StringVar(value="All")
        self.status = ctk.CTkOptionMenu(
            inner,
            values=["All", "FAIL", "WARNING", "OK", "NO_DATA"],
            variable=self.status_var,
            width=120,
            height=28,
            corner_radius=4,
            command=self._emit,
            font=font_body(),
        )
        self.status.pack(side="left", padx=4)

        ctk.CTkLabel(inner, text="Type:", font=font_body()).pack(side="left", padx=(GRID, 4))
        self.type_var = ctk.StringVar(value="All")
        self.ptype = ctk.CTkOptionMenu(
            inner,
            values=["All", "Temperature", "Pressure", "Emission", "Combustion", "Other"],
            variable=self.type_var,
            width=140,
            height=28,
            corner_radius=4,
            command=self._emit,
            font=font_body(),
        )
        self.ptype.pack(side="left", padx=4)

        ctk.CTkLabel(inner, text="Search:", font=font_body()).pack(side="left", padx=(GRID, 4))
        self.search_var = ctk.StringVar()
        self.search = ctk.CTkEntry(
            inner,
            textvariable=self.search_var,
            width=180,
            height=28,
            corner_radius=4,
            font=font_body(),
            border_color=BOSCH_MID_GRAY,
        )
        self.search.pack(side="left", padx=4)
        self.search.bind("<KeyRelease>", lambda e: self._emit())

    def _emit(self, *_args: object) -> None:
        self.on_change(self.status_var.get(), self.type_var.get())

    def get_search(self) -> str:
        return self.search_var.get().strip().lower()
