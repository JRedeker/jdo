"""Tests for AI timeout utilities."""

from __future__ import annotations

import asyncio
import time

import pytest

from jdo.ai.timeout import (
    AI_STREAM_TIMEOUT_SECONDS,
    AI_TIMEOUT_SECONDS,
    HTTP_TIMEOUT_SECONDS,
    run_sync_with_timeout,
    with_ai_timeout,
)


class TestTimeoutConstants:
    """Tests for timeout constant values."""

    def test_http_timeout_is_reasonable(self) -> None:
        """HTTP timeout should be reasonable (30 seconds)."""
        assert HTTP_TIMEOUT_SECONDS == 30.0

    def test_ai_timeout_is_reasonable(self) -> None:
        """AI timeout should be 2 minutes for standard calls."""
        assert AI_TIMEOUT_SECONDS == 120

    def test_ai_stream_timeout_is_longer(self) -> None:
        """Streaming timeout should be longer than standard."""
        assert AI_STREAM_TIMEOUT_SECONDS > AI_TIMEOUT_SECONDS
        assert AI_STREAM_TIMEOUT_SECONDS == 180


class TestWithAiTimeout:
    """Tests for with_ai_timeout async wrapper."""

    @pytest.mark.asyncio
    async def test_returns_result_on_success(self) -> None:
        """Successful coroutine returns its result."""

        async def fast_operation() -> str:
            return "success"

        result = await with_ai_timeout(fast_operation())
        assert result == "success"

    @pytest.mark.asyncio
    async def test_raises_timeout_on_slow_operation(self) -> None:
        """Slow operation raises TimeoutError."""

        async def slow_operation() -> str:
            await asyncio.sleep(10)
            return "should not reach"

        with pytest.raises(TimeoutError):
            await with_ai_timeout(slow_operation(), timeout_seconds=0.1)

    @pytest.mark.asyncio
    async def test_custom_timeout_is_respected(self) -> None:
        """Custom timeout value is used."""

        async def medium_operation() -> str:
            await asyncio.sleep(0.3)
            return "completed"

        # Should succeed with longer timeout
        result = await with_ai_timeout(medium_operation(), timeout_seconds=1.0)
        assert result == "completed"

        # Should fail with shorter timeout
        with pytest.raises(TimeoutError):
            await with_ai_timeout(medium_operation(), timeout_seconds=0.1)


class TestRunSyncWithTimeout:
    """Tests for run_sync_with_timeout function."""

    def test_returns_result_on_success(self) -> None:
        """Successful function returns its result."""

        def fast_function(x: int, y: int) -> int:
            return x + y

        result = run_sync_with_timeout(fast_function, 2, 3, timeout=5.0)
        assert result == 5

    def test_raises_timeout_on_slow_function(self) -> None:
        """Slow function raises TimeoutError."""

        def slow_function() -> str:
            time.sleep(10)
            return "should not reach"

        with pytest.raises(TimeoutError, match="timed out after"):
            run_sync_with_timeout(slow_function, timeout=0.1)

    def test_passes_kwargs(self) -> None:
        """Keyword arguments are passed correctly."""

        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"

        result = run_sync_with_timeout(greet, "World", greeting="Hi", timeout=5.0)
        assert result == "Hi, World!"

    def test_propagates_exceptions(self) -> None:
        """Exceptions from function are propagated."""

        def failing_function() -> None:
            msg = "Test error"
            raise ValueError(msg)

        with pytest.raises(ValueError, match="Test error"):
            run_sync_with_timeout(failing_function, timeout=5.0)

    def test_timeout_message_includes_seconds(self) -> None:
        """TimeoutError message includes the timeout value."""

        def slow_function() -> None:
            time.sleep(10)

        with pytest.raises(TimeoutError) as exc_info:
            run_sync_with_timeout(slow_function, timeout=0.5)

        assert "0.5 seconds" in str(exc_info.value)
