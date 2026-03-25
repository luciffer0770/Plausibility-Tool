"""Generate annotated Excel and PDF."""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Optional, Tuple

import customtkinter as ctk

from core.report_generator import (
    write_annotated_excel,
    write_pdf_summary,
    write_plausibility_report_excel,
)
from database.db_manager import DatabaseManager
from ui.pages.base_page import BasePage
from ui.theme import BOSCH_LIGHT_GRAY, BOSCH_MID_GRAY, BOSCH_WHITE, GRID, font_body


class ReportPage(BasePage):
    """Export reports for current session."""

    def __init__(self, parent: ctk.CTkFrame, controller: Any) -> None:
        super().__init__(parent, controller)
        self.setup_ui()

    def setup_ui(self) -> None:
        self.configure(fg_color=BOSCH_LIGHT_GRAY)
        box = ctk.CTkFrame(
            self,
            fg_color=BOSCH_WHITE,
            corner_radius=8,
            border_width=1,
            border_color=BOSCH_MID_GRAY,
        )
        box.pack(fill="both", expand=True, padx=GRID * 3, pady=GRID * 3)
        ctk.CTkLabel(box, text="Reports", font=font_body()).pack(anchor="w", padx=GRID, pady=GRID)
        ctk.CTkButton(
            box,
            text="Export plausibility report (Bosch format)…",
            width=280,
            height=36,
            corner_radius=4,
            command=self._export_report_xlsx,
            font=font_body(),
        ).pack(anchor="w", padx=GRID, pady=8)
        ctk.CTkButton(
            box,
            text="Export annotated workbook (original + analysis)…",
            width=280,
            height=36,
            corner_radius=4,
            command=self._export_xlsx,
            font=font_body(),
        ).pack(anchor="w", padx=GRID, pady=8)
        ctk.CTkButton(
            box,
            text="Export PDF summary…",
            width=200,
            height=36,
            corner_radius=4,
            command=self._export_pdf,
            font=font_body(),
        ).pack(anchor="w", padx=GRID, pady=8)

    def _session_context(self) -> Optional[Tuple[int, Path]]:
        sid = self.controller.current_session_id
        proj = self.controller.current_project
        if sid is None or proj is None:
            messagebox.showwarning("Bosch Plausibility Check", "No session or project.")
            return None
        db: DatabaseManager = self.controller.db
        sess = db.get_upload_session(sid)
        if not sess or not sess.get("file_path"):
            messagebox.showwarning("Bosch Plausibility Check", "Original file path not stored for this session.")
            return None
        return sid, Path(sess["file_path"])

    def _export_report_xlsx(self) -> None:
        sid = self.controller.current_session_id
        if sid is None:
            messagebox.showwarning("Bosch Plausibility Check", "No session.")
            return
        out = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
        )
        if not out:
            return
        try:
            write_plausibility_report_excel(Path(out), sid, self.controller.db)
            messagebox.showinfo("Bosch Plausibility Check", f"Saved:\n{out}")
        except Exception as e:
            messagebox.showerror("Bosch Plausibility Check", str(e))

    def _export_xlsx(self) -> None:
        ctx = self._session_context()
        if not ctx:
            return
        sid, src = ctx
        out = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
        )
        if not out:
            return
        try:
            write_annotated_excel(src, Path(out), sid, self.controller.db)
            messagebox.showinfo("Bosch Plausibility Check", f"Saved:\n{out}")
        except Exception as e:
            messagebox.showerror("Bosch Plausibility Check", str(e))

    def _export_pdf(self) -> None:
        sid = self.controller.current_session_id
        proj = self.controller.current_project
        if sid is None or proj is None:
            messagebox.showwarning("Bosch Plausibility Check", "No session or project.")
            return
        db = self.controller.db
        rows = db.get_measurements_for_session(sid)
        sess = db.get_upload_session(sid)
        ok_n = sum(1 for m in rows if m.get("status") == "OK")
        w_n = sum(1 for m in rows if m.get("status") == "WARNING")
        f_n = sum(
            1
            for m in rows
            if m.get("status") in ("FAIL", "HIGH", "LOW")
        )
        nd_n = sum(1 for m in rows if m.get("status") in ("NO_DATA", "N/A"))
        summary = {
            "ok_n": ok_n,
            "warn_n": w_n,
            "fail_n": f_n,
            "nd_n": nd_n,
            "file_name": sess.get("file_name") if sess else "",
            "upload_date": sess.get("upload_date") if sess else "",
        }
        out = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
        )
        if not out:
            return
        logo = Path(__file__).resolve().parent.parent.parent / "assets" / "bosch_logo.png"
        try:
            write_pdf_summary(Path(out), proj, summary, rows, logo if logo.is_file() else None)
            messagebox.showinfo("Bosch Plausibility Check", f"Saved:\n{out}")
        except Exception as e:
            messagebox.showerror("Bosch Plausibility Check", str(e))
