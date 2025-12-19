"""Timeout utilities for network and AI operations.

Provides timeout constants and wrapper functions to ensure all network
and AI operations have bounded execution times per core-rules P03.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from collections.abc import Awaitable, Callable
from typing import TypeVar

# Network timeouts (based on httpx defaults + industry standards)
HTTP_TIMEOUT_SECONDS = 30.0  # Total timeout for HTTP operations (OAuth, etc.)

# AI operation timeouts (LLM API calls can be slow)
AI_TIMEOUT_SECONDS = 120  # 2 minutes for standard AI calls
AI_STREAM_TIMEOUT_SECONDS = 180  # 3 minutes for streaming (longer due to chunked responses)

T = TypeVar("T")


async def with_ai_timeout(
    coro: Awaitable[T],
    timeout_seconds: float = AI_TIMEOUT_SECONDS,
) -> T:
    """Wrap an async coroutine with AI timeout.

    Args:
        coro: The coroutine to execute.
        timeout_seconds: Timeout in seconds (default: AI_TIMEOUT_SECONDS).

    Returns:
        The result of the coroutine.

    Raises:
        TimeoutError: If the operation times out.
    """
    async with asyncio.timeout(timeout_seconds):
        return await coro


def run_sync_with_timeout(
    func: Callable[..., T],
    *args: object,
    timeout: float = AI_TIMEOUT_SECONDS,
    **kwargs: object,
) -> T:
    """Run a synchronous function with a timeout.

    Uses ThreadPoolExecutor to run the function in a separate thread
    and enforces a timeout on the result.

    Args:
        func: The function to call.
        *args: Positional arguments to pass to the function.
        timeout: Timeout in seconds (default: AI_TIMEOUT_SECONDS).
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        The result of the function.

    Raises:
        TimeoutError: If the operation times out.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError as e:
            msg = f"Operation timed out after {timeout} seconds"
            raise TimeoutError(msg) from e
