"""Tests for task and commitment handlers."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from jdo.commands.handlers.commitment_handlers import CommitHandler
from jdo.commands.handlers.task_handlers import TaskHandler
from jdo.commands.parser import CommandType, ParsedCommand
from jdo.models import (
    Commitment,
    CommitmentStatus,
    Stakeholder,
    StakeholderType,
    Task,
    TaskStatus,
)
from jdo.models.task import EstimationConfidence


def make_command(name: str, args: list[str] | None = None) -> ParsedCommand:
    """Helper to create a ParsedCommand."""
    if args is None:
        args = []
    command_type = CommandType(name)
    return ParsedCommand(
        command_type=command_type,
        args=args,
        raw_text=f"/{name} {' '.join(args)}" if args else f"/{name}",
    )


class TestTaskHandler:
    """Tests for TaskHandler."""

    def test_task_without_commitment_prompts_user(self) -> None:
        """Task command without commitment context prompts for selection."""
        handler = TaskHandler()
        cmd = make_command("task", ["Do something"])
        context: dict[str, object] = {
            "current_commitment_id": None,
            "available_commitments": [],
        }

        result = handler.execute(cmd, context)

        assert "create a commitment first" in result.message.lower()
        assert result.panel_update is None

    def test_task_without_commitment_with_options(self) -> None:
        """Task command without commitment but with options shows list."""
        handler = TaskHandler()
        cmd = make_command("task", ["Do something"])
        context: dict[str, object] = {
            "current_commitment_id": None,
            "available_commitments": [{"id": str(uuid4()), "deliverable": "Test"}],
        }

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert result.panel_update.get("mode") == "list"

    def test_task_with_title_prompts_for_confirmation(self) -> None:
        """Task command with title shows confirmation message."""
        handler = TaskHandler()
        cmd = make_command("task", ["Complete the report"])
        context: dict[str, object] = {
            "current_commitment_id": str(uuid4()),
            "available_commitments": [],
            "extracted": {"title": "Complete the report", "scope": "Write findings"},
        }

        result = handler.execute(cmd, context)

        assert "Complete the report" in result.message
        assert result.needs_confirmation is True
        assert result.draft_data is not None
        assert result.draft_data["title"] == "Complete the report"

    def test_task_without_title_asks_for_input(self) -> None:
        """Task command without title asks for more info."""
        handler = TaskHandler()
        cmd = make_command("task")
        context: dict[str, object] = {
            "current_commitment_id": str(uuid4()),
            "available_commitments": [],
            "extracted": {},
        }

        result = handler.execute(cmd, context)

        assert "What task would you like" in result.message
        assert result.needs_confirmation is False

    def test_task_with_estimated_hours(self) -> None:
        """Task command includes estimated hours in draft."""
        handler = TaskHandler()
        cmd = make_command("task", ["Complete the report"])
        context: dict[str, object] = {
            "current_commitment_id": str(uuid4()),
            "available_commitments": [],
            "extracted": {
                "title": "Complete the report",
                "scope": "Write findings",
                "estimated_hours": 2.5,
            },
        }

        result = handler.execute(cmd, context)

        assert result.draft_data is not None
        assert result.draft_data["estimated_hours"] == 2.5


class TestCommitHandler:
    """Tests for CommitHandler."""

    def test_commit_extracts_data_from_input(self) -> None:
        """Commit command extracts data from input."""
        handler = CommitHandler()
        command_type = CommandType("commit")
        cmd = ParsedCommand(
            command_type=command_type,
            args=[],
            raw_text="/commit send report to Sarah",
        )
        context: dict[str, object] = {
            "extracted": {
                "deliverable": "send report to Sarah",
                "stakeholder": "Sarah",
                "due_date": date(2025, 1, 15),
            },
        }

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert result.panel_update.get("mode") == "draft"
        assert result.draft_data is not None

    def test_commit_without_extracted_prompts(self) -> None:
        """Commit without extracted data prompts for input."""
        handler = CommitHandler()
        cmd = make_command("commit", ["something"])
        context: dict[str, object] = {
            "extracted": {},
            "conversation": [{"role": "user", "content": "I need to do something"}],
        }

        result = handler.execute(cmd, context)

        assert result.needs_confirmation is False


class TestTaskHandlerUnitMocks:
    """Unit tests for TaskHandler with mocked dependencies."""

    def test_task_sets_commitment_id_in_draft(self) -> None:
        """Task handler includes commitment_id in draft data."""
        handler = TaskHandler()
        commitment_id = str(uuid4())
        cmd = make_command("task", ["Do work"])
        context: dict[str, object] = {
            "current_commitment_id": commitment_id,
            "available_commitments": [],
            "extracted": {"title": "Do work"},
        }

        result = handler.execute(cmd, context)

        assert result.draft_data is not None
        assert result.draft_data["commitment_id"] == commitment_id

    def test_task_with_scope_included(self) -> None:
        """Task handler includes scope in draft data."""
        handler = TaskHandler()
        cmd = make_command("task", ["Do work"])
        context: dict[str, object] = {
            "current_commitment_id": str(uuid4()),
            "available_commitments": [],
            "extracted": {"title": "Do work", "scope": "Detailed scope here"},
        }

        result = handler.execute(cmd, context)

        assert result.draft_data is not None
        assert result.draft_data["scope"] == "Detailed scope here"

    def test_task_with_low_confidence(self) -> None:
        """Task handler preserves estimation confidence when provided."""
        handler = TaskHandler()
        cmd = make_command("task", ["Do work"])
        context: dict[str, object] = {
            "current_commitment_id": str(uuid4()),
            "available_commitments": [],
            "extracted": {
                "title": "Do work",
                "estimated_hours": 1.0,
                "confidence": "low",
            },
        }

        result = handler.execute(cmd, context)

        assert result.draft_data is not None
        assert result.draft_data["estimated_hours"] == 1.0


class TestCommitHandlerUnitMocks:
    """Unit tests for CommitHandler with mocked dependencies."""

    def test_commit_includes_stakeholder(self) -> None:
        """Commit handler includes stakeholder in draft data."""
        handler = CommitHandler()
        cmd = make_command("commit", ["send report"])
        context: dict[str, object] = {
            "extracted": {
                "deliverable": "send report",
                "stakeholder": "Alice",
            },
        }

        result = handler.execute(cmd, context)

        assert result.draft_data is not None
        assert result.draft_data["stakeholder"] == "Alice"

    def test_commit_includes_due_date(self) -> None:
        """Commit handler includes due_date in draft data."""
        handler = CommitHandler()
        cmd = make_command("commit", ["send report"])
        due_date = date(2025, 6, 15)
        context: dict[str, object] = {
            "extracted": {
                "deliverable": "send report",
                "due_date": due_date,
            },
        }

        result = handler.execute(cmd, context)

        assert result.draft_data is not None
        assert result.draft_data["due_date"] == due_date

    def test_commit_includes_goal_id(self) -> None:
        """Commit handler includes goal_id in draft data when provided."""
        handler = CommitHandler()
        goal_id = str(uuid4())
        cmd = make_command("commit", ["send report"])
        context: dict[str, object] = {
            "extracted": {
                "deliverable": "send report",
                "goal_id": goal_id,
            },
        }

        result = handler.execute(cmd, context)

        assert result.draft_data is not None
        assert result.draft_data["goal_id"] == goal_id
