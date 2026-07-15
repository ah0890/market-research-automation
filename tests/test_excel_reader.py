import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from excel.excel_reader import read_input_workbook
from settings import INPUT_COLUMNS


class ReadInputWorkbookTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_dir.cleanup)
        self.workbook_path = Path(self._tmp_dir.name) / "input.xlsx"

    def _write_workbook(self, rows: list[list[str]]) -> None:
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(INPUT_COLUMNS)
        for row in rows:
            sheet.append(row)
        workbook.save(self.workbook_path)

    def test_reads_valid_rows(self) -> None:
        self._write_workbook(
            [
                ["Kitchen", "Ceramic Mug", "ceramic mug", "coffee mug", "", ""],
            ]
        )
        rows = read_input_workbook(self.workbook_path)
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0].is_valid)
        self.assertEqual(rows[0].main_keyword, "ceramic mug")

    def test_flags_row_missing_required_field(self) -> None:
        self._write_workbook(
            [
                ["Kitchen", "", "ceramic mug", "", "", ""],
            ]
        )
        rows = read_input_workbook(self.workbook_path)
        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0].is_valid)
        self.assertTrue(any("Product" in e for e in rows[0].validation_errors))

    def test_skips_blank_rows(self) -> None:
        self._write_workbook(
            [
                ["Kitchen", "Ceramic Mug", "ceramic mug", "", "", ""],
                [None, None, None, None, None, None],
            ]
        )
        rows = read_input_workbook(self.workbook_path)
        self.assertEqual(len(rows), 1)

    def test_missing_file_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            read_input_workbook(Path(self._tmp_dir.name) / "missing.xlsx")

    def test_missing_required_column_raises(self) -> None:
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(["Category", "Product"])
        sheet.append(["Kitchen", "Ceramic Mug"])
        workbook.save(self.workbook_path)

        with self.assertRaises(ValueError):
            read_input_workbook(self.workbook_path)


if __name__ == "__main__":
    unittest.main()
