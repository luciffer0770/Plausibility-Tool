"""PROJECTS tab: create project + list / select (reference-style)."""

from __future__ import annotations

import logging
from typing import Any, Optional

import customtkinter as ctk

from core.models import EngineType, Project
from core.profile_manager import ensure_default_profile
from ui.pages.base_page import BasePage
from ui.theme import (
    BOSCH_DARK_GRAY,
    BOSCH_LIGHT_GRAY,
    BOSCH_MID_GRAY,
    BOSCH_RED,
    BOSCH_WHITE,
    GRID,
    font_body,
    font_h3,
    font_small,
)

logger = logging.getLogger(__name__)


class ProjectsTabPage(BasePage):
    """Inline create form and project list."""

    def __init__(self, parent: ctk.CTkFrame, controller: Any) -> None:
        super().__init__(parent, controller)
        self.name_v = ctk.StringVar()
        self.engine_v = ctk.StringVar(value=EngineType.TURBO_4CYL.value)
        self.bed_v = ctk.StringVar(value="TB-03")
        self.search_var = ctk.StringVar()
        self.setup_ui()

    def setup_ui(self) -> None:
        self.configure(fg_color=BOSCH_LIGHT_GRAY)
        outer = ctk.CTkScrollableFrame(self, fg_color=BOSCH_LIGHT_GRAY)
        outer.pack(fill="both", expand=True, padx=GRID * 2, pady=GRID * 2)

        form = ctk.CTkFrame(
            outer,
            fg_color=BOSCH_WHITE,
            corner_radius=8,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
        )
        form.pack(fill="x", pady=(0, GRID * 2))
        ctk.CTkLabel(
            form,
            text="CREATE NEW PROJECT",
            font=font_small(),
            text_color=BOSCH_DARK_GRAY,
        ).pack(anchor="w", padx=GRID * 2, pady=(GRID, 4))

        grid = ctk.CTkFrame(form, fg_color="transparent")
        grid.pack(fill="x", padx=GRID * 2, pady=GRID)
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_columnconfigure(3, weight=1)

        def cell(r: int, c: int, label: str, widget: object) -> None:
            ctk.CTkLabel(grid, text=label, font=font_body(), anchor="w").grid(
                row=r, column=c * 2, sticky="w", padx=(0, 8), pady=4
            )
            widget.grid(row=r, column=c * 2 + 1, sticky="ew", pady=4)

        cell(
            0,
            0,
            "Project name",
            ctk.CTkEntry(grid, textvariable=self.name_v, placeholder_text="e.g. PROJECT_ALFA_2024", font=font_body()),
        )
        cell(
            0,
            1,
            "Engine type",
            ctk.CTkOptionMenu(
                grid,
                values=[e.value for e in EngineType],
                variable=self.engine_v,
                font=font_body(),
            ),
        )
        cell(
            1,
            0,
            "Test bed ID",
            ctk.CTkEntry(grid, textvariable=self.bed_v, placeholder_text="ST-092-B", font=font_body()),
        )
        cell(
            1,
            1,
            "Search list",
            ctk.CTkEntry(
                grid,
                textvariable=self.search_var,
                placeholder_text="Filter projects…",
                font=font_body(),
            ),
        )
        self.search_var.trace_add("write", lambda *_: self._refresh_list())

        btns = ctk.CTkFrame(form, fg_color="transparent")
        btns.pack(fill="x", padx=GRID * 2, pady=GRID)
        ctk.CTkButton(
            btns,
            text="+ Create project",
            width=160,
            height=36,
            corner_radius=4,
            fg_color=BOSCH_RED,
            hover_color="#C40007",
            font=font_body(),
            command=self._create_project,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            btns,
            text="Clear",
            width=88,
            height=36,
            corner_radius=4,
            fg_color=BOSCH_WHITE,
            text_color=BOSCH_DARK_GRAY,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
            font=font_body(),
            command=self._clear_form,
        ).pack(side="left")

        self.list_host = ctk.CTkFrame(outer, fg_color="transparent")
        self.list_host.pack(fill="both", expand=True)

    def _clear_form(self) -> None:
        self.name_v.set("")
        self.bed_v.set("TB-03")
        self.engine_v.set(EngineType.TURBO_4CYL.value)

    def _create_project(self) -> None:
        nm = self.name_v.get().strip()
        if not nm:
            logger.warning("Project name required")
            return
        et = EngineType.TURBO_4CYL
        for e in EngineType:
            if e.value == self.engine_v.get():
                et = e
                break
        proj = Project(name=nm, engine_type=et, test_bed_id=self.bed_v.get().strip())
        pid = self.controller.db.insert_project(proj)
        ensure_default_profile(self.controller.db, et.value)
        self.controller.enter_project(pid)
        self._refresh_list()

    def on_show(self) -> None:
        self._refresh_list()

    def _refresh_list(self) -> None:
        for w in self.list_host.winfo_children():
            w.destroy()
        q = self.search_var.get().strip().lower()
        hdr = ctk.CTkFrame(self.list_host, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, GRID))
        ctk.CTkLabel(hdr, text="EXISTING PROJECTS", font=font_h3(), text_color=BOSCH_DARK_GRAY).pack(side="left")
        items = self.controller.list_projects_with_stats()
        ctk.CTkLabel(
            hdr,
            text=f"COUNT: {len(items)}",
            font=font_small(),
            text_color=BOSCH_DARK_GRAY,
        ).pack(side="right")

        for item in items:
            p: Project = item["project"]
            if q and q not in p.name.lower():
                continue
            card = ctk.CTkFrame(
                self.list_host,
                fg_color=BOSCH_WHITE,
                corner_radius=8,
                border_width=1,
                border_color=BOSCH_MID_GRAY,
            )
            card.pack(fill="x", pady=6)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=GRID * 2, pady=GRID)
            title = p.name
            pid = p.id or 0
            cur = self.controller.current_project
            is_sel = cur and cur.id == p.id

            ctk.CTkLabel(inner, text=title, font=font_h3(), text_color=BOSCH_DARK_GRAY, anchor="w").pack(
                side="left", fill="x", expand=True
            )
            uploads = item.get("upload_count", 0)
            ctk.CTkLabel(
                inner,
                text=f"{p.engine_type.value}  |  {p.test_bed_id or '—'}  |  uploads: {uploads}",
                font=font_small(),
                text_color=BOSCH_DARK_GRAY,
            ).pack(side="left", padx=GRID)

            def select_project(project_id: int = pid) -> None:
                self.controller.enter_project(project_id)

            ctk.CTkButton(
                inner,
                text="SELECTED" if is_sel else "Select",
                width=100,
                height=32,
                corner_radius=4,
                fg_color="#003d7a" if is_sel else BOSCH_WHITE,
                text_color=BOSCH_WHITE if is_sel else BOSCH_DARK_GRAY,
                border_width=0 if is_sel else 1,
                border_color=BOSCH_MID_GRAY,
                command=select_project,
                font=font_small(),
            ).pack(side="right", padx=4)
