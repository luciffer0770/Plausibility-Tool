"""Persist simple UI preferences in config/settings.json (stdlib only)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


def _path() -> Path:
    root = Path(__file__).resolve().parent.parent
    d = root / "config"
    d.mkdir(parents=True, exist_ok=True)
    return d / "settings.json"


def load_settings() -> Dict[str, Any]:
    defaults: Dict[str, Any] = {
        "last_project_id": None,
        "last_puma_path": "",
        "default_export_dir": "",
        "window_geometry": "1400x850",
        "results_show": "All",
        "results_type": "All",
        "results_search": "",
    }
    p = _path()
    if not p.is_file():
        return dict(defaults)
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return dict(defaults)
        out = dict(defaults)
        for k in defaults:
            if k in raw:
                out[k] = raw[k]
        return out
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not read settings: %s", e)
        return dict(defaults)


def save_settings(updates: Dict[str, Any]) -> None:
    p = _path()
    cur = load_settings()
    cur.update(updates)
    try:
        p.write_text(json.dumps(cur, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError as e:
        logger.warning("Could not save settings: %s", e)
