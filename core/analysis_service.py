"""Run plausibility check for an upload and persist results."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from core.data_loader import apply_mapping, load_dataframe
from core.models import LimitDefinition, MeasurementResult, ParameterType, Status
from core.plausibility_engine import classify_with_limits, status_sort_rank
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


def _values_for_param(row: pd.Series, param: str) -> tuple[
    Optional[float], Optional[float], Optional[float], Optional[float]
]:
    """Return (instant, min, max, avg) from mapped row keys param__role."""
    instant = vmin = vmax = vavg = None
    for role, target in (
        ("instant", "instant"),
        ("min", "vmin"),
        ("max", "vmax"),
        ("avg", "vavg"),
    ):
        key = f"{param}__{role}"
        if key in row.index and pd.notna(row[key]):
            val = float(row[key])
            if target == "instant":
                instant = val
            elif target == "vmin":
                vmin = val
            elif target == "vmax":
                vmax = val
            else:
                vavg = val
    if instant is None and vavg is not None:
        instant = vavg
    return instant, vmin, vmax, vavg


def run_plausibility_for_file(
    db: DatabaseManager,
    project_id: int,
    engine_type_value: str,
    file_path: Path,
    timestamp_col: Optional[str],
    mappings: list[dict[str, Any]],
    file_name: Optional[str] = None,
) -> int:
    """
    Parse file, evaluate first data row against limits, store session + measurements.

    Returns:
        New upload_sessions.id.
    """
    path = Path(file_path)
    df_raw = load_dataframe(path)
    mapped_df, summary = apply_mapping(df_raw, timestamp_col, mappings)
    if mapped_df.empty:
        raise ValueError("No data rows after mapping")

    defs = db.get_limit_profile(engine_type_value)
    defs_by_name = {d.parameter_name: d for d in defs}
    default_pt = defs[0].parameter_type if defs else ParameterType.OTHER

    row0 = mapped_df.iloc[0]
    ts = None
    if "timestamp" in mapped_df.columns:
        raw_ts = row0["timestamp"]
        ts = str(raw_ts) if pd.notna(raw_ts) else None

    parameters: list[str] = summary.get("parameters") or []
    results: list[MeasurementResult] = []

    for param in parameters:
        d = defs_by_name.get(param)
        if d is None:
            d = LimitDefinition(
                parameter_name=param,
                parameter_type=default_pt,
                description="",
                unit="",
            )
        instant, vmin, vmax, vavg = _values_for_param(row0, param)
        check_val = instant
        if check_val is None and vavg is not None:
            check_val = vavg
        status_s, dev = classify_with_limits(
            check_val,
            d.lower_limit,
            d.upper_limit,
            d.warning_pct,
        )
        try:
            st = Status(status_s)
        except ValueError:
            st = Status.NO_DATA
        results.append(
            MeasurementResult(
                parameter_name=param,
                description=d.description,
                measured_value=check_val,
                value_min=vmin,
                value_max=vmax,
                value_avg=vavg,
                value_type="instant",
                status=st,
                lower_limit=d.lower_limit,
                upper_limit=d.upper_limit,
                deviation_pct=dev,
                root_cause=d.root_cause,
                corrective_action=d.corrective_action,
                timestamp=ts,
            )
        )

    ok_n = sum(1 for r in results if r.status == Status.OK)
    w_n = sum(1 for r in results if r.status == Status.WARNING)
    f_n = sum(1 for r in results if r.status == Status.FAIL)
    nd_n = sum(1 for r in results if r.status == Status.NO_DATA)

    fname = file_name or path.name
    sid = db.insert_upload_session(
        project_id,
        fname,
        str(path.resolve()),
        record_count=len(mapped_df),
        pass_count=ok_n,
        warn_count=w_n,
        fail_count=f_n,
    )

    batch: list[tuple[Any, ...]] = []
    for r in results:
        batch.append(
            (
                sid,
                r.parameter_name,
                r.measured_value,
                r.value_min,
                r.value_max,
                r.value_avg,
                r.value_type,
                r.timestamp,
                r.status.value,
                r.deviation_pct,
                r.lower_limit,
                r.upper_limit,
                r.root_cause,
                r.corrective_action,
            )
        )
    db.insert_measurements_batch(batch)
    db.update_upload_session_counts(sid, len(mapped_df), ok_n, w_n, f_n)
    logger.info(
        "Session %s: %s params OK=%s WARN=%s FAIL=%s ND=%s",
        sid,
        len(results),
        ok_n,
        w_n,
        f_n,
        nd_n,
    )
    return sid


def sort_measurement_results(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort by status priority then parameter name."""
    return sorted(
        rows,
        key=lambda m: (
            status_sort_rank(str(m.get("status", ""))),
            str(m.get("parameter_name", "")),
        ),
    )


def measurements_to_summary_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Count statuses from measurement rows."""
    out = {"OK": 0, "WARNING": 0, "FAIL": 0, "NO_DATA": 0}
    for m in rows:
        s = str(m.get("status", "NO_DATA"))
        if s in out:
            out[s] += 1
    return out
