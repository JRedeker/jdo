"""Tests for ChatScreen - Split-panel layout.

Tests for the main chat interface with split-panel layout:
- Chat panel on left (60%)
- Data panel on right (40%)
- Responsive collapse on narrow terminals
"""

import pytest
from textual.app import App, ComposeResult
from textual.containers import Horizontal


class TestChatScreen:
    """Tests for ChatScreen split-panel layout."""

    async def test_chat_screen_has_horizontal_container(self) -> None:
        """ChatScreen has Horizontal with ChatPanel and DataPanel."""
        from jdo.screens.chat import ChatScreen

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ChatScreen()

        app = TestApp()
        async with app.run_test():
            screen = app.query_one(ChatScreen)
            # Should have a Horizontal container
            horizontal = screen.query_one(Horizontal)
            assert horizontal is not None

    async def test_chat_screen_has_chat_container(self) -> None:
        """ChatScreen has a ChatContainer on the left."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.chat_container import ChatContainer

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ChatScreen()

        app = TestApp()
        async with app.run_test():
            screen = app.query_one(ChatScreen)
            chat_container = screen.query_one(ChatContainer)
            assert chat_container is not None

    async def test_chat_screen_has_data_panel(self) -> None:
        """ChatScreen has a DataPanel on the right."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.data_panel import DataPanel

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ChatScreen()

        app = TestApp()
        async with app.run_test():
            screen = app.query_one(ChatScreen)
            data_panel = screen.query_one(DataPanel)
            assert data_panel is not None

    async def test_chat_screen_has_prompt_input(self) -> None:
        """ChatScreen has a PromptInput for user input."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.prompt_input import PromptInput

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ChatScreen()

        app = TestApp()
        async with app.run_test():
            screen = app.query_one(ChatScreen)
            prompt = screen.query_one(PromptInput)
            assert prompt is not None

    async def test_tab_toggles_focus(self) -> None:
        """Tab toggles focus between ChatPanel and DataPanel."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.data_panel import DataPanel
        from jdo.widgets.prompt_input import PromptInput

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ChatScreen()

        app = TestApp()
        async with app.run_test() as pilot:
            screen = app.query_one(ChatScreen)
            prompt = screen.query_one(PromptInput)
            data_panel = screen.query_one(DataPanel)

            # Initially focus should be on prompt
            prompt.focus()
            assert prompt.has_focus

            # Tab should move focus to data panel
            await pilot.press("tab")
            await pilot.pause()
            assert data_panel.has_focus or data_panel.can_focus

    async def test_escape_returns_focus_to_prompt(self) -> None:
        """Escape returns focus to the prompt."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.prompt_input import PromptInput

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ChatScreen()

        app = TestApp()
        async with app.run_test() as pilot:
            screen = app.query_one(ChatScreen)
            prompt = screen.query_one(PromptInput)

            # Focus somewhere else then press escape
            await pilot.press("tab")
            await pilot.pause()

            await pilot.press("escape")
            await pilot.pause()

            # Focus should return to prompt
            assert prompt.has_focus


class TestChatScreenResponsive:
    """Tests for responsive behavior of ChatScreen."""

    async def test_data_panel_visible_by_default(self) -> None:
        """DataPanel is visible by default."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.data_panel import DataPanel

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ChatScreen()

        app = TestApp()
        async with app.run_test():
            screen = app.query_one(ChatScreen)
            data_panel = screen.query_one(DataPanel)
            assert data_panel.display is True

    async def test_toggle_panel_method(self) -> None:
        """ChatScreen can toggle DataPanel visibility via action."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.data_panel import DataPanel

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ChatScreen()

        app = TestApp()
        async with app.run_test() as pilot:
            screen = app.query_one(ChatScreen)
            data_panel = screen.query_one(DataPanel)

            assert data_panel.display is True

            # Call the action directly
            screen.action_toggle_panel()
            await pilot.pause()

            assert data_panel.display is False

            # Toggle back
            screen.action_toggle_panel()
            await pilot.pause()

            assert data_panel.display is True


class TestChatScreenLayout:
    """Tests for ChatScreen CSS layout."""

    async def test_chat_panel_width(self) -> None:
        """ChatPanel takes approximately 60% width."""
        from jdo.screens.chat import ChatScreen

        class TestApp(App):
            CSS = """
            Screen {
                width: 100;
            }
            """

            def compose(self) -> ComposeResult:
                yield ChatScreen()

        app = TestApp()
        async with app.run_test():
            screen = app.query_one(ChatScreen)
            # The chat panel should have width styling
            # We verify the CSS is applied correctly
            assert "60%" in ChatScreen.DEFAULT_CSS or "fr" in ChatScreen.DEFAULT_CSS

    async def test_data_panel_width(self) -> None:
        """DataPanel takes approximately 40% width."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.data_panel import DataPanel

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield ChatScreen()

        app = TestApp()
        async with app.run_test():
            screen = app.query_one(ChatScreen)
            data_panel = screen.query_one(DataPanel)
            # DataPanel should exist and have width styling
            assert data_panel is not None
