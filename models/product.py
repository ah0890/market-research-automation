"""Input row model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProductRow:
    """A single product idea read from the input workbook.

    Only ``main_keyword`` is sent to the DataForSEO APIs for research; the
    variant fields are retained for traceability and potential future use but
    are out of scope for API lookups in this version.
    """

    row_number: int
    category: str
    product: str
    main_keyword: str
    variant_1: str = ""
    variant_2: str = ""
    variant_3: str = ""
    validation_errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.validation_errors
