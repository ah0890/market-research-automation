"""Static application constants that do not change between environments.

Anything that *can* vary between machines or deployments (credentials, paths,
timeouts) belongs in :mod:`config` instead, where it is loaded from `.env`.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# DataForSEO endpoints (Standard / task-queue mode: task_post + task_get)
# ---------------------------------------------------------------------------
SEARCH_VOLUME_TASK_POST_PATH = "/v3/keywords_data/google_ads/search_volume/task_post"
SEARCH_VOLUME_TASK_GET_PATH = "/v3/keywords_data/google_ads/search_volume/task_get"

GOOGLE_TRENDS_TASK_POST_PATH = "/v3/keywords_data/google_trends/explore/task_post"
GOOGLE_TRENDS_TASK_GET_PATH = "/v3/keywords_data/google_trends/explore/task_get"

# Google Trends "explore" tasks accept multiple keywords per task and return a
# combined time series. Batching keeps the number of API calls down.
GOOGLE_TRENDS_MAX_KEYWORDS_PER_TASK = 5

# Google Trends "time_range" requesting five years of monthly interest data.
GOOGLE_TRENDS_TIME_RANGE = "past_5_years"

# DataForSEO task_get responses that mean "still processing, keep polling".
# Anything else with a non-20000 status code is treated as a hard failure.
TASK_PENDING_STATUS_CODES = {40601, 40602}
TASK_SUCCESS_STATUS_CODE = 20000

# ---------------------------------------------------------------------------
# Trend direction classification thresholds
# ---------------------------------------------------------------------------
# Compares the average interest of the most recent N months against the
# preceding N months. A relative change beyond the threshold is Rising/
# Declining; anything within the band is considered Stable.
TREND_COMPARISON_WINDOW_MONTHS = 6
TREND_RISING_THRESHOLD = 0.10
TREND_DECLINING_THRESHOLD = -0.10

TREND_DIRECTION_RISING = "Rising"
TREND_DIRECTION_DECLINING = "Declining"
TREND_DIRECTION_STABLE = "Stable"
TREND_DIRECTION_UNKNOWN = "Unknown"

# ---------------------------------------------------------------------------
# Row processing status labels (Summary sheet + internal tracking)
# ---------------------------------------------------------------------------
STATUS_SUCCESS = "Success"
STATUS_PARTIAL = "Partial"
STATUS_FAILED = "Failed"

# ---------------------------------------------------------------------------
# Output workbook sheet names
# ---------------------------------------------------------------------------
SHEET_SUMMARY = "Summary"
SHEET_SEARCH_VOLUME_DETAIL = "Detailed Search Volume"
SHEET_TRENDS_DETAIL = "Detailed Google Trends"
SHEET_ERROR_LOG = "Error Log"

SUMMARY_COLUMNS = [
    "Category",
    "Product",
    "Main Keyword",
    "Monthly Search Volume",
    "Average Trend",
    "Trend Direction",
    "CPC",
    "Competition",
    "Status",
]

SEARCH_VOLUME_DETAIL_COLUMNS = [
    "Category",
    "Product",
    "Keyword",
    "Search Volume",
    "CPC",
    "Competition",
    "Competition Index",
    "Month",
    "Year",
    "Monthly Search Volume",
]

TRENDS_DETAIL_COLUMNS = [
    "Category",
    "Product",
    "Keyword",
    "Date",
    "Interest Value",
]

ERROR_LOG_COLUMNS = [
    "Category",
    "Product",
    "Main Keyword",
    "Stage",
    "Error Message",
]

# Required input columns for a row to be considered valid.
REQUIRED_INPUT_COLUMNS = ["Category", "Product", "Main Keyword"]
INPUT_COLUMNS = [
    "Category",
    "Product",
    "Main Keyword",
    "Keyword Variant 1",
    "Keyword Variant 2",
    "Keyword Variant 3",
]
