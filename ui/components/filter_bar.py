"""Filter controls for results — one aligned row (Bosch styling)."""

from __future__ import annotations

from typing import Any, Callable, Dict

import customtkinter as ctk

from ui.theme import BOSCH_DARK_GRAY, BOSCH_MID_GRAY, BOSCH_WHITE, GRID, font_small
from ui.ttk_style import neutral_ctk_entry_focus

_H = 32


class FilterBar(ctk.CTkFrame):
    """SHOW + Type + Search."""

    def __init__(
        self,
        master: object,
        on_change: Callable[[str, str], None],
    ) -> None:
        super().__init__(master, fg_color=BOSCH_WHITE, corner_radius=6, border_width=1, border_color=BOSCH_MID_GRAY)
        self.on_change = on_change

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=GRID, pady=GRID - 2)

        ctk.CTkLabel(row, text="Show", font=font_small(), text_color=BOSCH_DARK_GRAY, width=40, anchor="w").pack(
            side="left", padx=(0, 4), pady=4
        )
        self.show_var = ctk.StringVar(value="All")

        def rb(val: str) -> ctk.CTkRadioButton:
            return ctk.CTkRadioButton(
                row,
                text=val,
                variable=self.show_var,
                value=val,
                command=self._emit,
                font=font_small(),
                height=_H,
                radiobutton_width=16,
                radiobutton_height=16,
            )

        rb("All").pack(side="left", padx=(0, 10))
        rb("Failed only").pack(side="left", padx=(0, 10))
        rb("Passed only").pack(side="left", padx=(0, 16))

        ctk.CTkLabel(row, text="Type", font=font_small(), text_color=BOSCH_DARK_GRAY, width=36, anchor="w").pack(
            side="left", padx=(0, 4), pady=4
        )
        self.type_var = ctk.StringVar(value="All")
        self.ptype = ctk.CTkComboBox(
            row,
            values=["All", "temperature", "pressure", "emission", "set", "other"],
            variable=self.type_var,
            width=150,
            height=_H,
            corner_radius=4,
            command=self._emit,
            font=font_small(),
            border_color=BOSCH_MID_GRAY,
            fg_color=BOSCH_WHITE,
            button_color=BOSCH_MID_GRAY,
            button_hover_color="#B8B8B8",
        )
        self.ptype.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(row, text="Search", font=font_small(), text_color=BOSCH_DARK_GRAY, width=48, anchor="w").pack(
            side="left", padx=(0, 4), pady=4
        )
        self.search_var = ctk.StringVar()
        self.search = ctk.CTkEntry(
            row,
            textvariable=self.search_var,
            width=220,
            height=_H,
            corner_radius=4,
            font=font_small(),
            border_color=BOSCH_MID_GRAY,
            fg_color=BOSCH_WHITE,
        )
        self.search.pack(side="left", padx=(0, 0), pady=2)
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
