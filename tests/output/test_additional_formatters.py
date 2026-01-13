"""Additional tests for output formatters to increase coverage."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from jdo.output.formatters import (
    format_date,
    format_empty_list,
    get_status_color,
)
from jdo.output.goal import (
    format_goal_list_plain,
    get_goal_status_color,
)
from jdo.output.task import (
    format_task_list_plain,
    get_task_status_color,
)


class TestFormatters:
    """Tests for output formatters."""

    def test_get_status_color_pending(self) -> None:
        """Test getting color for pending status."""
        assert get_status_color("pending") == "default"

    def test_get_status_color_in_progress(self) -> None:
        """Test getting color for in_progress status."""
        assert get_status_color("in_progress") == "blue"

    def test_get_status_color_completed(self) -> None:
        """Test getting color for completed status."""
        assert get_status_color("completed") == "green"

    def test_get_status_color_at_risk(self) -> None:
        """Test getting color for at_risk status."""
        assert get_status_color("at_risk") == "yellow"

    def test_get_status_color_abandoned(self) -> None:
        """Test getting color for abandoned status."""
        assert get_status_color("abandoned") == "red"

    def test_get_status_color_unknown(self) -> None:
        """Test getting color for unknown status."""
        assert get_status_color("unknown_status") == "default"

    def test_format_date_with_datetime(self) -> None:
        """Test formatting datetime object."""
        dt = datetime(2024, 1, 15, 14, 30)
        result = format_date(dt)
        assert "2024-01-15" in result
        assert "14:30" in result

    def test_format_date_with_date(self) -> None:
        """Test formatting date object."""
        d = date(2024, 1, 15)
        result = format_date(d)
        assert result == "2024-01-15"

    def test_format_date_with_none(self) -> None:
        """Test formatting None returns N/A."""
        result = format_date(None)
        assert result == "N/A"

    def test_format_empty_list(self) -> None:
        """Test formatting empty list."""
        result = format_empty_list("commitment")
        assert "No commitments" in result
        assert "yet" in result.lower()

    def test_format_task_list_plain_empty(self) -> None:
        """Test formatting empty task list."""
        result = format_task_list_plain([])
        assert "No tasks" in result
        assert "yet" in result.lower()

    def test_format_goal_list_plain_empty(self) -> None:
        """Test formatting empty goal list."""
        result = format_goal_list_plain([])
        assert "No goals" in result
        assert "yet" in result.lower()


class TestTaskFormatters:
    """Tests for task output formatters."""

    def test_get_task_status_color_pending(self) -> None:
        """Test getting color for pending task status."""
        assert get_task_status_color("pending") == "default"

    def test_get_task_status_color_in_progress(self) -> None:
        """Test getting color for in_progress task status."""
        assert get_task_status_color("in_progress") == "blue"

    def test_get_task_status_color_completed(self) -> None:
        """Test getting color for completed task status."""
        assert get_task_status_color("completed") == "green"

    def test_get_task_status_color_skipped(self) -> None:
        """Test getting color for skipped task status."""
        assert get_task_status_color("skipped") == "dim"

    def test_get_task_status_color_unknown(self) -> None:
        """Test getting color for unknown task status."""
        assert get_task_status_color("unknown") == "default"

    def test_format_task_list_plain_empty(self) -> None:
        """Test formatting empty task list."""
        result = format_task_list_plain([])
        assert "No tasks" in result
        assert "break down" in result.lower()

    def test_format_task_list_plain_with_tasks(self) -> None:
        """Test formatting task list with tasks."""
        tasks = [
            {
                "title": "Test Task",
                "scope": "Test scope",
                "status": "pending",
                "estimated_hours": 2.5,
            }
        ]
        result = format_task_list_plain(tasks)
        assert "Test Task" in result
        assert "Test scope" in result
        assert "pending" in result


class TestGoalFormatters:
    """Tests for goal output formatters."""

    def test_get_goal_status_color_active(self) -> None:
        """Test getting color for active goal status."""
        assert get_goal_status_color("active") == "green"

    def test_get_goal_status_color_on_hold(self) -> None:
        """Test getting color for on_hold goal status."""
        assert get_goal_status_color("on_hold") == "yellow"

    def test_get_goal_status_color_achieved(self) -> None:
        """Test getting color for achieved goal status."""
        assert get_goal_status_color("achieved") == "cyan"

    def test_get_goal_status_color_abandoned(self) -> None:
        """Test getting color for abandoned goal status."""
        assert get_goal_status_color("abandoned") == "red"

    def test_get_goal_status_color_unknown(self) -> None:
        """Test getting color for unknown goal status."""
        assert get_goal_status_color("unknown") == "default"

    def test_format_goal_list_plain_empty(self) -> None:
        """Test formatting empty goal list."""
        result = format_goal_list_plain([])
        assert "No goals" in result
        assert "achieve" in result.lower()

    def test_format_goal_list_plain_with_goals(self) -> None:
        """Test formatting goal list with goals."""
        goals = [
            {
                "title": "Test Goal",
                "problem_statement": "Test problem that needs solving",
                "status": "active",
            }
        ]
        result = format_goal_list_plain(goals)
        assert "Test Goal" in result
        assert "Test problem" in result
        assert "active" in result
