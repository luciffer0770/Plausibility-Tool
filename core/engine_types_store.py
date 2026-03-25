"""User-defined engine type names persisted in JSON (survives restarts)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def _store_path() -> Path:
    root = Path(__file__).resolve().parent.parent
    cfg = root / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    return cfg / "user_engine_types.json"


def load_extra_engine_types() -> List[str]:
    path = _store_path()
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
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
        logger.warning("Could not read %s: %s", path, e)
        return []


def save_extra_engine_types(names: List[str]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    uniq: List[str] = []
    for n in names:
        s = str(n).strip()
        if s and s not in uniq:
            uniq.append(s)
    path.write_text(json.dumps({"names": uniq}, indent=2, ensure_ascii=False), encoding="utf-8")


def add_extra_engine_type(name: str) -> List[str]:
    name = str(name).strip()
    if not name:
        return load_extra_engine_types()
    cur = load_extra_engine_types()
    if name not in cur:
        cur.append(name)
        save_extra_engine_types(cur)
    return cur


def remove_extra_engine_type(name: str) -> List[str]:
    name = str(name).strip()
    cur = load_extra_engine_types()
    cur = [x for x in cur if x != name]
    save_extra_engine_types(cur)
    return cur
