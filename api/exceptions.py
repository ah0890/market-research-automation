"""Exceptions raised by the DataForSEO integration layer."""

from __future__ import annotations


class DataForSeoError(Exception):
    """Base class for all DataForSEO-related errors."""


class DataForSeoRequestError(DataForSeoError):
    """A transient HTTP/network failure. Safe to retry."""


class DataForSeoTaskError(DataForSeoError):
    """The API accepted the request but the task itself failed. Not retryable."""


class DataForSeoTimeoutError(DataForSeoError):
    """A task did not complete within the configured maximum wait time."""
