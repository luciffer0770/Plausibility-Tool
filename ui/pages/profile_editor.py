"""Limit profile editor: full table, JSON import/export, Excel import, clone."""

from __future__ import annotations

import logging
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, List

import customtkinter as ctk

from core.models import EngineType, LimitDefinition, ParameterType
from core.profile_manager import (
    export_profile_json,
    import_parameters_from_excel,
    import_profile_json,
)
from database.db_manager import DatabaseManager
from ui.modal_utils import safe_grab_set
from ui.pages.base_page import BasePage
from ui.theme import (
    BOSCH_DARK_GRAY,
    BOSCH_LIGHT_GRAY,
    BOSCH_MID_GRAY,
    BOSCH_WHITE,
    GRID,
    STATUS_OK,
    font_body,
    font_small,
)

logger = logging.getLogger(__name__)


class _ProfileRow:
    """One editable row (widgets created in parent frame)."""

    def __init__(self, parent: ctk.CTkFrame, d: LimitDefinition, on_toggle_required: Any) -> None:
        self.data = d
        self.name_e = ctk.CTkEntry(parent, width=72, height=26, font=font_small())
        self.name_e.insert(0, d.parameter_name)
        self.type_m = ctk.CTkOptionMenu(
            parent,
            values=[p.value for p in ParameterType],
            width=100,
            height=26,
            font=font_small(),
        )
        self.type_m.set(d.parameter_type.value)
        self.desc_e = ctk.CTkEntry(parent, width=140, height=26, font=font_small())
        self.desc_e.insert(0, d.description)
        self.unit_e = ctk.CTkEntry(parent, width=44, height=26, font=font_small())
        self.unit_e.insert(0, d.unit)
        self.lo_e = ctk.CTkEntry(parent, width=56, height=26, font=font_small())
        if d.lower_limit is not None:
            self.lo_e.insert(0, str(d.lower_limit))
        self.hi_e = ctk.CTkEntry(parent, width=56, height=26, font=font_small())
        if d.upper_limit is not None:
            self.hi_e.insert(0, str(d.upper_limit))
        self.wp_e = ctk.CTkEntry(parent, width=44, height=26, font=font_small())
        self.wp_e.insert(0, str(d.warning_pct))
        self.rc_e = ctk.CTkEntry(parent, width=120, height=26, font=font_small())
        self.rc_e.insert(0, d.root_cause)
        self.ca_e = ctk.CTkEntry(parent, width=120, height=26, font=font_small())
        self.ca_e.insert(0, d.corrective_action)
        self.req_var = ctk.BooleanVar(value=d.is_required)
        self.req_btn = ctk.CTkButton(
            parent,
            text="Req: ON" if d.is_required else "Req: OFF",
            width=72,
            height=26,
            corner_radius=4,
            font=font_small(),
            fg_color="#E8E8E8" if not d.is_required else STATUS_OK,
            text_color=BOSCH_DARK_GRAY if not d.is_required else BOSCH_WHITE,
            command=self._toggle_req,
        )
        self.on_toggle_required = on_toggle_required

    def _toggle_req(self) -> None:
        self.req_var.set(not self.req_var.get())
        on = self.req_var.get()
        self.req_btn.configure(
            text="Req: ON" if on else "Req: OFF",
            fg_color=STATUS_OK if on else "#E8E8E8",
            text_color=BOSCH_WHITE if on else BOSCH_DARK_GRAY,
        )
        if self.on_toggle_required:
            self.on_toggle_required()

    def to_definition(self) -> LimitDefinition:
        pt = ParameterType.OTHER
        for p in ParameterType:
            if p.value == self.type_m.get():
                pt = p
                break
        lo = self._parse_float(self.lo_e.get())
        hi = self._parse_float(self.hi_e.get())
        wp = self._parse_float(self.wp_e.get()) or 10.0
        return LimitDefinition(
            parameter_name=self.name_e.get().strip(),
            parameter_type=pt,
            description=self.desc_e.get().strip(),
            unit=self.unit_e.get().strip(),
            lower_limit=lo,
            upper_limit=hi,
            warning_pct=float(wp),
            root_cause=self.rc_e.get().strip(),
            corrective_action=self.ca_e.get().strip(),
            is_required=self.req_var.get(),
        )

    @staticmethod
    def _parse_float(s: str) -> Any:
        s = s.strip()
        if not s:
            return None
        try:
            return float(s.replace(",", "."))
        except ValueError:
            return None

    def grid(self, row: int) -> None:
        c = 0
        for w in (
            self.name_e,
            self.type_m,
            self.desc_e,
            self.unit_e,
            self.lo_e,
            self.hi_e,
            self.wp_e,
            self.rc_e,
            self.ca_e,
            self.req_btn,
        ):
            w.grid(row=row, column=c, padx=2, pady=2, sticky="w")
            c += 1


class ProfileEditorPage(BasePage):
    """Edit limits for current project's engine type."""

    def __init__(self, parent: ctk.CTkFrame, controller: Any) -> None:
        super().__init__(parent, controller)
        self._rows: List[_ProfileRow] = []
        self.engine_override = ctk.StringVar()
        self.setup_ui()

    def setup_ui(self) -> None:
        self.configure(fg_color=BOSCH_LIGHT_GRAY)
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=GRID, pady=GRID)

        ctk.CTkLabel(top, text="Engine profile:", font=font_body()).pack(side="left", padx=4)
        self.engine_override.set(EngineType.TURBO_4CYL.value)
        self.engine_menu = ctk.CTkOptionMenu(
            top,
            values=[e.value for e in EngineType],
            variable=self.engine_override,
            command=lambda _v: self._load_engine_profile(),
            width=200,
            font=font_body(),
        )
        self.engine_menu.pack(side="left", padx=4)

        ctk.CTkButton(
            top,
            text="Save",
            width=88,
            corner_radius=4,
            command=self._save,
            font=font_body(),
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            top,
            text="Export JSON",
            width=100,
            corner_radius=4,
            command=self._export_json,
            font=font_body(),
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            top,
            text="Import JSON",
            width=100,
            corner_radius=4,
            command=self._import_json,
            font=font_body(),
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            top,
            text="Import Excel",
            width=110,
            corner_radius=4,
            command=self._import_excel,
            font=font_body(),
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            top,
            text="Clone from…",
            width=100,
            corner_radius=4,
            command=self._clone_dialog,
            font=font_body(),
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            top,
            text="+ Add parameter",
            width=120,
            corner_radius=4,
            command=self._add_blank_row,
            font=font_body(),
        ).pack(side="left", padx=4)

        self.table_host = ctk.CTkScrollableFrame(
            self,
            fg_color=BOSCH_WHITE,
            corner_radius=8,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
        )
        self.table_host.pack(fill="both", expand=True, padx=GRID, pady=GRID)

        hdr = ctk.CTkFrame(self.table_host, fg_color=BOSCH_WHITE)
        hdr.pack(fill="x")
        labels = (
            "Parameter",
            "Type",
            "Description",
            "Unit",
            "Lower",
            "Upper",
            "Warn %",
            "Root cause",
            "Corrective",
            "Required",
        )
        for i, lb in enumerate(labels):
            ctk.CTkLabel(hdr, text=lb, font=font_small(), width=72 if i == 0 else 100).grid(
                row=0, column=i, padx=2, pady=4, sticky="w"
            )
        self.rows_frame = ctk.CTkFrame(self.table_host, fg_color=BOSCH_WHITE)
        self.rows_frame.pack(fill="both", expand=True)

    def on_show(self) -> None:
        proj = self.controller.current_project
        if proj:
            self.engine_override.set(proj.engine_type.value)
        self._load_engine_profile()

    def _engine_type_value(self) -> str:
        return self.engine_override.get()

    def _load_engine_profile(self) -> None:
        for w in self.rows_frame.winfo_children():
            w.destroy()
        self._rows.clear()
        db: DatabaseManager = self.controller.db
        ev = self._engine_type_value()
        defs = db.get_limit_profile(ev)
        for d in defs:
            pr = _ProfileRow(self.rows_frame, d, None)
            pr.grid(len(self._rows) + 1)
            self._rows.append(pr)

    def _collect_definitions(self) -> list[LimitDefinition]:
        out: list[LimitDefinition] = []
        seen: set[str] = set()
        for r in self._rows:
            d = r.to_definition()
            if not d.parameter_name:
                continue
            if d.parameter_name in seen:
                messagebox.showwarning("PRÜF", f"Duplicate parameter: {d.parameter_name}")
                return []
            seen.add(d.parameter_name)
            out.append(d)
        return out

    def _save(self) -> None:
        defs = self._collect_definitions()
        if not defs:
            return
        self.controller.db.replace_limit_profile(self._engine_type_value(), defs)
        messagebox.showinfo("PRÜF", "Profile saved.")
        logger.info("Saved profile %s (%s rows)", self._engine_type_value(), len(defs))

    def _export_json(self) -> None:
        defs = self._collect_definitions()
        if not defs:
            defs = self.controller.db.get_limit_profile(self._engine_type_value())
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
        )
        if path:
            Path(path).write_text(export_profile_json(defs), encoding="utf-8")

    def _import_json(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            defs = import_profile_json(Path(path).read_text(encoding="utf-8"))
        except Exception as e:
            messagebox.showerror("PRÜF", str(e))
            return
        self.controller.db.replace_limit_profile(self._engine_type_value(), defs)
        self._load_engine_profile()

    def _import_excel(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if not path:
            return
        try:
            new_rows = import_parameters_from_excel(Path(path))
        except Exception as e:
            messagebox.showerror("PRÜF", str(e))
            return
        existing = {d.parameter_name: d for d in self.controller.db.get_limit_profile(self._engine_type_value())}
        for d in new_rows:
            existing[d.parameter_name] = d
        merged = list(existing.values())
        self.controller.db.replace_limit_profile(self._engine_type_value(), merged)
        self._load_engine_profile()
        messagebox.showinfo("PRÜF", f"Imported {len(new_rows)} row(s); merged with existing.")

    def _clone_dialog(self) -> None:
        dlg = ctk.CTkToplevel(self)
        dlg.title("Clone profile")
        dlg.geometry("360x140")
        try:
            dlg.transient(self.winfo_toplevel())
        except Exception:
            pass
        dlg.lift()
        dlg.focus_force()
        safe_grab_set(dlg)
        src = ctk.StringVar(value=EngineType.NA_4CYL.value)
        ctk.CTkLabel(dlg, text="Copy limits from engine type:", font=font_body()).pack(padx=GRID, pady=GRID)
        ctk.CTkOptionMenu(dlg, values=[e.value for e in EngineType], variable=src, width=240).pack(padx=GRID)
        def do_clone() -> None:
            defs = self.controller.db.get_limit_profile(src.get())
            self.controller.db.replace_limit_profile(self._engine_type_value(), defs)
            dlg.destroy()
            self._load_engine_profile()
        ctk.CTkButton(dlg, text="Clone", command=do_clone, corner_radius=4).pack(pady=GRID)

    def _add_blank_row(self) -> None:
        blank = LimitDefinition(
            parameter_name="",
            parameter_type=ParameterType.OTHER,
            description="",
            unit="",
        )
        pr = _ProfileRow(self.rows_frame, blank, None)
        pr.grid(len(self._rows) + 1)
        self._rows.append(pr)
