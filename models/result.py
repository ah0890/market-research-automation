"""Aggregate per-row research result model."""

from __future__ import annotations

from dataclasses import dataclass, field

from models.product import ProductRow
from models.search_volume import SearchVolumeResult
from models.trend import TrendResult


@dataclass
class ResearchResult:
    """The combined outcome of researching a single :class:`ProductRow`."""

    product: ProductRow
    status: str
    search_volume: SearchVolumeResult | None = None
    trend: TrendResult | None = None
    errors: list[tuple[str, str]] = field(default_factory=list)
    """List of (stage, error_message) tuples, e.g. ("search_volume", "timeout")."""
