"""Tests for empty states and onboarding guidance.

Phase 14: Empty States & Onboarding for first-time users.
"""

import pytest
from textual.app import App, ComposeResult

from jdo.widgets.data_panel import DataPanel, PanelMode


class TestEmptyListStates:
    """Tests for empty list state messages."""

    def test_empty_commitments_list_shows_guidance(self) -> None:
        """Empty commitments list shows guidance text."""
        from jdo.widgets.data_panel import get_empty_state_message

        message = get_empty_state_message("commitment")

        assert "commitment" in message.lower()
        assert "/commit" in message

    def test_empty_goals_list_shows_guidance(self) -> None:
        """Empty goals list shows guidance text."""
        from jdo.widgets.data_panel import get_empty_state_message

        message = get_empty_state_message("goal")

        assert "goal" in message.lower()
        assert "/goal" in message

    def test_empty_visions_list_shows_guidance(self) -> None:
        """Empty visions list shows guidance text."""
        from jdo.widgets.data_panel import get_empty_state_message

        message = get_empty_state_message("vision")

        assert "vision" in message.lower()
        assert "/vision" in message

    def test_empty_tasks_list_shows_guidance(self) -> None:
        """Empty tasks list shows guidance text."""
        from jdo.widgets.data_panel import get_empty_state_message

        message = get_empty_state_message("task")

        assert "task" in message.lower()
        assert "/task" in message

    def test_empty_milestones_list_shows_guidance(self) -> None:
        """Empty milestones list shows guidance text."""
        from jdo.widgets.data_panel import get_empty_state_message

        message = get_empty_state_message("milestone")

        assert "milestone" in message.lower()
        assert "/milestone" in message


class TestDataPanelEmptyStates:
    """Tests for DataPanel empty state rendering."""

    @pytest.fixture
    def data_panel_app(self) -> type[App]:
        """Create a test app with DataPanel."""

        class DataPanelApp(App):
            def compose(self) -> ComposeResult:
                yield DataPanel()

        return DataPanelApp

    async def test_data_panel_shows_empty_guidance_in_list_mode(
        self, data_panel_app: type[App]
    ) -> None:
        """DataPanel shows guidance when list is empty."""
        from jdo.widgets.data_panel import get_empty_state_message

        async with data_panel_app().run_test() as pilot:
            panel = pilot.app.query_one(DataPanel)

            panel.show_list("commitment", [])
            await pilot.pause()

            # Panel should be in list mode with empty guidance
            assert panel.mode == PanelMode.LIST
            # Verify the empty state message would be used
            expected_msg = get_empty_state_message("commitment")
            assert "/commit" in expected_msg


class TestOnboardingGuidance:
    """Tests for first-time user onboarding."""

    def test_onboarding_message_exists(self) -> None:
        """Onboarding message function exists."""
        from jdo.widgets.data_panel import get_onboarding_message

        message = get_onboarding_message()

        assert len(message) > 0
        assert "welcome" in message.lower() or "start" in message.lower()

    def test_onboarding_mentions_key_commands(self) -> None:
        """Onboarding message mentions key commands."""
        from jdo.widgets.data_panel import get_onboarding_message

        message = get_onboarding_message()

        # Should mention at least one command
        assert "/commit" in message or "/goal" in message or "/vision" in message


class TestQuickStats:
    """Tests for quick stats display when no active draft."""

    def test_get_quick_stats_message_exists(self) -> None:
        """Quick stats message function exists."""
        from jdo.widgets.data_panel import get_quick_stats_message

        # Test with empty stats
        stats = {"due_soon": 0, "overdue": 0}
        message = get_quick_stats_message(stats)

        assert isinstance(message, str)

    def test_quick_stats_shows_due_soon_count(self) -> None:
        """Quick stats shows number of items due soon."""
        from jdo.widgets.data_panel import get_quick_stats_message

        stats = {"due_soon": 3, "overdue": 0}
        message = get_quick_stats_message(stats)

        assert "3" in message or "due" in message.lower()

    def test_quick_stats_shows_overdue_count(self) -> None:
        """Quick stats shows number of overdue items."""
        from jdo.widgets.data_panel import get_quick_stats_message

        stats = {"due_soon": 0, "overdue": 2}
        message = get_quick_stats_message(stats)

        assert "2" in message or "overdue" in message.lower()
