"""Project selection and creation (landing)."""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

import customtkinter as ctk

from core.models import EngineType, Project
from core.profile_manager import ensure_default_profile
from ui.pages.base_page import BasePage
from ui.theme import (
    BOSCH_DARK_GRAY,
    BOSCH_LIGHT_GRAY,
    BOSCH_MID_GRAY,
    BOSCH_WHITE,
    GRID,
    font_body,
    font_h2,
    font_h3,
    font_small,
)

logger = logging.getLogger(__name__)


class LoginPage(BasePage):
    """Landing: recent projects and new project."""

    def __init__(self, parent: ctk.CTkFrame, controller: Any) -> None:
        super().__init__(parent, controller)
        self._on_enter: Optional[Callable[[int], None]] = None
        self.search_var = ctk.StringVar()
        self.setup_ui()

    def set_on_enter(self, cb: Callable[[int], None]) -> None:
        """Callback when user opens a project (project id)."""
        self._on_enter = cb

    def setup_ui(self) -> None:
        self.configure(fg_color=BOSCH_LIGHT_GRAY)
        outer = ctk.CTkFrame(self, fg_color=BOSCH_LIGHT_GRAY)
        outer.pack(fill="both", expand=True, padx=GRID * 3, pady=GRID * 3)

        top = ctk.CTkFrame(outer, fg_color=BOSCH_WHITE, corner_radius=8, border_width=1, border_color=BOSCH_MID_GRAY)
        top.pack(fill="x", pady=(0, GRID * 2))
        hdr = ctk.CTkFrame(top, fg_color=BOSCH_WHITE)
        hdr.pack(fill="x", padx=GRID * 2, pady=GRID * 2)
        ctk.CTkLabel(
            hdr,
            text="PRÜF — Plausibility Check Tool",
            font=font_h2(),
            text_color=BOSCH_DARK_GRAY,
        ).pack(side="left")

        row = ctk.CTkFrame(outer, fg_color="transparent")
        row.pack(fill="x", pady=GRID)
        ctk.CTkButton(
            row,
            text="+ New project",
            width=160,
            height=36,
            corner_radius=4,
            command=self._open_new_dialog,
            font=font_body(),
        ).pack(side="left", padx=(0, GRID))
        ctk.CTkEntry(
            row,
            placeholder_text="Search projects…",
            textvariable=self.search_var,
            width=240,
            height=32,
            corner_radius=4,
            border_color=BOSCH_MID_GRAY,
            font=font_body(),
        ).pack(side="left")
        self.search_var.trace_add("write", lambda *_: self._refresh_list())

        self.list_frame = ctk.CTkScrollableFrame(
            outer,
            fg_color=BOSCH_WHITE,
            corner_radius=8,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
        )
        self.list_frame.pack(fill="both", expand=True)

    def on_show(self) -> None:
        self._refresh_list()

    def _refresh_list(self) -> None:
        for w in self.list_frame.winfo_children():
            w.destroy()
        db = self.controller.db
        q = self.search_var.get().strip().lower()
        items = self.controller.list_projects_with_stats()
        ctk.CTkLabel(
            self.list_frame,
            text="RECENT PROJECTS",
            font=font_h3(),
            text_color=BOSCH_DARK_GRAY,
            anchor="w",
        ).pack(fill="x", padx=GRID, pady=GRID)
        for item in items:
            p: Project = item["project"]
            if q and q not in p.name.lower():
                continue
            card = ctk.CTkFrame(
                self.list_frame,
                fg_color="#F7F7F7",
                corner_radius=8,
                border_width=1,
                border_color=BOSCH_MID_GRAY,
            )
            card.pack(fill="x", padx=GRID, pady=6)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=GRID * 2, pady=GRID)
            title = f"● {p.name}"
            ctk.CTkLabel(inner, text=title, font=font_h3(), text_color=BOSCH_DARK_GRAY, anchor="w").pack(
                fill="x"
            )
            uploads = item.get("upload_count", 0)
            last = item.get("last_upload_date") or "—"
            pct = item.get("last_pass_pct")
            pct_s = f"{pct}%" if pct is not None else "—"
            sub = f"{p.engine_type.value}  |  Test bed: {p.test_bed_id or '—'}  |  Uploads: {uploads}  |  Last pass: {pct_s}  |  Last: {last}"
            ctk.CTkLabel(inner, text=sub, font=font_small(), text_color=BOSCH_DARK_GRAY, anchor="w").pack(
                fill="x"
            )
            pid = p.id or 0

            def _open(_: object = None, project_id: int = pid) -> None:
                if self._on_enter:
                    self._on_enter(project_id)

            ctk.CTkButton(
                inner,
                text="Open",
                width=88,
                height=28,
                corner_radius=4,
                command=_open,
                font=font_small(),
            ).pack(anchor="e", pady=4)

    def _open_new_dialog(self) -> None:
        dlg = ctk.CTkToplevel(self)
        dlg.title("New project")
        dlg.geometry("420x320")
        dlg.grab_set()

        name_v = ctk.StringVar()
        engine_v = ctk.StringVar(value=EngineType.TURBO_4CYL.value)
        bed_v = ctk.StringVar(value="TB-03")

        f = ctk.CTkFrame(dlg, fg_color=BOSCH_WHITE)
        f.pack(fill="both", expand=True, padx=GRID * 2, pady=GRID * 2)

        def row(label: str, widget: object) -> None:
            r = ctk.CTkFrame(f, fg_color="transparent")
            r.pack(fill="x", pady=4)
            ctk.CTkLabel(r, text=label, width=120, anchor="w", font=font_body()).pack(side="left")
            widget.pack(side="left", fill="x", expand=True)

        row("Project name", ctk.CTkEntry(f, textvariable=name_v, font=font_body()))
        row(
            "Engine type",
            ctk.CTkOptionMenu(
                f,
                values=[e.value for e in EngineType],
                variable=engine_v,
                font=font_body(),
            ),
        )
        row("Test bed ID", ctk.CTkEntry(f, textvariable=bed_v, font=font_body()))

        btns = ctk.CTkFrame(f, fg_color="transparent")
        btns.pack(fill="x", pady=GRID * 2)

        def create() -> None:
            nm = name_v.get().strip()
            if not nm:
                logger.warning("Project name required")
                return
            et = EngineType.TURBO_4CYL
            for e in EngineType:
                if e.value == engine_v.get():
                    et = e
                    break
            proj = Project(name=nm, engine_type=et, test_bed_id=bed_v.get().strip())
            db = self.controller.db
            pid = db.insert_project(proj)
            ensure_default_profile(db, et.value)
            dlg.destroy()
            self._refresh_list()
            if self._on_enter:
                self._on_enter(pid)

        ctk.CTkButton(btns, text="Cancel", width=100, corner_radius=4, command=dlg.destroy).pack(
            side="right", padx=4
        )
        ctk.CTkButton(btns, text="Create project", width=140, corner_radius=4, command=create).pack(
            side="right", padx=4
        )
