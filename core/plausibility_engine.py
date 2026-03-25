"""Plausibility: value vs limits (v3 HIGH/LOW/OK/NO_DATA + legacy WARNING mode)."""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from core.models import Status
from core.puma_constants import COLUMN_ALIAS_MAP

logger = logging.getLogger(__name__)


def check_plausibility(
    value: Optional[float],
    lower: Optional[float],
    upper: Optional[float],
    warning_pct: float,
) -> str:
    """
    Legacy single-value check with WARNING band.

    Returns:
        'OK', 'WARNING', 'FAIL', or 'NO_DATA'.
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return Status.NO_DATA.value

    if lower is None and upper is None:
        return Status.OK.value

    if lower is not None and value < lower:
        return Status.FAIL.value
    if upper is not None and value > upper:
        return Status.FAIL.value

    if lower is not None and upper is not None:
        range_span = upper - lower
        if range_span <= 0:
            logger.debug("Non-positive range for limits %s–%s", lower, upper)
            return Status.OK.value
        warn_band = range_span * (warning_pct / 100.0)
        if value < (lower + warn_band) or value > (upper - warn_band):
            return Status.WARNING.value
        return Status.OK.value

    ref = max(abs(lower if lower is not None else upper or 0.0), 1e-9)
    band = ref * (warning_pct / 100.0)
    if lower is not None and upper is None:
        if value < lower + band:
            return Status.WARNING.value
        return Status.OK.value
    if upper is not None and lower is None:
        if value > upper - band:
            return Status.WARNING.value
        return Status.OK.value

    return Status.OK.value


def deviation_percent(
    value: Optional[float],
    lower: Optional[float],
    upper: Optional[float],
) -> Optional[float]:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if lower is None and upper is None:
        return None

    if lower is not None and upper is not None:
        if value < lower:
            span = upper - lower
            if span <= 0:
                return 0.0
            return round(((lower - value) / span) * 100.0, 2)
        if value > upper:
            span = upper - lower
            if span <= 0:
                return 0.0
            return round(((value - upper) / span) * 100.0, 2)
        mid = (lower + upper) / 2.0
        half = (upper - lower) / 2.0
        if half <= 0:
            return 0.0
        return round((abs(value - mid) / half) * 100.0, 2)

    if upper is not None:
        ref = max(abs(upper), 1e-9)
        if value > upper:
            return round(((value - upper) / ref) * 100.0, 2)
        return round(((upper - value) / ref) * 100.0, 2)

    if lower is not None:
        ref = max(abs(lower), 1e-9)
        if value < lower:
            return round(((lower - value) / ref) * 100.0, 2)
        return round(((value - lower) / ref) * 100.0, 2)

    return None


def classify_with_limits(
    value: Optional[float],
    lower: Optional[float],
    upper: Optional[float],
    warning_pct: float,
) -> Tuple[str, Optional[float]]:
    status = check_plausibility(value, lower, upper, warning_pct)
    dev = deviation_percent(value, lower, upper)
    return status, dev


def limits_display_str(lower: Optional[float], upper: Optional[float], unit: str) -> str:
    u = (unit or "").strip()
    if lower is None and upper is None:
        return f"— — {u}".strip()
    lo = "" if lower is None else f"{lower:g}"
    hi = "" if upper is None else f"{upper:g}"
    return f"{lo} – {hi} {u}".strip()


def check_parameter(
    values: List[float],
    lower: Optional[float],
    upper: Optional[float],
) -> Dict[str, Any]:
    """
    v3: classify all runs against limits.

    Status:
        NO_DATA — no valid numeric values
        OK — both limits None, or all values in band
        HIGH — any value > upper (precedence over LOW)
        LOW — any value < lower (and not HIGH)
    """
    valid = [float(v) for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]

    if not valid:
        return {
            "min": None,
            "max": None,
            "avg": None,
            "num_runs": 0,
            "status": "NO_DATA",
            "limits_str": "",
        }

    vmin = min(valid)
    vmax = max(valid)
    vavg = sum(valid) / len(valid)
    n = len(valid)

    if lower is None and upper is None:
        return {
            "min": vmin,
            "max": vmax,
            "avg": vavg,
            "num_runs": n,
            "status": "OK",
            "limits_str": "",
        }

    any_high = upper is not None and any(v > upper for v in valid)
    any_low = lower is not None and any(v < lower for v in valid)

    if any_high:
        st = "HIGH"
    elif any_low:
        st = "LOW"
    else:
        st = "OK"

    return {
        "min": vmin,
        "max": vmax,
        "avg": vavg,
        "num_runs": n,
        "status": st,
        "limits_str": "",
    }


def resolve_data_column(param_name: str, canon_df_columns: Any) -> Optional[str]:
    """Find column in canonical frame for limit parameter name."""
    cols = list(canon_df_columns)
    if param_name in cols:
        return param_name
    for raw, canon in COLUMN_ALIAS_MAP.items():
        if canon == param_name and raw in cols:
            return raw
    return None


def status_sort_rank_v3(status: str) -> int:
    """Fail first: HIGH, LOW, NO_DATA, OK."""
    order = {"HIGH": 0, "LOW": 1, "NO_DATA": 2, "OK": 3}
    # legacy
    order.setdefault("FAIL", 0)
    order.setdefault("WARNING", 1)
    return order.get(status, 99)


def status_sort_rank(status: str) -> int:
    """Legacy + v3."""
    if status in ("HIGH", "LOW", "NO_DATA", "OK"):
        return status_sort_rank_v3(status)
    order = {
        Status.FAIL.value: 0,
        Status.WARNING.value: 1,
        Status.OK.value: 2,
        Status.NO_DATA.value: 3,
    }
    return order.get(status, 99)
