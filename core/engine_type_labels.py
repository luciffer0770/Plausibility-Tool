"""Single place to build engine-type dropdown lists (projects + limits stay in sync)."""

from __future__ import annotations

from typing import Any, List

from core.engine_types_store import load_extra_engine_types
from core.models import EngineType


def list_engine_type_labels(db: Any) -> List[str]:
    """Preset enums + JSON extras + DB engine_types table."""
    preset = [e.value for e in EngineType]
    seen = set(preset)
    out = list(preset)
    for n in load_extra_engine_types():
        if n not in seen:
            seen.add(n)
            out.append(n)
    try:
        for n in db.list_engine_type_names():
            if n not in seen:
                seen.add(n)
                out.append(n)
    except Exception:
        pass
    return out
