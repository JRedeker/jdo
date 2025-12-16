"""Tests for command handlers.

Command handlers execute parsed commands and return responses
for the chat interface, updating the DataPanel as needed.
"""

from dataclasses import dataclass
from datetime import date, time
from typing import Any
from uuid import UUID, uuid4

import pytest

from jdo.commands.parser import CommandType, ParsedCommand


# Expected handler result dataclass
@dataclass
class HandlerResult:
    """Result from executing a command handler.

    Attributes:
        message: Response message to display in chat.
        panel_update: Optional dict with panel mode and data.
        draft_data: Optional draft data being created/updated.
        needs_confirmation: Whether user confirmation is needed.
    """

    message: str
    panel_update: dict[str, Any] | None = None
    draft_data: dict[str, Any] | None = None
    needs_confirmation: bool = False


# ============================================================
# Phase 6.1: /commit Command Tests
# ============================================================


class TestCommitHandler:
    """Tests for the /commit command handler."""

    def test_commit_creates_draft_panel_update(self) -> None:
        """Test: /commit shows draft in data panel."""
        from jdo.commands.handlers import CommitHandler

        handler = CommitHandler()
        cmd = ParsedCommand(CommandType.COMMIT, [], "/commit")

        # With conversation context mentioning a deliverable
        context = {
            "conversation": [
                {"role": "user", "content": "I need to send the report to finance by Friday"},
            ]
        }

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert result.panel_update["mode"] == "draft"
        assert result.panel_update["entity_type"] == "commitment"

    def test_commit_extracts_deliverable_from_context(self) -> None:
        """Test: /commit extracts deliverable from conversation."""
        from jdo.commands.handlers import CommitHandler

        handler = CommitHandler()
        cmd = ParsedCommand(CommandType.COMMIT, [], "/commit")

        context = {
            "conversation": [
                {"role": "user", "content": "I need to send the quarterly report"},
            ]
        }

        result = handler.execute(cmd, context)

        assert result.draft_data is not None
        # The handler should extract deliverable from context
        # Even if empty, draft_data should have the key
        assert "deliverable" in result.draft_data

    def test_commit_prompts_for_missing_required_fields(self) -> None:
        """Test: /commit prompts for missing required fields."""
        from jdo.commands.handlers import CommitHandler

        handler = CommitHandler()
        cmd = ParsedCommand(CommandType.COMMIT, [], "/commit")

        # Empty context - no extractable data
        context = {"conversation": []}

        result = handler.execute(cmd, context)

        # Should prompt for required fields
        assert "deliverable" in result.message.lower() or "what" in result.message.lower()
        assert result.needs_confirmation is False  # Can't confirm without data

    def test_commit_needs_confirmation_with_complete_data(self) -> None:
        """Test: /commit with complete data needs confirmation."""
        from jdo.commands.handlers import CommitHandler

        handler = CommitHandler()
        cmd = ParsedCommand(CommandType.COMMIT, [], "/commit")

        # Full context with all required fields
        context = {
            "conversation": [
                {"role": "user", "content": "Send quarterly report to Finance by Friday 3pm"},
            ],
            "extracted": {
                "deliverable": "Send quarterly report",
                "stakeholder": "Finance",
                "due_date": date(2025, 12, 20),
                "due_time": time(15, 0),
            },
        }

        result = handler.execute(cmd, context)

        assert result.needs_confirmation is True
        assert result.draft_data is not None
        assert result.draft_data.get("deliverable") == "Send quarterly report"

    def test_commit_cancel_discards_draft(self) -> None:
        """Test: Cancel discards draft."""
        from jdo.commands.handlers import CommitHandler

        handler = CommitHandler()

        # First create a draft
        cmd = ParsedCommand(CommandType.COMMIT, [], "/commit")
        context = {
            "extracted": {
                "deliverable": "Test deliverable",
                "stakeholder": "Test stakeholder",
            }
        }
        handler.execute(cmd, context)

        # Now cancel
        cancel_result = handler.cancel()

        assert cancel_result.message is not None
        assert (
            "cancel" in cancel_result.message.lower() or "discard" in cancel_result.message.lower()
        )
        assert cancel_result.draft_data is None


# ============================================================
# Phase 6.3: /goal Command Tests
# ============================================================


class TestGoalHandler:
    """Tests for the /goal command handler."""

    def test_goal_creates_draft_panel_update(self) -> None:
        """Test: /goal shows draft in data panel."""
        from jdo.commands.handlers import GoalHandler

        handler = GoalHandler()
        cmd = ParsedCommand(CommandType.GOAL, [], "/goal")

        context = {
            "conversation": [
                {"role": "user", "content": "I want to improve team productivity"},
            ]
        }

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert result.panel_update["mode"] == "draft"
        assert result.panel_update["entity_type"] == "goal"

    def test_goal_extracts_title_from_context(self) -> None:
        """Test: /goal extracts title from conversation."""
        from jdo.commands.handlers import GoalHandler

        handler = GoalHandler()
        cmd = ParsedCommand(CommandType.GOAL, [], "/goal")

        context = {
            "conversation": [
                {"role": "user", "content": "My goal is to improve team productivity"},
            ]
        }

        result = handler.execute(cmd, context)

        assert result.draft_data is not None
        assert "title" in result.draft_data

    def test_goal_prompts_for_problem_statement(self) -> None:
        """Test: /goal prompts for missing problem_statement."""
        from jdo.commands.handlers import GoalHandler

        handler = GoalHandler()
        cmd = ParsedCommand(CommandType.GOAL, [], "/goal")

        # Context with title but no problem statement
        context = {
            "extracted": {
                "title": "Improve productivity",
            }
        }

        result = handler.execute(cmd, context)

        # Should prompt for problem statement
        assert "problem" in result.message.lower()

    def test_goal_prompts_for_vision_when_visions_exist(self) -> None:
        """Test: /goal prompts for vision when visions exist."""
        from jdo.commands.handlers import GoalHandler

        handler = GoalHandler()
        cmd = ParsedCommand(CommandType.GOAL, [], "/goal")

        context = {
            "extracted": {
                "title": "Improve productivity",
                "problem_statement": "Team is slow",
                "solution_vision": "Fast and efficient team",
            },
            "available_visions": [
                {"id": uuid4(), "title": "Q4 Vision"},
            ],
        }

        result = handler.execute(cmd, context)

        # Should ask about linking to a vision
        assert "vision" in result.message.lower()

    def test_goal_needs_confirmation_with_complete_data(self) -> None:
        """Test: /goal with complete data needs confirmation."""
        from jdo.commands.handlers import GoalHandler

        handler = GoalHandler()
        cmd = ParsedCommand(CommandType.GOAL, [], "/goal")

        context = {
            "extracted": {
                "title": "Improve productivity",
                "problem_statement": "Team delivers slowly",
                "solution_vision": "Fast, efficient delivery",
            }
        }

        result = handler.execute(cmd, context)

        assert result.needs_confirmation is True
        assert result.draft_data is not None


# ============================================================
# Phase 6.5: /task Command Tests
# ============================================================


class TestTaskHandler:
    """Tests for the /task command handler."""

    def test_task_requires_commitment_context(self) -> None:
        """Test: /task requires commitment context."""
        from jdo.commands.handlers import TaskHandler

        handler = TaskHandler()
        cmd = ParsedCommand(CommandType.TASK, [], "/task")

        # No commitment context
        context = {"conversation": []}

        result = handler.execute(cmd, context)

        # Should prompt for commitment selection
        assert "commitment" in result.message.lower()
        assert result.needs_confirmation is False

    def test_task_extracts_title_from_context(self) -> None:
        """Test: /task extracts title from conversation."""
        from jdo.commands.handlers import TaskHandler

        handler = TaskHandler()
        cmd = ParsedCommand(CommandType.TASK, [], "/task")

        commitment_id = uuid4()
        context = {
            "conversation": [
                {"role": "user", "content": "First I need to gather the data"},
            ],
            "current_commitment_id": commitment_id,
        }

        result = handler.execute(cmd, context)

        assert result.draft_data is not None
        assert "title" in result.draft_data

    def test_task_shows_draft_in_panel(self) -> None:
        """Test: /task shows draft in data panel."""
        from jdo.commands.handlers import TaskHandler

        handler = TaskHandler()
        cmd = ParsedCommand(CommandType.TASK, [], "/task")

        commitment_id = uuid4()
        context = {
            "current_commitment_id": commitment_id,
            "extracted": {
                "title": "Gather data",
            },
        }

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert result.panel_update["mode"] == "draft"
        assert result.panel_update["entity_type"] == "task"

    def test_task_without_context_prompts_for_commitment(self) -> None:
        """Test: /task without context prompts for commitment selection."""
        from jdo.commands.handlers import TaskHandler

        handler = TaskHandler()
        cmd = ParsedCommand(CommandType.TASK, [], "/task")

        # List of available commitments but none selected
        context = {
            "available_commitments": [
                {"id": uuid4(), "deliverable": "Send report"},
                {"id": uuid4(), "deliverable": "Review docs"},
            ]
        }

        result = handler.execute(cmd, context)

        # Should list commitments and ask user to select
        assert "commitment" in result.message.lower()
        assert "select" in result.message.lower() or "which" in result.message.lower()


# ============================================================
# Phase 6.7: /vision Command Tests
# ============================================================


class TestVisionHandler:
    """Tests for the /vision command handler."""

    def test_vision_lists_all_visions(self) -> None:
        """Test: /vision lists all visions."""
        from jdo.commands.handlers import VisionHandler

        handler = VisionHandler()
        cmd = ParsedCommand(CommandType.VISION, [], "/vision")

        context = {
            "available_visions": [
                {"id": uuid4(), "title": "Q4 Vision", "status": "active"},
                {"id": uuid4(), "title": "2026 Vision", "status": "active"},
            ]
        }

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert result.panel_update["mode"] == "list"
        assert result.panel_update["entity_type"] == "vision"

    def test_vision_new_starts_creation_flow(self) -> None:
        """Test: /vision new starts creation flow."""
        from jdo.commands.handlers import VisionHandler

        handler = VisionHandler()
        cmd = ParsedCommand(CommandType.VISION, ["new"], "/vision new")

        context = {"conversation": []}

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert result.panel_update["mode"] == "draft"
        assert "narrative" in result.message.lower() or "describe" in result.message.lower()

    def test_vision_review_lists_visions_due_for_review(self) -> None:
        """Test: /vision review lists visions due for review."""
        from jdo.commands.handlers import VisionHandler

        handler = VisionHandler()
        cmd = ParsedCommand(CommandType.VISION, ["review"], "/vision review")

        context = {
            "visions_due_for_review": [
                {"id": uuid4(), "title": "Q4 Vision"},
            ]
        }

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert "review" in result.message.lower()

    def test_vision_draft_shows_in_panel(self) -> None:
        """Test: Vision draft shows in data panel."""
        from jdo.commands.handlers import VisionHandler

        handler = VisionHandler()
        cmd = ParsedCommand(CommandType.VISION, ["new"], "/vision new")

        context = {
            "extracted": {
                "title": "2026 Company Vision",
                "narrative": "We will be the market leader...",
            }
        }

        result = handler.execute(cmd, context)

        assert result.panel_update["mode"] == "draft"
        assert result.draft_data is not None


# ============================================================
# Phase 6.9: /milestone Command Tests
# ============================================================


class TestMilestoneHandler:
    """Tests for the /milestone command handler."""

    def test_milestone_lists_milestones_for_current_goal(self) -> None:
        """Test: /milestone lists milestones for current goal."""
        from jdo.commands.handlers import MilestoneHandler

        handler = MilestoneHandler()
        cmd = ParsedCommand(CommandType.MILESTONE, [], "/milestone")

        goal_id = uuid4()
        context = {
            "current_goal_id": goal_id,
            "milestones_for_goal": [
                {"id": uuid4(), "title": "Phase 1 Complete", "target_date": date(2025, 12, 31)},
            ],
        }

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert result.panel_update["mode"] == "list"
        assert result.panel_update["entity_type"] == "milestone"

    def test_milestone_new_requires_goal_context(self) -> None:
        """Test: /milestone new requires goal context."""
        from jdo.commands.handlers import MilestoneHandler

        handler = MilestoneHandler()
        cmd = ParsedCommand(CommandType.MILESTONE, ["new"], "/milestone new")

        # No goal context
        context = {"conversation": []}

        result = handler.execute(cmd, context)

        # Should prompt for goal selection
        assert "goal" in result.message.lower()

    def test_milestone_new_prompts_for_target_date(self) -> None:
        """Test: /milestone new prompts for target_date."""
        from jdo.commands.handlers import MilestoneHandler

        handler = MilestoneHandler()
        cmd = ParsedCommand(CommandType.MILESTONE, ["new"], "/milestone new")

        goal_id = uuid4()
        context = {
            "current_goal_id": goal_id,
            "extracted": {
                "title": "Phase 1 Complete",
            },
        }

        result = handler.execute(cmd, context)

        # Should ask for target date
        assert "date" in result.message.lower() or "when" in result.message.lower()

    def test_milestone_draft_shows_in_panel(self) -> None:
        """Test: Milestone draft shows in data panel."""
        from jdo.commands.handlers import MilestoneHandler

        handler = MilestoneHandler()
        cmd = ParsedCommand(CommandType.MILESTONE, ["new"], "/milestone new")

        goal_id = uuid4()
        context = {
            "current_goal_id": goal_id,
            "extracted": {
                "title": "Phase 1 Complete",
                "target_date": date(2025, 12, 31),
            },
        }

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert result.panel_update["mode"] == "draft"


# ============================================================
# Phase 6.11: /show Command Tests
# ============================================================


class TestShowHandler:
    """Tests for the /show command handler."""

    def test_show_goals_displays_goal_list(self) -> None:
        """Test: /show goals displays goal list."""
        from jdo.commands.handlers import ShowHandler

        handler = ShowHandler()
        cmd = ParsedCommand(CommandType.SHOW, ["goals"], "/show goals")

        context = {
            "goals": [
                {"id": uuid4(), "title": "Improve productivity"},
                {"id": uuid4(), "title": "Learn Python"},
            ]
        }

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert result.panel_update["mode"] == "list"
        assert result.panel_update["entity_type"] == "goal"
        assert len(result.panel_update["items"]) == 2

    def test_show_commitments_displays_commitment_list(self) -> None:
        """Test: /show commitments displays commitment list."""
        from jdo.commands.handlers import ShowHandler

        handler = ShowHandler()
        cmd = ParsedCommand(CommandType.SHOW, ["commitments"], "/show commitments")

        context = {
            "commitments": [
                {"id": uuid4(), "deliverable": "Send report"},
            ]
        }

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert result.panel_update["entity_type"] == "commitment"

    def test_show_tasks_displays_tasks_for_commitment(self) -> None:
        """Test: /show tasks displays tasks for current commitment."""
        from jdo.commands.handlers import ShowHandler

        handler = ShowHandler()
        cmd = ParsedCommand(CommandType.SHOW, ["tasks"], "/show tasks")

        commitment_id = uuid4()
        context = {
            "current_commitment_id": commitment_id,
            "tasks": [
                {"id": uuid4(), "title": "Gather data"},
                {"id": uuid4(), "title": "Write analysis"},
            ],
        }

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert result.panel_update["entity_type"] == "task"

    def test_show_visions_displays_vision_list(self) -> None:
        """Test: /show visions displays vision list."""
        from jdo.commands.handlers import ShowHandler

        handler = ShowHandler()
        cmd = ParsedCommand(CommandType.SHOW, ["visions"], "/show visions")

        context = {
            "visions": [
                {"id": uuid4(), "title": "Q4 Vision"},
            ]
        }

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert result.panel_update["entity_type"] == "vision"

    def test_show_milestones_displays_milestones_for_goal(self) -> None:
        """Test: /show milestones displays milestones for current goal."""
        from jdo.commands.handlers import ShowHandler

        handler = ShowHandler()
        cmd = ParsedCommand(CommandType.SHOW, ["milestones"], "/show milestones")

        goal_id = uuid4()
        context = {
            "current_goal_id": goal_id,
            "milestones": [
                {"id": uuid4(), "title": "Phase 1"},
            ],
        }

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert result.panel_update["entity_type"] == "milestone"

    def test_show_stakeholders_displays_stakeholder_list(self) -> None:
        """Test: /show stakeholders displays stakeholder list."""
        from jdo.commands.handlers import ShowHandler

        handler = ShowHandler()
        cmd = ParsedCommand(CommandType.SHOW, ["stakeholders"], "/show stakeholders")

        context = {
            "stakeholders": [
                {"id": uuid4(), "name": "Finance Team"},
            ]
        }

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert result.panel_update["entity_type"] == "stakeholder"

    def test_show_orphans_displays_unlinked_commitments(self) -> None:
        """Test: /show orphans displays unlinked commitments."""
        from jdo.commands.handlers import ShowHandler

        handler = ShowHandler()
        cmd = ParsedCommand(CommandType.SHOW, ["orphans"], "/show orphans")

        context = {
            "orphan_commitments": [
                {"id": uuid4(), "deliverable": "Unlinked commitment"},
            ]
        }

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert "orphan" in result.message.lower()

    def test_show_without_arg_shows_help(self) -> None:
        """Test: /show without argument shows available options."""
        from jdo.commands.handlers import ShowHandler

        handler = ShowHandler()
        cmd = ParsedCommand(CommandType.SHOW, [], "/show")

        context = {}

        result = handler.execute(cmd, context)

        # Should list available show options
        assert "goals" in result.message.lower()
        assert "commitments" in result.message.lower()


# ============================================================
# Phase 6.13: Other Command Tests
# ============================================================


class TestHelpHandler:
    """Tests for the /help command handler."""

    def test_help_shows_command_list(self) -> None:
        """Test: /help shows command list."""
        from jdo.commands.handlers import HelpHandler

        handler = HelpHandler()
        cmd = ParsedCommand(CommandType.HELP, [], "/help")

        result = handler.execute(cmd, {})

        # Should list available commands
        assert "/commit" in result.message
        assert "/goal" in result.message
        assert "/task" in result.message

    def test_help_command_shows_details(self) -> None:
        """Test: /help <command> shows command details."""
        from jdo.commands.handlers import HelpHandler

        handler = HelpHandler()
        cmd = ParsedCommand(CommandType.HELP, ["commit"], "/help commit")

        result = handler.execute(cmd, {})

        # Should show details for /commit
        assert "commit" in result.message.lower()
        assert "deliverable" in result.message.lower() or "stakeholder" in result.message.lower()


class TestViewHandler:
    """Tests for the /view command handler."""

    def test_view_shows_object_in_panel(self) -> None:
        """Test: /view <id> shows object in data panel."""
        from jdo.commands.handlers import ViewHandler

        handler = ViewHandler()
        obj_id = uuid4()
        cmd = ParsedCommand(CommandType.VIEW, [str(obj_id)], f"/view {obj_id}")

        context = {
            "object_data": {
                "id": obj_id,
                "entity_type": "commitment",
                "deliverable": "Send report",
                "status": "pending",
            }
        }

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert result.panel_update["mode"] == "view"


class TestCancelHandler:
    """Tests for the /cancel command handler."""

    def test_cancel_discards_current_draft(self) -> None:
        """Test: /cancel discards current draft."""
        from jdo.commands.handlers import CancelHandler

        handler = CancelHandler()
        cmd = ParsedCommand(CommandType.CANCEL, [], "/cancel")

        context = {
            "current_draft": {
                "entity_type": "commitment",
                "data": {"deliverable": "Test"},
            }
        }

        result = handler.execute(cmd, context)

        assert "cancel" in result.message.lower() or "discard" in result.message.lower()
        # Panel should be cleared or show default
        assert result.panel_update is not None


class TestCompleteHandler:
    """Tests for the /complete command handler."""

    def test_complete_marks_object_completed(self) -> None:
        """Test: /complete marks object as completed."""
        from jdo.commands.handlers import CompleteHandler

        handler = CompleteHandler()
        cmd = ParsedCommand(CommandType.COMPLETE, [], "/complete")

        obj_id = uuid4()
        context = {
            "current_object": {
                "id": obj_id,
                "entity_type": "commitment",
                "deliverable": "Send report",
            }
        }

        result = handler.execute(cmd, context)

        assert "complet" in result.message.lower()
        assert result.needs_confirmation is True


# ============================================================
# Handler Registry Tests
# ============================================================


class TestHandlerRegistry:
    """Tests for the command handler registry."""

    def test_get_handler_returns_correct_handler(self) -> None:
        """Test: get_handler returns the correct handler for command type."""
        from jdo.commands.handlers import CommitHandler, get_handler

        handler = get_handler(CommandType.COMMIT)
        assert isinstance(handler, CommitHandler)

    def test_get_handler_for_all_command_types(self) -> None:
        """Test: get_handler works for all command types."""
        from jdo.commands.handlers import get_handler

        command_types = [
            CommandType.COMMIT,
            CommandType.GOAL,
            CommandType.TASK,
            CommandType.VISION,
            CommandType.MILESTONE,
            CommandType.SHOW,
            CommandType.VIEW,
            CommandType.HELP,
            CommandType.CANCEL,
            CommandType.COMPLETE,
        ]

        for cmd_type in command_types:
            handler = get_handler(cmd_type)
            assert handler is not None

    def test_get_handler_for_message_returns_none(self) -> None:
        """Test: get_handler returns None for MESSAGE type."""
        from jdo.commands.handlers import get_handler

        handler = get_handler(CommandType.MESSAGE)
        assert handler is None
