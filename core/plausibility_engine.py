"""Plausibility comparison: measured value vs limits."""

from __future__ import annotations

import logging
import math
from typing import Optional, Tuple

from core.models import Status

logger = logging.getLogger(__name__)


def check_plausibility(
    value: Optional[float],
    lower: Optional[float],
    upper: Optional[float],
    warning_pct: float,
) -> str:
    """
    Classify a single value against limits.

    Args:
        value: Measured value; None or NaN yields NO_DATA.
        lower: Lower limit.
        upper: Upper limit.
        warning_pct: Percentage of the valid range used as warning band
            near each limit (when both limits exist).

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

    # Both bounds: warning band inside the interval
    if lower is not None and upper is not None:
        range_span = upper - lower
        if range_span <= 0:
            logger.debug("Non-positive range for limits %s–%s", lower, upper)
            return Status.OK.value
        warn_band = range_span * (warning_pct / 100.0)
        if value < (lower + warn_band) or value > (upper - warn_band):
            return Status.WARNING.value
        return Status.OK.value

    # One-sided: warn when within warning_pct of the bound (relative to |bound|)
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
    """
    Distance to nearest limit as percentage of the interval (or bound magnitude).

    Returns:
        Non-negative percentage, or None if not computable.
    """
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
    """Return (status string, deviation_pct)."""
    status = check_plausibility(value, lower, upper, warning_pct)
    dev = deviation_percent(value, lower, upper)
    return status, dev


def status_sort_rank(status: str) -> int:
    """Sort order: FAIL, WARNING, OK, NO_DATA."""
    order = {
        Status.FAIL.value: 0,
        Status.WARNING.value: 1,
        Status.OK.value: 2,
        Status.NO_DATA.value: 3,
    }
    return order.get(status, 99)
