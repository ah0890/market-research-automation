"""Builds the four-sheet output workbook."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from openpyxl import Workbook

from excel.formatter import apply_standard_formatting
from settings import (
    ERROR_LOG_COLUMNS,
    SEARCH_VOLUME_DETAIL_COLUMNS,
    SHEET_ERROR_LOG,
    SHEET_SEARCH_VOLUME_DETAIL,
    SHEET_SUMMARY,
    SHEET_TRENDS_DETAIL,
    SUMMARY_COLUMNS,
    TRENDS_DETAIL_COLUMNS,
)

logger = logging.getLogger(__name__)


def write_output_workbook(
    output_path: Path,
    summary_rows: list[dict[str, Any]],
    search_volume_rows: list[dict[str, Any]],
    trends_rows: list[dict[str, Any]],
    error_rows: list[dict[str, Any]],
) -> None:
    """Write the Summary, Detailed Search Volume, Detailed Google Trends, and
    Error Log sheets to a single workbook.

    Args:
        output_path: Destination `.xlsx` path. Parent directories are created
            if missing.
        summary_rows: Row dicts matching :data:`settings.SUMMARY_COLUMNS`.
        search_volume_rows: Row dicts matching
            :data:`settings.SEARCH_VOLUME_DETAIL_COLUMNS`.
        trends_rows: Row dicts matching :data:`settings.TRENDS_DETAIL_COLUMNS`.
        error_rows: Row dicts matching :data:`settings.ERROR_LOG_COLUMNS`.
    """
    workbook = Workbook()
    workbook.remove(workbook.active)

    _write_sheet(workbook, SHEET_SUMMARY, SUMMARY_COLUMNS, summary_rows)
    _write_sheet(workbook, SHEET_SEARCH_VOLUME_DETAIL, SEARCH_VOLUME_DETAIL_COLUMNS, search_volume_rows)
    _write_sheet(workbook, SHEET_TRENDS_DETAIL, TRENDS_DETAIL_COLUMNS, trends_rows)
    _write_sheet(workbook, SHEET_ERROR_LOG, ERROR_LOG_COLUMNS, error_rows)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(output_path)
    logger.info("Wrote output workbook to %s", output_path)


def _write_sheet(
    workbook: Workbook,
    sheet_name: str,
    columns: list[str],
    rows: list[dict[str, Any]],
) -> None:
    sheet = workbook.create_sheet(title=sheet_name)
    sheet.append(columns)

    for row in rows:
        sheet.append([row.get(column, "") for column in columns])

    apply_standard_formatting(sheet)
