"""Tests for HTTP retry utilities."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from jdo.retry import http_retry


class TestHttpRetryDecorator:
    """Tests for http_retry decorator."""

    def test_returns_result_on_success(self) -> None:
        """Successful function returns its result without retry."""

        @http_retry()
        def always_succeeds() -> str:
            return "success"

        result = always_succeeds()
        assert result == "success"

    def test_retries_on_connect_error(self) -> None:
        """Function retries on ConnectError."""
        call_count = 0

        @http_retry()
        def fails_then_succeeds() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ConnectError("Connection refused")
            return "success after retry"

        result = fails_then_succeeds()
        assert result == "success after retry"
        assert call_count == 3

    def test_retries_on_timeout_exception(self) -> None:
        """Function retries on TimeoutException."""
        call_count = 0

        @http_retry()
        def times_out_then_succeeds() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.TimeoutException("Read timed out")
            return "success"

        result = times_out_then_succeeds()
        assert result == "success"
        assert call_count == 2

    def test_does_not_retry_on_http_status_error(self) -> None:
        """Function does NOT retry on HTTP status errors (401, 403, etc)."""
        call_count = 0

        @http_retry()
        def unauthorized() -> str:
            nonlocal call_count
            call_count += 1
            # Create a mock response for the error
            response = httpx.Response(401)
            raise httpx.HTTPStatusError("Unauthorized", request=MagicMock(), response=response)

        with pytest.raises(httpx.HTTPStatusError):
            unauthorized()

        # Should only be called once - no retries
        assert call_count == 1

    def test_does_not_retry_on_value_error(self) -> None:
        """Function does NOT retry on non-network errors."""
        call_count = 0

        @http_retry()
        def validation_error() -> str:
            nonlocal call_count
            call_count += 1
            msg = "Invalid input"
            raise ValueError(msg)

        with pytest.raises(ValueError, match="Invalid input"):
            validation_error()

        # Should only be called once - no retries
        assert call_count == 1

    def test_gives_up_after_max_attempts(self) -> None:
        """Function gives up after max retry attempts."""
        call_count = 0

        @http_retry()
        def always_fails() -> str:
            nonlocal call_count
            call_count += 1
            raise httpx.ConnectError("Connection refused")

        with pytest.raises(httpx.ConnectError):
            always_fails()

        # Default is 3 attempts (initial + 2 retries)
        assert call_count == 3

    def test_preserves_function_metadata(self) -> None:
        """Decorator preserves function name and docstring."""

        @http_retry()
        def documented_function() -> str:
            """This is the docstring."""
            return "result"

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is the docstring."

    def test_works_with_async_functions(self) -> None:
        """Decorator works with async functions."""
        import asyncio

        call_count = 0

        @http_retry()
        async def async_fails_then_succeeds() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.ConnectError("Connection refused")
            return "async success"

        result = asyncio.run(async_fails_then_succeeds())
        assert result == "async success"
        assert call_count == 2
