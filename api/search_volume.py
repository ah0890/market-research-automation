"""DataForSEO Google Ads Search Volume (Standard/task-queue) integration."""

from __future__ import annotations

import logging
from typing import Any

from api.dataforseo_client import DataForSeoClient
from models.search_volume import MonthlySearchVolume, SearchVolumeResult
from settings import SEARCH_VOLUME_TASK_GET_PATH, SEARCH_VOLUME_TASK_POST_PATH

logger = logging.getLogger(__name__)


def fetch_search_volume(
    client: DataForSeoClient,
    keywords: list[str],
    location_code: int,
    language_code: str,
) -> dict[str, SearchVolumeResult]:
    """Submit and retrieve Search Volume data for a batch of keywords.

    A single task_post call can carry many keywords, so this should be called
    once per run (or per chunk, for very large workbooks) rather than once
    per keyword.

    Args:
        client: Configured DataForSEO API client.
        keywords: Keywords to look up (deduplication is the caller's job).
        location_code: DataForSEO numeric location code (e.g. 2840 = US).
        language_code: DataForSEO language code (e.g. "en").

    Returns:
        A mapping of lowercased keyword -> :class:`SearchVolumeResult`.

    Raises:
        DataForSeoTaskError: If the task fails outright.
        DataForSeoTimeoutError: If results are not ready within the configured wait time.
    """
    payload = [
        {
            "location_code": location_code,
            "language_code": language_code,
            "keywords": keywords,
        }
    ]

    task = client.post_task(SEARCH_VOLUME_TASK_POST_PATH, payload)
    task_id = task["id"]
    logger.info("Submitted Search Volume task %s for %d keyword(s)", task_id, len(keywords))

    completed_task = client.poll_task_until_ready(SEARCH_VOLUME_TASK_GET_PATH, task_id)
    result_items = completed_task.get("result") or []

    results: dict[str, SearchVolumeResult] = {}
    for item in result_items:
        parsed = _parse_search_volume_item(item)
        results[parsed.keyword.lower()] = parsed

    return results


def _parse_search_volume_item(item: dict[str, Any]) -> SearchVolumeResult:
    """Normalize a single raw Search Volume result item."""
    monthly_history = [
        MonthlySearchVolume(
            year=entry.get("year"),
            month=entry.get("month"),
            search_volume=entry.get("search_volume") or 0,
        )
        for entry in (item.get("monthly_searches") or [])
    ]

    return SearchVolumeResult(
        keyword=item.get("keyword", ""),
        search_volume=item.get("search_volume"),
        cpc=item.get("cpc"),
        competition=item.get("competition"),
        competition_index=item.get("competition_index"),
        monthly_search_volume_history=monthly_history,
        raw_response=item,
    )
