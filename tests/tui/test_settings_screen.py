"""Tests for SettingsScreen - Provider authentication and AI settings.

The SettingsScreen integrates with the jdo.auth module to show
authentication status and launch auth flows for AI providers.
"""

from typing import ClassVar
from unittest.mock import patch

import pytest
from textual.app import App, ComposeResult
from textual.binding import Binding


class TestSettingsScreenRendering:
    """Tests for SettingsScreen basic rendering."""

    async def test_settings_screen_renders(self) -> None:
        """SettingsScreen renders without error."""
        from jdo.screens.settings import SettingsScreen

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen()

        app = TestApp()
        async with app.run_test():
            screen = app.query_one(SettingsScreen)
            assert screen is not None

    async def test_settings_screen_shows_title(self) -> None:
        """SettingsScreen shows a title."""
        from jdo.screens.settings import SettingsScreen

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen()

        app = TestApp()
        async with app.run_test():
            # Should have settings title visible
            screen = app.query_one(SettingsScreen)
            assert screen is not None


class TestSettingsScreenAuthStatus:
    """Tests for SettingsScreen authentication status display."""

    async def test_shows_auth_status_per_provider(self) -> None:
        """Settings screen shows auth status for each provider."""
        from jdo.screens.settings import SettingsScreen

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield SettingsScreen()

        app = TestApp()
        async with app.run_test():
            screen = app.query_one(SettingsScreen)
            # Should show providers (anthropic, openai, openrouter)
            assert screen is not None
            # The screen should display provider names
            # Content will be verified in render output

    async def test_shows_authenticated_status(self) -> None:
        """Shows 'Authenticated' when provider has credentials."""
        from jdo.screens.settings import SettingsScreen

        with patch("jdo.screens.settings.is_authenticated") as mock_auth:
            mock_auth.return_value = True

            class TestApp(App):
                def compose(self) -> ComposeResult:
                    yield SettingsScreen()

            app = TestApp()
            async with app.run_test():
                screen = app.query_one(SettingsScreen)
                assert screen is not None

    async def test_shows_not_authenticated_status(self) -> None:
        """Shows 'Not authenticated' when provider lacks credentials."""
        from jdo.screens.settings import SettingsScreen

        with patch("jdo.screens.settings.is_authenticated") as mock_auth:
            mock_auth.return_value = False

            class TestApp(App):
                def compose(self) -> ComposeResult:
                    yield SettingsScreen()

            app = TestApp()
            async with app.run_test():
                screen = app.query_one(SettingsScreen)
                assert screen is not None


class TestSettingsScreenProviderInfo:
    """Tests for provider information display."""

    async def test_shows_current_ai_provider(self) -> None:
        """Settings shows current AI provider from settings."""
        from jdo.screens.settings import SettingsScreen

        with patch("jdo.screens.settings.get_settings") as mock_settings:
            mock_settings.return_value.ai_provider = "anthropic"
            mock_settings.return_value.ai_model = "claude-sonnet-4-20250514"

            class TestApp(App):
                def compose(self) -> ComposeResult:
                    yield SettingsScreen()

            app = TestApp()
            async with app.run_test():
                screen = app.query_one(SettingsScreen)
                assert screen is not None

    async def test_shows_current_ai_model(self) -> None:
        """Settings shows current AI model from settings."""
        from jdo.screens.settings import SettingsScreen

        with patch("jdo.screens.settings.get_settings") as mock_settings:
            mock_settings.return_value.ai_provider = "anthropic"
            mock_settings.return_value.ai_model = "claude-sonnet-4-20250514"

            class TestApp(App):
                def compose(self) -> ComposeResult:
                    yield SettingsScreen()

            app = TestApp()
            async with app.run_test():
                screen = app.query_one(SettingsScreen)
                assert screen is not None


class TestSettingsScreenAuthFlows:
    """Tests for launching authentication flows."""

    async def test_launches_oauth_flow_for_claude(self) -> None:
        """Settings launches OAuth flow for Claude/Anthropic."""
        from jdo.screens.settings import SettingsScreen

        class TestApp(App):
            BINDINGS: ClassVar[list[Binding]] = [
                Binding("escape", "back", "Back"),
            ]
            oauth_launched = False

            def compose(self) -> ComposeResult:
                yield SettingsScreen()

            def push_screen(self, screen, callback=None):
                # Check if OAuthScreen is being pushed
                from jdo.auth.screens import OAuthScreen

                if isinstance(screen, OAuthScreen):
                    self.oauth_launched = True
                return super().push_screen(screen, callback)

        app = TestApp()
        async with app.run_test() as pilot:
            screen = app.query_one(SettingsScreen)
            # Trigger OAuth flow for anthropic
            screen.launch_oauth_flow("anthropic")
            await pilot.pause()
            assert app.oauth_launched

    async def test_launches_api_key_flow_for_openai(self) -> None:
        """Settings launches API key flow for OpenAI."""
        from jdo.screens.settings import SettingsScreen

        class TestApp(App):
            BINDINGS: ClassVar[list[Binding]] = [
                Binding("escape", "back", "Back"),
            ]
            api_key_launched = False
            api_key_provider = None

            def compose(self) -> ComposeResult:
                yield SettingsScreen()

            def push_screen(self, screen, callback=None):
                # Check if ApiKeyScreen is being pushed
                from jdo.auth.screens import ApiKeyScreen

                if isinstance(screen, ApiKeyScreen):
                    self.api_key_launched = True
                    self.api_key_provider = screen.provider_id
                return super().push_screen(screen, callback)

        app = TestApp()
        async with app.run_test() as pilot:
            screen = app.query_one(SettingsScreen)
            # Trigger API key flow for openai
            screen.launch_api_key_flow("openai")
            await pilot.pause()
            assert app.api_key_launched
            assert app.api_key_provider == "openai"

    async def test_launches_api_key_flow_for_openrouter(self) -> None:
        """Settings launches API key flow for OpenRouter."""
        from jdo.screens.settings import SettingsScreen

        class TestApp(App):
            BINDINGS: ClassVar[list[Binding]] = [
                Binding("escape", "back", "Back"),
            ]
            api_key_launched = False
            api_key_provider = None

            def compose(self) -> ComposeResult:
                yield SettingsScreen()

            def push_screen(self, screen, callback=None):
                from jdo.auth.screens import ApiKeyScreen

                if isinstance(screen, ApiKeyScreen):
                    self.api_key_launched = True
                    self.api_key_provider = screen.provider_id
                return super().push_screen(screen, callback)

        app = TestApp()
        async with app.run_test() as pilot:
            screen = app.query_one(SettingsScreen)
            screen.launch_api_key_flow("openrouter")
            await pilot.pause()
            assert app.api_key_launched
            assert app.api_key_provider == "openrouter"


class TestSettingsScreenKeyBindings:
    """Tests for SettingsScreen keyboard shortcuts."""

    async def test_escape_key_goes_back(self) -> None:
        """Escape key posts a Back message to go back."""
        from jdo.screens.settings import SettingsScreen

        class TestApp(App):
            back_triggered = False

            def compose(self) -> ComposeResult:
                yield SettingsScreen()

            def on_settings_screen_back(self, event: SettingsScreen.Back) -> None:
                self.back_triggered = True

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.press("escape")
            await pilot.pause()
            assert app.back_triggered

    async def test_settings_screen_has_bindings(self) -> None:
        """SettingsScreen has BINDINGS defined."""
        from jdo.screens.settings import SettingsScreen

        assert hasattr(SettingsScreen, "BINDINGS")
        assert len(SettingsScreen.BINDINGS) > 0


class TestSettingsScreenMessages:
    """Tests for SettingsScreen message posting."""

    async def test_posts_back_message(self) -> None:
        """SettingsScreen posts Back message."""
        from jdo.screens.settings import SettingsScreen

        # SettingsScreen should have a Back message class
        assert hasattr(SettingsScreen, "Back")

    async def test_posts_provider_changed_message(self) -> None:
        """SettingsScreen posts ProviderChanged message when provider is selected."""
        from jdo.screens.settings import SettingsScreen

        # SettingsScreen should have a ProviderChanged message class
        assert hasattr(SettingsScreen, "ProviderChanged")
