"""Modal dialog helpers for Tk on slow or virtual displays (e.g. Codespaces / noVNC)."""

from __future__ import annotations

import logging
import tkinter as tk
from typing import Any

logger = logging.getLogger(__name__)


def safe_grab_set(widget: Any) -> None:
    """
    Call grab_set after the window is mapped.

    Immediate grab_set() can raise TclError: 'grab failed: window not viewable'
    on Linux / remote desktop; modal still works without grab on most setups.
    """

    def attempt() -> None:
        try:
            widget.update_idletasks()
            widget.grab_set()
        except tk.TclError as e:
            logger.debug("grab_set skipped: %s", e)

    try:
        widget.after_idle(attempt)
        widget.after(100, attempt)
    except tk.TclError as e:
        logger.debug("schedule grab failed: %s", e)
