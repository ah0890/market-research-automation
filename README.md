# Market Research Automation

A local Windows Python application that automates market research for product ideas. It reads product ideas from an Excel workbook, retrieves Google Search Volume and Google Trends data via the DataForSEO API, and produces a structured Excel report.

This tool **only collects market research data**. It does not score products, generate recommendations, or provide a UI/dashboard — see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full scope boundary.

## Current status: Phase 1 (Proof of Concept)

Phase 1 validates the full pipeline end-to-end but is deliberately scoped down:

- Processes **one product row** (`PHASE_1_MAX_ROWS = 1` in [main.py](main.py)).
- Researches the **Main Keyword only** (variant columns are read and stored but not sent to the API).
- Uses DataForSEO's **Standard (task-queue)** API mode: submit a task, poll until it completes.

Phase 2 will remove the row limit and extend logging/error-handling polish for unlimited rows — see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#phased-plan) for what changes.

## Testing without a funded DataForSEO account

Set `USE_MOCK_API=true` in `.env` to run the entire pipeline — input validation, batching, normalization, and the 4-sheet report — without making any network calls. Search Volume and Google Trends data is fabricated locally (deterministic per keyword, so repeated runs are stable) purely so the report format and error handling can be exercised end-to-end. `DATAFORSEO_LOGIN`/`DATAFORSEO_PASSWORD` are not required in this mode. **Never leave this on in production** — DataForSEO remains the application's one real data source; a `MOCK MODE ACTIVE` warning is logged whenever it's enabled so fabricated reports are never mistaken for real ones.

## Requirements

- Python 3.12+ (tested with 3.14)
- A [DataForSEO](https://dataforseo.com/) account (API login + password from [app.dataforseo.com/api-access](https://app.dataforseo.com/api-access))

## Installation

```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure credentials and paths
copy .env.example .env
# then edit .env and fill in DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD

# 4. Provide an input workbook
copy examples\example_input.xlsx data\input\products.xlsx
# or point INPUT_FILE_PATH in .env at your own workbook
```

## Usage

```powershell
python main.py
```

The report is written to `data/output/market_research_<timestamp>.xlsx`. Logs are written to `logs/market_research.log` and echoed to the console.

## Input format

The input workbook's first worksheet must contain these columns (any order, exact header names):

| Column | Required | Notes |
|---|---|---|
| Category | Yes | |
| Product | Yes | |
| Main Keyword | Yes | The only keyword sent to DataForSEO in this version |
| Keyword Variant 1 | No | Read and stored; not researched |
| Keyword Variant 2 | No | Read and stored; not researched |
| Keyword Variant 3 | No | Read and stored; not researched |

Rows missing a required column are skipped from API processing and reported in the Error Log with status `Failed` in the Summary sheet — a single bad row never stops the run.

See [examples/example_input.xlsx](examples/example_input.xlsx).

## Output format

One workbook with four sheets, all with bold headers, a frozen header row, and auto-sized columns:

1. **Summary** — Category, Product, Main Keyword, Monthly Search Volume, Average Trend, Trend Direction, CPC, Competition, Status.
2. **Detailed Search Volume** — one row per keyword per month of history.
3. **Detailed Google Trends** — one row per keyword per monthly interest data point (up to 5 years).
4. **Error Log** — one row per error, tagged with the pipeline stage (`validation`, `search_volume`, `google_trends`).

See [examples/example_output.xlsx](examples/example_output.xlsx) — a **static, hand-built example** (not a live API run) that demonstrates the format, including a deliberately failed row so the Error Log is populated too. Regenerate it with `python examples/generate_example_output.py`.

## Configuration reference (`.env`)

| Variable | Purpose | Default |
|---|---|---|
| `DATAFORSEO_LOGIN` / `DATAFORSEO_PASSWORD` | API credentials (HTTP Basic Auth) | — (required unless `USE_MOCK_API=true`) |
| `DATAFORSEO_BASE_URL` | API base URL | `https://api.dataforseo.com` |
| `USE_MOCK_API` | Skip DataForSEO entirely and fabricate data locally for testing | `false` |
| `INPUT_FILE_PATH` | Input workbook path | `data/input/products.xlsx` |
| `OUTPUT_DIR` | Output directory | `data/output` |
| `REQUEST_TIMEOUT_SECONDS` | Per-HTTP-request timeout | `30` |
| `RETRY_COUNT` | Max attempts for transient HTTP failures | `3` |
| `RETRY_BACKOFF_SECONDS` | Base delay for exponential backoff | `2` |
| `TASK_POLL_INTERVAL_SECONDS` | Delay between task_get polls | `10` |
| `TASK_MAX_WAIT_SECONDS` | Max time to wait for a task before treating it as timed out | `180` |
| `DEFAULT_LOCATION_CODE` | DataForSEO location code (2840 = United States) | `2840` |
| `DEFAULT_LANGUAGE_CODE` | DataForSEO language code | `en` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `LOG_DIR` | Log file directory | `logs` |

## Error handling

The pipeline never stops because one keyword or row fails. Every stage (input validation, Search Volume request, Google Trends request) catches its own errors, logs them, and records them in the Error Log sheet without interrupting the rest of the run. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#error-handling) for the full behavior.

## Running tests

```powershell
python -m unittest discover -s tests -v
```

## Project structure

```text
main.py                    CLI entrypoint
config.py                  Environment-driven runtime configuration (.env)
settings.py                Static constants (endpoints, thresholds, sheet layouts)
logger.py                  Logging setup

api/                        DataForSEO integration
  dataforseo_client.py      Auth, retry, task_post/task_get polling
  search_volume.py          Search Volume request/parsing
  google_trends.py          Google Trends request/parsing

excel/
  excel_reader.py           Input workbook reading + validation
  excel_writer.py           Output workbook assembly
  formatter.py              Shared worksheet formatting

models/                     Typed dataclasses (ProductRow, SearchVolumeResult, TrendResult, ResearchResult)

services/
  processor.py              Per-row result building + report row projection
  market_research.py        Pipeline orchestration

utils/                      Retry decorator, trend-direction calculation, validation

tests/                      unittest suite
examples/                   Example input/output workbooks + generator scripts
docs/                       Architecture and DataForSEO integration notes
data/input/, data/output/   Runtime input/output (gitignored)
logs/                       Runtime logs (gitignored)
```

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — data flow, design decisions, phased plan.
- [docs/DATAFORSEO.md](docs/DATAFORSEO.md) — exact endpoints, request/response shapes, and assumptions that should be verified against a live account.
