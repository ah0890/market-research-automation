"""DataForSEO Google Trends "explore" (Standard/task-queue) integration."""

from __future__ import annotations

import logging
from typing import Any

from api.dataforseo_client import DataForSeoClient
from api.exceptions import DataForSeoError
from models.trend import TrendPoint, TrendResult
from settings import (
    GOOGLE_TRENDS_MAX_KEYWORDS_PER_TASK,
    GOOGLE_TRENDS_TASK_GET_PATH,
    GOOGLE_TRENDS_TASK_POST_PATH,
    GOOGLE_TRENDS_TIME_RANGE,
)
from utils.trend_utils import calculate_average_trend, calculate_trend_direction

logger = logging.getLogger(__name__)

_TRENDS_GRAPH_ITEM_TYPE = "google_trends_graph"


def fetch_google_trends(
    client: DataForSeoClient,
    keywords: list[str],
    location_code: int,
    language_code: str,
) -> tuple[dict[str, TrendResult], dict[str, str]]:
    """Submit and retrieve Google Trends interest-over-time data for keywords.

    DataForSEO's Trends "explore" endpoint accepts at most
    ``GOOGLE_TRENDS_MAX_KEYWORDS_PER_TASK`` keywords per task, so keywords are
    automatically chunked and submitted as separate tasks. Each chunk is
    isolated: if one chunk's task fails, the keywords in other chunks are
    still returned rather than losing the whole run.

    Args:
        client: Configured DataForSEO API client.
        keywords: Keywords to look up (deduplication is the caller's job).
        location_code: DataForSEO numeric location code (e.g. 2840 = US).
        language_code: DataForSEO language code (e.g. "en").

    Returns:
        A tuple of:
            - mapping of lowercased keyword -> :class:`TrendResult` for
              keywords whose chunk succeeded.
            - mapping of lowercased keyword -> error message for keywords
              whose chunk failed.
    """
    results: dict[str, TrendResult] = {}
    errors: dict[str, str] = {}

    for chunk in _chunk(keywords, GOOGLE_TRENDS_MAX_KEYWORDS_PER_TASK):
        payload = [
            {
                "location_code": location_code,
                "language_code": language_code,
                "keywords": chunk,
                "time_range": GOOGLE_TRENDS_TIME_RANGE,
            }
        ]

        try:
            task = client.post_task(GOOGLE_TRENDS_TASK_POST_PATH, payload)
            task_id = task["id"]
            logger.info("Submitted Google Trends task %s for keywords: %s", task_id, chunk)

            completed_task = client.poll_task_until_ready(GOOGLE_TRENDS_TASK_GET_PATH, task_id)
            result_items = completed_task.get("result") or []
            results.update(_parse_trends_result_items(result_items))
        except DataForSeoError as exc:
            logger.error("Google Trends request failed for keywords %s: %s", chunk, exc)
            for keyword in chunk:
                errors[keyword.lower()] = str(exc)
        except Exception as exc:  # unexpected/malformed response; don't abort the run
            logger.exception("Unexpected error processing Google Trends for keywords %s", chunk)
            for keyword in chunk:
                errors[keyword.lower()] = f"Unexpected error: {exc}"

    return results, errors


def _parse_trends_result_items(result_items: list[dict[str, Any]]) -> dict[str, TrendResult]:
    parsed: dict[str, TrendResult] = {}

    for result in result_items:
        keyword_order: list[str] = result.get("keywords") or []
        graph_item = next(
            (item for item in (result.get("items") or []) if item.get("type") == _TRENDS_GRAPH_ITEM_TYPE),
            None,
        )
        if graph_item is None:
            continue

        series_by_keyword: dict[str, list[TrendPoint]] = {kw: [] for kw in keyword_order}
        for data_point in graph_item.get("data") or []:
            date = data_point.get("date_from") or data_point.get("date_to") or ""
            values = data_point.get("values") or []
            for index, keyword in enumerate(keyword_order):
                value = values[index] if index < len(values) and values[index] is not None else 0
                series_by_keyword[keyword].append(TrendPoint(date=date, interest_value=value))

        for keyword, points in series_by_keyword.items():
            parsed[keyword.lower()] = TrendResult(
                keyword=keyword,
                monthly_values=points,
                average_trend=calculate_average_trend(points),
                trend_direction=calculate_trend_direction(points),
                raw_response=result,
            )

    return parsed


def _chunk(items: list[str], size: int) -> list[list[str]]:
    return [items[i : i + size] for i in range(0, len(items), size)]
