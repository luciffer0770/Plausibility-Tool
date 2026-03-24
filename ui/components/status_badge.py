"""12px status circle indicator."""

from __future__ import annotations

import customtkinter as ctk

from ui.theme import STATUS_FAIL, STATUS_NO_DATA, STATUS_OK, STATUS_WARNING


def status_color(status: str) -> str:
    """Map status string to Bosch status color."""
    s = (status or "").upper()
    if s == "OK":
        return STATUS_OK
    if s == "WARNING":
        return STATUS_WARNING
    if s == "FAIL":
        return STATUS_FAIL
    return STATUS_NO_DATA


class StatusBadge(ctk.CTkFrame):
    """Small colored circle for table or summary."""

    def __init__(self, master: object, status: str, size: int = 12) -> None:
        super().__init__(master, width=size + 4, height=size + 4, fg_color="transparent")
        self.circle = ctk.CTkFrame(
            self,
            width=size,
            height=size,
            corner_radius=size // 2,
            fg_color=status_color(status),
        )
        self.circle.place(relx=0.5, rely=0.5, anchor="center")

    def set_status(self, status: str) -> None:
        """Update fill color."""
        self.circle.configure(fg_color=status_color(status))
