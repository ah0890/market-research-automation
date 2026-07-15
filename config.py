"""Environment-driven runtime configuration.

All values that differ between machines or environments (credentials, file
paths, timeouts) are loaded here from a `.env` file via python-dotenv. Static
constants that never change belong in :mod:`settings` instead.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class AppConfig:
    """Immutable application configuration resolved from environment variables."""

    dataforseo_login: str
    dataforseo_password: str
    dataforseo_base_url: str

    use_mock_api: bool

    input_file_path: Path
    output_dir: Path

    request_timeout_seconds: int
    retry_count: int
    retry_backoff_seconds: float

    task_poll_interval_seconds: int
    task_max_wait_seconds: int

    default_location_code: int
    default_language_code: str

    log_level: str
    log_dir: Path

    @classmethod
    def load(cls, env_file: str | Path = ".env") -> "AppConfig":
        """Load configuration from the given `.env` file and process environment.

        Args:
            env_file: Path to the dotenv file to load before reading variables.

        Returns:
            A populated, validated :class:`AppConfig` instance.

        Raises:
            ConfigurationError: If a required variable is missing or malformed.
        """
        load_dotenv(dotenv_path=env_file, override=False)

        use_mock_api = _require_bool("USE_MOCK_API", False)

        try:
            return cls(
                dataforseo_login=(
                    os.getenv("DATAFORSEO_LOGIN", "") if use_mock_api else _require("DATAFORSEO_LOGIN")
                ),
                dataforseo_password=(
                    os.getenv("DATAFORSEO_PASSWORD", "") if use_mock_api else _require("DATAFORSEO_PASSWORD")
                ),
                dataforseo_base_url=os.getenv(
                    "DATAFORSEO_BASE_URL", "https://api.dataforseo.com"
                ).rstrip("/"),
                use_mock_api=use_mock_api,
                input_file_path=Path(
                    os.getenv("INPUT_FILE_PATH", "data/input/products.xlsx")
                ),
                output_dir=Path(os.getenv("OUTPUT_DIR", "data/output")),
                request_timeout_seconds=_require_int("REQUEST_TIMEOUT_SECONDS", 30),
                retry_count=_require_int("RETRY_COUNT", 3),
                retry_backoff_seconds=_require_float("RETRY_BACKOFF_SECONDS", 2.0),
                task_poll_interval_seconds=_require_int(
                    "TASK_POLL_INTERVAL_SECONDS", 10
                ),
                task_max_wait_seconds=_require_int("TASK_MAX_WAIT_SECONDS", 180),
                default_location_code=_require_int("DEFAULT_LOCATION_CODE", 2840),
                default_language_code=os.getenv("DEFAULT_LANGUAGE_CODE", "en"),
                log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
                log_dir=Path(os.getenv("LOG_DIR", "logs")),
            )
        except ValueError as exc:
            raise ConfigurationError(str(exc)) from exc


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ConfigurationError(f"Missing required environment variable: {name}")
    return value


def _require_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigurationError(f"Environment variable {name} must be an integer") from exc


def _require_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ConfigurationError(f"Environment variable {name} must be a number") from exc


def _require_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    normalized = value.strip().lower()
    if normalized in ("true", "1", "yes"):
        return True
    if normalized in ("false", "0", "no"):
        return False
    raise ConfigurationError(f"Environment variable {name} must be a boolean (true/false)")
