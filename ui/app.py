"""Main application shell: routing, project context, navigation."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import customtkinter as ctk

from core.models import Project
from core.profile_manager import ensure_default_profile
from core.project_manager import list_projects_with_stats
from database.db_manager import DatabaseManager
from ui.components.header_bar import HeaderBar
from ui.components.sidebar import Sidebar
from ui.pages.analysis_page import AnalysisPage
from ui.pages.dashboard_page import DashboardPage
from ui.pages.history_page import HistoryPage
from ui.pages.login_page import LoginPage
from ui.pages.profile_editor import ProfileEditorPage
from ui.pages.report_page import ReportPage
from ui.pages.settings_page import SettingsPage
from ui.pages.upload_page import UploadPage
from ui.theme import (
    BOSCH_LIGHT_GRAY,
    BOSCH_MID_GRAY,
    BOSCH_STEEL,
    GRID,
    ensure_theme_ready,
    font_small,
)

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent
_LOGO = _ROOT / "assets" / "bosch_logo.png"


class PrufApp(ctk.CTk):
    """PRÜF desktop application."""

    def __init__(self) -> None:
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        super().__init__()
        ensure_theme_ready()
        self.title("PRÜF — Plausibility Check Tool")
        geo = os.environ.get("PRUF_GEOMETRY", "1400x850")
        minsz = os.environ.get("PRUF_MINSIZE", "1200x700")
        try:
            w, h = minsz.lower().replace(" ", "").split("x", 1)
            self.minsize(int(w), int(h))
        except (ValueError, TypeError):
            self.minsize(1200, 700)
        self.geometry(geo)

        self.db = DatabaseManager()
        self.db.connect()

        self.current_project: Optional[Project] = None
        self.current_session_id: Optional[int] = None

        self._pages: Dict[str, ctk.CTkFrame] = {}
        self._main_body: Optional[ctk.CTkFrame] = None
        self._content: Optional[ctk.CTkFrame] = None
        self._sidebar: Optional[Sidebar] = None
        self._header: Optional[HeaderBar] = None

        self.container = ctk.CTkFrame(self, fg_color=BOSCH_LIGHT_GRAY)
        self.container.pack(fill="both", expand=True)

        self.login_page = LoginPage(self.container, self)
        self.login_page.set_on_enter(self.enter_project)
        self.login_page.pack(fill="both", expand=True)

        self.main_shell = ctk.CTkFrame(self.container, fg_color=BOSCH_LIGHT_GRAY)
        self._build_main_shell()

    def _build_main_shell(self) -> None:
        self._header = HeaderBar(
            self.main_shell,
            on_export=lambda: self.show_page("reports"),
            on_settings=lambda: self.show_page("settings"),
            logo_path=_LOGO if _LOGO.is_file() else None,
        )
        self._header.pack(fill="x")

        self._main_body = ctk.CTkFrame(self.main_shell, fg_color=BOSCH_LIGHT_GRAY)
        self._main_body.pack(fill="both", expand=True)

        self._sidebar = Sidebar(self._main_body, on_nav=self.show_page)
        self._sidebar.pack(side="left", fill="y")

        self._content = ctk.CTkFrame(self._main_body, fg_color=BOSCH_LIGHT_GRAY)
        self._content.pack(side="right", fill="both", expand=True, padx=0, pady=0)

        self._pages["dashboard"] = DashboardPage(self._content, self)
        self._pages["upload"] = UploadPage(self._content, self)
        self._pages["analysis"] = AnalysisPage(self._content, self)
        self._pages["profiles"] = ProfileEditorPage(self._content, self)
        self._pages["history"] = HistoryPage(self._content, self)
        self._pages["reports"] = ReportPage(self._content, self)
        self._pages["settings"] = SettingsPage(self._content, self)

        for p in self._pages.values():
            p.place(relx=0, rely=0, relwidth=1, relheight=1)
            p.place_forget()

        foot = ctk.CTkFrame(self.main_shell, height=28, fg_color=BOSCH_LIGHT_GRAY)
        foot.pack(fill="x", side="bottom")
        sep = ctk.CTkFrame(foot, height=1, fg_color=BOSCH_MID_GRAY)
        sep.pack(fill="x", side="top")
        ctk.CTkLabel(
            foot,
            text="PRÜF v1.0  |  Bosch Engineering  |  Plausibility Check Tool",
            font=font_small(),
            text_color=BOSCH_STEEL,
        ).pack(side="left", padx=GRID * 2, pady=4)

    def list_projects_with_stats(self) -> list[dict[str, Any]]:
        """Projects with upload statistics for landing."""
        return list_projects_with_stats(self.db)

    def enter_project(self, project_id: int) -> None:
        """Open main shell for project."""
        proj = self.db.get_project(project_id)
        if not proj:
            logger.error("Project %s not found", project_id)
            return
        ensure_default_profile(self.db, proj.engine_type.value)
        self.current_project = proj
        self.current_session_id = None
        last = self.db.list_upload_sessions(project_id, limit=1)
        if last:
            self.current_session_id = last[0]["id"]

        if self._header:
            self._header.set_project_text(
                f"Project: {proj.name}  |  {proj.engine_type.value}  |  {proj.test_bed_id or '—'}"
            )

        self.login_page.pack_forget()
        self.main_shell.pack(fill="both", expand=True)
        self.show_page("dashboard")

    def show_page(self, page_name: str) -> None:
        """Switch content page and refresh."""
        if self._sidebar:
            self._sidebar.set_active(page_name)
        for name, frame in self._pages.items():
            if name == page_name:
                frame.place(relx=0, rely=0, relwidth=1, relheight=1)
                if hasattr(frame, "on_show"):
                    frame.on_show()
            else:
                frame.place_forget()

    def set_current_session(self, session_id: int) -> None:
        """Set active analysis session."""
        self.current_session_id = session_id

    def back_to_login(self) -> None:
        """Return to project selection."""
        self.main_shell.pack_forget()
        self.login_page.pack(fill="both", expand=True)
        self.login_page.on_show()
