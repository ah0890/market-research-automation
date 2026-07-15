import unittest

from models.product import ProductRow
from models.search_volume import SearchVolumeResult
from models.trend import TrendPoint, TrendResult
from services.processor import (
    build_error_rows,
    build_summary_row,
    build_validation_failure_result,
    process_row,
)
from settings import STATUS_FAILED, STATUS_PARTIAL, STATUS_SUCCESS


def _row(main_keyword: str = "ceramic mug") -> ProductRow:
    return ProductRow(row_number=2, category="Kitchen", product="Mug", main_keyword=main_keyword)


class ProcessRowTests(unittest.TestCase):
    def test_success_when_both_datasets_present(self) -> None:
        row = _row()
        search_volume_map = {"ceramic mug": SearchVolumeResult(keyword="ceramic mug", search_volume=1000, cpc=1.2, competition="LOW", competition_index=10)}
        trend_map = {"ceramic mug": TrendResult(keyword="ceramic mug", monthly_values=[TrendPoint("2024-01-01", 50)], average_trend=50, trend_direction="Stable")}

        result = process_row(row, search_volume_map, trend_map)

        self.assertEqual(result.status, STATUS_SUCCESS)
        self.assertEqual(result.errors, [])

    def test_partial_when_only_one_dataset_present(self) -> None:
        row = _row()
        search_volume_map = {"ceramic mug": SearchVolumeResult(keyword="ceramic mug", search_volume=1000, cpc=1.2, competition="LOW", competition_index=10)}
        trend_map: dict = {}

        result = process_row(row, search_volume_map, trend_map)

        self.assertEqual(result.status, STATUS_PARTIAL)
        self.assertEqual(len(result.errors), 1)

    def test_failed_when_neither_dataset_present(self) -> None:
        row = _row()
        result = process_row(row, {}, {})

        self.assertEqual(result.status, STATUS_FAILED)
        self.assertEqual(len(result.errors), 2)

    def test_batch_error_messages_are_surfaced_verbatim(self) -> None:
        row = _row()
        result = process_row(
            row,
            {},
            {},
            search_volume_error="DataForSEO task timed out after 180s",
            trend_errors={"ceramic mug": "HTTP 401: unauthorized"},
        )

        self.assertEqual(result.status, STATUS_FAILED)
        self.assertIn(("search_volume", "DataForSEO task timed out after 180s"), result.errors)
        self.assertIn(("google_trends", "HTTP 401: unauthorized"), result.errors)

    def test_lookup_is_case_insensitive(self) -> None:
        row = _row("Ceramic Mug")
        search_volume_map = {"ceramic mug": SearchVolumeResult(keyword="Ceramic Mug", search_volume=500, cpc=None, competition=None, competition_index=None)}

        result = process_row(row, search_volume_map, {})

        self.assertIsNotNone(result.search_volume)
        self.assertEqual(result.search_volume.search_volume, 500)


class BuildValidationFailureResultTests(unittest.TestCase):
    def test_carries_validation_errors(self) -> None:
        row = ProductRow(row_number=3, category="", product="Mug", main_keyword="mug", validation_errors=["Row 3: missing required value for 'Category'"])
        result = build_validation_failure_result(row)

        self.assertEqual(result.status, STATUS_FAILED)
        self.assertEqual(result.errors, [("validation", "Row 3: missing required value for 'Category'")])


class BuildSummaryRowTests(unittest.TestCase):
    def test_blank_fields_when_no_data(self) -> None:
        row = _row()
        result = build_validation_failure_result(row)
        summary = build_summary_row(result)

        self.assertEqual(summary["Category"], "Kitchen")
        self.assertEqual(summary["Status"], STATUS_FAILED)
        self.assertEqual(summary["Monthly Search Volume"], "")


class BuildErrorRowsTests(unittest.TestCase):
    def test_one_row_per_error(self) -> None:
        row = _row()
        result = process_row(row, {}, {})
        error_rows = build_error_rows(result)

        self.assertEqual(len(error_rows), 2)
        self.assertEqual(error_rows[0]["Main Keyword"], "ceramic mug")


if __name__ == "__main__":
    unittest.main()
