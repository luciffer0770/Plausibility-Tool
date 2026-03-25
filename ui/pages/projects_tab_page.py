"""PROJECTS tab: create project + list / select / delete (v3)."""

from __future__ import annotations

import logging
from tkinter import messagebox
from typing import Any, List, Optional

import customtkinter as ctk

from core.engine_types_store import (
    add_extra_engine_type,
    load_extra_engine_types,
    remove_extra_engine_type,
)
from core.models import EngineType, Project
from core.profile_manager import ensure_default_profile
from ui.pages.base_page import BasePage
from ui.theme import (
    BOSCH_DARK_GRAY,
    BOSCH_LIGHT_GRAY,
    BOSCH_MID_GRAY,
    BOSCH_RED,
    BOSCH_STEEL,
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
        self.engine_combo: Any = None
        self.bed_v = ctk.StringVar(value="ST-092-B")
        self.code_v = ctk.StringVar()
        self.oem_v = ctk.StringVar()
        self.emission_v = ctk.StringVar()
        self.search_var = ctk.StringVar()
        self._selected_project_id: Optional[int] = None
        self._project_rows: dict[int, ctk.CTkFrame] = {}
        self.setup_ui()

    def _all_engine_type_labels(self) -> List[str]:
        preset = [e.value for e in EngineType]
        seen = set(preset)
        out = list(preset)
        for n in load_extra_engine_types():
            if n not in seen:
                seen.add(n)
                out.append(n)
        try:
            for n in self.controller.db.list_engine_type_names():
                if n not in seen:
                    seen.add(n)
                    out.append(n)
        except Exception:
            pass
        return out

    def _refresh_engine_combo(self, keep_selection: bool = True) -> None:
        cur = (self.engine_combo.get() or "").strip() if self.engine_combo else ""
        vals = self._all_engine_type_labels()
        if self.engine_combo:
            self.engine_combo.configure(values=vals)
            if keep_selection and cur in vals:
                self.engine_combo.set(cur)
            elif vals:
                self.engine_combo.set(vals[0])

    def setup_ui(self) -> None:
        self.configure(fg_color=BOSCH_LIGHT_GRAY)
        outer = ctk.CTkScrollableFrame(self, fg_color=BOSCH_LIGHT_GRAY)
        outer.pack(fill="both", expand=True, padx=GRID * 2, pady=GRID * 2)

        form = ctk.CTkFrame(
            outer,
            fg_color=BOSCH_WHITE,
            corner_radius=6,
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

        form_inner = ctk.CTkFrame(form, fg_color="transparent")
        form_inner.pack(fill="x", padx=GRID * 2, pady=GRID)
        form_inner.grid_columnconfigure(0, weight=0)
        form_inner.grid_columnconfigure(1, weight=0)
        max_w = 520

        def add_row(r: int, label: str, widget: Any) -> None:
            ctk.CTkLabel(form_inner, text=label, font=font_body(), anchor="w", width=140).grid(
                row=r, column=0, sticky="nw", padx=(0, 12), pady=6
            )
            widget.grid(row=r, column=1, sticky="w", pady=6)

        add_row(
            0,
            "Project name",
            ctk.CTkEntry(
                form_inner,
                textvariable=self.name_v,
                placeholder_text="e.g. PROJECT_ALFA_2024",
                font=font_body(),
                width=max_w,
            ),
        )

        eng_row = ctk.CTkFrame(form_inner, fg_color="transparent")
        self.engine_combo = ctk.CTkComboBox(
            eng_row,
            values=self._all_engine_type_labels(),
            width=max_w - 88,
            font=font_body(),
        )
        self.engine_combo.set(EngineType.TURBO_4CYL.value)
        self.engine_combo.pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            eng_row,
            text="+",
            width=36,
            height=32,
            font=font_h3(),
            fg_color=BOSCH_RED,
            hover_color="#C40007",
            command=self._add_engine_type,
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            eng_row,
            text="−",
            width=36,
            height=32,
            font=font_h3(),
            fg_color=BOSCH_WHITE,
            text_color=BOSCH_DARK_GRAY,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
            command=self._remove_engine_type,
        ).pack(side="left", padx=2)
        ctk.CTkLabel(form_inner, text="Engine type", font=font_body(), anchor="w", width=140).grid(
            row=1, column=0, sticky="nw", padx=(0, 12), pady=6
        )
        eng_row.grid(row=1, column=1, sticky="w", pady=6)

        add_row(
            2,
            "Test bed ID",
            ctk.CTkEntry(form_inner, textvariable=self.bed_v, placeholder_text="ST-092-B", font=font_body(), width=max_w),
        )
        add_row(
            3,
            "Engine code",
            ctk.CTkEntry(form_inner, textvariable=self.code_v, placeholder_text="EA888-G3", font=font_body(), width=max_w),
        )
        add_row(
            4,
            "Customer / OEM",
            ctk.CTkEntry(
                form_inner,
                textvariable=self.oem_v,
                placeholder_text="Internal Development",
                font=font_body(),
                width=max_w,
            ),
        )
        add_row(
            5,
            "Emission norm",
            ctk.CTkEntry(
                form_inner,
                textvariable=self.emission_v,
                placeholder_text="Euro 6d-TEMP (free text)",
                font=font_body(),
                width=max_w,
            ),
        )
        add_row(
            6,
            "Search list",
            ctk.CTkEntry(
                form_inner,
                textvariable=self.search_var,
                placeholder_text="Filter projects…",
                font=font_body(),
                width=max_w,
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

        list_section = ctk.CTkFrame(outer, fg_color="transparent")
        list_section.pack(fill="both", expand=True)

        hdr = ctk.CTkFrame(list_section, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, GRID))
        ctk.CTkLabel(hdr, text="EXISTING PROJECTS", font=font_h3(), text_color=BOSCH_DARK_GRAY).pack(side="left")

        self._count_label = ctk.CTkLabel(
            hdr,
            text="COUNT: 0",
            font=font_small(),
            text_color=BOSCH_DARK_GRAY,
        )
        self._count_label.pack(side="right", padx=(GRID, 0))

        toolbar = ctk.CTkFrame(
            list_section,
            fg_color=BOSCH_WHITE,
            corner_radius=6,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
        )
        toolbar.pack(fill="x", pady=(0, GRID))
        ctk.CTkLabel(
            toolbar,
            text="Click a project below, then:",
            font=font_small(),
            text_color=BOSCH_STEEL,
        ).pack(side="left", padx=GRID, pady=8)

        ctk.CTkButton(
            toolbar,
            text="Select as active",
            width=140,
            height=32,
            corner_radius=4,
            fg_color=BOSCH_RED,
            hover_color="#C40007",
            font=font_body(),
            command=self._toolbar_select,
        ).pack(side="right", padx=6, pady=8)
        ctk.CTkButton(
            toolbar,
            text="Delete project",
            width=120,
            height=32,
            corner_radius=4,
            fg_color=BOSCH_WHITE,
            text_color=BOSCH_RED,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
            font=font_body(),
            command=self._toolbar_delete,
        ).pack(side="right", padx=6, pady=8)

        self.list_host = ctk.CTkScrollableFrame(list_section, fg_color=BOSCH_LIGHT_GRAY)
        self.list_host.pack(fill="both", expand=True)

    def _add_engine_type(self) -> None:
        name = (self.engine_combo.get() or "").strip()
        if not name:
            messagebox.showwarning("Bosch Plausibility Check", "Type a new engine type name in the field, then click +.")
            return
        add_extra_engine_type(name)
        self.controller.db.insert_engine_type_if_missing(name)
        self._refresh_engine_combo(keep_selection=True)

    def _remove_engine_type(self) -> None:
        name = (self.engine_combo.get() or "").strip()
        if not name:
            return
        if not messagebox.askyesno(
            "Bosch Plausibility Check",
            f'Remove engine type "{name}" from your saved list?\n\n'
            "Limit profiles in the database for this name are not deleted.",
        ):
            return
        remove_extra_engine_type(name)
        self.controller.db.delete_engine_type_row(name)
        self._refresh_engine_combo(keep_selection=False)

    def _clear_form(self) -> None:
        self.name_v.set("")
        self.bed_v.set("ST-092-B")
        self.code_v.set("")
        self.oem_v.set("")
        self.emission_v.set("")
        self.engine_combo.set(EngineType.TURBO_4CYL.value)

    def _create_project(self) -> None:
        nm = self.name_v.get().strip()
        if not nm:
            logger.warning("Project name required")
            return
        et_key = (self.engine_combo.get() or "").strip()
        if not et_key:
            et_key = EngineType.TURBO_4CYL.value
        et_enum = EngineType.TURBO_4CYL
        et_custom = ""
        for e in EngineType:
            if e.value == et_key:
                et_enum = e
                break
        else:
            et_custom = et_key
        proj = Project(
            name=nm,
            engine_type=et_enum,
            engine_type_name=et_custom,
            test_bed_id=self.bed_v.get().strip(),
            engine_code=self.code_v.get().strip(),
            customer_oem=self.oem_v.get().strip(),
            emission_norm=self.emission_v.get().strip(),
        )
        self.controller.db.insert_engine_type_if_missing(et_key)
        add_extra_engine_type(et_key)
        pid = self.controller.db.insert_project(proj)
        ensure_default_profile(self.controller.db, proj.engine_type_key())
        self.controller.enter_project(pid)
        self._refresh_list()
        self._refresh_engine_combo()

    def on_show(self) -> None:
        self._refresh_engine_combo()
        self._refresh_list()

    def _set_selection(self, project_id: int) -> None:
        self._selected_project_id = project_id
        for pid, fr in self._project_rows.items():
            if pid == project_id:
                fr.configure(border_width=2, border_color=BOSCH_RED)
            else:
                fr.configure(border_width=1, border_color=BOSCH_MID_GRAY)

    def _toolbar_select(self) -> None:
        if self._selected_project_id is None:
            messagebox.showinfo("Bosch Plausibility Check", "Click a project in the list first.")
            return
        self.controller.enter_project(self._selected_project_id)

    def _toolbar_delete(self) -> None:
        if self._selected_project_id is None:
            messagebox.showinfo("Bosch Plausibility Check", "Click a project in the list first.")
            return
        pid = self._selected_project_id
        p = self.controller.db.get_project(pid)
        name = p.name if p else str(pid)
        if not messagebox.askyesno("Bosch Plausibility Check", f'Delete project "{name}" and all its upload sessions?'):
            return
        self.controller.db.delete_project(pid)
        if self.controller.current_project and self.controller.current_project.id == pid:
            self.controller.back_to_login()
        self._selected_project_id = None
        self._refresh_list()

    def _refresh_list(self) -> None:
        for w in self.list_host.winfo_children():
            w.destroy()
        self._project_rows.clear()

        q = self.search_var.get().strip().lower()
        items = self.controller.list_projects_with_stats()
        self._count_label.configure(text=f"COUNT: {len(items)}")

        for item in items:
            p: Project = item["project"]
            if q and q not in p.name.lower():
                continue
            pid = p.id or 0
            card = ctk.CTkFrame(
                self.list_host,
                fg_color=BOSCH_WHITE,
                corner_radius=6,
                border_width=1,
                border_color=BOSCH_MID_GRAY,
            )
            card.pack(fill="x", pady=6)
            self._project_rows[pid] = card

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=GRID * 2, pady=GRID)

            cur = self.controller.current_project
            is_active = cur and cur.id == p.id
            et_display = p.engine_type_key()
            uploads = item.get("upload_count", 0)

            title = ctk.CTkLabel(
                inner,
                text=p.name + ("  ● ACTIVE" if is_active else ""),
                font=font_h3(),
                text_color=BOSCH_DARK_GRAY,
                anchor="w",
            )
            title.pack(anchor="w")
            sub = (
                f"{et_display}  |  Bed: {p.test_bed_id or '—'}  |  Code: {p.engine_code or '—'}  "
                f"|  OEM: {p.customer_oem or '—'}  |  Norm: {p.emission_norm or '—'}  |  Uploads: {uploads}"
            )
            ctk.CTkLabel(inner, text=sub, font=font_small(), text_color=BOSCH_DARK_GRAY, anchor="w").pack(
                anchor="w"
            )

            def on_click(_e: object, project_id: int = pid) -> None:
                self._set_selection(project_id)

            card.bind("<Button-1>", on_click)
            inner.bind("<Button-1>", on_click)
            title.bind("<Button-1>", on_click)
            for ch in inner.winfo_children():
                ch.bind("<Button-1>", on_click)

            if is_active:
                self._set_selection(pid)
