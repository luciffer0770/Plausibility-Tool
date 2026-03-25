"""Run plausibility check for an upload and persist results (v3 full-DataFrame)."""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any, List, Optional

import pandas as pd

from core.data_loader import build_canonical_numeric_df, load_puma_file, row_time_labels_for_dataframe
from core.models import LimitDefinition, ParameterType
from core.plausibility_engine import (
    check_parameter,
    limits_display_str,
    resolve_data_column,
    status_sort_rank,
)
from core.puma_constants import parameter_defaults
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

_MAX_VALUES_SAMPLE = 12


def _format_values_sample(vals: List[float]) -> str:
    if not vals:
        return ""
    show = vals[:_MAX_VALUES_SAMPLE]
    parts: List[str] = []
    for v in show:
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            parts.append("—")
        elif isinstance(v, float) and v == int(v):
            parts.append(str(int(v)))
        else:
            parts.append(f"{v:.4g}")
    if len(vals) > _MAX_VALUES_SAMPLE:
        parts.append("…")
    return ", ".join(parts)


def run_plausibility_for_file(
    db: DatabaseManager,
    project_id: int,
    engine_type_value: str,
    file_path: Path,
    timestamp_col: Optional[str],
    mappings: Optional[List[dict[str, Any]]],
    file_name: Optional[str] = None,
    session_note: Optional[str] = None,
) -> int:
    """
    Parse PUMA file, run limits on all data rows per parameter, persist session.

    For each **enabled** limit with a matching column: every numeric row is checked;
    HIGH if any value > upper, LOW if any < lower (HIGH wins if both), OK if in band,
    NO_DATA if column missing or no numbers. Optional ZEIT column aligns row index with
    violation timestamps stored in `measurements.timestamp`.

    `mappings` is ignored in v3 (kept for API compatibility).
    """
    path = Path(file_path)
    df_raw, meta = load_puma_file(path)
    canon_df, _ = build_canonical_numeric_df(df_raw)

    zeit_series = row_time_labels_for_dataframe(df_raw)

    defs = db.get_limit_profile(engine_type_value)
    defs_by_name = {d.parameter_name: d for d in defs}

    results: List[tuple[Any, ...]] = []
    ok_n = high_n = low_n = nd_n = 0

    for d in sorted(defs, key=lambda x: x.parameter_name):
        if not d.is_enabled:
            continue
        col = resolve_data_column(d.parameter_name, canon_df.columns)
        desc = d.description or parameter_defaults(d.parameter_name)[0]
        cat = d.category or parameter_defaults(d.parameter_name)[1]
        ptype = d.parameter_type.value.lower()
        unit = d.unit or parameter_defaults(d.parameter_name)[3]

        if col is None:
            st = "NO_DATA"
            chk = {
                "min": None,
                "max": None,
                "avg": None,
                "num_runs": 0,
                "status": st,
                "limits_str": "",
            }
            vals: List[float] = []
        else:
            series = canon_df[col]
            vals = []
            zeit_labels: List[str] = []
            for i in range(len(series)):
                v = series.iloc[i]
                if pd.notna(v):
                    try:
                        vals.append(float(v))
                        if zeit_series is not None and i < len(zeit_series):
                            z = zeit_series.iloc[i]
                            zeit_labels.append(str(z).strip() if pd.notna(z) else "")
                        else:
                            zeit_labels.append("")
                    except (TypeError, ValueError):
                        pass
            chk = check_parameter(vals, d.lower_limit, d.upper_limit, zeit_labels=zeit_labels or None)
            st = chk["status"]
            chk["limits_str"] = limits_display_str(d.lower_limit, d.upper_limit, unit)

        if st == "OK":
            ok_n += 1
        elif st == "HIGH":
            high_n += 1
        elif st == "LOW":
            low_n += 1
        else:
            nd_n += 1

        vmin = chk.get("min")
        vmax = chk.get("max")
        vavg = chk.get("avg")
        nruns = chk.get("num_runs") or 0
        vsample = _format_values_sample(vals)
        viol_zeit = str(chk.get("violation_zeit") or "").strip() or None

        results.append(
            (
                0,
                d.parameter_name,
                desc,
                cat,
                ptype,
                unit,
                nruns,
                vavg,
                vmin,
                vmax,
                vavg,
                "aggregate",
                viol_zeit,
                st,
                None,
                d.lower_limit,
                d.upper_limit,
                d.root_cause or "",
                d.corrective_action or "",
                vsample,
            )
        )

    fname = file_name or path.name
    sid = db.insert_upload_session(
        project_id,
        fname,
        str(path.resolve()),
        record_count=len(canon_df),
        pass_count=ok_n,
        warn_count=0,
        fail_count=high_n + low_n,
        version_test=meta.get("versiont"),
        application=meta.get("prname"),
        datum=meta.get("datum"),
        above_count=high_n,
        below_count=low_n,
        nodata_count=nd_n,
        session_note=session_note,
    )

    batch = []
    for row in results:
        r = list(row)
        r[0] = sid
        batch.append(tuple(r))

    db.insert_measurements_batch(batch)
    db.update_upload_session_counts(
        sid,
        len(canon_df),
        ok_n,
        0,
        high_n + low_n,
        high_n,
        low_n,
        nd_n,
    )
    logger.info(
        "Session %s: rows=%s OK=%s HIGH=%s LOW=%s ND=%s",
        sid,
        len(canon_df),
        ok_n,
        high_n,
        low_n,
        nd_n,
    )
    return sid


def sort_measurement_results(rows: List[dict[str, Any]]) -> List[dict[str, Any]]:
    """Sort: failures first, then alphabetically."""
    return sorted(
        rows,
        key=lambda m: (
            status_sort_rank(str(m.get("status", ""))),
            str(m.get("parameter_name", "")),
        ),
    )


def measurements_to_summary_counts(rows: List[dict[str, Any]]) -> dict[str, int]:
    """Counts for v3 statuses."""
    out = {
        "OK": 0,
        "HIGH": 0,
        "LOW": 0,
        "NO_DATA": 0,
        "WARNING": 0,
        "FAIL": 0,
    }
    for m in rows:
        s = str(m.get("status", "NO_DATA"))
        if s in out:
            out[s] += 1
        elif s == "FAIL":
            out["FAIL"] += 1
    out["TOTAL"] = len(rows)
    out["PASS"] = out["OK"]
    out["ABOVE"] = out["HIGH"]
    out["BELOW"] = out["LOW"]
    return out
