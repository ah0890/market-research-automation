"""CLI entrypoint for the market research automation tool.

Phase 1 (current): proof-of-concept scope, limited to a single product row
to validate the end-to-end pipeline (read workbook -> DataForSEO -> normalize
-> Excel report) before scaling up to unlimited rows in Phase 2.
"""

from __future__ import annotations

import logging
import sys

from config import AppConfig, ConfigurationError
from logger import configure_logging
from services.market_research import MarketResearchService

# Phase 1 proof-of-concept scope limiter. Set to None once Phase 2
# (unlimited rows) is approved.
PHASE_1_MAX_ROWS: int | None = 1


def main() -> int:
    try:
        config = AppConfig.load()
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    configure_logging(config.log_dir, config.log_level)
    logger = logging.getLogger(__name__)

    logger.info("Starting market research run")
    try:
        service = MarketResearchService(config)
        output_path = service.run(max_rows=PHASE_1_MAX_ROWS)
    except FileNotFoundError as exc:
        logger.error("Input file error: %s", exc)
        return 1
    except ValueError as exc:
        logger.error("Input validation error: %s", exc)
        return 1
    except Exception:
        logger.exception("Unexpected error during market research run")
        return 1

    logger.info("Report written to %s", output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
