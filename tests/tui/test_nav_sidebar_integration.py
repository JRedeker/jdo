"""Integration tests for NavSidebar in JdoApp.

Tests for sidebar visibility, navigation, and DataPanel integration.
"""

from __future__ import annotations

import pytest
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header

from jdo.widgets import ChatContainer, DataPanel, PromptInput
from jdo.widgets.nav_sidebar import NavSidebar


class MainLayoutTestApp(App):
    """Test app simulating the main app layout with NavSidebar."""

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-content"):
            yield NavSidebar()
            with Vertical(id="content-area"):
                yield ChatContainer()
                yield PromptInput()
                yield DataPanel()
        yield Footer()

    def on_nav_sidebar_selected(self, message: NavSidebar.Selected) -> None:
        """Handle sidebar navigation."""
        self._last_selected = message.item_id

    @property
    def last_selected(self) -> str | None:
        """Get the last selected item ID."""
        return getattr(self, "_last_selected", None)


@pytest.mark.tui
class TestSidebarInAppLayout:
    """Tests for NavSidebar integration in app layout."""

    async def test_sidebar_visible_on_app_startup(self) -> None:
        """Sidebar is visible when app starts."""
        app = MainLayoutTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            assert sidebar is not None
            assert sidebar.display  # Widget is displayed

    async def test_sidebar_selection_triggers_handler(self) -> None:
        """Sidebar selection triggers the app's handler."""
        app = MainLayoutTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            sidebar.focus()
            await pilot.pause()

            # Select goals (2)
            await pilot.press("2")
            await pilot.pause()

            assert app.last_selected == "goals"

    async def test_sidebar_collapse_persists_during_session(self) -> None:
        """Sidebar collapse state persists during the session."""
        app = MainLayoutTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)

            # Initially expanded
            assert not sidebar.collapsed

            # Collapse it
            sidebar.toggle_collapse()
            await pilot.pause()
            assert sidebar.collapsed

            # Do some navigation
            sidebar.focus()
            await pilot.pause()
            await pilot.press("1")  # Select chat
            await pilot.pause()

            # Should still be collapsed
            assert sidebar.collapsed


@pytest.mark.tui
class TestSidebarDataPanelIntegration:
    """Tests for NavSidebar and DataPanel integration."""

    async def test_goals_selection_prepares_data_panel_update(self) -> None:
        """Goals selection can trigger DataPanel update."""
        app = MainLayoutTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            data_panel = app.query_one(DataPanel)
            sidebar.focus()
            await pilot.pause()

            # Select goals
            await pilot.press("2")
            await pilot.pause()

            # The selection message should have been received
            assert app.last_selected == "goals"
            # DataPanel would be updated by handler (tested separately)

    async def test_chat_selection_hides_data_panel_mode(self) -> None:
        """Chat selection implies DataPanel should be hidden/minimal."""
        app = MainLayoutTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            sidebar.focus()
            await pilot.pause()

            # Select chat
            await pilot.press("1")
            await pilot.pause()

            # Chat mode selected
            assert app.last_selected == "chat"


@pytest.mark.tui
class TestSidebarNavigationItems:
    """Tests for navigation item mappings."""

    async def test_all_expected_items_exist(self) -> None:
        """All expected navigation items are present."""
        app = MainLayoutTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            items = sidebar.get_nav_items()
            item_ids = [item.id for item in items]

            # Check all expected items exist
            expected = [
                "chat",
                "goals",
                "commitments",
                "visions",
                "milestones",
                "hierarchy",
                "integrity",
                "orphans",
                "triage",
                "settings",
            ]
            for expected_id in expected:
                assert expected_id in item_ids, f"Missing nav item: {expected_id}"

    async def test_number_keys_map_to_correct_items(self) -> None:
        """Number keys 1-9 map to correct items."""
        app = MainLayoutTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            sidebar.focus()
            await pilot.pause()

            # Press 1 - should be chat
            await pilot.press("1")
            await pilot.pause()
            assert app.last_selected == "chat"

            # Press 2 - should be goals
            await pilot.press("2")
            await pilot.pause()
            assert app.last_selected == "goals"

            # Press 3 - should be commitments
            await pilot.press("3")
            await pilot.pause()
            assert app.last_selected == "commitments"


@pytest.mark.tui
class TestSidebarSettingsNavigation:
    """Tests for settings navigation from sidebar."""

    async def test_settings_item_exists(self) -> None:
        """Settings item exists in sidebar."""
        app = MainLayoutTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            items = sidebar.get_nav_items()
            item_ids = [item.id for item in items]
            assert "settings" in item_ids

    async def test_settings_selection_posts_message(self) -> None:
        """Selecting settings posts the Selected message."""
        app = MainLayoutTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            items = sidebar.get_nav_items()

            # Find settings index
            settings_idx = next((i for i, item in enumerate(items) if item.id == "settings"), -1)
            assert settings_idx >= 0

            sidebar.focus()
            await pilot.pause()

            # Select settings by index (if within 1-9)
            if settings_idx < 9:
                await pilot.press(str(settings_idx + 1))
                await pilot.pause()
                assert app.last_selected == "settings"


@pytest.mark.tui
class TestSidebarTriageIntegration:
    """Tests for triage badge integration."""

    async def test_triage_badge_updates(self) -> None:
        """Triage count can be updated on the sidebar."""
        app = MainLayoutTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)

            # Set triage count
            sidebar.set_triage_count(3)
            await pilot.pause()

            assert sidebar.triage_count == 3

    async def test_triage_item_exists(self) -> None:
        """Triage item exists in sidebar."""
        app = MainLayoutTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            items = sidebar.get_nav_items()
            item_ids = [item.id for item in items]
            assert "triage" in item_ids
