"""Upload history list."""

from __future__ import annotations

from typing import Any

import customtkinter as ctk

from database.db_manager import DatabaseManager
from ui.pages.base_page import BasePage
from ui.theme import BOSCH_DARK_GRAY, BOSCH_LIGHT_GRAY, BOSCH_MID_GRAY, BOSCH_WHITE, GRID, font_body, font_small


class HistoryPage(BasePage):
    """List past uploads; open one for analysis."""

    def __init__(self, parent: ctk.CTkFrame, controller: Any) -> None:
        super().__init__(parent, controller)
        self.setup_ui()

    def setup_ui(self) -> None:
        self.configure(fg_color=BOSCH_LIGHT_GRAY)
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=BOSCH_WHITE,
            corner_radius=8,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
        )
        self.list_frame.pack(fill="both", expand=True, padx=GRID, pady=GRID)

    def on_show(self) -> None:
        for w in self.list_frame.winfo_children():
            w.destroy()
        proj = self.controller.current_project
        if not proj or proj.id is None:
            ctk.CTkLabel(self.list_frame, text="No project", font=font_body()).pack(padx=GRID, pady=GRID)
            return
        db: DatabaseManager = self.controller.db
        sessions = db.list_upload_sessions(proj.id, limit=100)
        for s in sessions:
            fr = ctk.CTkFrame(self.list_frame, fg_color="#F7F7F7", corner_radius=4)
            fr.pack(fill="x", padx=GRID, pady=4)
            txt = (
                f"{s['file_name']}  |  {s['upload_date']}  |  "
                f"OK {s['pass_count']} / W {s['warn_count']} / F {s['fail_count']}"
            )
            ctk.CTkLabel(fr, text=txt, font=font_small(), text_color=BOSCH_DARK_GRAY, anchor="w").pack(
                side="left", padx=GRID, pady=6
            )
            sid = int(s["id"])

            def open_s(_: object = None, session_id: int = sid) -> None:
                self.controller.set_current_session(session_id)
                self.controller.show_page("analysis")

            ctk.CTkButton(fr, text="Open", width=72, height=28, corner_radius=4, command=open_s).pack(
                side="right", padx=GRID, pady=4
            )
