"""Top-level pipeline: read workbook -> call APIs -> normalize -> write report."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from api.dataforseo_client import DataForSeoClient
from api.exceptions import DataForSeoError
from api.google_trends import fetch_google_trends
from api.mock_provider import fetch_google_trends_mock, fetch_search_volume_mock
from api.search_volume import fetch_search_volume
from config import AppConfig
from excel.excel_reader import read_input_workbook
from excel.excel_writer import write_output_workbook
from models.result import ResearchResult
from services.processor import (
    build_error_rows,
    build_search_volume_detail_rows,
    build_summary_row,
    build_trends_detail_rows,
    build_validation_failure_result,
    process_row,
)

logger = logging.getLogger(__name__)


class MarketResearchService:
    """Coordinates reading input, calling DataForSEO, and writing the report."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._client: DataForSeoClient | None = None

        if config.use_mock_api:
            logger.warning(
                "MOCK MODE ACTIVE: DataForSEO will not be called. "
                "All Search Volume and Google Trends data in this report is fabricated for local testing only."
            )
        else:
            self._client = DataForSeoClient(
                base_url=config.dataforseo_base_url,
                login=config.dataforseo_login,
                password=config.dataforseo_password,
                timeout_seconds=config.request_timeout_seconds,
                retry_count=config.retry_count,
                retry_backoff_seconds=config.retry_backoff_seconds,
                poll_interval_seconds=config.task_poll_interval_seconds,
                max_wait_seconds=config.task_max_wait_seconds,
            )

    def run(self, max_rows: int | None = None) -> Path:
        """Execute the full pipeline and return the path to the written report.

        Args:
            max_rows: If set, only the first ``max_rows`` valid rows are sent
                to the API. This is the Phase 1 proof-of-concept scope limiter
                (single product) and should be left as ``None`` for the full
                Phase 2 multi-row run.
        """
        rows = read_input_workbook(self._config.input_file_path)
        valid_rows = [row for row in rows if row.is_valid]
        invalid_rows = [row for row in rows if not row.is_valid]

        if max_rows is not None:
            valid_rows = valid_rows[:max_rows]

        logger.info(
            "Processing %d valid row(s), %d invalid row(s) skipped",
            len(valid_rows),
            len(invalid_rows),
        )

        keywords = [row.main_keyword for row in valid_rows]

        search_volume_map, search_volume_error = self._safe_fetch_search_volume(keywords)
        trend_map, trend_errors = self._safe_fetch_trends(keywords)

        results: list[ResearchResult] = [build_validation_failure_result(row) for row in invalid_rows]
        results.extend(
            process_row(row, search_volume_map, trend_map, search_volume_error, trend_errors)
            for row in valid_rows
        )

        output_path = self._write_report(results)
        return output_path

    def _safe_fetch_search_volume(self, keywords: list[str]) -> tuple[dict, str | None]:
        if not keywords:
            return {}, None

        if self._config.use_mock_api:
            return (
                fetch_search_volume_mock(
                    keywords, self._config.default_location_code, self._config.default_language_code
                ),
                None,
            )

        try:
            return (
                fetch_search_volume(
                    self._client,
                    keywords,
                    self._config.default_location_code,
                    self._config.default_language_code,
                ),
                None,
            )
        except DataForSeoError as exc:
            logger.error("Search Volume request failed for the entire batch: %s", exc)
            return {}, str(exc)
        except Exception as exc:  # unexpected/malformed response; don't abort the run
            logger.exception("Unexpected error fetching Search Volume")
            return {}, f"Unexpected error: {exc}"

    def _safe_fetch_trends(self, keywords: list[str]) -> tuple[dict, dict]:
        if not keywords:
            return {}, {}

        if self._config.use_mock_api:
            return fetch_google_trends_mock(
                keywords, self._config.default_location_code, self._config.default_language_code
            )

        return fetch_google_trends(
            self._client,
            keywords,
            self._config.default_location_code,
            self._config.default_language_code,
        )

    def _write_report(self, results: list[ResearchResult]) -> Path:
        summary_rows = [build_summary_row(result) for result in results]
        search_volume_rows = [row for result in results for row in build_search_volume_detail_rows(result)]
        trends_rows = [row for result in results for row in build_trends_detail_rows(result)]
        error_rows = [row for result in results for row in build_error_rows(result)]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self._config.output_dir / f"market_research_{timestamp}.xlsx"

        write_output_workbook(output_path, summary_rows, search_volume_rows, trends_rows, error_rows)
        return output_path
