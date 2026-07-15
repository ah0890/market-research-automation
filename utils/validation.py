"""Input row validation."""

from __future__ import annotations

from typing import Any


def validate_row(row_number: int, values: dict[str, Any]) -> list[str]:
    """Validate a raw input row and return a list of human-readable errors.

    Args:
        row_number: 1-based Excel row number, used only for error messages.
        values: Mapping of column name to cell value for the row.

    Returns:
        A list of error messages. Empty if the row is valid.
    """
    errors: list[str] = []

    for required_column in ("Category", "Product", "Main Keyword"):
        value = values.get(required_column)
        if value is None or str(value).strip() == "":
            errors.append(f"Row {row_number}: missing required value for '{required_column}'")

    return errors
