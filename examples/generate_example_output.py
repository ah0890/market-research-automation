"""Generates examples/example_output.xlsx: a static, fabricated example report.

This does NOT call the DataForSEO API - it demonstrates the output workbook
format (Summary / Detailed Search Volume / Detailed Google Trends / Error Log)
using hand-built sample data, including one deliberately failed row so the
Error Log sheet is populated too.

Run with: python examples/generate_example_output.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from excel.excel_writer import write_output_workbook

SUMMARY_ROWS = [
    {
        "Category": "Kitchen",
        "Product": "Ceramic Coffee Mug",
        "Main Keyword": "ceramic coffee mug",
        "Monthly Search Volume": 8100,
        "Average Trend": 62.4,
        "Trend Direction": "Rising",
        "CPC": 0.85,
        "Competition": "MEDIUM",
        "Status": "Success",
    },
    {
        "Category": "Home Decor",
        "Product": "Macrame Wall Hanging",
        "Main Keyword": "macrame wall hanging",
        "Monthly Search Volume": 14800,
        "Average Trend": 58.1,
        "Trend Direction": "Stable",
        "CPC": 0.62,
        "Competition": "LOW",
        "Status": "Success",
    },
    {
        "Category": "Pet Supplies",
        "Product": "No-Pull Dog Harness",
        "Main Keyword": "no pull dog harness",
        "Monthly Search Volume": 22200,
        "Average Trend": 71.9,
        "Trend Direction": "Rising",
        "CPC": 1.35,
        "Competition": "HIGH",
        "Status": "Success",
    },
    {
        "Category": "Fitness",
        "Product": "Resistance Bands Set",
        "Main Keyword": "resistance bands set",
        "Monthly Search Volume": 9900,
        "Average Trend": 40.3,
        "Trend Direction": "Declining",
        "CPC": 0.71,
        "Competition": "MEDIUM",
        "Status": "Success",
    },
    {
        "Category": "Outdoor",
        "Product": "Portable Camping Chair",
        "Main Keyword": "portable camping chair",
        "Monthly Search Volume": "",
        "Average Trend": "",
        "Trend Direction": "",
        "CPC": "",
        "Competition": "",
        "Status": "Failed",
    },
]

SEARCH_VOLUME_ROWS = [
    {
        "Category": "Kitchen",
        "Product": "Ceramic Coffee Mug",
        "Keyword": "ceramic coffee mug",
        "Search Volume": 8100,
        "CPC": 0.85,
        "Competition": "MEDIUM",
        "Competition Index": 45,
        "Month": month,
        "Year": 2025,
        "Monthly Search Volume": volume,
    }
    for month, volume in enumerate(
        [7200, 7400, 7900, 8200, 8600, 9100, 9400, 9000, 8500, 8100, 7800, 8100], start=1
    )
]

TRENDS_ROWS = [
    {
        "Category": "Kitchen",
        "Product": "Ceramic Coffee Mug",
        "Keyword": "ceramic coffee mug",
        "Date": f"2025-{month:02d}-01",
        "Interest Value": value,
    }
    for month, value in enumerate([48, 51, 55, 58, 61, 65, 68, 64, 60, 58, 56, 60], start=1)
]

ERROR_ROWS = [
    {
        "Category": "Outdoor",
        "Product": "Portable Camping Chair",
        "Main Keyword": "portable camping chair",
        "Stage": "search_volume",
        "Error Message": "DataForSEO task timed out after 180s",
    },
    {
        "Category": "Outdoor",
        "Product": "Portable Camping Chair",
        "Main Keyword": "portable camping chair",
        "Stage": "google_trends",
        "Error Message": "DataForSEO task timed out after 180s",
    },
]


def main() -> None:
    output_path = Path(__file__).parent / "example_output.xlsx"
    write_output_workbook(output_path, SUMMARY_ROWS, SEARCH_VOLUME_ROWS, TRENDS_ROWS, ERROR_ROWS)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
