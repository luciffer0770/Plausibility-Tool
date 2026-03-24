"""PUMA Excel/CSV import and column mapping."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from core.standard_parameters import all_standard_parameter_names

logger = logging.getLogger(__name__)

_TIMESTAMP_HINTS = frozenset(
    {
        "time",
        "timestamp",
        "date",
        "datetime",
        "zeit",
        "datum",
    }
)


def _normalize_header(h: Any) -> str:
    s = str(h).strip()
    s = re.sub(r"\s+", "_", s)
    return s


def _strip_suffix(name: str) -> tuple[str, Optional[str]]:
    """Return (base, suffix) for _min/_max/_avg/MIN/MAX/AVG."""
    lower = name.lower()
    for suf, tag in (
        ("_min", "min"),
        ("_max", "max"),
        ("_avg", "avg"),
        (" min", "min"),
        (" max", "max"),
        (" avg", "avg"),
    ):
        if lower.endswith(suf.replace(" ", "_")):
            base = name[: -len(suf)].strip()
            return base, tag
    return name, None


def detect_column_mapping(df: pd.DataFrame) -> dict[str, Any]:
    """
    Map dataframe columns to parameter names and timestamp.

    Returns:
        Dict with keys: timestamp_col, mappings (list of dicts with
        excel_col, parameter, value_role).
    """
    cols = list(df.columns)
    norm_map: dict[str, str] = {}
    for c in cols:
        norm_map[_normalize_header(c)] = str(c)

    standards = set(all_standard_parameter_names())
    mappings: list[dict[str, Any]] = []
    used_excel: set[str] = set()

    timestamp_col: Optional[str] = None
    for c in cols:
        n = _normalize_header(c).lower()
        for hint in _TIMESTAMP_HINTS:
            if hint in n:
                timestamp_col = str(c)
                break
        if timestamp_col:
            break

    for c in cols:
        if str(c) == timestamp_col:
            continue
        raw = str(c)
        base, role = _strip_suffix(raw)
        nb = _normalize_header(base)
        # exact match
        param = None
        if nb in standards:
            param = nb
        elif nb.upper() in {s.upper() for s in standards}:
            for s in standards:
                if s.upper() == nb.upper():
                    param = s
                    break
        if param:
            mappings.append(
                {
                    "excel_col": raw,
                    "parameter": param,
                    "value_role": role or "instant",
                }
            )
            used_excel.add(raw)

    unmapped = [str(c) for c in cols if str(c) not in used_excel and str(c) != timestamp_col]

    return {
        "timestamp_col": timestamp_col,
        "mappings": mappings,
        "unmapped_columns": unmapped,
    }


def load_dataframe(path: Path) -> pd.DataFrame:
    """Load xlsx/xls/csv into DataFrame."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".xlsx":
        return pd.read_excel(path, engine="openpyxl")
    if suffix == ".xls":
        return pd.read_excel(path, engine="xlrd")
    if suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported format: {suffix}")


def apply_mapping(
    df: pd.DataFrame,
    timestamp_col: Optional[str],
    mappings: list[dict[str, Any]],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Build a narrow table: timestamp + one column per (parameter, role).

    Returns:
        (result_df, summary dict).
    """
    out_cols: dict[str, list[Any]] = {}
    if timestamp_col and timestamp_col in df.columns:
        out_cols["timestamp"] = df[timestamp_col].astype(str).tolist()

    param_roles: dict[str, set[str]] = {}
    for m in mappings:
        col = m["excel_col"]
        param = m["parameter"]
        role = m.get("value_role") or "instant"
        if col not in df.columns:
            logger.warning("Mapped column missing: %s", col)
            continue
        key = f"{param}__{role}"
        out_cols[key] = pd.to_numeric(df[col], errors="coerce").tolist()
        param_roles.setdefault(param, set()).add(role)

    result = pd.DataFrame(out_cols)
    summary = {
        "rows": len(result),
        "parameters": sorted(param_roles.keys()),
        "roles_per_param": {k: sorted(v) for k, v in param_roles.items()},
    }
    return result, summary


def preview_dataframe(df: pd.DataFrame, max_rows: int = 8) -> pd.DataFrame:
    """First N rows for UI preview."""
    return df.head(max_rows).copy()
