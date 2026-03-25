"""Limit profile CRUD and JSON import/export."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from core.models import LimitDefinition, ParameterType
from core.standard_parameters import default_limit_definitions
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


def _definition_to_dict(d: LimitDefinition) -> dict[str, Any]:
    return {
        "parameter_name": d.parameter_name,
        "parameter_type": d.parameter_type.value,
        "description": d.description,
        "unit": d.unit,
        "lower_limit": d.lower_limit,
        "upper_limit": d.upper_limit,
        "warning_pct": d.warning_pct,
        "root_cause": d.root_cause,
        "corrective_action": d.corrective_action,
        "is_required": d.is_required,
        "is_enabled": d.is_enabled,
    }


def _dict_to_definition(data: dict[str, Any]) -> LimitDefinition:
    pt = ParameterType.OTHER
    for p in ParameterType:
        if p.value == data.get("parameter_type"):
            pt = p
            break
    return LimitDefinition(
        parameter_name=str(data["parameter_name"]),
        parameter_type=pt,
        description=str(data.get("description", "")),
        unit=str(data.get("unit", "")),
        lower_limit=data.get("lower_limit"),
        upper_limit=data.get("upper_limit"),
        warning_pct=float(data.get("warning_pct", 10.0)),
        root_cause=str(data.get("root_cause", "")),
        corrective_action=str(data.get("corrective_action", "")),
        is_required=bool(data.get("is_required", False)),
        is_enabled=bool(data.get("is_enabled", True)),
    )


def ensure_default_profile(db: DatabaseManager, engine_type_value: str) -> None:
    """Seed profile from standard layout if none exists."""
    existing = db.get_limit_profile(engine_type_value)
    if existing:
        return
    na = "NA" in engine_type_value.upper()
    defs = default_limit_definitions(engine_na=na)
    db.replace_limit_profile(engine_type_value, defs)
    logger.info("Seeded default profile for %s", engine_type_value)


def export_profile_json(definitions: list[LimitDefinition]) -> str:
    """Serialize profile to JSON string."""
    payload = {"version": 1, "limits": [_definition_to_dict(d) for d in definitions]}
    return json.dumps(payload, indent=2, ensure_ascii=False)


def import_profile_json(text: str) -> list[LimitDefinition]:
    """Parse profile JSON."""
    data = json.loads(text)
    limits = data.get("limits", data)
    if not isinstance(limits, list):
        raise ValueError("Invalid profile JSON: expected 'limits' array")
    return [_dict_to_definition(x) for x in limits]


def import_parameters_from_excel(path: Path) -> list[LimitDefinition]:
    """
    Import additional parameter rows from an Excel sheet.

    Expected columns (case-insensitive): parameter_name, type, description,
    unit, lower_limit, upper_limit, warning_pct, root_cause, corrective_action,
    required / is_required.
    """
    import pandas as pd

    df = pd.read_excel(path, engine="openpyxl")
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    def col(*names: str) -> Optional[str]:
        for n in names:
            if n in df.columns:
                return n
        return None

    name_c = col("parameter_name", "parameter", "name")
    if not name_c:
        raise ValueError("Excel must contain a parameter name column")

    type_c = col("parameter_type", "type")
    desc_c = col("description", "desc")
    unit_c = col("unit")
    lo_c = col("lower_limit", "lower")
    hi_c = col("upper_limit", "upper")
    wp_c = col("warning_pct", "warning_%")
    rc_c = col("root_cause")
    ca_c = col("corrective_action", "action")
    req_c = col("is_required", "required")
    en_c = col("is_enabled", "enabled", "on")

    out: list[LimitDefinition] = []
    for _, row in df.iterrows():
        pname = str(row[name_c]).strip()
        if not pname or pname.lower() == "nan":
            continue
        pt = ParameterType.OTHER
        if type_c and pd.notna(row[type_c]):
            raw = str(row[type_c]).strip()
            for p in ParameterType:
                if p.value.lower() == raw.lower():
                    pt = p
                    break
        desc = str(row[desc_c]).strip() if desc_c and pd.notna(row.get(desc_c)) else ""
        unit = str(row[unit_c]).strip() if unit_c and pd.notna(row.get(unit_c)) else ""
        lo = float(row[lo_c]) if lo_c and pd.notna(row.get(lo_c)) else None
        hi = float(row[hi_c]) if hi_c and pd.notna(row.get(hi_c)) else None
        wp = float(row[wp_c]) if wp_c and pd.notna(row.get(wp_c)) else 10.0
        rc = str(row[rc_c]).strip() if rc_c and pd.notna(row.get(rc_c)) else ""
        ca = str(row[ca_c]).strip() if ca_c and pd.notna(row.get(ca_c)) else ""
        req = False
        if req_c and pd.notna(row.get(req_c)):
            v = row[req_c]
            if isinstance(v, (int, float)):
                req = bool(int(v))
            else:
                req = str(v).strip().lower() in ("1", "true", "yes", "y", "x")
        enabled = True
        if en_c and pd.notna(row.get(en_c)):
            v = row[en_c]
            if isinstance(v, (int, float)):
                enabled = bool(int(v))
            else:
                enabled = str(v).strip().lower() in ("1", "true", "yes", "y", "x")

        out.append(
            LimitDefinition(
                parameter_name=pname,
                parameter_type=pt,
                description=desc,
                unit=unit,
                lower_limit=lo,
                upper_limit=hi,
                warning_pct=wp,
                root_cause=rc,
                corrective_action=ca,
                is_required=req,
                is_enabled=enabled,
            )
        )
    return out
