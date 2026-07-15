"""Thin HTTP client for DataForSEO's Standard (task-queue) API mode.

DataForSEO's "Standard" mode is asynchronous: a task is submitted via a
``task_post`` endpoint, which returns a task id, and the result is later
retrieved via the matching ``task_get/{id}`` endpoint once processing
completes. This client centralizes authentication, retryable HTTP calls, and
the poll-until-ready loop so that ``api/search_volume.py`` and
``api/google_trends.py`` only need to build request payloads and parse
results.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from api.exceptions import (
    DataForSeoRequestError,
    DataForSeoTaskError,
    DataForSeoTimeoutError,
)
from settings import TASK_PENDING_STATUS_CODES, TASK_SUCCESS_STATUS_CODE
from utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)

_RETRYABLE_HTTP_STATUS_CODES = {429, 500, 502, 503, 504}


class DataForSeoClient:
    """Authenticated HTTP client for DataForSEO's task-queue endpoints."""

    def __init__(
        self,
        base_url: str,
        login: str,
        password: str,
        timeout_seconds: int,
        retry_count: int,
        retry_backoff_seconds: float,
        poll_interval_seconds: int,
        max_wait_seconds: int,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._poll_interval_seconds = poll_interval_seconds
        self._max_wait_seconds = max_wait_seconds

        self._session = requests.Session()
        self._session.auth = (login, password)
        self._session.headers.update({"Content-Type": "application/json"})

        # Wrap the low-level HTTP methods with retry behaviour built from the
        # instance's configured retry count/backoff (set at construction time
        # so it can differ between environments without touching call sites).
        self._post_json = retry_with_backoff(
            retries=retry_count,
            backoff_seconds=retry_backoff_seconds,
            retryable_exceptions=(DataForSeoRequestError,),
        )(self._post_json_once)
        self._get_json = retry_with_backoff(
            retries=retry_count,
            backoff_seconds=retry_backoff_seconds,
            retryable_exceptions=(DataForSeoRequestError,),
        )(self._get_json_once)

    def post_task(self, path: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
        """Submit a task to a ``task_post`` endpoint and return the created task."""
        response = self._post_json(path, payload)
        return _extract_single_task(response)

    def poll_task_until_ready(self, get_path_prefix: str, task_id: str) -> dict[str, Any]:
        """Poll a ``task_get/{id}`` endpoint until the task succeeds or fails.

        Args:
            get_path_prefix: The task_get base path (task id is appended).
            task_id: The id returned by the corresponding ``task_post`` call.

        Returns:
            The completed task dict (with populated ``result``).

        Raises:
            DataForSeoTaskError: If the task reaches a non-success, non-pending
                status code (e.g. invalid keyword, malformed request).
            DataForSeoTimeoutError: If the task is still pending after
                ``max_wait_seconds``.
        """
        deadline = time.monotonic() + self._max_wait_seconds
        path = f"{get_path_prefix.rstrip('/')}/{task_id}"

        while True:
            response = self._get_json(path)
            task = _extract_single_task(response)
            status_code = task.get("status_code")

            if status_code == TASK_SUCCESS_STATUS_CODE:
                return task

            if status_code not in TASK_PENDING_STATUS_CODES:
                raise DataForSeoTaskError(
                    f"Task {task_id} failed with status {status_code}: "
                    f"{task.get('status_message')}"
                )

            if time.monotonic() >= deadline:
                raise DataForSeoTimeoutError(
                    f"Task {task_id} did not complete within "
                    f"{self._max_wait_seconds}s"
                )

            logger.debug(
                "Task %s still pending (status %s); polling again in %ds",
                task_id,
                status_code,
                self._poll_interval_seconds,
            )
            time.sleep(self._poll_interval_seconds)

    def _post_json_once(self, path: str, payload: list[dict[str, Any]]) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            response = self._session.post(url, json=payload, timeout=self._timeout_seconds)
        except requests.exceptions.RequestException as exc:
            raise DataForSeoRequestError(f"POST {path} failed: {exc}") from exc
        return _parse_response(response, path)

    def _get_json_once(self, path: str) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            response = self._session.get(url, timeout=self._timeout_seconds)
        except requests.exceptions.RequestException as exc:
            raise DataForSeoRequestError(f"GET {path} failed: {exc}") from exc
        return _parse_response(response, path)


def _parse_response(response: requests.Response, path: str) -> dict[str, Any]:
    if response.status_code in _RETRYABLE_HTTP_STATUS_CODES:
        raise DataForSeoRequestError(
            f"{path} returned transient HTTP {response.status_code}"
        )
    if response.status_code >= 400:
        raise DataForSeoTaskError(
            f"{path} returned HTTP {response.status_code}: {response.text[:500]}"
        )
    try:
        return response.json()
    except ValueError as exc:
        raise DataForSeoTaskError(f"{path} returned non-JSON response") from exc


def _extract_single_task(response: dict[str, Any]) -> dict[str, Any]:
    tasks = response.get("tasks") or []
    if not tasks:
        raise DataForSeoTaskError(
            f"DataForSEO response contained no tasks: {response.get('status_message')}"
        )
    return tasks[0]
