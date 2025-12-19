"""Tests for auth screens helper functions."""

from __future__ import annotations

from jdo.auth.screens import ApiKeyScreen


class TestApiKeyScreen:
    """Basic smoke tests for ApiKeyScreen wiring."""

    def test_screen_initializes_with_provider(self):
        """ApiKeyScreen stores provider metadata."""
        screen = ApiKeyScreen("openai")
        assert screen.provider_id == "openai"
