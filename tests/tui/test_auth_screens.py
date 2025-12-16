"""Tests for TUI auth screens."""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Input, Static

# Mark all tests in this module as TUI tests
pytestmark = pytest.mark.tui


class TestOAuthScreen:
    """Tests for OAuthScreen."""

    async def test_oauth_screen_displays_authorization_url(self):
        """OAuthScreen displays authorization URL."""
        from jdo.auth.screens import OAuthScreen

        screen = OAuthScreen()

        class TestApp(App):
            CSS = "Screen { min-height: 30; min-width: 100; }"

            def compose(self) -> ComposeResult:
                return []

            def on_mount(self):
                self.push_screen(screen)

        async with TestApp().run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            # Check the screen's auth_url attribute
            assert "claude.ai" in screen.auth_url

    async def test_oauth_screen_has_input_for_auth_code(self):
        """OAuthScreen has input for auth code."""
        from jdo.auth.screens import OAuthScreen

        class TestApp(App):
            CSS = "Screen { min-height: 30; min-width: 100; }"

            def compose(self) -> ComposeResult:
                return []

            def on_mount(self):
                self.push_screen(OAuthScreen())

        async with TestApp().run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            screen = pilot.app.screen_stack[-1]
            code_input = screen.query_one("#code-input", Input)
            assert code_input is not None
            assert code_input.placeholder == "Paste authorization code here"

    async def test_oauth_screen_dismiss_false_on_cancel(self):
        """OAuthScreen dismiss(False) on cancel via escape key."""
        from jdo.auth.screens import OAuthScreen

        result = None

        def capture_result(r):
            nonlocal result
            result = r

        class TestApp(App):
            CSS = "Screen { min-height: 30; min-width: 100; }"

            def compose(self) -> ComposeResult:
                return []

            def on_mount(self):
                self.push_screen(OAuthScreen(), callback=capture_result)

        async with TestApp().run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            # Press escape to cancel
            await pilot.press("escape")
            await pilot.pause()

        assert result is False

    async def test_oauth_screen_stores_verifier(self):
        """OAuthScreen stores PKCE verifier for code exchange."""
        from jdo.auth.screens import OAuthScreen

        screen = OAuthScreen()

        class TestApp(App):
            CSS = "Screen { min-height: 30; min-width: 100; }"

            def compose(self) -> ComposeResult:
                return []

            def on_mount(self):
                self.push_screen(screen)

        async with TestApp().run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            # The screen should have a verifier stored
            assert screen.verifier is not None
            assert len(screen.verifier) >= 43


class TestApiKeyScreen:
    """Tests for ApiKeyScreen."""

    async def test_api_key_screen_has_input_for_api_key(self):
        """ApiKeyScreen has input for API key."""
        from jdo.auth.screens import ApiKeyScreen

        class TestApp(App):
            CSS = "Screen { min-height: 30; min-width: 100; }"

            def compose(self) -> ComposeResult:
                return []

            def on_mount(self):
                self.push_screen(ApiKeyScreen(provider_id="openai"))

        async with TestApp().run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            screen = pilot.app.screen_stack[-1]
            key_input = screen.query_one("#api-key-input", Input)
            assert key_input is not None

    async def test_api_key_screen_masks_key_input(self):
        """ApiKeyScreen masks key input."""
        from jdo.auth.screens import ApiKeyScreen

        class TestApp(App):
            CSS = "Screen { min-height: 30; min-width: 100; }"

            def compose(self) -> ComposeResult:
                return []

            def on_mount(self):
                self.push_screen(ApiKeyScreen(provider_id="openai"))

        async with TestApp().run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            screen = pilot.app.screen_stack[-1]
            key_input = screen.query_one("#api-key-input", Input)
            assert key_input.password is True

    async def test_api_key_screen_stores_provider_id(self):
        """ApiKeyScreen stores provider id."""
        from jdo.auth.screens import ApiKeyScreen

        screen = ApiKeyScreen(provider_id="openai")

        class TestApp(App):
            CSS = "Screen { min-height: 30; min-width: 100; }"

            def compose(self) -> ComposeResult:
                return []

            def on_mount(self):
                self.push_screen(screen)

        async with TestApp().run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            assert screen.provider_id == "openai"
            assert "OpenAI" in screen.provider_name

    async def test_api_key_screen_dismiss_false_on_cancel(self):
        """ApiKeyScreen dismiss(False) on cancel via escape key."""
        from jdo.auth.screens import ApiKeyScreen

        result = None

        def capture_result(r):
            nonlocal result
            result = r

        class TestApp(App):
            CSS = "Screen { min-height: 30; min-width: 100; }"

            def compose(self) -> ComposeResult:
                return []

            def on_mount(self):
                self.push_screen(ApiKeyScreen(provider_id="openai"), callback=capture_result)

        async with TestApp().run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            # Press escape to cancel
            await pilot.press("escape")
            await pilot.pause()

        assert result is False

    async def test_api_key_screen_validates_non_empty(self, tmp_path, monkeypatch):
        """ApiKeyScreen validates key is non-empty."""
        from jdo.auth.screens import ApiKeyScreen

        # Mock auth path to use temp directory
        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)

        screen = ApiKeyScreen(provider_id="openai")

        class TestApp(App):
            CSS = "Screen { min-height: 30; min-width: 100; }"

            def compose(self) -> ComposeResult:
                return []

            def on_mount(self):
                self.push_screen(screen)

        async with TestApp().run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            # The screen has an empty input - calling _save_key() directly
            # should NOT dismiss (error label shown instead)
            screen._save_key()
            await pilot.pause()

            # Screen should still be attached
            assert screen.is_attached
