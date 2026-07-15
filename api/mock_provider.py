"""Local, no-network stand-in for the DataForSEO API.

Enabled via ``USE_MOCK_API=true`` in `.env`. Generates deterministic but
keyword-varying fake data so the rest of the pipeline (validation, batching,
normalization, Excel report generation) can be exercised end-to-end without
spending DataForSEO credits or requiring live API access.

This is a testing aid only -- DataForSEO remains the application's one real
data source. Nothing here is returned unless the mock flag is explicitly set.
"""

from __future__ import annotations

import logging
import random
from datetime import date

from models.search_volume import MonthlySearchVolume, SearchVolumeResult
from models.trend import TrendPoint, TrendResult
from utils.trend_utils import calculate_average_trend, calculate_trend_direction

logger = logging.getLogger(__name__)

_SEARCH_VOLUME_HISTORY_MONTHS = 12
_TRENDS_HISTORY_MONTHS = 60  # 5 years


def fetch_search_volume_mock(
    keywords: list[str],
    location_code: int,
    language_code: str,
) -> dict[str, SearchVolumeResult]:
    """Generate fake Search Volume results for each keyword.

    Signature mirrors :func:`api.search_volume.fetch_search_volume` (minus the
    client argument) so callers can branch on ``use_mock_api`` without
    changing how the result is consumed.
    """
    logger.warning("MOCK MODE: generating fabricated Search Volume data for %d keyword(s)", len(keywords))
    return {keyword.lower(): _generate_search_volume(keyword) for keyword in keywords}


def fetch_google_trends_mock(
    keywords: list[str],
    location_code: int,
    language_code: str,
) -> tuple[dict[str, TrendResult], dict[str, str]]:
    """Generate fake Google Trends results for each keyword.

    Signature mirrors :func:`api.google_trends.fetch_google_trends` (minus the
    client argument), including the (results, errors) return shape.
    """
    logger.warning("MOCK MODE: generating fabricated Google Trends data for %d keyword(s)", len(keywords))
    results = {keyword.lower(): _generate_trend(keyword) for keyword in keywords}
    return results, {}


def _generate_search_volume(keyword: str) -> SearchVolumeResult:
    rng = random.Random(f"search_volume:{keyword.lower()}")

    base_volume = rng.randint(500, 30_000)
    history: list[MonthlySearchVolume] = []
    volume = base_volume
    for year, month in _last_n_months(_SEARCH_VOLUME_HISTORY_MONTHS):
        volume = max(0, round(volume * rng.uniform(0.85, 1.15)))
        history.append(MonthlySearchVolume(year=year, month=month, search_volume=volume))

    competition_index = rng.randint(0, 100)
    if competition_index < 33:
        competition = "LOW"
    elif competition_index < 66:
        competition = "MEDIUM"
    else:
        competition = "HIGH"

    return SearchVolumeResult(
        keyword=keyword,
        search_volume=base_volume,
        cpc=round(rng.uniform(0.15, 3.50), 2),
        competition=competition,
        competition_index=competition_index,
        monthly_search_volume_history=history,
        raw_response={"mock": True},
    )


def _generate_trend(keyword: str) -> TrendResult:
    rng = random.Random(f"trend:{keyword.lower()}")

    value = rng.randint(30, 70)
    points: list[TrendPoint] = []
    for year, month in _last_n_months(_TRENDS_HISTORY_MONTHS):
        value = max(0, min(100, value + rng.randint(-8, 8)))
        points.append(TrendPoint(date=f"{year:04d}-{month:02d}-01", interest_value=value))

    return TrendResult(
        keyword=keyword,
        monthly_values=points,
        average_trend=calculate_average_trend(points),
        trend_direction=calculate_trend_direction(points),
        raw_response={"mock": True},
    )


def _last_n_months(n: int) -> list[tuple[int, int]]:
    """Return the last ``n`` (year, month) pairs up to and including the current month, oldest first."""
    months: list[tuple[int, int]] = []
    year, month = date.today().year, date.today().month
    for _ in range(n):
        months.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(months))
