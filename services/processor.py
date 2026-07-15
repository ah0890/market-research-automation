"""Per-row result building and report-row projection.

This module has no network or file I/O of its own: it turns already-fetched
API results into :class:`ResearchResult` objects, and turns those results
into the flat row dicts the Excel writer expects.
"""

from __future__ import annotations

from typing import Any

from models.product import ProductRow
from models.result import ResearchResult
from models.search_volume import SearchVolumeResult
from models.trend import TrendResult
from settings import STATUS_FAILED, STATUS_PARTIAL, STATUS_SUCCESS


def build_validation_failure_result(row: ProductRow) -> ResearchResult:
    """Build a Failed result for a row that never reached the API stage."""
    errors = [("validation", message) for message in row.validation_errors]
    return ResearchResult(product=row, status=STATUS_FAILED, errors=errors)


def process_row(
    row: ProductRow,
    search_volume_map: dict[str, SearchVolumeResult],
    trend_map: dict[str, TrendResult],
    search_volume_error: str | None = None,
    trend_errors: dict[str, str] | None = None,
) -> ResearchResult:
    """Combine a valid row with its looked-up API results.

    Args:
        row: A previously-validated product row.
        search_volume_map: Lowercased keyword -> SearchVolumeResult, as
            returned by :func:`api.search_volume.fetch_search_volume`.
        trend_map: Lowercased keyword -> TrendResult, as returned by
            :func:`api.google_trends.fetch_google_trends`.
        search_volume_error: If the whole Search Volume batch failed, the
            error message to report for every affected row.
        trend_errors: Lowercased keyword -> error message, for keywords whose
            Google Trends chunk failed.

    Returns:
        A :class:`ResearchResult` with a status reflecting how much data was
        successfully retrieved for this row's keyword.
    """
    trend_errors = trend_errors or {}
    keyword_key = row.main_keyword.lower()
    search_volume = search_volume_map.get(keyword_key)
    trend = trend_map.get(keyword_key)

    errors: list[tuple[str, str]] = []
    if search_volume is None:
        message = search_volume_error or f"No search volume data returned for '{row.main_keyword}'"
        errors.append(("search_volume", message))
    if trend is None:
        message = trend_errors.get(keyword_key) or f"No trend data returned for '{row.main_keyword}'"
        errors.append(("google_trends", message))

    if not errors:
        status = STATUS_SUCCESS
    elif search_volume is not None or trend is not None:
        status = STATUS_PARTIAL
    else:
        status = STATUS_FAILED

    return ResearchResult(
        product=row,
        status=status,
        search_volume=search_volume,
        trend=trend,
        errors=errors,
    )


def build_summary_row(result: ResearchResult) -> dict[str, Any]:
    product = result.product
    search_volume = result.search_volume
    trend = result.trend

    average_trend = None
    if trend and trend.average_trend is not None:
        average_trend = round(trend.average_trend, 2)

    return {
        "Category": product.category,
        "Product": product.product,
        "Main Keyword": product.main_keyword,
        "Monthly Search Volume": search_volume.search_volume if search_volume else "",
        "Average Trend": average_trend if average_trend is not None else "",
        "Trend Direction": trend.trend_direction if trend else "",
        "CPC": search_volume.cpc if search_volume else "",
        "Competition": search_volume.competition if search_volume else "",
        "Status": result.status,
    }


def build_search_volume_detail_rows(result: ResearchResult) -> list[dict[str, Any]]:
    product = result.product
    search_volume = result.search_volume
    if search_volume is None:
        return []

    base = {
        "Category": product.category,
        "Product": product.product,
        "Keyword": search_volume.keyword,
        "Search Volume": search_volume.search_volume,
        "CPC": search_volume.cpc,
        "Competition": search_volume.competition,
        "Competition Index": search_volume.competition_index,
    }

    if not search_volume.monthly_search_volume_history:
        return [{**base, "Month": "", "Year": "", "Monthly Search Volume": ""}]

    return [
        {
            **base,
            "Month": entry.month,
            "Year": entry.year,
            "Monthly Search Volume": entry.search_volume,
        }
        for entry in search_volume.monthly_search_volume_history
    ]


def build_trends_detail_rows(result: ResearchResult) -> list[dict[str, Any]]:
    product = result.product
    trend = result.trend
    if trend is None:
        return []

    return [
        {
            "Category": product.category,
            "Product": product.product,
            "Keyword": trend.keyword,
            "Date": point.date,
            "Interest Value": point.interest_value,
        }
        for point in trend.monthly_values
    ]


def build_error_rows(result: ResearchResult) -> list[dict[str, Any]]:
    product = result.product
    return [
        {
            "Category": product.category,
            "Product": product.product,
            "Main Keyword": product.main_keyword,
            "Stage": stage,
            "Error Message": message,
        }
        for stage, message in result.errors
    ]
