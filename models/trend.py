"""Google Trends result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TrendPoint:
    """One monthly interest data point in a Google Trends time series."""

    date: str
    interest_value: int


@dataclass(frozen=True)
class TrendResult:
    """Normalized Google Trends data for a single keyword."""

    keyword: str
    monthly_values: list[TrendPoint] = field(default_factory=list)
    average_trend: float | None = None
    trend_direction: str = "Unknown"
    raw_response: dict[str, Any] | None = None
