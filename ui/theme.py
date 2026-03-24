"""Bosch design tokens: typography, spacing, re-export colors."""

from __future__ import annotations

import logging
from typing import Optional

import tkinter.font as tkfont

from core.style_constants import (
    BOSCH_DARK_BLUE,
    BOSCH_DARK_GRAY,
    BOSCH_LIGHT_GRAY,
    BOSCH_MID_GRAY,
    BOSCH_RED,
    BOSCH_STEEL,
    BOSCH_WHITE,
    STATUS_FAIL,
    STATUS_NO_DATA,
    STATUS_OK,
    STATUS_WARNING,
)

logger = logging.getLogger(__name__)

# Re-export colors for UI
BOSCH_RED = BOSCH_RED
BOSCH_DARK_BLUE = BOSCH_DARK_BLUE
BOSCH_WHITE = BOSCH_WHITE
BOSCH_LIGHT_GRAY = BOSCH_LIGHT_GRAY
BOSCH_MID_GRAY = BOSCH_MID_GRAY
BOSCH_DARK_GRAY = BOSCH_DARK_GRAY
BOSCH_STEEL = BOSCH_STEEL
STATUS_OK = STATUS_OK
STATUS_WARNING = STATUS_WARNING
STATUS_FAIL = STATUS_FAIL
STATUS_NO_DATA = STATUS_NO_DATA

FONT_PRIMARY = "Bosch Sans"
FONT_FALLBACK = "Segoe UI"
FONT_MONO = "Consolas"

GRID = 8
SIDEBAR_WIDTH = 240
HEADER_HEIGHT = 56
CARD_RADIUS = 8
BUTTON_RADIUS = 4

ROW_ALT_A = BOSCH_WHITE
ROW_ALT_B = "#F7F7F7"
ROW_FAIL_BG = "#FDEDED"
ROW_WARN_BG = "#FFF8E6"

SUMMARY_OK = STATUS_OK
SUMMARY_WARN = STATUS_WARNING
SUMMARY_FAIL = STATUS_FAIL
SUMMARY_ND = STATUS_NO_DATA

_FONT_FAMILY: Optional[str] = None


def ensure_theme_ready() -> None:
    """Call once after the main CTk window exists so font resolution succeeds."""
    _resolved_family()


def _resolved_family() -> str:
    """
    Resolve UI font after a Tk root exists.

    tkinter.font.families() requires a default root; this must not run at import time.
    """
    global _FONT_FAMILY
    if _FONT_FAMILY is not None:
        return _FONT_FAMILY
    names = (FONT_PRIMARY, FONT_FALLBACK, "Ubuntu", "DejaVu Sans")
    try:
        available = tkfont.families()
        for n in names:
            if n in available:
                _FONT_FAMILY = n
                return n
    except RuntimeError as e:
        logger.debug("Font probe skipped: %s", e)
    _FONT_FAMILY = "DejaVu Sans"
    return _FONT_FAMILY


def font_h1() -> tuple[str, int, str]:
    return (_resolved_family(), 22, "bold")


def font_h2() -> tuple[str, int, str]:
    return (_resolved_family(), 16, "bold")


def font_h3() -> tuple[str, int, str]:
    return (_resolved_family(), 13, "bold")


def font_body() -> tuple[str, int]:
    return (_resolved_family(), 12)


def font_small() -> tuple[str, int]:
    return (_resolved_family(), 10)


def font_mono() -> tuple[str, int]:
    return (FONT_MONO, 12)
