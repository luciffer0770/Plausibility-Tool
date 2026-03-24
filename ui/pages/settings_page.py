"""Application settings."""

from __future__ import annotations

import json
from pathlib import Path
from tkinter import messagebox
from typing import Any

import customtkinter as ctk

from ui.pages.base_page import BasePage
from ui.theme import BOSCH_LIGHT_GRAY, BOSCH_MID_GRAY, BOSCH_WHITE, GRID, font_body


def _settings_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "config" / "settings.json"


class SettingsPage(BasePage):
    """Persist default export folder and notes."""

    def __init__(self, parent: ctk.CTkFrame, controller: Any) -> None:
        super().__init__(parent, controller)
        self.export_dir = ctk.StringVar()
        self.setup_ui()
        self._load()

    def setup_ui(self) -> None:
        self.configure(fg_color=BOSCH_LIGHT_GRAY)
        box = ctk.CTkFrame(
            self,
            fg_color=BOSCH_WHITE,
            corner_radius=8,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
        )
        box.pack(fill="both", expand=True, padx=GRID * 3, pady=GRID * 3)
        ctk.CTkLabel(box, text="Settings", font=font_body()).pack(anchor="w", padx=GRID, pady=GRID)
        row = ctk.CTkFrame(box, fg_color="transparent")
        row.pack(fill="x", padx=GRID, pady=4)
        ctk.CTkLabel(row, text="Default export folder", width=160, anchor="w", font=font_body()).pack(
            side="left"
        )
        ctk.CTkEntry(row, textvariable=self.export_dir, font=font_body()).pack(
            side="left", fill="x", expand=True, padx=4
        )
        ctk.CTkButton(row, text="Save", width=80, corner_radius=4, command=self._save).pack(side="left")
        ctk.CTkButton(
            box,
            text="Switch project…",
            width=160,
            height=32,
            corner_radius=4,
            command=self._switch_project,
            font=font_body(),
        ).pack(anchor="w", padx=GRID, pady=GRID)

    def _load(self) -> None:
        p = _settings_path()
        if p.is_file():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                self.export_dir.set(data.get("default_export_dir", ""))
            except json.JSONDecodeError:
                pass

    def _save(self) -> None:
        p = _settings_path()
        data = {}
        if p.is_file():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = {}
        data["default_export_dir"] = self.export_dir.get().strip()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        messagebox.showinfo("PRÜF", "Settings saved.")

    def _switch_project(self) -> None:
        if hasattr(self.controller, "back_to_login"):
            self.controller.back_to_login()
