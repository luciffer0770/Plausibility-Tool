"""Set a simple red window icon so the OS does not show the default blue Tk feather."""

from __future__ import annotations

import logging
from io import BytesIO
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Bosch red #ED0007 — small solid icon (no image file required)
_ICON_RGB = (237, 0, 7)


def apply_window_icon(root: Any) -> None:
    """
    Apply icon to the Tk root (taskbar / title bar on many systems).

    Keeps a reference on root._bosch_icon_photo to avoid GC.
    """
    try:
        from PIL import Image, ImageTk
    except ImportError:
        logger.debug("Pillow not available; skipping custom window icon")
        return

    try:
        img = Image.new("RGBA", (64, 64), _ICON_RGB + (255,))
        photo = ImageTk.PhotoImage(img)
        root.iconphoto(True, photo)
        root._bosch_icon_photo = photo  # noqa: SLF001 — prevent GC
    except Exception as e:
        logger.debug("Could not set window icon: %s", e)
