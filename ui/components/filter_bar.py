"""Filter controls for results table (v3)."""

from __future__ import annotations

from typing import Any, Callable, Dict

import customtkinter as ctk

from ui.theme import BOSCH_LIGHT_GRAY, BOSCH_MID_GRAY, GRID, font_body
from ui.ttk_style import neutral_ctk_entry_focus


class FilterBar(ctk.CTkFrame):
    """Show filter: All / Failed only / Passed only."""

    def __init__(
        self,
        master: object,
        on_change: Callable[[str, str], None],
    ) -> None:
        super().__init__(master, fg_color=BOSCH_LIGHT_GRAY, corner_radius=6)
        self.on_change = on_change

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=GRID, pady=GRID)

        ctk.CTkLabel(inner, text="SHOW:", font=font_body()).pack(side="left", padx=(0, 8))
        self.show_var = ctk.StringVar(value="All")

        def rb(val: str) -> ctk.CTkRadioButton:
            return ctk.CTkRadioButton(
                inner,
                text=val,
                variable=self.show_var,
                value=val,
                command=self._emit,
                font=font_body(),
            )

        rb("All").pack(side="left", padx=8)
        rb("Failed only").pack(side="left", padx=8)
        rb("Passed only").pack(side="left", padx=8)

        ctk.CTkLabel(inner, text="Type:", font=font_body()).pack(side="left", padx=(GRID * 2, 4))
        self.type_var = ctk.StringVar(value="All")
        self.ptype = ctk.CTkOptionMenu(
            inner,
            values=["All", "temperature", "pressure", "emission", "set", "other"],
            variable=self.type_var,
            width=120,
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
            width=160,
            height=28,
            corner_radius=4,
            font=font_body(),
            border_color=BOSCH_MID_GRAY,
        )
        self.search.pack(side="left", padx=4)
        self.after_idle(neutral_ctk_entry_focus, self.search)
        self.search.bind("<KeyRelease>", lambda e: self._emit())

    def _emit(self, *_args: object) -> None:
        self.on_change(self.show_var.get(), self.type_var.get())

    def get_search(self) -> str:
        return self.search_var.get().strip().lower()

    def apply_saved(self, d: Dict[str, Any]) -> None:
        show = d.get("results_show", "All")
        ptype = d.get("results_type", "All")
        search = d.get("results_search", "")
        if show in ("All", "Failed only", "Passed only"):
            self.show_var.set(show)
        if ptype:
            vals = list(self.ptype.cget("values"))
            if ptype in vals:
                self.type_var.set(ptype)
        self.search_var.set(str(search or ""))

    def snapshot(self) -> Dict[str, str]:
        return {
            "results_show": self.show_var.get(),
            "results_type": self.type_var.get(),
            "results_search": self.search_var.get(),
        }
