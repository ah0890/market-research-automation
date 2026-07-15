"""Typed data containers shared across the application."""

from models.product import ProductRow
from models.result import ResearchResult
from models.search_volume import MonthlySearchVolume, SearchVolumeResult
from models.trend import TrendPoint, TrendResult

__all__ = [
    "ProductRow",
    "ResearchResult",
    "MonthlySearchVolume",
    "SearchVolumeResult",
    "TrendPoint",
    "TrendResult",
]
