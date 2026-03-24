"""Dashboard: overview cards and matplotlib charts."""

from __future__ import annotations

from typing import Any

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from database.db_manager import DatabaseManager
from ui.pages.base_page import BasePage
from ui.theme import BOSCH_DARK_GRAY, BOSCH_LIGHT_GRAY, BOSCH_MID_GRAY, BOSCH_WHITE, GRID, font_body, font_h3


class DashboardPage(BasePage):
    """Pass/warn/fail over sessions and top failing parameters."""

    def __init__(self, parent: ctk.CTkFrame, controller: Any) -> None:
        super().__init__(parent, controller)
        self._canvas_bar: Any = None
        self.setup_ui()

    def setup_ui(self) -> None:
        self.configure(fg_color=BOSCH_LIGHT_GRAY)
        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="x", padx=GRID, pady=GRID)

        self.card_uploads = self._card(cards, "Total uploads", "0")
        self.card_pass = self._card(cards, "Last session pass %", "—")
        self.card_top = self._card(cards, "Top failing parameter", "—")

        charts = ctk.CTkFrame(
            self,
            fg_color=BOSCH_WHITE,
            corner_radius=8,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
        )
        charts.pack(fill="both", expand=True, padx=GRID, pady=GRID)

        self.fig = Figure(figsize=(5, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self._canvas_bar = FigureCanvasTkAgg(self.fig, master=charts)
        self._canvas_bar.get_tk_widget().pack(fill="both", expand=True, padx=GRID, pady=GRID)

    def _card(self, parent: ctk.CTkFrame, title: str, value: str) -> ctk.CTkLabel:
        f = ctk.CTkFrame(
            parent,
            fg_color=BOSCH_WHITE,
            corner_radius=8,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
            width=200,
            height=88,
        )
        f.pack(side="left", padx=8, pady=4)
        f.pack_propagate(False)
        ctk.CTkLabel(f, text=title, font=font_body(), text_color=BOSCH_DARK_GRAY).pack(anchor="w", padx=GRID, pady=4)
        lbl = ctk.CTkLabel(f, text=value, font=font_h3(), text_color=BOSCH_DARK_GRAY)
        lbl.pack(anchor="w", padx=GRID)
        return lbl

    def on_show(self) -> None:
        pid = self.controller.current_project.id if self.controller.current_project else None
        if not pid:
            return
        db: DatabaseManager = self.controller.db
        st = db.project_upload_stats(pid)
        self.card_uploads.configure(text=str(st.get("upload_count", 0)))
        pct = st.get("last_pass_pct")
        self.card_pass.configure(text=f"{pct}%" if pct is not None else "—")
        top = db.top_failing_parameters(pid, 1)
        if top:
            self.card_top.configure(text=f"{top[0]['parameter_name']} ({top[0]['fails']})")
        else:
            self.card_top.configure(text="—")

        agg = db.aggregate_status_by_session(pid)
        self.ax.clear()
        if agg:
            labels = [str(a["upload_date"])[:10] for a in reversed(agg)]
            ok = [int(a["ok_n"] or 0) for a in reversed(agg)]
            wn = [int(a["warn_n"] or 0) for a in reversed(agg)]
            fl = [int(a["fail_n"] or 0) for a in reversed(agg)]
            x = range(len(labels))
            self.ax.bar(x, ok, label="OK", color="#00884B")
            self.ax.bar(x, wn, bottom=ok, label="WARN", color="#F5A623")
            b2 = [ok[i] + wn[i] for i in x]
            self.ax.bar(x, fl, bottom=b2, label="FAIL", color="#ED0007")
            self.ax.set_xticks(list(x))
            self.ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7)
            self.ax.legend(fontsize=7)
        self.ax.set_title("Status by upload (recent)")
        self.fig.tight_layout()
        if self._canvas_bar:
            self._canvas_bar.draw()
