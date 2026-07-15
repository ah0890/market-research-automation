# Architecture

## Scope

This application collects market research data only:

- Reads product ideas from an Excel workbook.
- Retrieves Google Search Volume and Google Trends data from DataForSEO.
- Normalizes the results.
- Writes a single, formatted Excel report.

Explicitly out of scope: AI, scoring/recommendations, dashboards, a web app or GUI, a database, authentication, SEO/SERP analysis, keyword generation, and any Pinterest/Etsy/TikTok/Reddit integration.

## Data flow

```text
Excel input (data/input/*.xlsx)
        |
        v
excel_reader.read_input_workbook()   -- validates required columns per row
        |
        v
services.market_research.MarketResearchService.run()
        |-- fetch_search_volume()   (one task_post covering all keywords)
        |-- fetch_google_trends()   (one task_post per chunk of <=5 keywords)
        |
        v
services.processor.process_row()     -- combines a row with its API results
        |
        v
excel_writer.write_output_workbook() -- Summary / Search Volume / Trends / Error Log
        |
        v
Excel output (data/output/market_research_<timestamp>.xlsx)
```

Every row is processed independently after the batch API calls return: a row missing search volume or trend data is marked `Partial`, a row missing both is marked `Failed`, and a row that failed input validation never reaches the API at all. No single row or keyword failure stops the run.

## Key design decisions

**DataForSEO Standard (task-queue) mode.** Chosen over Live because it pairs naturally with the retry/error-handling requirements: `task_post` submits work, `task_get` is polled until the task completes or a configurable `TASK_MAX_WAIT_SECONDS` is exceeded. See [DATAFORSEO.md](DATAFORSEO.md) for the exact endpoints and payload shapes.

**Main Keyword only.** Only the `Main Keyword` column is sent to the API; `Keyword Variant 1-3` are read and preserved on `ProductRow` for traceability but are not researched in this version. Extending to variants later only requires building a keyword list from more columns before calling `fetch_search_volume`/`fetch_google_trends` — the batching and error-handling design already supports many keywords per row.

**Batching.** Search Volume accepts many keywords in a single task, so all rows' keywords are submitted in one `task_post` call. Google Trends "explore" tasks are limited to `GOOGLE_TRENDS_MAX_KEYWORDS_PER_TASK` (5) keywords each, so keywords are chunked; each chunk is a separate task and a failure in one chunk does not affect the others (see `api/google_trends.py::fetch_google_trends`).

**Trend Direction.** Google Trends returns a monthly interest series, not a direction label. `utils/trend_utils.py` computes it by comparing the average interest of the most recent `TREND_COMPARISON_WINDOW_MONTHS` (6) months against the preceding 6 months: >=10% higher is `Rising`, <=10% lower is `Declining`, otherwise `Stable`. Fewer than 12 months of data yields `Unknown`.

**Location/language targeting.** Global defaults from `.env` (`DEFAULT_LOCATION_CODE` / `DEFAULT_LANGUAGE_CODE`), not configurable per row, per the input schema.

**Models as plain dataclasses.** `models/` contains no logic, only typed containers (`ProductRow`, `SearchVolumeResult`, `TrendResult`, `ResearchResult`), keeping parsing/business logic in `api/` and `services/` testable in isolation.

**Tests use stdlib `unittest`**, not pytest, to avoid adding a dependency beyond the approved list (`requests`, `openpyxl`, `pandas`, `python-dotenv`).

## Error handling

Every stage catches its own errors and records them without stopping the run:

| Stage | Failure handling |
|---|---|
| Input validation | Row missing Category/Product/Main Keyword is excluded from API calls; recorded as a `Failed` row with a `validation` Error Log entry. |
| Search Volume request | Transient HTTP errors (429/5xx/timeouts) retry with exponential backoff (`RETRY_COUNT`/`RETRY_BACKOFF_SECONDS`). A hard failure (e.g. bad auth, malformed request) marks every keyword in that batch with the real error message. |
| Google Trends request | Same retry behavior per chunk. A chunk failure only affects the up-to-5 keywords in that chunk; other chunks still succeed. |
| Task polling | If a task never reaches a terminal status within `TASK_MAX_WAIT_SECONDS`, it is treated as a timeout error for the affected keyword(s). |
| Unexpected/malformed API responses | Caught broadly (not just known exception types) so a single malformed response cannot crash the run; logged with a full traceback and surfaced as a row-level error. |

## Phased plan

**Phase 1 (current).** Proof of concept: one product row (`PHASE_1_MAX_ROWS = 1` in `main.py`), Main Keyword only, full pipeline exercised end-to-end including the task-queue polling and 4-sheet report.

**Phase 2 (pending approval).** Set `PHASE_1_MAX_ROWS = None` to process unlimited rows. The batching design in `api/search_volume.py` and `api/google_trends.py` already scales to many rows; Phase 2 work is primarily: verifying DataForSEO's real "pending" status codes against a live account (see [DATAFORSEO.md](DATAFORSEO.md#open-verification-items)), chunking Search Volume beyond 1000 keywords if needed, and any logging/error-handling refinements that surface once real multi-row runs are observed.
