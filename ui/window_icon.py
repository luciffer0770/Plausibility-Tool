"""Window / taskbar icon: Bosch red (no default blue Tk feather)."""

from __future__ import annotations

import logging
import sys
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_ICON_RGB = (237, 0, 7)


def apply_window_icon(root: Any) -> None:
    """
    Set taskbar and title-bar icon on Windows/Linux/macOS where supported.

    - iconphoto: works on many platforms (keeps PhotoImage on root)
    - Windows: also try iconbitmap with a temporary .ico for the title bar
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
        root._bosch_icon_photo = photo  # noqa: SLF001
    except Exception as e:
        logger.debug("iconphoto failed: %s", e)
        return

    if sys.platform.startswith("win"):
        try:
            ico_path = Path(tempfile.gettempdir()) / "bosch_plausibility_check_icon.ico"
            sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]
            img_win = Image.new("RGBA", (256, 256), _ICON_RGB + (255,))
            img_win.save(str(ico_path), format="ICO", sizes=sizes)
            root.iconbitmap(default=str(ico_path))
        except Exception as e:
            logger.debug("Windows iconbitmap skipped: %s", e)
