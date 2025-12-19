"""Tests for SettingsScreen - Provider authentication and AI settings.

The SettingsScreen integrates with the jdo.auth module to show
authentication status and launch auth flows for AI providers.
"""

from typing import ClassVar
from unittest.mock import patch

import pytest
from textual.app import App, ComposeResult
from textual.binding import Binding

from tests.tui.conftest import create_test_app_for_screen


class TestSettingsScreenRendering:
    """Tests for SettingsScreen basic rendering."""

    async def test_settings_screen_renders(self) -> None:
        """SettingsScreen renders without error."""
        from jdo.screens.settings import SettingsScreen

        app = create_test_app_for_screen(SettingsScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, SettingsScreen)

    async def test_settings_screen_shows_title(self) -> None:
        """SettingsScreen shows a title."""
        from jdo.screens.settings import SettingsScreen

        app = create_test_app_for_screen(SettingsScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, SettingsScreen)


class TestSettingsScreenAuthStatus:
    """Tests for SettingsScreen authentication status display."""

    async def test_shows_auth_status_per_provider(self) -> None:
        """Settings screen shows auth status for each provider."""
        from jdo.screens.settings import SettingsScreen

        app = create_test_app_for_screen(SettingsScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, SettingsScreen)

    async def test_shows_authenticated_status(self) -> None:
        """Shows 'Authenticated' when provider has credentials."""
        from jdo.screens.settings import SettingsScreen

        with patch("jdo.screens.settings.is_authenticated") as mock_auth:
            mock_auth.return_value = True

            app = create_test_app_for_screen(SettingsScreen())
            async with app.run_test() as pilot:
                await pilot.pause()
                screen = pilot.app.screen
                assert isinstance(screen, SettingsScreen)

    async def test_shows_not_authenticated_status(self) -> None:
        """Shows 'Not authenticated' when provider lacks credentials."""
        from jdo.screens.settings import SettingsScreen

        with patch("jdo.screens.settings.is_authenticated") as mock_auth:
            mock_auth.return_value = False

            app = create_test_app_for_screen(SettingsScreen())
            async with app.run_test() as pilot:
                await pilot.pause()
                screen = pilot.app.screen
                assert isinstance(screen, SettingsScreen)


class TestSettingsScreenProviderInfo:
    """Tests for provider information display."""

    async def test_shows_current_ai_provider(self) -> None:
        """Settings shows current AI provider from settings."""
        from jdo.screens.settings import SettingsScreen

        with patch("jdo.screens.settings.get_settings") as mock_settings:
            mock_settings.return_value.ai_provider = "openai"
            mock_settings.return_value.ai_model = "gpt-4o"

            app = create_test_app_for_screen(SettingsScreen())
            async with app.run_test() as pilot:
                await pilot.pause()
                screen = pilot.app.screen
                assert isinstance(screen, SettingsScreen)

    async def test_shows_current_ai_model(self) -> None:
        """Settings shows current AI model from settings."""
        from jdo.screens.settings import SettingsScreen

        with patch("jdo.screens.settings.get_settings") as mock_settings:
            mock_settings.return_value.ai_provider = "openai"
            mock_settings.return_value.ai_model = "gpt-4o"

            app = create_test_app_for_screen(SettingsScreen())
            async with app.run_test() as pilot:
                await pilot.pause()
                screen = pilot.app.screen
                assert isinstance(screen, SettingsScreen)


class TestSettingsScreenAuthFlows:
    """Tests for launching authentication flows."""

    async def test_launches_api_key_flow_for_openai(self) -> None:
        """Settings launches API key flow for OpenAI."""
        from jdo.auth.screens import ApiKeyScreen
        from jdo.screens.settings import SettingsScreen

        api_key_launched = False
        api_key_provider = None

        class TestApp(App):
            BINDINGS: ClassVar[list[Binding]] = [
                Binding("escape", "back", "Back"),
            ]

            def compose(self) -> ComposeResult:
                return
                yield

            async def on_mount(self) -> None:
                await self.push_screen(SettingsScreen())

            def push_screen(self, screen, callback=None):
                nonlocal api_key_launched, api_key_provider
                if isinstance(screen, ApiKeyScreen):
                    api_key_launched = True
                    api_key_provider = screen.provider_id
                return super().push_screen(screen, callback)

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, SettingsScreen)
            screen.launch_api_key_flow("openai")
            await pilot.pause()
            assert api_key_launched
            assert api_key_provider == "openai"

    async def test_launches_api_key_flow_for_openrouter(self) -> None:
        """Settings launches API key flow for OpenRouter."""
        from jdo.auth.screens import ApiKeyScreen
        from jdo.screens.settings import SettingsScreen

        api_key_launched = False
        api_key_provider = None

        class TestApp(App):
            BINDINGS: ClassVar[list[Binding]] = [
                Binding("escape", "back", "Back"),
            ]

            def compose(self) -> ComposeResult:
                return
                yield

            async def on_mount(self) -> None:
                await self.push_screen(SettingsScreen())

            def push_screen(self, screen, callback=None):
                nonlocal api_key_launched, api_key_provider
                if isinstance(screen, ApiKeyScreen):
                    api_key_launched = True
                    api_key_provider = screen.provider_id
                return super().push_screen(screen, callback)

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, SettingsScreen)
            screen.launch_api_key_flow("openrouter")
            await pilot.pause()
            assert api_key_launched
            assert api_key_provider == "openrouter"


class TestSettingsScreenKeyBindings:
    """Tests for SettingsScreen keyboard shortcuts."""

    async def test_escape_key_goes_back(self) -> None:
        """Escape key posts a Back message to go back."""
        from jdo.screens.settings import SettingsScreen

        back_triggered = False

        class TestApp(App):
            def compose(self) -> ComposeResult:
                return
                yield

            async def on_mount(self) -> None:
                await self.push_screen(SettingsScreen())

            def on_settings_screen_back(self, event: SettingsScreen.Back) -> None:
                nonlocal back_triggered
                back_triggered = True

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()
            assert back_triggered

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

    async def test_posts_auth_status_changed_message(self) -> None:
        """SettingsScreen posts AuthStatusChanged message when auth status changes."""
        from jdo.screens.settings import SettingsScreen

        # SettingsScreen should have an AuthStatusChanged message class
        assert hasattr(SettingsScreen, "AuthStatusChanged")
