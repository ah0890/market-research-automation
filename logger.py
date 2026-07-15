"""Application-wide logging configuration."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(log_dir: Path, log_level: str = "INFO") -> logging.Logger:
    """Configure the root logger with console and file handlers.

    Args:
        log_dir: Directory where the log file will be written. Created if missing.
        log_level: Logging level name (e.g. "INFO", "DEBUG").

    Returns:
        The configured root logger for the application.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "market_research.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    return root_logger
