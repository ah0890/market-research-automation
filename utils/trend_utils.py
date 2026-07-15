"""Google Trends derived-metric calculations."""

from __future__ import annotations

from models.trend import TrendPoint
from settings import (
    TREND_COMPARISON_WINDOW_MONTHS,
    TREND_DECLINING_THRESHOLD,
    TREND_DIRECTION_DECLINING,
    TREND_DIRECTION_RISING,
    TREND_DIRECTION_STABLE,
    TREND_DIRECTION_UNKNOWN,
    TREND_RISING_THRESHOLD,
)


def calculate_average_trend(monthly_values: list[TrendPoint]) -> float | None:
    """Return the mean interest value across all monthly data points."""
    if not monthly_values:
        return None
    return sum(point.interest_value for point in monthly_values) / len(monthly_values)


def calculate_trend_direction(monthly_values: list[TrendPoint]) -> str:
    """Classify a keyword's trend as Rising, Declining, or Stable.

    Compares the average interest of the most recent
    ``TREND_COMPARISON_WINDOW_MONTHS`` months against the preceding window of
    the same size. Requires at least two full windows of data; otherwise the
    direction cannot be determined.
    """
    window = TREND_COMPARISON_WINDOW_MONTHS
    if len(monthly_values) < window * 2:
        return TREND_DIRECTION_UNKNOWN

    recent_window = monthly_values[-window:]
    previous_window = monthly_values[-window * 2 : -window]

    recent_avg = sum(p.interest_value for p in recent_window) / window
    previous_avg = sum(p.interest_value for p in previous_window) / window

    if previous_avg == 0:
        return TREND_DIRECTION_UNKNOWN if recent_avg == 0 else TREND_DIRECTION_RISING

    relative_change = (recent_avg - previous_avg) / previous_avg

    if relative_change >= TREND_RISING_THRESHOLD:
        return TREND_DIRECTION_RISING
    if relative_change <= TREND_DECLINING_THRESHOLD:
        return TREND_DIRECTION_DECLINING
    return TREND_DIRECTION_STABLE
