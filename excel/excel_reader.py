"""Reads and validates the input product-idea workbook."""

from __future__ import annotations

import logging
from pathlib import Path

import openpyxl

from models.product import ProductRow
from settings import REQUIRED_INPUT_COLUMNS
from utils.validation import validate_row

logger = logging.getLogger(__name__)

_COLUMN_TO_FIELD = {
    "Category": "category",
    "Product": "product",
    "Main Keyword": "main_keyword",
    "Keyword Variant 1": "variant_1",
    "Keyword Variant 2": "variant_2",
    "Keyword Variant 3": "variant_3",
}


def read_input_workbook(path: Path) -> list[ProductRow]:
    """Read the input workbook into a list of :class:`ProductRow` objects.

    Blank rows are skipped. Rows missing required fields are still returned
    (with ``validation_errors`` populated) so the caller can log them to the
    Error Log rather than silently dropping data.

    Args:
        path: Path to the input `.xlsx` file.

    Returns:
        All non-blank rows found in the first worksheet.

    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the worksheet is missing required columns.
    """
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = workbook.active
        rows_iter = sheet.iter_rows(values_only=True)

        try:
            header = next(rows_iter)
        except StopIteration:
            raise ValueError("Input workbook is empty") from None

        header_index = {str(name).strip(): idx for idx, name in enumerate(header) if name}
        missing_columns = [c for c in REQUIRED_INPUT_COLUMNS if c not in header_index]
        if missing_columns:
            raise ValueError(f"Input workbook missing required columns: {missing_columns}")

        product_rows: list[ProductRow] = []
        for row_number, raw_row in enumerate(rows_iter, start=2):
            if raw_row is None or all(cell is None for cell in raw_row):
                continue

            values = {
                column: (raw_row[idx] if idx < len(raw_row) else None)
                for column, idx in header_index.items()
            }
            errors = validate_row(row_number, values)

            field_values = {
                field_name: str(values.get(column) or "").strip()
                for column, field_name in _COLUMN_TO_FIELD.items()
            }

            product_rows.append(
                ProductRow(row_number=row_number, validation_errors=errors, **field_values)
            )

        logger.info("Read %d row(s) from %s", len(product_rows), path)
        return product_rows
    finally:
        workbook.close()
