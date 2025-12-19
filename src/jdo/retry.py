"""Retry utilities with exponential backoff using tenacity.

Provides retry decorators for HTTP operations to handle transient
network failures per core-rules P10 (idempotence).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import ParamSpec, TypeVar

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

# Retry configuration
MAX_RETRIES = 3
MIN_WAIT_SECONDS = 1
MAX_WAIT_SECONDS = 10

# Retryable HTTP exceptions (transient network failures only)
# Does NOT include HTTPStatusError - auth failures (401/403) are not transient
RETRYABLE_HTTP_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.TimeoutException,  # Base class for all timeout types
)

P = ParamSpec("P")
T = TypeVar("T")


def http_retry() -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator for retrying HTTP operations with exponential backoff.

    Retries on transient network errors only (connect, timeout).
    Does NOT retry on HTTP status errors (4xx, 5xx) as those require
    different handling (auth refresh, user notification, etc.).

    Uses exponential backoff with jitter to avoid thundering herd.

    Returns:
        Decorator that adds retry behavior to async functions.

    Example:
        @http_retry()
        async def fetch_data():
            async with httpx.AsyncClient() as client:
                return await client.get(url)
    """
    return retry(
        retry=retry_if_exception_type(RETRYABLE_HTTP_EXCEPTIONS),
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential_jitter(initial=MIN_WAIT_SECONDS, max=MAX_WAIT_SECONDS),
        reraise=True,
    )
