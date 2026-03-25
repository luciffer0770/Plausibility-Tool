#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bosch Plausibility Check Tool — entry point."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure package root is importable when run as script
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ui.app import PlausibilityApp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main() -> None:
    """Start the application."""
    app = PlausibilityApp()
    try:
        app.mainloop()
    finally:
        app.db.close()


if __name__ == "__main__":
    main()
