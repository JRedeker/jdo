"""Tests for the output formatters module."""

from datetime import UTC, date, datetime, time
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from rich.panel import Panel
from rich.table import Table

from jdo.models.commitment import Commitment, CommitmentStatus
from jdo.output.formatters import (
    STATUS_COLORS,
    format_commitment_detail,
    format_commitment_list,
    format_commitment_list_plain,
    format_commitment_proposal,
    format_commitment_summary,
    format_date,
    format_empty_list,
    format_error,
    format_milestones_plain,
    format_overdue_commitments_plain,
    format_relative_date,
    format_success,
    format_visions_plain,
    get_status_color,
)


class TestGetStatusColor:
    """Tests for status color mapping."""

    def test_pending_status(self):
        """Pending status returns default color."""
        assert get_status_color("pending") == "default"
        assert get_status_color(CommitmentStatus.PENDING) == "default"

    def test_in_progress_status(self):
        """In progress status returns blue."""
        assert get_status_color("in_progress") == "blue"
        assert get_status_color(CommitmentStatus.IN_PROGRESS) == "blue"

    def test_completed_status(self):
        """Completed status returns green."""
        assert get_status_color("completed") == "green"
        assert get_status_color(CommitmentStatus.COMPLETED) == "green"

    def test_at_risk_status(self):
        """At risk status returns yellow."""
        assert get_status_color("at_risk") == "yellow"
        assert get_status_color(CommitmentStatus.AT_RISK) == "yellow"

    def test_abandoned_status(self):
        """Abandoned status returns red."""
        assert get_status_color("abandoned") == "red"
        assert get_status_color(CommitmentStatus.ABANDONED) == "red"

    def test_unknown_status(self):
        """Unknown status returns default."""
        assert get_status_color("unknown") == "default"

    def test_case_insensitive(self):
        """Status matching is case insensitive."""
        assert get_status_color("PENDING") == "default"
        assert get_status_color("Completed") == "green"


class TestFormatDate:
    """Tests for date formatting."""

    def test_none_returns_na(self):
        """None date returns N/A."""
        assert format_date(None) == "N/A"

    def test_date_format(self):
        """Date formats as YYYY-MM-DD."""
        d = date(2025, 1, 15)
        assert format_date(d) == "2025-01-15"

    def test_datetime_format(self):
        """Datetime formats with time."""
        dt = datetime(2025, 1, 15, 14, 30, tzinfo=UTC)
        assert format_date(dt) == "2025-01-15 14:30"


class TestFormatCommitmentList:
    """Tests for commitment list formatting."""

    def test_empty_list_returns_table(self):
        """Empty list returns empty table."""
        table = format_commitment_list([])
        assert isinstance(table, Table)

    def test_table_has_expected_columns(self):
        """Table has expected columns."""
        table = format_commitment_list([])

        # Check column names
        column_names = [col.header for col in table.columns]
        assert "ID" in column_names
        assert "Deliverable" in column_names
        assert "Stakeholder" in column_names
        assert "Due" in column_names
        assert "Status" in column_names


class TestFormatCommitmentDetail:
    """Tests for commitment detail formatting."""

    def test_returns_panel(self):
        """Detail view returns a Panel."""
        # Create mock commitment
        commitment = MagicMock(spec=Commitment)
        commitment.id = uuid4()
        commitment.deliverable = "Test deliverable"
        commitment.stakeholder = MagicMock()
        commitment.stakeholder.name = "Test Stakeholder"
        commitment.due_date = date(2025, 1, 15)
        commitment.status = CommitmentStatus.PENDING
        commitment.goal = None

        panel = format_commitment_detail(commitment)
        assert isinstance(panel, Panel)


class TestFormatEmptyList:
    """Tests for empty list messages."""

    def test_commitment_message(self):
        """Commitment empty message is friendly."""
        msg = format_empty_list("commitment")
        assert "commitment" in msg.lower()

    def test_goal_message(self):
        """Goal empty message is friendly."""
        msg = format_empty_list("goal")
        assert "goal" in msg.lower()

    def test_task_message(self):
        """Task empty message is friendly."""
        msg = format_empty_list("task")
        assert "task" in msg.lower()

    def test_vision_message(self):
        """Vision empty message is friendly."""
        msg = format_empty_list("vision")
        assert "vision" in msg.lower()

    def test_milestone_message(self):
        """Milestone empty message is friendly."""
        msg = format_empty_list("milestone")
        assert "milestone" in msg.lower()

    def test_unknown_type(self):
        """Unknown type returns generic message."""
        msg = format_empty_list("unknown")
        assert "unknown" in msg.lower()

    def test_case_insensitive(self):
        """Entity type matching is case insensitive."""
        msg1 = format_empty_list("COMMITMENT")
        msg2 = format_empty_list("commitment")
        assert msg1 == msg2


class TestStatusColors:
    """Tests for STATUS_COLORS constant."""

    def test_all_statuses_have_colors(self):
        """All commitment statuses have colors defined."""
        for status in CommitmentStatus:
            assert status.value in STATUS_COLORS


class TestFormatCommitmentProposal:
    """Tests for commitment proposal formatting."""

    def test_returns_panel(self):
        """Proposal returns a Panel."""
        panel = format_commitment_proposal(
            deliverable="Send report",
            stakeholder="Sarah",
            due_date=date(2025, 1, 15),
        )
        assert isinstance(panel, Panel)

    def test_contains_deliverable(self):
        """Panel contains deliverable text."""
        panel = format_commitment_proposal(
            deliverable="Send quarterly report",
            stakeholder="Sarah",
            due_date=date(2025, 1, 15),
        )
        # Check the renderable content contains deliverable
        content = str(panel.renderable)
        assert "quarterly report" in content

    def test_contains_stakeholder(self):
        """Panel contains stakeholder name."""
        panel = format_commitment_proposal(
            deliverable="Send report",
            stakeholder="Sarah Johnson",
            due_date=date(2025, 1, 15),
        )
        content = str(panel.renderable)
        assert "Sarah Johnson" in content

    def test_contains_due_date(self):
        """Panel contains formatted due date."""
        panel = format_commitment_proposal(
            deliverable="Send report",
            stakeholder="Sarah",
            due_date=date(2025, 1, 15),
        )
        content = str(panel.renderable)
        assert "2025-01-15" in content

    def test_contains_due_time_when_provided(self):
        """Panel contains due time when provided."""
        panel = format_commitment_proposal(
            deliverable="Send report",
            stakeholder="Sarah",
            due_date=date(2025, 1, 15),
            due_time="3:00 PM",
        )
        content = str(panel.renderable)
        assert "3:00 PM" in content

    def test_contains_goal_when_provided(self):
        """Panel contains goal title when provided."""
        panel = format_commitment_proposal(
            deliverable="Send report",
            stakeholder="Sarah",
            due_date=date(2025, 1, 15),
            goal_title="Quarterly Reporting",
        )
        content = str(panel.renderable)
        assert "Quarterly Reporting" in content

    def test_contains_confirmation_prompt(self):
        """Panel contains confirmation prompt."""
        panel = format_commitment_proposal(
            deliverable="Send report",
            stakeholder="Sarah",
            due_date=date(2025, 1, 15),
        )
        content = str(panel.renderable)
        assert "Does this look right?" in content

    def test_handles_none_due_date(self):
        """Panel handles None due date gracefully."""
        panel = format_commitment_proposal(
            deliverable="Send report",
            stakeholder="Sarah",
            due_date=None,
        )
        content = str(panel.renderable)
        assert "N/A" in content


class TestFormatCommitmentListPlain:
    """Tests for plain text commitment list formatting."""

    def test_empty_list(self):
        """Empty list returns friendly message."""
        result = format_commitment_list_plain([])
        assert "No commitment" in result

    def test_single_commitment(self):
        """Single commitment is formatted correctly."""
        commitments = [
            {
                "id": "123",
                "deliverable": "Send report",
                "stakeholder_name": "Sarah",
                "due_date": "2025-01-15",
                "status": "pending",
            }
        ]
        result = format_commitment_list_plain(commitments)
        assert "Send report" in result
        assert "Sarah" in result
        assert "2025-01-15" in result
        assert "pending" in result

    def test_multiple_commitments(self):
        """Multiple commitments are all included."""
        commitments = [
            {
                "id": "1",
                "deliverable": "First task",
                "stakeholder_name": "Alice",
                "due_date": "2025-01-15",
                "status": "pending",
            },
            {
                "id": "2",
                "deliverable": "Second task",
                "stakeholder_name": "Bob",
                "due_date": "2025-01-20",
                "status": "in_progress",
            },
        ]
        result = format_commitment_list_plain(commitments)
        assert "First task" in result
        assert "Second task" in result
        assert "Alice" in result
        assert "Bob" in result

    def test_handles_missing_fields(self):
        """Missing fields show as N/A."""
        commitments = [{"id": "123"}]
        result = format_commitment_list_plain(commitments)
        assert "N/A" in result


class TestFormatOverdueCommitmentsPlain:
    """Tests for overdue commitments plain text formatting."""

    def test_empty_list(self):
        """Empty list returns positive message."""
        result = format_overdue_commitments_plain([])
        assert "No overdue" in result
        assert "Great job" in result

    def test_single_overdue_commitment(self):
        """Single overdue commitment shows days overdue."""
        commitments = [
            {
                "id": "1",
                "deliverable": "Late report",
                "stakeholder_name": "Boss",
                "due_date": "2025-01-10",
                "status": "pending",
                "days_overdue": 5,
            }
        ]
        result = format_overdue_commitments_plain(commitments)
        assert "Late report" in result
        assert "5 days overdue" in result
        assert "Boss" in result

    def test_header_present(self):
        """Output includes OVERDUE header."""
        commitments = [{"id": "1", "deliverable": "Late", "days_overdue": 1}]
        result = format_overdue_commitments_plain(commitments)
        assert "OVERDUE" in result


class TestFormatVisionsPlain:
    """Tests for visions plain text formatting."""

    def test_empty_list(self):
        """Empty list returns friendly message."""
        result = format_visions_plain([])
        assert "No vision" in result

    def test_single_vision(self):
        """Single vision is formatted correctly."""
        visions = [
            {
                "id": "1",
                "title": "Published Author",
                "timeframe": "5 years",
                "narrative": "I see myself as a published author with multiple books.",
            }
        ]
        result = format_visions_plain(visions)
        assert "Published Author" in result
        assert "5 years" in result

    def test_vision_with_review_overdue(self):
        """Vision shows days overdue for review."""
        visions = [
            {
                "id": "1",
                "title": "My Vision",
                "days_overdue": 10,
            }
        ]
        result = format_visions_plain(visions)
        assert "10 days" in result


class TestFormatMilestonesPlain:
    """Tests for milestones plain text formatting."""

    def test_empty_list(self):
        """Empty list returns friendly message."""
        result = format_milestones_plain([])
        assert "No milestone" in result

    def test_single_milestone(self):
        """Single milestone is formatted correctly."""
        milestones = [
            {
                "id": "1",
                "title": "Complete draft",
                "target_date": "2025-03-01",
                "status": "pending",
                "description": "Complete the first draft of the manuscript",
            }
        ]
        result = format_milestones_plain(milestones)
        assert "Complete draft" in result
        assert "2025-03-01" in result
        assert "pending" in result


class TestFormatRelativeDate:
    """Tests for relative date formatting."""

    def test_today(self):
        """Same day returns 'Today'."""
        today = date(2025, 1, 15)
        assert format_relative_date(today, today=today) == "Today"

    def test_tomorrow(self):
        """Next day returns 'Tomorrow'."""
        today = date(2025, 1, 15)
        tomorrow = date(2025, 1, 16)
        assert format_relative_date(tomorrow, today=today) == "Tomorrow"

    def test_same_week_shows_weekday(self):
        """2-6 days out shows abbreviated weekday name."""
        today = date(2025, 1, 15)  # Wednesday

        # Thursday (1 day out is Tomorrow, so test 2 days)
        friday = date(2025, 1, 17)
        assert format_relative_date(friday, today=today) == "Fri"

        # Monday (5 days out)
        monday = date(2025, 1, 20)
        assert format_relative_date(monday, today=today) == "Mon"

        # Tuesday (6 days out - still within week range)
        tuesday = date(2025, 1, 21)
        assert format_relative_date(tuesday, today=today) == "Tue"

    def test_beyond_week_shows_in_x_days(self):
        """7+ days out shows 'in X days'."""
        today = date(2025, 1, 15)

        # 7 days out
        week_later = date(2025, 1, 22)
        assert format_relative_date(week_later, today=today) == "in 7 days"

        # 10 days out
        ten_days = date(2025, 1, 25)
        assert format_relative_date(ten_days, today=today) == "in 10 days"

    def test_past_date_shows_iso(self):
        """Past dates fall back to ISO format."""
        today = date(2025, 1, 15)
        yesterday = date(2025, 1, 14)
        assert format_relative_date(yesterday, today=today) == "2025-01-14"

    def test_default_today_uses_current_date(self):
        """Without explicit today, uses current date."""
        # This is hard to test deterministically, but we can at least
        # verify it doesn't crash
        result = format_relative_date(date(2099, 12, 31))
        assert "in " in result or result == "2099-12-31"


class TestFormatCommitmentSummary:
    """Tests for commitment summary panel formatting."""

    def test_no_commitments_returns_none(self):
        """Zero active commitments returns None."""
        result = format_commitment_summary(
            active_count=0,
            at_risk_count=0,
        )
        assert result is None

    def test_returns_panel_with_commitments(self):
        """Non-zero commitments returns a Panel."""
        result = format_commitment_summary(
            active_count=3,
            at_risk_count=0,
        )
        assert isinstance(result, Panel)

    def test_contains_active_count(self):
        """Panel contains active count."""
        result = format_commitment_summary(
            active_count=5,
            at_risk_count=0,
        )
        content = str(result.renderable)
        assert "5" in content
        assert "active" in content

    def test_contains_at_risk_count(self):
        """Panel contains at-risk count when > 0."""
        result = format_commitment_summary(
            active_count=3,
            at_risk_count=2,
        )
        content = str(result.renderable)
        assert "2" in content

    def test_contains_next_due_item(self):
        """Panel contains next due item when provided."""
        result = format_commitment_summary(
            active_count=3,
            at_risk_count=0,
            next_due_deliverable="Send report to Sarah",
            next_due_date=date(2025, 1, 17),
        )
        content = str(result.renderable)
        assert "Send report" in content  # Truncated
        assert "Next" in content

    def test_truncates_long_deliverable(self):
        """Long deliverables are truncated."""
        long_deliverable = "This is a very long deliverable that should be truncated"
        result = format_commitment_summary(
            active_count=1,
            at_risk_count=0,
            next_due_deliverable=long_deliverable,
            next_due_date=date(2025, 1, 17),
        )
        content = str(result.renderable)
        # Should be truncated with ellipsis
        assert "..." in content
        # Should not contain full deliverable
        assert long_deliverable not in content

    def test_no_next_due_section_without_data(self):
        """Panel omits 'Next:' section when no next due data."""
        result = format_commitment_summary(
            active_count=3,
            at_risk_count=1,
            next_due_deliverable=None,
            next_due_date=None,
        )
        content = str(result.renderable)
        assert "Next" not in content
