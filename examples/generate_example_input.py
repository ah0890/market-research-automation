"""Generates examples/example_input.xlsx: a sample product-idea workbook.

Run with: python examples/generate_example_input.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openpyxl import Workbook

from settings import INPUT_COLUMNS

EXAMPLE_ROWS = [
    ["Kitchen", "Ceramic Coffee Mug", "ceramic coffee mug", "coffee mug", "handmade mug", "mug gift"],
    ["Home Decor", "Macrame Wall Hanging", "macrame wall hanging", "boho wall decor", "woven wall art", ""],
    ["Pet Supplies", "No-Pull Dog Harness", "no pull dog harness", "dog harness", "puppy harness", "adjustable dog harness"],
    ["Fitness", "Resistance Bands Set", "resistance bands set", "workout bands", "exercise bands", ""],
    ["Outdoor", "Portable Camping Chair", "portable camping chair", "folding camp chair", "lightweight camping chair", ""],
]


def main() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Products"
    sheet.append(INPUT_COLUMNS)
    for row in EXAMPLE_ROWS:
        sheet.append(row)

    output_path = Path(__file__).parent / "example_input.xlsx"
    workbook.save(output_path)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
