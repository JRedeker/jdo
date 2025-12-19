"""Tests for auth screens helper functions."""

from __future__ import annotations

import pytest

from jdo.auth.screens import _extract_auth_code


class TestExtractAuthCode:
    """Tests for authorization code extraction from user input."""

    def test_extracts_raw_code(self):
        """Returns raw code unchanged."""
        code = "abc123XYZ"
        assert _extract_auth_code(code) == "abc123XYZ"

    def test_strips_whitespace_from_raw_code(self):
        """Strips leading/trailing whitespace from raw code."""
        assert _extract_auth_code("  code123  ") == "code123"
        assert _extract_auth_code("\ncode123\n") == "code123"

    def test_returns_empty_string_for_empty_input(self):
        """Returns empty string for empty/whitespace input."""
        assert _extract_auth_code("") == ""
        assert _extract_auth_code("   ") == ""

    def test_extracts_code_from_callback_url_https(self):
        """Extracts code parameter from HTTPS callback URL."""
        url = "https://console.anthropic.com/oauth/code/callback?code=auth_code_123&state=verifier_abc"
        assert _extract_auth_code(url) == "auth_code_123"

    def test_extracts_code_from_callback_url_http(self):
        """Extracts code parameter from HTTP callback URL."""
        url = "http://localhost:8080/callback?code=local_code_456&state=test"
        assert _extract_auth_code(url) == "local_code_456"

    def test_extracts_code_with_special_characters(self):
        """Handles codes with URL-safe special characters."""
        url = "https://example.com/callback?code=abc-123_XYZ.test&state=s"
        assert _extract_auth_code(url) == "abc-123_XYZ.test"

    def test_returns_url_when_no_code_param(self):
        """Returns original URL if no code parameter found."""
        url = "https://example.com/callback?error=access_denied"
        assert _extract_auth_code(url) == url

    def test_handles_url_with_multiple_params(self):
        """Correctly extracts code from URL with many parameters."""
        url = "https://console.anthropic.com/oauth/code/callback?state=verifier&code=my_code&extra=foo"
        assert _extract_auth_code(url) == "my_code"

    def test_handles_code_only_url(self):
        """Handles URL with only code parameter."""
        url = "https://example.com/?code=solo_code"
        assert _extract_auth_code(url) == "solo_code"

    @pytest.mark.parametrize(
        "raw_code",
        [
            "simple_code",
            "CODE_WITH_UNDERSCORE",
            "code-with-dashes",
            "code.with.dots",
            "1234567890",
            "a" * 100,  # Long code
        ],
    )
    def test_various_raw_code_formats(self, raw_code: str):
        """Various raw code formats are returned unchanged."""
        assert _extract_auth_code(raw_code) == raw_code
