"""Tests for the goal formatters module."""

from datetime import date
from unittest.mock import MagicMock
from uuid import uuid4

from rich.panel import Panel
from rich.table import Table

from jdo.models.goal import GoalStatus
from jdo.output.goal import (
    GOAL_STATUS_COLORS,
    format_goal_detail,
    format_goal_list,
    format_goal_list_plain,
    format_goal_proposal,
    get_goal_status_color,
)


class TestGetGoalStatusColor:
    """Tests for goal status color mapping."""

    def test_active_status(self):
        """Active status returns green."""
        assert get_goal_status_color("active") == "green"
        assert get_goal_status_color(GoalStatus.ACTIVE) == "green"

    def test_on_hold_status(self):
        """On hold status returns yellow."""
        assert get_goal_status_color("on_hold") == "yellow"
        assert get_goal_status_color(GoalStatus.ON_HOLD) == "yellow"

    def test_achieved_status(self):
        """Achieved status returns cyan."""
        assert get_goal_status_color("achieved") == "cyan"
        assert get_goal_status_color(GoalStatus.ACHIEVED) == "cyan"

    def test_abandoned_status(self):
        """Abandoned status returns red."""
        assert get_goal_status_color("abandoned") == "red"
        assert get_goal_status_color(GoalStatus.ABANDONED) == "red"

    def test_unknown_status(self):
        """Unknown status returns default."""
        assert get_goal_status_color("unknown") == "default"


class TestFormatGoalList:
    """Tests for goal list formatting."""

    def test_empty_list_returns_table(self):
        """Empty list returns empty table."""
        table = format_goal_list([])
        assert isinstance(table, Table)

    def test_table_has_expected_columns(self):
        """Table has expected columns."""
        table = format_goal_list([])
        column_names = [col.header for col in table.columns]
        assert "ID" in column_names
        assert "Title" in column_names
        assert "Status" in column_names
        assert "Vision" in column_names


class TestFormatGoalDetail:
    """Tests for goal detail formatting."""

    def test_returns_panel(self):
        """Detail view returns a Panel."""
        goal = MagicMock()
        goal.id = uuid4()
        goal.title = "Test Goal"
        goal.problem_statement = "Test problem"
        goal.solution_vision = "Test solution"
        goal.status = GoalStatus.ACTIVE
        goal.motivation = None
        goal.next_review_date = None

        panel = format_goal_detail(goal)
        assert isinstance(panel, Panel)


class TestFormatGoalProposal:
    """Tests for goal proposal formatting."""

    def test_returns_panel(self):
        """Proposal returns a Panel."""
        panel = format_goal_proposal(
            title="My Goal",
            problem_statement="The problem",
            solution_vision="The solution",
        )
        assert isinstance(panel, Panel)

    def test_contains_title(self):
        """Panel contains title text."""
        panel = format_goal_proposal(
            title="Improve health",
            problem_statement="Poor fitness",
            solution_vision="Run a marathon",
        )
        content = str(panel.renderable)
        assert "Improve health" in content

    def test_contains_confirmation_prompt(self):
        """Panel contains confirmation prompt."""
        panel = format_goal_proposal(
            title="My Goal",
            problem_statement="Problem",
            solution_vision="Solution",
        )
        content = str(panel.renderable)
        assert "Does this look right?" in content


class TestFormatGoalListPlain:
    """Tests for plain text goal list formatting."""

    def test_empty_list(self):
        """Empty list returns friendly message."""
        result = format_goal_list_plain([])
        assert "No goal" in result

    def test_single_goal(self):
        """Single goal is formatted correctly."""
        goals = [
            {
                "id": "1",
                "title": "Get healthy",
                "problem_statement": "Poor fitness",
                "status": "active",
            }
        ]
        result = format_goal_list_plain(goals)
        assert "Get healthy" in result
        assert "active" in result


class TestGoalStatusColors:
    """Tests for GOAL_STATUS_COLORS constant."""

    def test_all_statuses_have_colors(self):
        """All goal statuses have colors defined."""
        for status in GoalStatus:
            assert status.value in GOAL_STATUS_COLORS
