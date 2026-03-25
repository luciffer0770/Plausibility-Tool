"""LIMITS CONFIG tab: editable table (reference-style)."""

from __future__ import annotations

import logging
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, List, Optional

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
    BOSCH_RED,
    BOSCH_WHITE,
    GRID,
    STATUS_OK,
    font_body,
    font_small,
)

logger = logging.getLogger(__name__)

_TYPE_SHORT = {
    ParameterType.TEMPERATURE: "Temp",
    ParameterType.PRESSURE: "Press",
    ParameterType.EMISSION: "Emiss",
    ParameterType.COMBUSTION: "Comb",
    ParameterType.SET: "Set",
    ParameterType.OTHER: "Other",
}


def _type_from_short(s: str) -> ParameterType:
    for pt, short in _TYPE_SHORT.items():
        if short == s:
            return pt
    return ParameterType.OTHER


class _LimitTableRow:
    """One data row in the limits grid."""

    def __init__(
        self,
        parent: ctk.CTkFrame,
        row_idx: int,
        d: LimitDefinition,
        on_enabled_toggle: Any,
        original_name: str,
    ) -> None:
        self._original_name = original_name
        self._on_enabled = on_enabled_toggle
        bg = "#F7F7F7" if row_idx % 2 == 0 else BOSCH_WHITE
        self.frame = ctk.CTkFrame(parent, fg_color=bg, corner_radius=0)

        short = _TYPE_SHORT.get(d.parameter_type, "Other")
        self.type_var = ctk.StringVar(value=short)

        ctk.CTkLabel(self.frame, text=f"{row_idx + 1:02d}", width=36, font=font_small(), text_color=BOSCH_DARK_GRAY).grid(
            row=0, column=0, padx=2, pady=2, sticky="w"
        )
        self.label_e = ctk.CTkEntry(self.frame, width=88, height=28, font=font_small(), border_color=BOSCH_MID_GRAY)
        self.label_e.insert(0, d.parameter_name)
        self.label_e.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        self.type_m = ctk.CTkOptionMenu(
            self.frame,
            values=list(_TYPE_SHORT.values()),
            variable=self.type_var,
            width=72,
            height=28,
            font=font_small(),
            command=lambda _v: self._apply_type_color(),
        )
        self.type_m.grid(row=0, column=2, padx=2, pady=2, sticky="w")
        self._apply_type_color()

        self.desc_e = ctk.CTkEntry(self.frame, width=160, height=28, font=font_small(), border_color=BOSCH_MID_GRAY)
        self.desc_e.insert(0, d.description)
        self.desc_e.grid(row=0, column=3, padx=2, pady=2, sticky="ew")

        self.cat_e = ctk.CTkEntry(self.frame, width=100, height=28, font=font_small(), border_color=BOSCH_MID_GRAY)
        self.cat_e.insert(0, d.category or "")
        self.cat_e.grid(row=0, column=4, padx=2, pady=2, sticky="ew")

        self.lo_e = ctk.CTkEntry(self.frame, width=72, height=28, font=font_small(), border_color=BOSCH_MID_GRAY)
        if d.lower_limit is not None:
            self.lo_e.insert(0, str(d.lower_limit))
        self.lo_e.grid(row=0, column=5, padx=2, pady=2, sticky="ew")

        self.hi_e = ctk.CTkEntry(self.frame, width=72, height=28, font=font_small(), border_color=BOSCH_MID_GRAY)
        if d.upper_limit is not None:
            self.hi_e.insert(0, str(d.upper_limit))
        self.hi_e.grid(row=0, column=6, padx=2, pady=2, sticky="ew")

        self.unit_e = ctk.CTkEntry(self.frame, width=52, height=28, font=font_small(), border_color=BOSCH_MID_GRAY)
        self.unit_e.insert(0, d.unit)
        self.unit_e.grid(row=0, column=7, padx=2, pady=2, sticky="ew")

        self.rc_e = ctk.CTkEntry(self.frame, width=180, height=28, font=font_small(), border_color=BOSCH_MID_GRAY)
        self.rc_e.insert(0, d.root_cause)
        self.rc_e.grid(row=0, column=8, padx=2, pady=2, sticky="ew")

        self.enabled_var = ctk.BooleanVar(value=d.is_enabled)
        self.en_cb = ctk.CTkCheckBox(
            self.frame,
            text="",
            variable=self.enabled_var,
            width=28,
            command=lambda: self._on_enabled(self),
        )
        self.en_cb.grid(row=0, column=9, padx=4, pady=2)

        self.wp_hidden = d.warning_pct
        self.ca_hidden = d.corrective_action
        self.req_hidden = d.is_required

        for c in range(10):
            self.frame.grid_columnconfigure(c, weight=1 if c in (3, 8) else 0)

    def _apply_type_color(self) -> None:
        s = self.type_var.get()
        color = BOSCH_RED if s == "Temp" else "#0066CC" if s == "Press" else BOSCH_DARK_GRAY
        self.type_m.configure(text_color=color)

    def set_enabled_style(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for w in (
            self.label_e,
            self.type_m,
            self.desc_e,
            self.cat_e,
            self.lo_e,
            self.hi_e,
            self.unit_e,
            self.rc_e,
        ):
            w.configure(state=state)

    def to_definition(self) -> LimitDefinition:
        pt = _type_from_short(self.type_var.get())
        lo = self._parse_float(self.lo_e.get())
        hi = self._parse_float(self.hi_e.get())
        return LimitDefinition(
            parameter_name=self.label_e.get().strip(),
            parameter_type=pt,
            description=self.desc_e.get().strip(),
            category=self.cat_e.get().strip(),
            unit=self.unit_e.get().strip(),
            lower_limit=lo,
            upper_limit=hi,
            warning_pct=float(self.wp_hidden),
            root_cause=self.rc_e.get().strip(),
            corrective_action=self.ca_hidden or "",
            is_required=self.req_hidden,
            is_enabled=self.enabled_var.get(),
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


class ProfileEditorPage(BasePage):
    """LIMITS CONFIG — full editable table."""

    def __init__(self, parent: ctk.CTkFrame, controller: Any) -> None:
        super().__init__(parent, controller)
        self._all_defs: list[LimitDefinition] = []
        self._rows: List[_LimitTableRow] = []
        self.engine_override = ctk.StringVar()
        self.cat_filter = ctk.StringVar(value="All")
        self.setup_ui()

    def setup_ui(self) -> None:
        self.configure(fg_color=BOSCH_LIGHT_GRAY)

        bar = ctk.CTkFrame(self, fg_color=BOSCH_LIGHT_GRAY)
        bar.pack(fill="x", padx=GRID, pady=GRID)

        ctk.CTkLabel(bar, text="Engine profile:", font=font_body()).pack(side="left", padx=4)
        self.engine_override.set(EngineType.TURBO_4CYL.value)
        ctk.CTkOptionMenu(
            bar,
            values=[e.value for e in EngineType],
            variable=self.engine_override,
            command=lambda _v: self._load_engine_profile(),
            width=200,
            font=font_body(),
        ).pack(side="left", padx=4)

        ctk.CTkLabel(bar, text="CATEGORY:", font=font_body()).pack(side="left", padx=(GRID, 4))
        ctk.CTkOptionMenu(
            bar,
            values=["All", "Temperature", "Pressure", "Emission", "Combustion", "Other"],
            variable=self.cat_filter,
            command=lambda _v: self._rebuild_table(),
            width=140,
            font=font_body(),
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            bar,
            text="SAVE ALL LIMITS",
            width=160,
            height=36,
            corner_radius=4,
            fg_color=BOSCH_RED,
            hover_color="#C40007",
            font=font_body(),
            command=self._save,
        ).pack(side="right", padx=8)

        tools = ctk.CTkFrame(self, fg_color="transparent")
        tools.pack(fill="x", padx=GRID, pady=(0, GRID))
        for txt, cmd in (
            ("Export JSON", self._export_json),
            ("Import JSON", self._import_json),
            ("Import Excel", self._import_excel),
            ("Clone from…", self._clone_dialog),
            ("+ Add row", self._add_blank_row),
        ):
            ctk.CTkButton(tools, text=txt, width=110, height=30, corner_radius=4, command=cmd, font=font_small()).pack(
                side="left", padx=4
            )

        self.table_wrap = ctk.CTkFrame(self, fg_color=BOSCH_WHITE, corner_radius=8, border_width=1, border_color=BOSCH_MID_GRAY)
        self.table_wrap.pack(fill="both", expand=True, padx=GRID, pady=GRID)

        hdr = ctk.CTkFrame(self.table_wrap, fg_color="#EEEEEE", corner_radius=0)
        hdr.pack(fill="x")
        labels = (
            "#",
            "LABEL",
            "TYPE",
            "DESCRIPTION",
            "CATEGORY",
            "LOWER",
            "UPPER",
            "UNIT",
            "ROOT CAUSE",
            "ON",
        )
        widths = (36, 88, 72, 160, 100, 72, 72, 52, 180, 40)
        for i, (lb, w) in enumerate(zip(labels, widths)):
            ctk.CTkLabel(hdr, text=lb, width=w, font=font_small(), text_color=BOSCH_DARK_GRAY, anchor="w").grid(
                row=0, column=i, padx=2, pady=6, sticky="w"
            )

        self.scroll = ctk.CTkScrollableFrame(self.table_wrap, fg_color=BOSCH_WHITE)
        self.scroll.pack(fill="both", expand=True)

    def on_show(self) -> None:
        proj = self.controller.current_project
        if proj:
            self.engine_override.set(proj.engine_type_key())
        self._load_engine_profile()

    def _engine_type_value(self) -> str:
        return self.engine_override.get()

    def _load_engine_profile(self) -> None:
        db: DatabaseManager = self.controller.db
        self._all_defs = db.get_limit_profile(self._engine_type_value())
        self._rebuild_table()

    def _rebuild_table(self) -> None:
        for w in self.scroll.winfo_children():
            w.destroy()
        self._rows.clear()
        cat = self.cat_filter.get()
        filtered: list[LimitDefinition] = []
        for d in self._all_defs:
            if cat != "All" and d.parameter_type.value != cat:
                continue
            filtered.append(d)
        for i, d in enumerate(filtered):
            orig = d.parameter_name
            row = _LimitTableRow(self.scroll, i, d, self._on_enabled_toggle, original_name=orig)
            row.frame.pack(fill="x")
            self._rows.append(row)
            row.set_enabled_style(d.is_enabled)

    def _on_enabled_toggle(self, row: _LimitTableRow) -> None:
        on = row.enabled_var.get()
        row.set_enabled_style(on)

    def _collect_definitions(self) -> list[LimitDefinition]:
        """Merge visible table rows into full profile (respects category filter)."""
        by_old: dict[str, LimitDefinition] = {}
        for r in self._rows:
            d = r.to_definition()
            if not d.parameter_name:
                messagebox.showwarning("PRÜF", "Every row needs a parameter label.")
                return []
            by_old[r._original_name] = d

        out: list[LimitDefinition] = []
        seen_new: set[str] = set()
        for d in self._all_defs:
            key = d.parameter_name
            if key in by_old:
                nd = by_old[key]
                out.append(nd)
                seen_new.add(nd.parameter_name)
            else:
                out.append(d)
        for old, nd in by_old.items():
            if old not in {x.parameter_name for x in self._all_defs}:
                out.append(nd)
                seen_new.add(nd.parameter_name)
        names = [x.parameter_name for x in out]
        if len(names) != len(set(names)):
            messagebox.showwarning("PRÜF", "Duplicate parameter labels.")
            return []
        return out

    def _save(self) -> None:
        defs = self._collect_definitions()
        if not defs:
            return
        self.controller.db.replace_limit_profile(self._engine_type_value(), defs)
        self._all_defs = defs
        messagebox.showinfo("PRÜF", "All limits saved.")
        logger.info("Saved profile %s (%s rows)", self._engine_type_value(), len(defs))

    def _export_json(self) -> None:
        defs = self._collect_definitions()
        if not defs:
            defs = self.controller.db.get_limit_profile(self._engine_type_value())
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
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
        messagebox.showinfo("PRÜF", f"Imported {len(new_rows)} row(s).")

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
        n = sum(1 for d in self._all_defs if d.parameter_name.startswith("__new__"))
        blank = LimitDefinition(
            parameter_name=f"__new__{n + 1}",
            parameter_type=ParameterType.OTHER,
            description="",
            unit="",
            is_enabled=True,
        )
        self._all_defs.append(blank)
        self._rebuild_table()
