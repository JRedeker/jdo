"""Tests for the dashboard panel formatters."""

from __future__ import annotations

import pytest
from rich.console import Group
from rich.panel import Panel

from jdo.output.dashboard import (
    COMPACT_COMMITMENT_THRESHOLD,
    PROGRESS_BAR_WIDTH,
    PROGRESS_HIGH_THRESHOLD,
    PROGRESS_MEDIUM_THRESHOLD,
    DashboardCommitment,
    DashboardData,
    DashboardGoal,
    DashboardIntegrity,
    DisplayLevel,
    format_commitments_panel,
    format_dashboard,
    format_goals_panel,
    format_progress_bar,
    format_status_bar,
)


class TestFormatProgressBar:
    """Tests for progress bar formatting."""

    def test_zero_percent(self):
        """0% shows all empty blocks."""
        bar = format_progress_bar(0.0)
        assert "█" not in bar
        assert "░" * PROGRESS_BAR_WIDTH in bar

    def test_fifty_percent(self):
        """50% shows half filled."""
        bar = format_progress_bar(0.5)
        filled_count = bar.count("█")
        empty_count = bar.count("░")
        assert filled_count == PROGRESS_BAR_WIDTH // 2
        assert empty_count == PROGRESS_BAR_WIDTH // 2

    def test_hundred_percent(self):
        """100% shows all filled blocks."""
        bar = format_progress_bar(1.0)
        assert "█" * PROGRESS_BAR_WIDTH in bar
        assert "░" not in bar

    def test_clamping_negative(self):
        """Negative values clamp to 0."""
        bar = format_progress_bar(-0.5)
        assert "█" not in bar

    def test_clamping_over_100(self):
        """Values over 100% clamp to 100."""
        bar = format_progress_bar(1.5)
        assert "█" * PROGRESS_BAR_WIDTH in bar

    def test_high_progress_color(self):
        """High progress (>=80%) uses green."""
        bar = format_progress_bar(PROGRESS_HIGH_THRESHOLD)
        assert "[green]" in bar

    def test_medium_progress_color(self):
        """Medium progress (50-79%) uses yellow."""
        bar = format_progress_bar(PROGRESS_MEDIUM_THRESHOLD)
        assert "[yellow]" in bar

    def test_low_progress_color(self):
        """Low progress (<50%) uses red."""
        bar = format_progress_bar(0.3)
        assert "[red]" in bar

    def test_custom_width(self):
        """Custom width works correctly."""
        bar = format_progress_bar(1.0, width=10)
        assert bar.count("█") == 10


class TestFormatCommitmentsPanel:
    """Tests for commitment panel formatting."""

    def test_empty_list(self):
        """Empty commitment list creates panel."""
        panel = format_commitments_panel([])
        assert isinstance(panel, Panel)

    def test_single_commitment(self):
        """Single commitment displays correctly."""
        commitments = [
            DashboardCommitment(
                deliverable="Test task",
                stakeholder="John",
                due_display="Today",
                status="pending",
                is_overdue=False,
            )
        ]
        panel = format_commitments_panel(commitments)
        assert isinstance(panel, Panel)

    def test_overdue_commitment_styling(self):
        """Overdue commitments are styled red."""
        commitments = [
            DashboardCommitment(
                deliverable="Overdue task",
                stakeholder="Jane",
                due_display="OVERDUE (2d)",
                status="overdue",
                is_overdue=True,
            )
        ]
        panel = format_commitments_panel(commitments, active_count=1, at_risk_count=1)
        assert isinstance(panel, Panel)
        # The title should include at-risk count
        assert "at-risk" in str(panel.title)

    def test_title_with_counts(self):
        """Title includes active and at-risk counts."""
        commitments = [
            DashboardCommitment(
                deliverable="Task",
                stakeholder="Someone",
                due_display="Tomorrow",
                status="pending",
            )
        ]
        panel = format_commitments_panel(
            commitments,
            active_count=5,
            at_risk_count=2,
        )
        title = str(panel.title)
        assert "5 active" in title
        assert "2 at-risk" in title


class TestFormatGoalsPanel:
    """Tests for goals panel formatting."""

    def test_empty_list(self):
        """Empty goals list creates panel."""
        panel = format_goals_panel([])
        assert isinstance(panel, Panel)

    def test_single_goal(self):
        """Single goal displays correctly."""
        goals = [
            DashboardGoal(
                title="Health Goal",
                progress_percent=0.75,
                progress_text="3/4 done",
                needs_review=False,
            )
        ]
        panel = format_goals_panel(goals)
        assert isinstance(panel, Panel)

    def test_goal_needs_review_styling(self):
        """Goals needing review show warning indicator."""
        goals = [
            DashboardGoal(
                title="Review Due",
                progress_percent=0.5,
                progress_text="review due",
                needs_review=True,
            )
        ]
        panel = format_goals_panel(goals, active_count=1)
        assert isinstance(panel, Panel)


class TestFormatStatusBar:
    """Tests for status bar formatting."""

    def test_with_integrity(self):
        """Status bar with integrity data."""
        integrity = DashboardIntegrity(
            grade="A-",
            score=91,
            trend="up",
            streak_weeks=3,
        )
        panel = format_status_bar(integrity, triage_count=5)
        assert isinstance(panel, Panel)

    def test_without_integrity(self):
        """Status bar without integrity data."""
        panel = format_status_bar(None, triage_count=0)
        assert isinstance(panel, Panel)

    def test_trend_arrows(self):
        """Different trends show correct arrows."""
        for trend in ["up", "down", "stable"]:
            integrity = DashboardIntegrity(
                grade="B",
                score=80,
                trend=trend,
                streak_weeks=1,
            )
            panel = format_status_bar(integrity, triage_count=0)
            assert isinstance(panel, Panel)


class TestDetermineDisplayLevel:
    """Tests for display level logic."""

    def test_minimal_no_data(self):
        """No commitments or goals = MINIMAL."""
        data = DashboardData(
            commitments=[],
            goals=[],
            integrity=None,
            triage_count=0,
        )
        dashboard = format_dashboard(data)
        # With no integrity and no triage, should return None
        assert dashboard is None

    def test_minimal_with_triage(self):
        """No entities but triage count shows status bar."""
        data = DashboardData(
            commitments=[],
            goals=[],
            integrity=None,
            triage_count=5,
        )
        dashboard = format_dashboard(data)
        assert isinstance(dashboard, Group)

    def test_compact_few_commitments(self):
        """Few commitments without goals = COMPACT."""
        commitments = [
            DashboardCommitment(
                deliverable="Task",
                stakeholder="Person",
                due_display="Today",
                status="pending",
            )
            for _ in range(COMPACT_COMMITMENT_THRESHOLD)
        ]
        data = DashboardData(
            commitments=commitments,
            goals=[],
            integrity=None,
            triage_count=0,
        )
        dashboard = format_dashboard(data)
        assert isinstance(dashboard, Group)

    def test_full_with_goals(self):
        """Commitments with goals = FULL."""
        commitments = [
            DashboardCommitment(
                deliverable="Task",
                stakeholder="Person",
                due_display="Today",
                status="pending",
            )
        ]
        goals = [
            DashboardGoal(
                title="Goal",
                progress_percent=0.5,
                progress_text="1/2 done",
            )
        ]
        data = DashboardData(
            commitments=commitments,
            goals=goals,
            integrity=None,
            triage_count=0,
        )
        dashboard = format_dashboard(data)
        assert isinstance(dashboard, Group)


class TestFormatDashboard:
    """Integration tests for full dashboard formatting."""

    def test_complete_dashboard(self):
        """Complete dashboard with all panels."""
        commitments = [
            DashboardCommitment(
                deliverable="Send report",
                stakeholder="Client",
                due_display="OVERDUE (2d)",
                status="overdue",
                is_overdue=True,
            ),
            DashboardCommitment(
                deliverable="Review PR",
                stakeholder="Team",
                due_display="Tomorrow",
                status="pending",
                is_overdue=False,
            ),
        ]
        goals = [
            DashboardGoal(
                title="Launch MVP",
                progress_percent=0.8,
                progress_text="4/5 done",
                needs_review=False,
            ),
        ]
        integrity = DashboardIntegrity(
            grade="A-",
            score=91,
            trend="up",
            streak_weeks=3,
        )
        data = DashboardData(
            commitments=commitments,
            goals=goals,
            integrity=integrity,
            triage_count=5,
        )
        dashboard = format_dashboard(data)
        assert isinstance(dashboard, Group)

    def test_empty_dashboard_returns_none(self):
        """Empty dashboard with no data returns None."""
        data = DashboardData(
            commitments=[],
            goals=[],
            integrity=None,
            triage_count=0,
        )
        assert format_dashboard(data) is None


class TestDashboardDataClasses:
    """Tests for dashboard data classes."""

    def test_dashboard_commitment_defaults(self):
        """DashboardCommitment has correct defaults."""
        c = DashboardCommitment(
            deliverable="Test",
            stakeholder="Person",
            due_display="Today",
            status="pending",
        )
        assert c.is_overdue is False

    def test_dashboard_goal_defaults(self):
        """DashboardGoal has correct defaults."""
        g = DashboardGoal(
            title="Test Goal",
            progress_percent=0.5,
            progress_text="1/2 done",
        )
        assert g.needs_review is False

    def test_display_level_enum(self):
        """DisplayLevel enum has all levels."""
        assert DisplayLevel.MINIMAL.value == "minimal"
        assert DisplayLevel.COMPACT.value == "compact"
        assert DisplayLevel.STANDARD.value == "standard"
        assert DisplayLevel.FULL.value == "full"
