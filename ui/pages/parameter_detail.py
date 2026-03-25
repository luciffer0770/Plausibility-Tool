"""Detail panel for selected parameter."""

from __future__ import annotations

from typing import Any, Optional

import customtkinter as ctk

from ui.theme import BOSCH_MID_GRAY, BOSCH_WHITE, GRID, font_body, font_small


class ParameterDetailPanel(ctk.CTkFrame):
    """Root cause and corrective action for selected row."""

    def __init__(self, master: object) -> None:
        super().__init__(
            master,
            width=300,
            fg_color=BOSCH_WHITE,
            corner_radius=8,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
        )
        self.pack_propagate(False)
        self.title = ctk.CTkLabel(self, text="Parameter detail", font=font_body(), anchor="w")
        self.title.pack(fill="x", padx=GRID, pady=GRID)
        self.body = ctk.CTkTextbox(self, font=font_small(), border_color=BOSCH_MID_GRAY)
        self.body.pack(fill="both", expand=True, padx=GRID, pady=(0, GRID))

    def show_measurement(self, m: dict[str, Any]) -> None:
        """Display fields for one measurement."""
        name = m.get("parameter_name", "")
        self.title.configure(text=name)
        vs = m.get("values_sample")
        lines = [
            f"Status: {m.get('status')}",
            f"Value: {m.get('measured_value')}",
            f"Min / Max / Avg: {m.get('value_min')} / {m.get('value_max')} / {m.get('value_avg')}",
            f"Values (all runs): {vs or '—'}",
            f"Limits: {m.get('limit_lower')} – {m.get('limit_upper')}",
            f"Deviation %: {m.get('deviation')}",
            "",
            "Root cause:",
            str(m.get("root_cause") or "—"),
            "",
            "Corrective action:",
            str(m.get("corrective_action") or "—"),
        ]
        self.body.delete("1.0", "end")
        self.body.insert("1.0", "\n".join(lines))
