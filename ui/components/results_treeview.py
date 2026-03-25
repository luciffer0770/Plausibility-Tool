"""Results table using ttk.Treeview — fast, readable, native scrollbars."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, List, Optional

from core.plausibility_engine import limits_display_str
from ui.theme import BOSCH_DARK_GRAY, BOSCH_WHITE


def _status_tag(st: str) -> str:
    s = (st or "").upper()
    if s == "OK":
        return "ok"
    if s in ("HIGH", "LOW", "FAIL"):
        return "fail"
    return "nodata"


class ResultsTreeview(ttk.Frame):
    """Scrollable results table (ttk is much faster than dozens of CTk widgets per row)."""

    def __init__(
        self,
        master: tk.Misc,
        on_row_select: Optional[Callable[[dict[str, Any]], None]] = None,
    ) -> None:
        super().__init__(master)
        self._on_select = on_row_select
        self._rows: List[dict[str, Any]] = []

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Results.Treeview",
            rowheight=22,
            fieldbackground=BOSCH_WHITE,
            background=BOSCH_WHITE,
            foreground=BOSCH_DARK_GRAY,
        )
        style.configure(
            "Results.Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#E8E8E8",
            foreground=BOSCH_DARK_GRAY,
        )
        style.map("Results.Treeview", background=[("selected", "#F5D5D5")])

        cols = (
            "parameter",
            "description",
            "category",
            "ptype",
            "runs",
            "vmin",
            "vmax",
            "vavg",
            "zeit_viol",
            "vsample",
            "limits",
            "status",
            "root",
        )
        self.tree = ttk.Treeview(
            self,
            columns=cols,
            show="headings",
            selectmode="browse",
            style="Results.Treeview",
            height=16,
        )
        headings = {
            "parameter": ("Parameter", 82),
            "description": ("Description", 140),
            "category": ("Category", 80),
            "ptype": ("Type", 48),
            "runs": ("Runs", 34),
            "vmin": ("Min", 48),
            "vmax": ("Max", 48),
            "vavg": ("Avg", 48),
            "zeit_viol": ("ZEIT (out of range)", 140),
            "vsample": ("Values (sample)", 110),
            "limits": ("Limits", 92),
            "status": ("Status", 44),
            "root": ("Root cause", 160),
        }
        for c, (text, w) in headings.items():
            self.tree.heading(c, text=text, anchor="w")
            self.tree.column(c, width=w, minwidth=36, anchor="w", stretch=True)

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.tree.tag_configure("ok", background="#E8F5E9")
        self.tree.tag_configure("fail", background="#FDEDED")
        self.tree.tag_configure("nodata", background="#F0F0F0")

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def _on_tree_select(self, _e: object) -> None:
        if not self._on_select:
            return
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        try:
            idx = int(iid)
            if 0 <= idx < len(self._rows):
                self._on_select(self._rows[idx])
        except ValueError:
            pass

    def set_rows(self, rows: List[dict[str, Any]]) -> None:
        self._rows = list(rows)
        self.tree.delete(*self.tree.get_children())

        def fmt(v: Any) -> str:
            if v is None:
                return "—"
            if isinstance(v, float):
                return f"{v:.2f}"
            return str(v)

        for idx, m in enumerate(self._rows):
            st = str(m.get("status", ""))
            lo = m.get("limit_lower")
            hi = m.get("limit_upper")
            unit = str(m.get("unit") or "")
            lims = limits_display_str(
                float(lo) if lo is not None else None,
                float(hi) if hi is not None else None,
                unit,
            )
            vs = str(m.get("values_sample") or "")
            if not vs:
                vshort = "—"
            elif len(vs) > 55:
                vshort = vs[:52] + "…"
            else:
                vshort = vs
            zv = str(m.get("timestamp") or "").strip()
            if not zv:
                zv = "—"
            elif len(zv) > 48:
                zv = zv[:45] + "…"
            root = str(m.get("root_cause") or "")
            if len(root) > 70:
                root = root[:67] + "…"

            self.tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(
                    str(m.get("parameter_name", "")),
                    str(m.get("description", ""))[:50],
                    str(m.get("category", ""))[:26],
                    str(m.get("param_type", m.get("parameter_type", "")))[:12],
                    str(m.get("num_runs", "")),
                    fmt(m.get("value_min")),
                    fmt(m.get("value_max")),
                    fmt(m.get("value_avg")),
                    zv,
                    vshort,
                    lims[:40],
                    st,
                    root,
                ),
                tags=(_status_tag(st),),
            )
