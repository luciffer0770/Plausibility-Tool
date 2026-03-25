"""Global ttk styling: reduce blue focus rings; align with Bosch neutrals + red accent."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ui.theme import BOSCH_DARK_GRAY, BOSCH_LIGHT_GRAY, BOSCH_MID_GRAY, BOSCH_WHITE


def neutral_ctk_entry_focus(widget: object) -> None:
    """Remove blue Tk focus ring on CustomTkinter entry (inner tk.Entry)."""
    try:
        for ch in widget.winfo_children():  # type: ignore[attr-defined]
            if ch.winfo_class() == "Entry":
                ch.configure(  # type: ignore[union-attr]
                    highlightthickness=1,
                    highlightbackground=BOSCH_MID_GRAY,
                    highlightcolor=BOSCH_MID_GRAY,
                    insertbackground=BOSCH_DARK_GRAY,
                )
                break
    except Exception:
        pass


def apply_global_ttk_style(root: tk.Misc) -> None:
    """Call once after the main window exists."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # Entry / combobox: gray focus instead of default blue highlight
    style.configure(
        "TEntry",
        fieldbackground=BOSCH_WHITE,
        foreground=BOSCH_DARK_GRAY,
        insertcolor=BOSCH_DARK_GRAY,
    )
    style.map(
        "TEntry",
        bordercolor=[("focus", BOSCH_MID_GRAY)],
        lightcolor=[("focus", BOSCH_MID_GRAY)],
        darkcolor=[("focus", BOSCH_MID_GRAY)],
    )
    style.configure(
        "TCombobox",
        fieldbackground=BOSCH_WHITE,
        foreground=BOSCH_DARK_GRAY,
        arrowcolor=BOSCH_DARK_GRAY,
    )
    style.map(
        "TCombobox",
        bordercolor=[("focus", BOSCH_MID_GRAY)],
        lightcolor=[("focus", BOSCH_MID_GRAY)],
        darkcolor=[("focus", BOSCH_MID_GRAY)],
    )

    # Treeviews: selection tint (red-tinted gray, not system blue)
    style.configure(
        "Treeview",
        background=BOSCH_WHITE,
        fieldbackground=BOSCH_WHITE,
        foreground=BOSCH_DARK_GRAY,
        rowheight=22,
    )
    style.map(
        "Treeview",
        background=[("selected", "#F5D5D5")],
        foreground=[("selected", BOSCH_DARK_GRAY)],
    )
    style.configure(
        "Treeview.Heading",
        background="#EEEEEE",
        foreground=BOSCH_DARK_GRAY,
        relief="flat",
    )
    style.configure(
        "Vertical.TScrollbar",
        troughcolor=BOSCH_LIGHT_GRAY,
        background=BOSCH_MID_GRAY,
        arrowcolor=BOSCH_DARK_GRAY,
    )
    style.configure(
        "Horizontal.TScrollbar",
        troughcolor=BOSCH_LIGHT_GRAY,
        background=BOSCH_MID_GRAY,
        arrowcolor=BOSCH_DARK_GRAY,
    )

    # Notebook (if used later)
    style.configure("TNotebook.Tab", padding=[10, 4])
