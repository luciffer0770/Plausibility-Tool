"""PUMA file parser: TSV .xls, xlsx, csv — units row, **, aliases."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from core.puma_constants import COLUMN_ALIAS_MAP, canonical_column_name, parameter_defaults
from core.standard_parameters import all_standard_parameter_names

logger = logging.getLogger(__name__)

_TIMESTAMP_HINTS = frozenset(
    {"time", "timestamp", "date", "datetime", "zeit", "datum"}
)

_EXCEL_MAGIC = bytes([0xD0, 0xCF, 0x11, 0xE0])
_ZIP_MAGIC = b"PK"

# Substrings suggesting a units row cell
_UNIT_TOKENS = (
    "°c",
    "°f",
    "mbar",
    "bar",
    "nm",
    "1/min",
    "mg/hub",
    "mg/stroke",
    "ppm",
    "%",
    "kw",
    "fsn",
)


def detect_file_type(path: Path) -> str:
    """
    Return 'xlsx', 'csv', 'tsv', or 'xls_binary'.

    PUMA often uses .xls extension for tab-separated text (not OLE2).
    """
    path = Path(path)
    suf = path.suffix.lower()
    if suf == ".csv":
        return "csv"
    if suf == ".xlsx":
        return "xlsx"
    with open(path, "rb") as f:
        head = f.read(8)
    if len(head) >= 4 and head[:4] == _EXCEL_MAGIC:
        return "xls_binary"
    if len(head) >= 2 and head[:2] == _ZIP_MAGIC and suf == ".xls":
        return "xlsx"
    if suf == ".xls":
        return "tsv"
    return "csv"


def _replace_star_star(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    def _clean(x: Any) -> Any:
        if isinstance(x, str) and x.strip() == "**":
            return np.nan
        return x

    for c in out.columns:
        out[c] = out[c].map(_clean)
    return out


def _row_looks_like_units(row: pd.Series, numeric_candidate_cols: List[str]) -> bool:
    hits = 0
    checked = 0
    for c in numeric_candidate_cols[: min(20, len(numeric_candidate_cols))]:
        v = row.get(c)
        if v is None or (isinstance(v, float) and pd.isna(v)):
            continue
        checked += 1
        s = str(v).strip().lower()
        if any(tok in s for tok in _UNIT_TOKENS):
            hits += 1
        elif s in ("-", "nan", ""):
            continue
        elif re.match(r"^-?[\d.]+\s*$", s):
            continue
        else:
            # non-numeric text in a mostly-numeric column region
            if len(s) < 20 and not s.replace(".", "").replace("-", "").isdigit():
                hits += 1
    return checked > 0 and hits >= max(2, checked // 4)


def load_puma_file(file_path: Path) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load PUMA export: detect format, drop units row, clean numeric columns.

    Returns:
        (dataframe with original column names, metadata dict)
    """
    path = Path(file_path)
    ftype = detect_file_type(path)
    meta: Dict[str, Any] = {"file_type": ftype, "path": str(path.resolve())}

    if ftype == "xlsx":
        df = pd.read_excel(path, engine="openpyxl", header=0)
    elif ftype == "xls_binary":
        try:
            df = pd.read_excel(path, engine="xlrd")
        except Exception:
            df = pd.read_csv(path, sep="\t", encoding="latin-1", header=0, low_memory=False)
            ftype = "tsv"
            meta["file_type"] = "tsv_fallback"
    elif ftype == "tsv":
        df = pd.read_csv(path, sep="\t", encoding="latin-1", header=0, low_memory=False)
    else:
        df = pd.read_csv(path, low_memory=False)

    df.columns = [str(c).strip() for c in df.columns]
    df = _replace_star_star(df)

    # Candidate numeric columns (skip obvious meta columns)
    skip_prefix = ("prname", "datum", "zeit", "version")
    num_candidates: List[str] = []
    for c in df.columns:
        cl = c.lower()
        if any(cl.startswith(p) for p in skip_prefix) or c.upper() == "AVL_INDEP_TIME":
            continue
        num_candidates.append(c)

    if len(df) > 1:
        row1 = df.iloc[0]
        if _row_looks_like_units(row1, num_candidates):
            df = df.iloc[1:].reset_index(drop=True)
            logger.debug("Dropped units row (row 1)")

    for c in df.columns:
        if c in ("PRNAME", "DATUM", "ZEIT", "VERSIONT"):
            continue
        try:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        except Exception:
            pass

    # Metadata from first data row if present
    if len(df) > 0:
        r0 = df.iloc[0]
        if "VERSIONT" in df.columns:
            v = r0.get("VERSIONT")
            meta["versiont"] = "" if pd.isna(v) else str(v)
        if "PRNAME" in df.columns:
            v = r0.get("PRNAME")
            meta["prname"] = "" if pd.isna(v) else str(v)
        if "DATUM" in df.columns:
            v = r0.get("DATUM")
            meta["datum"] = "" if pd.isna(v) else str(v)

    meta["num_rows"] = len(df)
    meta["num_cols"] = len(df.columns)
    meta["parameter_column_count"] = len(
        [
            c
            for c in df.columns
            if str(c).strip().upper()
            not in ("PRNAME", "DATUM", "ZEIT", "VERSIONT", "AVL_INDEP_TIME")
        ]
    )
    if len(df) > 0 and "N" in df.columns:
        try:
            n0 = df["N"].iloc[0]
            if pd.notna(n0):
                meta["rpm_sample"] = str(n0).strip()
        except Exception:
            pass
    return df, meta


def preview_parameters_by_zeit(
    df: pd.DataFrame,
    max_runs: int = 20,
    max_parameters: int = 80,
) -> pd.DataFrame:
    """
    Rows = parameter columns, columns = ZEIT (or row index) for each run.

    PUMA exports use ZEIT per row; use those as column headers instead of Run 1, Run 2.
    """
    if df.empty:
        return pd.DataFrame()
    n = min(max_runs, len(df))
    sub = df.iloc[:n].copy()
    skip = {"PRNAME", "DATUM", "ZEIT", "VERSIONT", "AVL_INDEP_TIME"}
    param_cols = [
        c
        for c in df.columns
        if str(c).strip().upper() not in {s.upper() for s in skip}
    ][:max_parameters]

    col_labels: List[str] = []
    seen: Dict[str, int] = {}
    for i in range(n):
        if "ZEIT" in sub.columns:
            z = sub["ZEIT"].iloc[i]
            lab = str(z).strip() if pd.notna(z) and str(z).strip() else f"Row {i + 1}"
        else:
            lab = f"Row {i + 1}"
        if lab in seen:
            seen[lab] += 1
            lab = f"{lab} ({seen[lab]})"
        else:
            seen[lab] = 0
        col_labels.append(lab)

    data: Dict[str, List[Any]] = {lab: [] for lab in col_labels}

    def _fmt_cell(v: Any) -> Any:
        if isinstance(v, float) and pd.isna(v):
            return "—"
        if isinstance(v, float):
            return round(v, 4) if abs(v) < 1e6 else f"{v:.4g}"
        return str(v) if v is not None else "—"

    for p in param_cols:
        for i, lab in enumerate(col_labels):
            data[lab].append(_fmt_cell(sub[p].iloc[i]))

    out = pd.DataFrame(data, index=param_cols)
    out.index.name = "Parameter"
    return out


def preview_parameters_detailed_table(
    df: pd.DataFrame,
    max_runs: int = 12,
    max_parameters: int = 80,
) -> Tuple[List[str], List[Tuple[str, str, str, str, str, List[str]]]]:
    """
    Build rows for a Treeview preview: Parameter, Unit, Min, Max, Avg, then ZEIT columns.

    Returns (column_ids, rows) where each row is
    (param, unit, min_s, max_s, avg_s, list of per-run cell strings).
    """
    if df.empty:
        return [], []

    n = min(max_runs, len(df))
    sub = df.iloc[:n].copy()
    skip = {"PRNAME", "DATUM", "ZEIT", "VERSIONT", "AVL_INDEP_TIME"}
    param_cols = [
        c
        for c in df.columns
        if str(c).strip().upper() not in {s.upper() for s in skip}
    ][:max_parameters]

    col_labels: List[str] = []
    seen: Dict[str, int] = {}
    for i in range(n):
        if "ZEIT" in sub.columns:
            z = sub["ZEIT"].iloc[i]
            lab = str(z).strip() if pd.notna(z) and str(z).strip() else f"Row {i + 1}"
        else:
            lab = f"Row {i + 1}"
        if lab in seen:
            seen[lab] += 1
            lab = f"{lab} ({seen[lab]})"
        else:
            seen[lab] = 0
        col_labels.append(f"ZEIT {lab}")

    def _fmt_cell(v: Any) -> str:
        if isinstance(v, float) and pd.isna(v):
            return "—"
        if isinstance(v, float):
            return f"{v:.4g}" if abs(v) >= 1e6 or (abs(v) > 0 and abs(v) < 1e-4) else f"{v:.2f}".rstrip("0").rstrip(".")
        return str(v) if v is not None else "—"

    rows_out: List[Tuple[str, str, str, str, str, List[str]]] = []
    for raw_col in param_cols:
        canon = canonical_column_name(str(raw_col))
        _desc, _cat, _ptype, unit = parameter_defaults(canon)
        series = pd.to_numeric(sub[raw_col], errors="coerce")
        valid = series.dropna()
        if len(valid) == 0:
            mn_s = mx_s = av_s = "—"
        else:
            mn = float(valid.min())
            mx = float(valid.max())
            av = float(valid.mean())
            mn_s = _fmt_cell(mn)
            mx_s = _fmt_cell(mx)
            av_s = _fmt_cell(av)
        cells = [_fmt_cell(sub[raw_col].iloc[i]) for i in range(n)]
        rows_out.append((canon, unit or "—", mn_s, mx_s, av_s, cells))

    cols = ["Parameter", "Unit", "Min", "Max", "Avg"] + col_labels
    return cols, rows_out


def build_canonical_numeric_df(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Collapse duplicate columns to canonical names (prefer .1 suffix for measured).

    Returns:
        (canonical_df, col_map: canonical -> first source column name)
    """
    groups: Dict[str, List[str]] = {}
    for c in df.columns:
        canon = canonical_column_name(c)
        groups.setdefault(canon, []).append(c)

    out_cols: Dict[str, pd.Series] = {}
    col_map: Dict[str, str] = {}

    for canon, sources in groups.items():
        chosen = None
        for s in sources:
            if ".1" in s or s.endswith(".1"):
                chosen = s
                break
        if chosen is None:
            chosen = sources[0]
        out_cols[canon] = df[chosen]
        col_map[canon] = chosen

    return pd.DataFrame(out_cols), col_map


def load_dataframe(path: Path) -> pd.DataFrame:
    """Backward-compatible: return cleaned PUMA dataframe only."""
    df, _ = load_puma_file(path)
    return df


def _strip_suffix(name: str) -> Tuple[str, Optional[str]]:
    lower = name.lower()
    for suf, tag in (
        ("_min", "min"),
        ("_max", "max"),
        ("_avg", "avg"),
    ):
        if lower.endswith(suf):
            return name[: -len(suf)].strip(), tag
    return name, None


def detect_column_mapping(df: pd.DataFrame) -> Dict[str, Any]:
    """Map columns to parameters; supports min/max/avg suffixes and Timestamp."""
    cols = list(df.columns)
    standards = set(all_standard_parameter_names())

    timestamp_col: Optional[str] = None
    for c in cols:
        n = str(c).lower().replace(" ", "_")
        for hint in _TIMESTAMP_HINTS:
            if hint in n:
                timestamp_col = str(c)
                break
        if timestamp_col:
            break
    if timestamp_col is None and "AVL_INDEP_TIME" in df.columns:
        timestamp_col = "AVL_INDEP_TIME"

    mappings: List[Dict[str, Any]] = []
    used: set[str] = set()
    for c in cols:
        if str(c) == timestamp_col:
            continue
        raw = str(c)
        base, role = _strip_suffix(raw)
        canon = canonical_column_name(base)
        if canon in standards or base in standards:
            param = canon if canon in standards else base
            mappings.append(
                {"excel_col": raw, "parameter": param, "value_role": role or "instant"}
            )
            used.add(raw)

    unmapped = [str(c) for c in cols if str(c) not in used and str(c) != timestamp_col]
    return {
        "timestamp_col": timestamp_col,
        "mappings": mappings,
        "unmapped_columns": unmapped,
    }


def apply_mapping(
    df: pd.DataFrame,
    timestamp_col: Optional[str],
    mappings: List[Dict[str, Any]],
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Build narrow table from legacy mapping (unused in v3 pipeline)."""
    canon_df, _ = build_canonical_numeric_df(df)
    out_cols: Dict[str, List[Any]] = {}
    if timestamp_col and timestamp_col in df.columns:
        out_cols["timestamp"] = df[timestamp_col].astype(str).tolist()

    param_roles: Dict[str, Any] = {}
    for m in mappings:
        col = m["excel_col"]
        param = m["parameter"]
        role = m.get("value_role") or "instant"
        src = col if col in df.columns else None
        if src is None and param in canon_df.columns:
            series = canon_df[param]
        elif src and src in df.columns:
            series = df[src]
        else:
            continue
        key = f"{param}__{role}"
        out_cols[key] = pd.to_numeric(series, errors="coerce").tolist()
        param_roles.setdefault(param, set()).add(role)

    result = pd.DataFrame(out_cols)
    summary = {
        "rows": len(result),
        "parameters": sorted(param_roles.keys()),
        "roles_per_param": {k: sorted(v) for k, v in param_roles.items()},
    }
    return result, summary


def preview_dataframe(df: pd.DataFrame, max_rows: int = 12) -> pd.DataFrame:
    return df.head(max_rows).copy()
