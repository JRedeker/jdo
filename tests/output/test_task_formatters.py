"""Tests for the task formatters module."""

from unittest.mock import MagicMock
from uuid import uuid4

from rich.panel import Panel
from rich.table import Table

from jdo.models.task import TaskStatus
from jdo.output.task import (
    TASK_STATUS_COLORS,
    format_task_detail,
    format_task_list,
    format_task_list_plain,
    format_task_proposal,
    get_task_status_color,
)


class TestGetTaskStatusColor:
    """Tests for task status color mapping."""

    def test_pending_status(self):
        """Pending status returns default."""
        assert get_task_status_color("pending") == "default"
        assert get_task_status_color(TaskStatus.PENDING) == "default"

    def test_in_progress_status(self):
        """In progress status returns blue."""
        assert get_task_status_color("in_progress") == "blue"
        assert get_task_status_color(TaskStatus.IN_PROGRESS) == "blue"

    def test_completed_status(self):
        """Completed status returns green."""
        assert get_task_status_color("completed") == "green"
        assert get_task_status_color(TaskStatus.COMPLETED) == "green"

    def test_skipped_status(self):
        """Skipped status returns dim."""
        assert get_task_status_color("skipped") == "dim"
        assert get_task_status_color(TaskStatus.SKIPPED) == "dim"

    def test_unknown_status(self):
        """Unknown status returns default."""
        assert get_task_status_color("unknown") == "default"


class TestFormatTaskList:
    """Tests for task list formatting."""

    def test_empty_list_returns_table(self):
        """Empty list returns empty table."""
        table = format_task_list([])
        assert isinstance(table, Table)

    def test_table_has_expected_columns(self):
        """Table has expected columns."""
        table = format_task_list([])
        column_names = [col.header for col in table.columns]
        assert "ID" in column_names
        assert "Title" in column_names
        assert "Status" in column_names
        assert "Est. Hours" in column_names
        assert "Commitment" in column_names


class TestFormatTaskDetail:
    """Tests for task detail formatting."""

    def test_returns_panel(self):
        """Detail view returns a Panel."""
        task = MagicMock()
        task.id = uuid4()
        task.title = "Test Task"
        task.scope = "Do the thing"
        task.status = TaskStatus.PENDING
        task.estimated_hours = None
        task.actual_hours_category = None
        task.estimation_confidence = None
        task.sub_tasks = []
        # Ensure no commitment relationship is present to avoid mock issues
        task.commitment = None

        panel = format_task_detail(task)
        assert isinstance(panel, Panel)


class TestFormatTaskProposal:
    """Tests for task proposal formatting."""

    def test_returns_panel(self):
        """Proposal returns a Panel."""
        panel = format_task_proposal(
            title="Write chapter 1",
            scope="Write the first 2000 words",
        )
        assert isinstance(panel, Panel)

    def test_contains_title(self):
        """Panel contains title text."""
        panel = format_task_proposal(
            title="Write chapter 1",
            scope="Write the first 2000 words",
        )
        content = str(panel.renderable)
        assert "Write chapter 1" in content

    def test_contains_estimate_when_provided(self):
        """Panel contains estimate when provided."""
        panel = format_task_proposal(
            title="Write chapter",
            scope="Write words",
            estimated_hours=2.5,
        )
        content = str(panel.renderable)
        assert "2.5h" in content

    def test_contains_confirmation_prompt(self):
        """Panel contains confirmation prompt."""
        panel = format_task_proposal(
            title="Task",
            scope="Scope",
        )
        content = str(panel.renderable)
        assert "Does this look right?" in content


class TestFormatTaskListPlain:
    """Tests for plain text task list formatting."""

    def test_empty_list(self):
        """Empty list returns friendly message."""
        result = format_task_list_plain([])
        assert "No task" in result

    def test_single_task(self):
        """Single task is formatted correctly."""
        tasks = [
            {
                "id": "1",
                "title": "Write chapter",
                "scope": "Write 2000 words",
                "status": "pending",
                "estimated_hours": 2.0,
            }
        ]
        result = format_task_list_plain(tasks)
        assert "Write chapter" in result
        assert "2.0h" in result


class TestTaskStatusColors:
    """Tests for TASK_STATUS_COLORS constant."""

    def test_all_statuses_have_colors(self):
        """All task statuses have colors defined."""
        for status in TaskStatus:
            assert status.value in TASK_STATUS_COLORS
