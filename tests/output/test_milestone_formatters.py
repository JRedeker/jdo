"""Tests for the milestone formatters module."""

from datetime import date
from unittest.mock import MagicMock
from uuid import uuid4

from rich.panel import Panel
from rich.table import Table

from jdo.models.milestone import MilestoneStatus
from jdo.output.milestone import (
    MILESTONE_STATUS_COLORS,
    format_milestone_detail,
    format_milestone_list,
    format_milestone_list_plain,
    format_milestone_proposal,
    get_milestone_status_color,
)


class TestGetMilestoneStatusColor:
    """Tests for milestone status color mapping."""

    def test_pending_status(self):
        """Pending status returns default."""
        assert get_milestone_status_color("pending") == "default"
        assert get_milestone_status_color(MilestoneStatus.PENDING) == "default"

    def test_in_progress_status(self):
        """In progress status returns blue."""
        assert get_milestone_status_color("in_progress") == "blue"
        assert get_milestone_status_color(MilestoneStatus.IN_PROGRESS) == "blue"

    def test_completed_status(self):
        """Completed status returns green."""
        assert get_milestone_status_color("completed") == "green"
        assert get_milestone_status_color(MilestoneStatus.COMPLETED) == "green"

    def test_missed_status(self):
        """Missed status returns red."""
        assert get_milestone_status_color("missed") == "red"
        assert get_milestone_status_color(MilestoneStatus.MISSED) == "red"

    def test_unknown_status(self):
        """Unknown status returns default."""
        assert get_milestone_status_color("unknown") == "default"


class TestFormatMilestoneList:
    """Tests for milestone list formatting."""

    def test_empty_list_returns_table(self):
        """Empty list returns empty table."""
        table = format_milestone_list([])
        assert isinstance(table, Table)

    def test_table_has_expected_columns(self):
        """Table has expected columns."""
        table = format_milestone_list([])
        column_names = [col.header for col in table.columns]
        assert "ID" in column_names
        assert "Title" in column_names
        assert "Target Date" in column_names
        assert "Status" in column_names
        assert "Goal" in column_names


class TestFormatMilestoneDetail:
    """Tests for milestone detail formatting."""

    def test_returns_panel(self):
        """Detail view returns a Panel."""
        milestone = MagicMock()
        milestone.id = uuid4()
        milestone.title = "Test Milestone"
        milestone.target_date = date(2025, 6, 1)
        milestone.status = MilestoneStatus.PENDING
        milestone.description = None
        milestone.completed_at = None
        # Ensure no goal relationship is present to avoid mock issues
        milestone.goal = None

        panel = format_milestone_detail(milestone)
        assert isinstance(panel, Panel)


class TestFormatMilestoneProposal:
    """Tests for milestone proposal formatting."""

    def test_returns_panel(self):
        """Proposal returns a Panel."""
        panel = format_milestone_proposal(
            title="Complete Draft",
            target_date="2025-06-01",
        )
        assert isinstance(panel, Panel)

    def test_contains_title(self):
        """Panel contains title text."""
        panel = format_milestone_proposal(
            title="Complete first draft",
            target_date="2025-06-01",
        )
        content = str(panel.renderable)
        assert "Complete first draft" in content

    def test_contains_goal_when_provided(self):
        """Panel contains goal when provided."""
        panel = format_milestone_proposal(
            title="Complete Draft",
            target_date="2025-06-01",
            goal_title="Write a book",
        )
        content = str(panel.renderable)
        assert "Write a book" in content

    def test_contains_confirmation_prompt(self):
        """Panel contains confirmation prompt."""
        panel = format_milestone_proposal(
            title="Milestone",
            target_date="2025-06-01",
        )
        content = str(panel.renderable)
        assert "Does this look right?" in content


class TestFormatMilestoneListPlain:
    """Tests for plain text milestone list formatting."""

    def test_empty_list(self):
        """Empty list returns friendly message."""
        result = format_milestone_list_plain([])
        assert "No milestone" in result

    def test_single_milestone(self):
        """Single milestone is formatted correctly."""
        milestones = [
            {
                "id": "1",
                "title": "Complete draft",
                "target_date": "2025-06-01",
                "status": "pending",
            }
        ]
        result = format_milestone_list_plain(milestones)
        assert "Complete draft" in result
        assert "2025-06-01" in result


class TestMilestoneStatusColors:
    """Tests for MILESTONE_STATUS_COLORS constant."""

    def test_all_statuses_have_colors(self):
        """All milestone statuses have colors defined."""
        for status in MilestoneStatus:
            assert status.value in MILESTONE_STATUS_COLORS
