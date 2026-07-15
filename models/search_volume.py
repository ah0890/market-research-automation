"""Search Volume result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MonthlySearchVolume:
    """One month of historical search volume for a keyword."""

    year: int
    month: int
    search_volume: int


@dataclass(frozen=True)
class SearchVolumeResult:
    """Normalized Search Volume data for a single keyword."""

    keyword: str
    search_volume: int | None
    cpc: float | None
    competition: str | None
    competition_index: int | None
    monthly_search_volume_history: list[MonthlySearchVolume] = field(default_factory=list)
    raw_response: dict[str, Any] | None = None
