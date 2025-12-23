"""Tests for NavSidebar widget - TDD Red phase.

Tests for the navigation sidebar widget that provides persistent navigation.
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import OptionList

from jdo.widgets.nav_sidebar import NavItem, NavSidebar


class NavSidebarTestApp(App):
    """Test app for NavSidebar widget."""

    def __init__(self) -> None:
        super().__init__()
        self.selected_items: list[str] = []

    def compose(self) -> ComposeResult:
        yield NavSidebar()

    def on_nav_sidebar_selected(self, message: NavSidebar.Selected) -> None:
        """Track selected items for testing."""
        self.selected_items.append(message.item_id)


class TestNavSidebarBasics:
    """Basic tests for NavSidebar widget."""

    async def test_widget_renders_with_expected_navigation_items(self) -> None:
        """NavSidebar renders with all expected navigation items."""
        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()  # Wait for compose to complete
            sidebar = app.query_one(NavSidebar)
            option_list = sidebar.query_one(OptionList)

            # Check that we have the expected items
            # Expected: chat, goals, commitments, visions, milestones,
            #           hierarchy, integrity, orphans, triage, settings
            # 10 items total (not counting separators)
            assert option_list.option_count >= 9  # At least 9 navigation items

    async def test_widget_contains_option_list(self) -> None:
        """NavSidebar contains an OptionList widget."""
        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            option_list = sidebar.query_one(OptionList)
            assert option_list is not None

    async def test_up_down_keys_navigate_items(self) -> None:
        """Up/down arrow keys navigate between items."""
        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            option_list = sidebar.query_one(OptionList)
            option_list.focus()
            await pilot.pause()

            # Press down to highlight first item (OptionList starts with nothing highlighted)
            await pilot.press("down")
            await pilot.pause()

            # Should now have first item highlighted
            first_index = option_list.highlighted
            assert first_index is not None

            # Press down again to move to next item
            await pilot.press("down")
            await pilot.pause()

            # Should have moved to next item
            second_index = option_list.highlighted
            assert second_index is not None
            assert second_index != first_index

            # Press up to go back
            await pilot.press("up")
            await pilot.pause()

            # Should be back at first item
            assert option_list.highlighted == first_index

    async def test_enter_key_posts_selected_message(self) -> None:
        """Enter key posts Selected message with correct item_id."""
        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            option_list = sidebar.query_one(OptionList)
            option_list.focus()
            await pilot.pause()

            # First navigate to highlight an item (OptionList starts empty)
            await pilot.press("down")
            await pilot.pause()

            # Press enter to select current item
            await pilot.press("enter")
            await pilot.pause()

            # Should have received a selected message
            assert len(app.selected_items) == 1
            # First item should be "chat"
            assert app.selected_items[0] == "chat"

    async def test_number_keys_select_items_directly(self) -> None:
        """Number keys (1-9, 0) select items directly by position."""
        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            sidebar.focus()
            await pilot.pause()

            # Press 1 to select first item (chat)
            await pilot.press("1")
            await pilot.pause()
            assert len(app.selected_items) >= 1
            assert app.selected_items[-1] == "chat"

            # Press 2 to select second item (goals)
            await pilot.press("2")
            await pilot.pause()
            assert len(app.selected_items) >= 2
            assert app.selected_items[-1] == "goals"

            # Press 3 to select third item (commitments)
            await pilot.press("3")
            await pilot.pause()
            assert len(app.selected_items) >= 3
            assert app.selected_items[-1] == "commitments"

            # Press 9 to select triage
            await pilot.press("9")
            await pilot.pause()
            assert app.selected_items[-1] == "triage"

            # Press 0 to select settings (10th item)
            await pilot.press("0")
            await pilot.pause()
            assert app.selected_items[-1] == "settings"


class TestNavSidebarCollapse:
    """Tests for NavSidebar collapse functionality."""

    async def test_collapse_toggle_changes_display_mode(self) -> None:
        """Collapse toggle changes the sidebar width."""
        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)

            # Initially expanded
            assert not sidebar.collapsed

            # Toggle collapse
            sidebar.toggle_collapse()
            await pilot.pause()

            # Should be collapsed
            assert sidebar.collapsed

            # Toggle again
            sidebar.toggle_collapse()
            await pilot.pause()

            # Should be expanded again
            assert not sidebar.collapsed

    async def test_bracket_key_toggles_collapse(self) -> None:
        """Left bracket key toggles collapse state."""
        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            sidebar.focus()
            await pilot.pause()

            # Initially expanded
            assert not sidebar.collapsed

            # Press [ to collapse
            await pilot.press("[")
            await pilot.pause()

            # Should be collapsed
            assert sidebar.collapsed

    async def test_collapsed_mode_shows_single_letters(self) -> None:
        """Collapsed mode shows single-letter shortcuts."""
        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            sidebar.toggle_collapse()
            await pilot.pause()

            # Should have collapsed class
            assert sidebar.has_class("-collapsed")


class TestNavSidebarItems:
    """Tests for NavSidebar navigation items."""

    async def test_has_chat_item(self) -> None:
        """NavSidebar has 'chat' navigation item."""
        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            items = sidebar.get_nav_items()
            item_ids = [item.id for item in items]
            assert "chat" in item_ids

    async def test_has_goals_item(self) -> None:
        """NavSidebar has 'goals' navigation item."""
        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            items = sidebar.get_nav_items()
            item_ids = [item.id for item in items]
            assert "goals" in item_ids

    async def test_has_commitments_item(self) -> None:
        """NavSidebar has 'commitments' navigation item."""
        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            items = sidebar.get_nav_items()
            item_ids = [item.id for item in items]
            assert "commitments" in item_ids

    async def test_has_settings_item(self) -> None:
        """NavSidebar has 'settings' navigation item."""
        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            items = sidebar.get_nav_items()
            item_ids = [item.id for item in items]
            assert "settings" in item_ids

    async def test_has_hierarchy_item(self) -> None:
        """NavSidebar has 'hierarchy' navigation item."""
        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            items = sidebar.get_nav_items()
            item_ids = [item.id for item in items]
            assert "hierarchy" in item_ids

    async def test_has_integrity_item(self) -> None:
        """NavSidebar has 'integrity' navigation item."""
        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            items = sidebar.get_nav_items()
            item_ids = [item.id for item in items]
            assert "integrity" in item_ids

    async def test_nav_item_has_id_label_and_shortcut(self) -> None:
        """NavItem has id, label, and shortcut attributes."""
        item = NavItem(id="test", label="Test Item", shortcut="t")
        assert item.id == "test"
        assert item.label == "Test Item"
        assert item.shortcut == "t"


class TestNavSidebarMessage:
    """Tests for NavSidebar.Selected message."""

    async def test_selected_message_has_item_id(self) -> None:
        """Selected message includes the selected item's ID."""
        message = NavSidebar.Selected(item_id="goals")
        assert message.item_id == "goals"

    async def test_selecting_different_items_posts_correct_ids(self) -> None:
        """Selecting different items posts messages with correct IDs."""
        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            sidebar.focus()
            await pilot.pause()

            # Select goals (2)
            await pilot.press("2")
            await pilot.pause()
            assert "goals" in app.selected_items

            # Select settings (9 or similar)
            # First navigate to find settings position
            items = sidebar.get_nav_items()
            settings_idx = next((i for i, item in enumerate(items) if item.id == "settings"), -1)
            if settings_idx >= 0 and settings_idx < 9:
                await pilot.press(str(settings_idx + 1))
                await pilot.pause()
                assert "settings" in app.selected_items


class TestNavSidebarActiveState:
    """Tests for NavSidebar active item state."""

    async def test_set_active_item_highlights_item(self) -> None:
        """set_active_item highlights the specified item."""
        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)

            # Set goals as active
            sidebar.set_active_item("goals")
            await pilot.pause()

            # Check that goals is now the highlighted item
            assert sidebar.active_item == "goals"

    async def test_set_active_item_uses_correct_option_list_index(self) -> None:
        """set_active_item highlights correct OptionList index for selectable options."""
        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            option_list = sidebar.query_one(OptionList)

            # OptionList.highlighted uses selectable option indices (excludes separators)
            # So the index matches _nav_items index directly
            sidebar.set_active_item("goals")
            await pilot.pause()
            assert option_list.highlighted == 1  # goals is index 1 in _nav_items

            sidebar.set_active_item("hierarchy")
            await pilot.pause()
            assert option_list.highlighted == 5  # hierarchy is index 5 in _nav_items

            sidebar.set_active_item("settings")
            await pilot.pause()
            assert option_list.highlighted == 9  # settings is index 9 in _nav_items

    async def test_active_item_persists_after_selection(self) -> None:
        """Active item updates after selection."""
        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            sidebar.focus()
            await pilot.pause()

            # Select goals via number key
            await pilot.press("2")
            await pilot.pause()

            # Active item should be goals
            assert sidebar.active_item == "goals"


class TestNavSidebarTriageBadge:
    """Tests for triage badge functionality."""

    async def test_set_triage_count_shows_badge(self) -> None:
        """set_triage_count shows badge when count > 0."""
        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)

            # Set triage count
            sidebar.set_triage_count(5)
            await pilot.pause()

            # Should have triage count stored
            assert sidebar.triage_count == 5

    async def test_zero_triage_count_hides_badge(self) -> None:
        """Triage badge hidden when count is 0."""
        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)

            # Set then clear triage count
            sidebar.set_triage_count(5)
            sidebar.set_triage_count(0)
            await pilot.pause()

            assert sidebar.triage_count == 0


class TestIntegritySummaryWidget:
    """Tests for IntegritySummary widget in NavSidebar."""

    async def test_integrity_summary_present_in_sidebar(self) -> None:
        """NavSidebar contains an IntegritySummary widget."""
        from jdo.widgets.integrity_summary import IntegritySummary

        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            summary = sidebar.query_one(IntegritySummary)
            assert summary is not None

    async def test_integrity_summary_default_values(self) -> None:
        """IntegritySummary shows default values when not updated."""
        from jdo.widgets.integrity_summary import IntegritySummary

        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            summary = sidebar.query_one(IntegritySummary)
            assert summary.grade == "--"
            assert summary.score == 0.0

    async def test_update_integrity_updates_summary(self) -> None:
        """update_integrity method updates the IntegritySummary widget."""
        from jdo.models.integrity_metrics import IntegrityMetrics

        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)

            # Create mock metrics
            metrics = IntegrityMetrics(
                on_time_rate=0.9,
                notification_timeliness=0.85,
                cleanup_completion_rate=0.8,
                current_streak_weeks=2,
                total_completed=10,
                total_on_time=9,
                total_at_risk=1,
                total_abandoned=0,
            )

            sidebar.update_integrity(metrics)
            await pilot.pause()

            from jdo.widgets.integrity_summary import IntegritySummary

            summary = sidebar.query_one(IntegritySummary)
            # Should show B+ grade (score ~88)
            assert summary.grade.startswith("B") or summary.grade.startswith("A")
            assert summary.score > 80

    async def test_collapsed_sidebar_collapses_summary(self) -> None:
        """Collapsing sidebar collapses IntegritySummary display."""
        from jdo.widgets.integrity_summary import IntegritySummary

        app = NavSidebarTestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            sidebar = app.query_one(NavSidebar)
            summary = sidebar.query_one(IntegritySummary)

            # Initially not collapsed
            assert not summary.collapsed

            # Collapse sidebar
            sidebar.toggle_collapse()
            await pilot.pause()

            # Summary should also be collapsed
            assert summary.collapsed
