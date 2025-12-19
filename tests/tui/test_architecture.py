"""Tests for TUI architecture - Screen vs Widget subclass verification.

This module verifies that:
- Navigation targets (HomeScreen, ChatScreen, SettingsScreen) are Screen subclasses
- Composable components (ChatContainer, DataPanel, etc.) are Widget subclasses
- Screens have proper message classes for parent communication
"""

from textual.screen import Screen
from textual.widget import Widget

from tests.tui.conftest import create_test_app_for_screen


class TestScreenSubclasses:
    """Verify navigation targets are Screen subclasses."""

    def test_home_screen_is_screen_subclass(self) -> None:
        """HomeScreen must be a Screen subclass for navigation stack."""
        from jdo.screens.home import HomeScreen

        assert isinstance(HomeScreen, type), "HomeScreen should be a class"
        assert issubclass(HomeScreen, Screen), "HomeScreen should inherit from Screen"

    def test_chat_screen_is_screen_subclass(self) -> None:
        """ChatScreen must be a Screen subclass for navigation stack."""
        from jdo.screens.chat import ChatScreen

        assert isinstance(ChatScreen, type), "ChatScreen should be a class"
        assert issubclass(ChatScreen, Screen), "ChatScreen should inherit from Screen"

    def test_settings_screen_is_screen_subclass(self) -> None:
        """SettingsScreen must be a Screen subclass for navigation stack."""
        from jdo.screens.settings import SettingsScreen

        assert isinstance(SettingsScreen, type), "SettingsScreen should be a class"
        assert issubclass(SettingsScreen, Screen), "SettingsScreen should inherit from Screen"


class TestWidgetSubclasses:
    """Verify composable components are Widget subclasses."""

    def test_chat_container_is_widget_subclass(self) -> None:
        """ChatContainer is a composable Widget."""
        from jdo.widgets.chat_container import ChatContainer

        assert isinstance(ChatContainer, type), "ChatContainer should be a class"
        assert issubclass(ChatContainer, Widget), "ChatContainer should inherit from Widget"

    def test_data_panel_is_widget_subclass(self) -> None:
        """DataPanel is a composable Widget."""
        from jdo.widgets.data_panel import DataPanel

        assert isinstance(DataPanel, type), "DataPanel should be a class"
        assert issubclass(DataPanel, Widget), "DataPanel should inherit from Widget"

    def test_prompt_input_is_widget_subclass(self) -> None:
        """PromptInput is a composable Widget."""
        from jdo.widgets.prompt_input import PromptInput

        assert isinstance(PromptInput, type), "PromptInput should be a class"
        assert issubclass(PromptInput, Widget), "PromptInput should inherit from Widget"

    def test_chat_message_is_widget_subclass(self) -> None:
        """ChatMessage is a composable Widget."""
        from jdo.widgets.chat_message import ChatMessage

        assert isinstance(ChatMessage, type), "ChatMessage should be a class"
        assert issubclass(ChatMessage, Widget), "ChatMessage should inherit from Widget"

    def test_hierarchy_view_is_widget_subclass(self) -> None:
        """HierarchyView is a composable Widget."""
        from jdo.widgets.hierarchy_view import HierarchyView

        assert isinstance(HierarchyView, type), "HierarchyView should be a class"
        assert issubclass(HierarchyView, Widget), "HierarchyView should inherit from Widget"


class TestScreenMessages:
    """Verify screens have proper message classes for parent communication."""

    def test_home_screen_has_new_chat_message(self) -> None:
        """HomeScreen has NewChat message class."""
        from jdo.screens.home import HomeScreen

        assert hasattr(HomeScreen, "NewChat"), "HomeScreen should have NewChat message"

    def test_home_screen_has_open_settings_message(self) -> None:
        """HomeScreen has OpenSettings message class."""
        from jdo.screens.home import HomeScreen

        assert hasattr(HomeScreen, "OpenSettings"), "HomeScreen should have OpenSettings message"

    def test_settings_screen_has_back_message(self) -> None:
        """SettingsScreen has Back message class."""
        from jdo.screens.settings import SettingsScreen

        assert hasattr(SettingsScreen, "Back"), "SettingsScreen should have Back message"

    def test_settings_screen_has_auth_status_changed_message(self) -> None:
        """SettingsScreen has AuthStatusChanged message class."""
        from jdo.screens.settings import SettingsScreen

        assert hasattr(SettingsScreen, "AuthStatusChanged"), (
            "SettingsScreen should have AuthStatusChanged message"
        )


class TestScreenComposition:
    """Verify screens compose the expected widgets."""

    async def test_home_screen_compose_yields_widgets(self) -> None:
        """HomeScreen.compose() yields expected widget structure."""
        from textual.containers import Container, Vertical
        from textual.widgets import Static

        from jdo.screens.home import HomeScreen

        app = create_test_app_for_screen(HomeScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            # Should have welcome container and box
            assert screen.query_one("#welcome-container", Container) is not None
            assert screen.query_one("#welcome-box", Vertical) is not None
            # Should have static content
            statics = screen.query(Static)
            assert len(statics) > 0, "HomeScreen should have Static widgets"

    async def test_chat_screen_compose_yields_widgets(self) -> None:
        """ChatScreen.compose() yields ChatContainer, PromptInput, DataPanel."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.chat_container import ChatContainer
        from jdo.widgets.data_panel import DataPanel
        from jdo.widgets.prompt_input import PromptInput

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert screen.query_one(ChatContainer) is not None
            assert screen.query_one(PromptInput) is not None
            assert screen.query_one(DataPanel) is not None

    async def test_settings_screen_compose_yields_widgets(self) -> None:
        """SettingsScreen.compose() yields expected widget structure."""
        from textual.containers import Container, Vertical
        from textual.widgets import Static

        from jdo.screens.settings import SettingsScreen

        app = create_test_app_for_screen(SettingsScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            # Should have settings container and box
            assert screen.query_one("#settings-container", Container) is not None
            assert screen.query_one("#settings-box", Vertical) is not None
            # Should have static content
            statics = screen.query(Static)
            assert len(statics) > 0, "SettingsScreen should have Static widgets"
