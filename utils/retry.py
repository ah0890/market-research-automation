"""Retry-with-backoff decorator used by the DataForSEO API client.

Kept generic and dependency-free (no third-party retry library) so it can
wrap any callable and be unit tested in isolation.
"""

from __future__ import annotations

import logging
import time
from functools import wraps
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    retries: int,
    backoff_seconds: float,
    retryable_exceptions: tuple[type[Exception], ...],
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Retry a callable on specified exceptions using exponential backoff.

    Args:
        retries: Maximum number of attempts (including the first).
        backoff_seconds: Base delay; doubled after each failed attempt.
        retryable_exceptions: Exception types that should trigger a retry.
            Any other exception propagates immediately without retrying.

    Returns:
        A decorator that wraps the target function with retry behaviour.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            attempt = 1
            delay = backoff_seconds
            while True:
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as exc:
                    if attempt >= retries:
                        logger.error(
                            "%s failed after %d attempt(s): %s",
                            func.__qualname__,
                            attempt,
                            exc,
                        )
                        raise
                    logger.warning(
                        "%s attempt %d/%d failed (%s); retrying in %.1fs",
                        func.__qualname__,
                        attempt,
                        retries,
                        exc,
                        delay,
                    )
                    time.sleep(delay)
                    attempt += 1
                    delay *= 2

        return wrapper

    return decorator
