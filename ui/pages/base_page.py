"""Base page for Bosch Plausibility Check Tool."""

from __future__ import annotations

from typing import Any, Optional

import customtkinter as ctk


class BasePage(ctk.CTkFrame):
    """Page with optional refresh hook."""

    def __init__(self, parent: ctk.CTkFrame, controller: Any) -> None:
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

    def setup_ui(self) -> None:
        """Build widgets; override in subclass."""
        raise NotImplementedError

    def on_show(self) -> None:
        """Called when page becomes visible."""
        pass
