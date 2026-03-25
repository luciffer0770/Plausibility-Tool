"""User-defined limit categories (filter presets) in JSON."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Set

from core.puma_constants import PARAMETER_INFO

logger = logging.getLogger(__name__)

_BUILTIN_ORDER = [
    "All",
    "Temperature",
    "Pressure",
    "Emission",
    "Combustion",
    "Other",
    "Set",
]


def _path() -> Path:
    root = Path(__file__).resolve().parent.parent
    d = root / "config"
    d.mkdir(parents=True, exist_ok=True)
    return d / "user_limit_categories.json"


def _categories_from_parameter_info() -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for meta in PARAMETER_INFO.values():
        c = (meta.get("category") or "").strip()
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    out.sort()
    return out


def default_category_presets() -> List[str]:
    """Built-in filter values (no 'All' — that is UI-only)."""
    merged: List[str] = []
    seen: Set[str] = set()
    for c in _BUILTIN_ORDER[1:] + _categories_from_parameter_info():
        if c and c not in seen:
            seen.add(c)
            merged.append(c)
    return merged


def load_extra_categories() -> List[str]:
    p = _path()
    if not p.is_file():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        raw = data.get("names", data) if isinstance(data, dict) else data
        if not isinstance(raw, list):
            return []
        out: List[str] = []
        for x in raw:
            s = str(x).strip()
            if s and s not in out:
                out.append(s)
        return out
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not read limit categories: %s", e)
        return []


def save_extra_categories(names: List[str]) -> None:
    p = _path()
    uniq: List[str] = []
    for n in names:
        s = str(n).strip()
        if s and s not in uniq:
            uniq.append(s)
    p.write_text(json.dumps({"names": uniq}, indent=2, ensure_ascii=False), encoding="utf-8")


def add_category(name: str) -> List[str]:
    name = str(name).strip()
    if not name:
        return merged_filter_values()
    cur = load_extra_categories()
    if name not in cur:
        cur.append(name)
        save_extra_categories(cur)
    return merged_filter_values()


def remove_category(name: str) -> List[str]:
    name = str(name).strip()
    builtins = set(_BUILTIN_ORDER[1:])
    if name in builtins:
        return merged_filter_values()
    cur = [x for x in load_extra_categories() if x != name]
    save_extra_categories(cur)
    return merged_filter_values()


def merged_filter_values() -> List[str]:
    """Ordered list for filter dropdowns (excludes 'All')."""
    seen: Set[str] = set()
    out: List[str] = []
    for c in _BUILTIN_ORDER[1:] + _categories_from_parameter_info() + load_extra_categories():
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out
