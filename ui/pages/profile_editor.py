"""LIMITS CONFIG — ttk.Treeview list + detail panel (fast; no full rebuild on add row)."""

from __future__ import annotations

import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, List, Optional

import customtkinter as ctk

from core.models import EngineType, LimitDefinition, ParameterType
from core.limit_categories_store import (
    add_category,
    merged_filter_values,
    remove_category,
)
from core.limits_template_export import write_limits_template_excel
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
    font_body,
    font_h3,
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
_SHORT_TO_PT = {v: k for k, v in _TYPE_SHORT.items()}


def _type_from_short(s: str) -> ParameterType:
    return _SHORT_TO_PT.get(s, ParameterType.OTHER)


class ProfileEditorPage(BasePage):
    """Tree list (fast) + right-side editor for the selected limit row."""

    def __init__(self, parent: ctk.CTkFrame, controller: Any) -> None:
        super().__init__(parent, controller)
        self._all_defs: List[LimitDefinition] = []
        self._selected_index: Optional[int] = None
        self.engine_override = ctk.StringVar()
        self.cat_filter = ctk.StringVar(value="All")
        self._tree: Optional[ttk.Treeview] = None
        self._tk_wrap: Optional[tk.Frame] = None
        self._limits_dirty: bool = False
        self._save_status: Optional[ctk.CTkLabel] = None
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
        self._cat_menu = ctk.CTkOptionMenu(
            bar,
            values=self._category_menu_values(),
            variable=self.cat_filter,
            command=lambda _v: self._rebuild_tree_only(),
            width=200,
            font=font_body(),
        )
        self._cat_menu.pack(side="left", padx=2)
        ctk.CTkButton(
            bar,
            text="+",
            width=32,
            height=32,
            font=font_h3(),
            fg_color=BOSCH_RED,
            hover_color="#C40007",
            command=self._add_category_dialog,
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            bar,
            text="−",
            width=32,
            height=32,
            font=font_h3(),
            fg_color=BOSCH_WHITE,
            text_color=BOSCH_DARK_GRAY,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
            command=self._remove_current_category_preset,
        ).pack(side="left", padx=2)

        save_row = ctk.CTkFrame(bar, fg_color="transparent")
        save_row.pack(side="right", padx=8)
        ctk.CTkButton(
            save_row,
            text="SAVE ALL LIMITS",
            width=170,
            height=40,
            corner_radius=4,
            fg_color=BOSCH_RED,
            hover_color="#C40007",
            font=font_body(),
            command=self._save,
        ).pack(side="left", padx=(0, 8))
        self._save_status = ctk.CTkLabel(save_row, text="", font=font_small(), text_color=BOSCH_RED)
        self._save_status.pack(side="left")

        tools = ctk.CTkFrame(self, fg_color="transparent")
        tools.pack(fill="x", padx=GRID, pady=(0, GRID))
        for txt, cmd in (
            ("Export JSON", self._export_json),
            ("Import JSON", self._import_json),
            ("Import Excel", self._import_excel),
            ("Export empty template", self._export_template),
            ("Clone from…", self._clone_dialog),
            ("+ Add row", self._add_blank_row),
        ):
            ctk.CTkButton(tools, text=txt, width=118, height=34, corner_radius=4, command=cmd, font=font_small()).pack(
                side="left", padx=4
            )

        paned = ctk.CTkFrame(self, fg_color="transparent")
        paned.pack(fill="both", expand=True, padx=GRID, pady=(0, GRID))

        left_card = ctk.CTkFrame(paned, fg_color=BOSCH_WHITE, corner_radius=8, border_width=1, border_color=BOSCH_MID_GRAY)
        left_card.pack(side="left", fill="both", expand=True, padx=(0, GRID))

        ctk.CTkLabel(
            left_card,
            text="Parameters (click a row to edit on the right)",
            font=font_small(),
            text_color=BOSCH_DARK_GRAY,
        ).pack(anchor="w", padx=GRID, pady=(GRID, 4))

        self._tk_wrap = tk.Frame(left_card, bg=BOSCH_WHITE, highlightthickness=0)
        self._tk_wrap.pack(fill="both", expand=True, padx=GRID, pady=(0, GRID))

        style = ttk.Style(self._tk_wrap)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Limits.Treeview",
            rowheight=22,
            fieldbackground=BOSCH_WHITE,
            background=BOSCH_WHITE,
            foreground=BOSCH_DARK_GRAY,
        )
        style.configure(
            "Limits.Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#EEEEEE",
            foreground=BOSCH_DARK_GRAY,
        )

        cols = ("num", "label", "type", "desc", "cat", "lo", "hi", "unit", "on")
        self._tree = ttk.Treeview(
            self._tk_wrap,
            columns=cols,
            show="headings",
            selectmode="browse",
            style="Limits.Treeview",
            height=18,
        )
        hw = {
            "num": ("#", 32),
            "label": ("Label", 72),
            "type": ("Type", 48),
            "desc": ("Description", 140),
            "cat": ("Category", 88),
            "lo": ("Lower", 56),
            "hi": ("Upper", 56),
            "unit": ("Unit", 40),
            "on": ("ON", 28),
        }
        for c, (t, w) in hw.items():
            self._tree.heading(c, text=t, anchor="w")
            self._tree.column(c, width=w, minwidth=28, anchor="w", stretch=True)

        vsb = ttk.Scrollbar(self._tk_wrap, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(self._tk_wrap, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self._tk_wrap.grid_rowconfigure(0, weight=1)
        self._tk_wrap.grid_columnconfigure(0, weight=1)

        self._tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self._tree.bind("<Double-1>", self._on_tree_double)

        right_card = ctk.CTkFrame(paned, fg_color=BOSCH_WHITE, corner_radius=8, border_width=1, border_color=BOSCH_MID_GRAY, width=320)
        right_card.pack(side="right", fill="y")
        right_card.pack_propagate(False)

        ctk.CTkLabel(right_card, text="Edit selected row", font=font_body(), text_color=BOSCH_DARK_GRAY).pack(
            anchor="w", padx=GRID, pady=(GRID, 8)
        )

        self._e_label = ctk.CTkEntry(right_card, placeholder_text="Parameter label", width=260, font=font_small())
        self._e_type = ctk.CTkOptionMenu(right_card, values=list(_TYPE_SHORT.values()), width=260, font=font_small())
        self._e_desc = ctk.CTkEntry(right_card, placeholder_text="Description", width=260, font=font_small())
        self._e_cat = ctk.CTkEntry(right_card, placeholder_text="Category", width=260, font=font_small())
        self._e_lo = ctk.CTkEntry(right_card, placeholder_text="Lower limit", width=260, font=font_small())
        self._e_hi = ctk.CTkEntry(right_card, placeholder_text="Upper limit", width=260, font=font_small())
        self._e_unit = ctk.CTkEntry(right_card, placeholder_text="Unit", width=260, font=font_small())
        self._e_rc = ctk.CTkEntry(right_card, placeholder_text="Root cause if out of range", width=260, font=font_small())
        self._en_var = ctk.BooleanVar(value=True)
        self._en_cb = ctk.CTkCheckBox(right_card, text="Enabled (include in check)", variable=self._en_var, font=font_small())

        for lb, w in (
            ("Label", self._e_label),
            ("Type", self._e_type),
            ("Description", self._e_desc),
            ("Category", self._e_cat),
            ("Lower limit", self._e_lo),
            ("Upper limit", self._e_hi),
            ("Unit", self._e_unit),
            ("Root cause", self._e_rc),
        ):
            ctk.CTkLabel(right_card, text=lb, font=font_small(), text_color=BOSCH_DARK_GRAY).pack(anchor="w", padx=GRID)
            w.pack(anchor="w", padx=GRID, pady=(0, 6))
        self._en_cb.pack(anchor="w", padx=GRID, pady=6)

        def _dirty_hook(_e: object = None) -> None:
            self._mark_limits_dirty()

        for w in (
            self._e_label,
            self._e_desc,
            self._e_cat,
            self._e_lo,
            self._e_hi,
            self._e_unit,
            self._e_rc,
        ):
            w.bind("<KeyRelease>", _dirty_hook)
        self._e_type.configure(command=lambda _v: self._mark_limits_dirty())
        self._en_cb.configure(command=self._mark_limits_dirty)

        ctk.CTkButton(
            right_card,
            text="Apply to row",
            width=200,
            height=32,
            corner_radius=4,
            fg_color=BOSCH_RED,
            font=font_body(),
            command=self._apply_detail_to_def,
        ).pack(anchor="w", padx=GRID, pady=GRID)
        ctk.CTkLabel(
            right_card,
            text="Tip: double-click the ON column to toggle enabled.",
            font=font_small(),
            text_color=BOSCH_MID_GRAY,
            wraplength=280,
        ).pack(anchor="w", padx=GRID, pady=(0, GRID))

    def _mark_limits_dirty(self) -> None:
        self._limits_dirty = True
        if self._save_status:
            self._save_status.configure(text="• Unsaved changes")

    def _mark_limits_clean(self) -> None:
        self._limits_dirty = False
        if self._save_status:
            self._save_status.configure(text="")

    def _category_menu_values(self) -> List[str]:
        return ["All"] + merged_filter_values()

    def _refresh_category_menu(self) -> None:
        if not self._cat_menu:
            return
        cur = self.cat_filter.get()
        vals = self._category_menu_values()
        self._cat_menu.configure(values=vals)
        if cur in vals:
            self.cat_filter.set(cur)
        else:
            self.cat_filter.set("All")

    def _add_category_dialog(self) -> None:
        dlg = ctk.CTkInputDialog(text="New category name (for filter & limits):", title="Bosch Plausibility Check")
        name = (dlg.get_input() or "").strip()
        if not name:
            return
        add_category(name)
        self._refresh_category_menu()
        self.cat_filter.set(name)
        self._rebuild_tree_only()

    def _remove_current_category_preset(self) -> None:
        sel = (self.cat_filter.get() or "").strip()
        if sel in ("", "All"):
            messagebox.showinfo("Bosch Plausibility Check", "Select a category in the list first (not “All”).")
            return
        if not messagebox.askyesno(
            "Bosch Plausibility Check",
            f'Remove "{sel}" from your saved category presets?\n\n'
            "Built-in types (Temperature, …) stay available. "
            "Rows that use this category text are not changed.",
        ):
            return
        remove_category(sel)
        self._refresh_category_menu()
        self.cat_filter.set("All")
        self._rebuild_tree_only()

    def _passes_filter(self, d: LimitDefinition) -> bool:
        cat = self.cat_filter.get()
        if cat == "All":
            return True
        row_cat = (d.category or "").strip()
        if row_cat and row_cat == cat:
            return True
        return d.parameter_type.value == cat

    def _rebuild_tree_only(self) -> None:
        if self._tree is None:
            return
        self._flush_detail_to_selection()
        self._tree.delete(*self._tree.get_children())
        self._selected_index = None
        shown = 0
        for i, d in enumerate(self._all_defs):
            if not self._passes_filter(d):
                continue
            shown += 1
            short = _TYPE_SHORT.get(d.parameter_type, "Other")
            self._tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    f"{shown:02d}",
                    d.parameter_name,
                    short,
                    (d.description or "")[:42],
                    (d.category or "")[:22],
                    "" if d.lower_limit is None else str(d.lower_limit),
                    "" if d.upper_limit is None else str(d.upper_limit),
                    d.unit or "",
                    "Y" if d.is_enabled else "·",
                ),
            )

    def _on_tree_select(self, _e: object) -> None:
        if not self._tree:
            return
        sel = self._tree.selection()
        if not sel:
            return
        try:
            idx = int(sel[0])
        except ValueError:
            return
        self._flush_detail_to_selection()
        self._selected_index = idx
        if 0 <= idx < len(self._all_defs):
            self._load_detail(self._all_defs[idx])

    def _on_tree_double(self, _e: object) -> None:
        """Double-click ON column toggles enabled."""
        if not self._tree:
            return
        region = self._tree.identify_region(_e.x, _e.y)
        if region != "cell":
            return
        col = self._tree.identify_column(_e.x)
        if col != "#9":
            return
        sel = self._tree.selection()
        if not sel:
            return
        try:
            idx = int(sel[0])
        except ValueError:
            return
        if 0 <= idx < len(self._all_defs):
            self._all_defs[idx].is_enabled = not self._all_defs[idx].is_enabled
            self._mark_limits_dirty()
            self._rebuild_tree_only()
            self._tree.selection_set(str(idx))
            self._load_detail(self._all_defs[idx])

    def _load_detail(self, d: LimitDefinition) -> None:
        self._e_label.delete(0, "end")
        self._e_label.insert(0, d.parameter_name if not d.parameter_name.startswith("__new__") else "")
        self._e_type.set(_TYPE_SHORT.get(d.parameter_type, "Other"))
        self._e_desc.delete(0, "end")
        self._e_desc.insert(0, d.description or "")
        self._e_cat.delete(0, "end")
        self._e_cat.insert(0, d.category or "")
        self._e_lo.delete(0, "end")
        if d.lower_limit is not None:
            self._e_lo.insert(0, str(d.lower_limit))
        self._e_hi.delete(0, "end")
        if d.upper_limit is not None:
            self._e_hi.insert(0, str(d.upper_limit))
        self._e_unit.delete(0, "end")
        self._e_unit.insert(0, d.unit or "")
        self._e_rc.delete(0, "end")
        self._e_rc.insert(0, d.root_cause or "")
        self._en_var.set(d.is_enabled)

    def _flush_detail_to_selection(self) -> None:
        if self._selected_index is None:
            return
        idx = self._selected_index
        if idx < 0 or idx >= len(self._all_defs):
            return
        d = self._all_defs[idx]
        label = self._e_label.get().strip()
        if not label and d.parameter_name.startswith("__new__"):
            label = d.parameter_name
        elif not label:
            return
        d.parameter_name = label
        d.parameter_type = _type_from_short(self._e_type.get())
        d.description = self._e_desc.get().strip()
        d.category = self._e_cat.get().strip()
        d.unit = self._e_unit.get().strip()
        d.root_cause = self._e_rc.get().strip()
        d.lower_limit = self._parse_float(self._e_lo.get())
        d.upper_limit = self._parse_float(self._e_hi.get())
        d.is_enabled = self._en_var.get()

    def _apply_detail_to_def(self) -> None:
        if self._selected_index is None:
            messagebox.showinfo("Bosch Plausibility Check", "Select a row in the table first.")
            return
        self._flush_detail_to_selection()
        self._mark_limits_dirty()
        self._rebuild_tree_only()
        if self._tree and self._selected_index is not None:
            iid = str(self._selected_index)
            if self._tree.exists(iid):
                self._tree.selection_set(iid)
                self._tree.see(iid)

    @staticmethod
    def _parse_float(s: str) -> Any:
        s = s.strip()
        if not s:
            return None
        try:
            return float(s.replace(",", "."))
        except ValueError:
            return None

    def on_show(self) -> None:
        self._refresh_category_menu()
        proj = self.controller.current_project
        if proj:
            self.engine_override.set(proj.engine_type_key())
        self._load_engine_profile()

    def _engine_type_value(self) -> str:
        return self.engine_override.get()

    def _load_engine_profile(self) -> None:
        db: DatabaseManager = self.controller.db
        self._all_defs = db.get_limit_profile(self._engine_type_value())
        self._selected_index = None
        self._mark_limits_clean()
        self._rebuild_tree_only()

    def _collect_definitions(self) -> List[LimitDefinition]:
        self._flush_detail_to_selection()
        names = [x.parameter_name for x in self._all_defs]
        if len(names) != len(set(names)):
            messagebox.showwarning("Bosch Plausibility Check", "Duplicate parameter labels.")
            return []
        for d in self._all_defs:
            if not d.parameter_name or d.parameter_name.startswith("__new__"):
                messagebox.showwarning("Bosch Plausibility Check", "Every row needs a parameter label (use Edit panel).")
                return []
            if not d.parameter_name.strip():
                messagebox.showwarning(
                    "Bosch Plausibility Check",
                    "Empty parameter label is not allowed. Use the edit panel to set a name.",
                )
                return []
            lo, hi = d.lower_limit, d.upper_limit
            if lo is not None and hi is not None and lo > hi:
                messagebox.showwarning(
                    "Bosch Plausibility Check",
                    f'Lower limit > upper limit for "{d.parameter_name}". Fix before saving.',
                )
                return []
        return list(self._all_defs)

    def _save(self) -> None:
        defs = self._collect_definitions()
        if not defs:
            return
        self.controller.db.replace_limit_profile(self._engine_type_value(), defs)
        self._all_defs = defs
        self._mark_limits_clean()
        messagebox.showinfo("Bosch Plausibility Check", "All limits saved.")
        self._rebuild_tree_only()
        logger.info("Saved profile %s (%s rows)", self._engine_type_value(), len(defs))

    def _export_json(self) -> None:
        defs = self._collect_definitions()
        if not defs:
            defs = self.controller.db.get_limit_profile(self._engine_type_value())
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            Path(path).write_text(export_profile_json(defs), encoding="utf-8")

    def _export_template(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="limits_template.xlsx",
        )
        if not path:
            return
        try:
            write_limits_template_excel(Path(path))
            messagebox.showinfo("Bosch Plausibility Check", f"Template saved:\n{path}")
        except Exception as e:
            messagebox.showerror("Bosch Plausibility Check", str(e))

    def _import_json(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            defs = import_profile_json(Path(path).read_text(encoding="utf-8"))
        except Exception as e:
            messagebox.showerror("Bosch Plausibility Check", str(e))
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
            messagebox.showerror("Bosch Plausibility Check", str(e))
            return
        existing = {d.parameter_name: d for d in self.controller.db.get_limit_profile(self._engine_type_value())}
        for d in new_rows:
            existing[d.parameter_name] = d
        merged = list(existing.values())
        self.controller.db.replace_limit_profile(self._engine_type_value(), merged)
        self._load_engine_profile()
        messagebox.showinfo("Bosch Plausibility Check", f"Imported {len(new_rows)} row(s).")

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
        self._flush_detail_to_selection()
        n = sum(1 for d in self._all_defs if d.parameter_name.startswith("__new__"))
        blank = LimitDefinition(
            parameter_name=f"__new__{n + 1}",
            parameter_type=ParameterType.OTHER,
            description="",
            unit="",
            is_enabled=True,
        )
        self._all_defs.append(blank)
        self._mark_limits_dirty()
        new_i = len(self._all_defs) - 1
        if not self._passes_filter(blank):
            self.cat_filter.set("All")
        self._rebuild_tree_only()
        if self._tree:
            self._tree.selection_set(str(new_i))
            self._tree.see(str(new_i))
            self._selected_index = new_i
            self._load_detail(blank)
