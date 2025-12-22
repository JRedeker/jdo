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

    def test_no_velocity_warning_when_balanced(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that no warning appears when velocity is balanced."""
        from pathlib import Path
        from unittest.mock import Mock, patch

        from jdo.commands.handlers import CommitHandler

        # Mock database to return balanced velocity
        mock_service = Mock()
        mock_service.get_commitment_velocity.return_value = (3, 3)

        with (
            patch("jdo.commands.handlers.commitment_handlers.get_session"),
            patch(
                "jdo.commands.handlers.commitment_handlers.PersistenceService",
                return_value=mock_service,
            ),
            patch("jdo.config.settings.get_database_path", return_value=Path("/tmp/test.db")),
        ):
            handler = CommitHandler()
            cmd = ParsedCommand(CommandType.COMMIT, [], "/commit")

            context = {
                "conversation": [
                    {"role": "user", "content": "Send the report to Finance by Jan 15"}
                ]
            }
            result = handler.execute(cmd, context)

        # Should not contain warning
        assert "**Note**" not in result.message
        assert "overcommitting" not in result.message

    def test_velocity_warning(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that velocity warning appears when creating more than completing."""
        from datetime import date as date_cls
        from pathlib import Path
        from unittest.mock import Mock, patch

        from jdo.commands.handlers import CommitHandler

        # Mock database to show high creation velocity
        mock_service = Mock()
        mock_service.count_active_commitments.return_value = 5
        mock_service.get_commitment_velocity.return_value = (8, 2)  # 8 created, 2 completed

        with (
            patch("jdo.commands.handlers.commitment_handlers.get_session"),
            patch(
                "jdo.commands.handlers.commitment_handlers.PersistenceService",
                return_value=mock_service,
            ),
            patch("jdo.config.settings.get_database_path", return_value=Path("/tmp/test.db")),
        ):
            handler = CommitHandler()
            cmd = ParsedCommand(CommandType.COMMIT, [], "/commit")

            # Provide complete extracted data in context
            context = {
                "conversation": [],
                "extracted": {
                    "deliverable": "Send the report",
                    "stakeholder": "Finance",
                    "due_date": date_cls(2026, 1, 15),
                },
            }
            result = handler.execute(cmd, context)

        # Should contain velocity warning
        assert "**Note**: You've created 8 commitments this week" in result.message
        assert "but only completed 2" in result.message
        assert "Are you overcommitting?" in result.message


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


# ============================================================
# Phase 7: /recurring Command Tests
# ============================================================


class TestRecurringHandler:
    """Tests for the /recurring command handler."""

    def test_recurring_lists_all_recurring_commitments(self) -> None:
        """Test: /recurring lists all recurring commitments."""
        from jdo.commands.handlers import RecurringHandler

        handler = RecurringHandler()
        cmd = ParsedCommand(CommandType.RECURRING, [], "/recurring")

        context = {
            "recurring_commitments": [
                {
                    "id": uuid4(),
                    "deliverable_template": "Weekly status report",
                    "recurrence_type": "weekly",
                    "status": "active",
                },
                {
                    "id": uuid4(),
                    "deliverable_template": "Monthly review",
                    "recurrence_type": "monthly",
                    "status": "active",
                },
            ]
        }

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert result.panel_update["mode"] == "list"
        assert result.panel_update["entity_type"] == "recurring_commitment"
        assert len(result.panel_update["items"]) == 2

    def test_recurring_shows_pattern_summary(self) -> None:
        """Test: /recurring shows pattern summary (e.g., 'Weekly on Mon, Wed')."""
        from jdo.commands.handlers import RecurringHandler

        handler = RecurringHandler()
        cmd = ParsedCommand(CommandType.RECURRING, [], "/recurring")

        context = {
            "recurring_commitments": [
                {
                    "id": uuid4(),
                    "deliverable_template": "Weekly status report",
                    "recurrence_type": "weekly",
                    "days_of_week": [0, 2, 4],  # Mon, Wed, Fri
                    "status": "active",
                },
            ]
        }

        result = handler.execute(cmd, context)

        # Panel should contain the recurring commitment data
        assert result.panel_update is not None
        assert len(result.panel_update["items"]) == 1
        item = result.panel_update["items"][0]
        assert item["days_of_week"] == [0, 2, 4]

    def test_recurring_shows_active_paused_status(self) -> None:
        """Test: /recurring shows active/paused status."""
        from jdo.commands.handlers import RecurringHandler

        handler = RecurringHandler()
        cmd = ParsedCommand(CommandType.RECURRING, [], "/recurring")

        context = {
            "recurring_commitments": [
                {
                    "id": uuid4(),
                    "deliverable_template": "Active task",
                    "recurrence_type": "daily",
                    "status": "active",
                },
                {
                    "id": uuid4(),
                    "deliverable_template": "Paused task",
                    "recurrence_type": "daily",
                    "status": "paused",
                },
            ]
        }

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        items = result.panel_update["items"]
        statuses = [item["status"] for item in items]
        assert "active" in statuses
        assert "paused" in statuses

    def test_recurring_new_starts_creation_flow(self) -> None:
        """Test: /recurring new starts creation flow."""
        from jdo.commands.handlers import RecurringHandler

        handler = RecurringHandler()
        cmd = ParsedCommand(CommandType.RECURRING, ["new"], "/recurring new")

        context = {"conversation": []}

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert result.panel_update["mode"] == "draft"
        assert result.panel_update["entity_type"] == "recurring_commitment"
        assert "recurring" in result.message.lower() or "regularly" in result.message.lower()

    def test_recurring_pause_prompts_for_confirmation(self) -> None:
        """Test: /recurring pause <id> sets status to paused."""
        from jdo.commands.handlers import RecurringHandler

        handler = RecurringHandler()
        recurring_id = str(uuid4())
        cmd = ParsedCommand(
            CommandType.RECURRING, ["pause", recurring_id], f"/recurring pause {recurring_id}"
        )

        context = {}

        result = handler.execute(cmd, context)

        assert result.needs_confirmation is True
        assert "pause" in result.message.lower()

    def test_recurring_resume_prompts_for_confirmation(self) -> None:
        """Test: /recurring resume <id> sets status to active."""
        from jdo.commands.handlers import RecurringHandler

        handler = RecurringHandler()
        recurring_id = str(uuid4())
        cmd = ParsedCommand(
            CommandType.RECURRING, ["resume", recurring_id], f"/recurring resume {recurring_id}"
        )

        context = {}

        result = handler.execute(cmd, context)

        assert result.needs_confirmation is True
        assert "resume" in result.message.lower()

    def test_recurring_delete_prompts_for_confirmation(self) -> None:
        """Test: /recurring delete <id> prompts for confirmation."""
        from jdo.commands.handlers import RecurringHandler

        handler = RecurringHandler()
        recurring_id = str(uuid4())
        cmd = ParsedCommand(
            CommandType.RECURRING, ["delete", recurring_id], f"/recurring delete {recurring_id}"
        )

        context = {}

        result = handler.execute(cmd, context)

        assert result.needs_confirmation is True
        assert "delete" in result.message.lower()
        # Should mention instances will remain
        assert "instance" in result.message.lower() or "remain" in result.message.lower()

    def test_show_recurring_displays_recurring_list(self) -> None:
        """Test: /show recurring displays recurring commitment list."""
        from jdo.commands.handlers import ShowHandler

        handler = ShowHandler()
        cmd = ParsedCommand(CommandType.SHOW, ["recurring"], "/show recurring")

        context = {
            "recurring": [
                {"id": uuid4(), "deliverable_template": "Weekly report"},
            ]
        }

        result = handler.execute(cmd, context)

        assert result.panel_update is not None
        assert result.panel_update["entity_type"] == "recurring_commitment"


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


# ============================================================
# Phase 8: Integrity Protocol Command Tests (/atrisk, /cleanup, /integrity)
# ============================================================


class TestAtRiskHandler:
    """Tests for the /atrisk command handler."""

    def test_atrisk_without_commitment_prompts_for_selection(self) -> None:
        """Test: /atrisk without commitment context prompts for selection."""
        from jdo.commands.handlers import AtRiskHandler

        handler = AtRiskHandler()
        cmd = ParsedCommand(CommandType.ATRISK, [], "/atrisk")

        context = {
            "available_commitments": [
                {"id": uuid4(), "deliverable": "Send report", "status": "pending"},
                {"id": uuid4(), "deliverable": "Review docs", "status": "in_progress"},
            ]
        }

        result = handler.execute(cmd, context)

        assert "which" in result.message.lower() or "at risk" in result.message.lower()
        assert result.panel_update is not None
        assert result.panel_update["mode"] == "list"

    def test_atrisk_without_commitments_shows_error(self) -> None:
        """Test: /atrisk without any commitments shows appropriate error."""
        from jdo.commands.handlers import AtRiskHandler

        handler = AtRiskHandler()
        cmd = ParsedCommand(CommandType.ATRISK, [], "/atrisk")

        context = {}  # No commitments at all

        result = handler.execute(cmd, context)

        assert "no active commitments" in result.message.lower()
        assert result.panel_update is None

    def test_atrisk_on_already_at_risk_commitment_shows_message(self) -> None:
        """Test: /atrisk on already at-risk commitment shows appropriate message."""
        from jdo.commands.handlers import AtRiskHandler

        handler = AtRiskHandler()
        cmd = ParsedCommand(CommandType.ATRISK, [], "/atrisk")

        context = {
            "current_commitment": {
                "id": uuid4(),
                "deliverable": "Send report",
                "status": "at_risk",
            }
        }

        result = handler.execute(cmd, context)

        assert "already" in result.message.lower()
        assert "at-risk" in result.message.lower() or "at_risk" in result.message.lower()

    def test_atrisk_on_completed_commitment_shows_error(self) -> None:
        """Test: /atrisk on completed commitment shows error."""
        from jdo.commands.handlers import AtRiskHandler

        handler = AtRiskHandler()
        cmd = ParsedCommand(CommandType.ATRISK, [], "/atrisk")

        context = {
            "current_commitment": {
                "id": uuid4(),
                "deliverable": "Send report",
                "status": "completed",
            }
        }

        result = handler.execute(cmd, context)

        assert "completed" in result.message.lower()
        assert "pending" in result.message.lower() or "in-progress" in result.message.lower()

    def test_atrisk_on_abandoned_commitment_shows_error(self) -> None:
        """Test: /atrisk on abandoned commitment shows error."""
        from jdo.commands.handlers import AtRiskHandler

        handler = AtRiskHandler()
        cmd = ParsedCommand(CommandType.ATRISK, [], "/atrisk")

        context = {
            "current_commitment": {
                "id": uuid4(),
                "deliverable": "Send report",
                "status": "abandoned",
            }
        }

        result = handler.execute(cmd, context)

        assert "abandoned" in result.message.lower()

    def test_atrisk_starts_workflow_for_pending_commitment(self) -> None:
        """Test: /atrisk starts workflow for pending commitment."""
        from jdo.commands.handlers import AtRiskHandler

        handler = AtRiskHandler()
        cmd = ParsedCommand(CommandType.ATRISK, [], "/atrisk")

        commitment_id = uuid4()
        context = {
            "current_commitment": {
                "id": commitment_id,
                "deliverable": "Send quarterly report",
                "status": "pending",
                "stakeholder_name": "Finance Team",
            }
        }

        result = handler.execute(cmd, context)

        # Should ask why the commitment is at risk
        assert "why" in result.message.lower() or "reason" in result.message.lower()
        assert result.panel_update is not None
        assert result.panel_update["mode"] == "atrisk_workflow"
        assert result.draft_data is not None
        assert result.draft_data["commitment_id"] == commitment_id

    def test_atrisk_starts_workflow_for_in_progress_commitment(self) -> None:
        """Test: /atrisk starts workflow for in-progress commitment."""
        from jdo.commands.handlers import AtRiskHandler

        handler = AtRiskHandler()
        cmd = ParsedCommand(CommandType.ATRISK, [], "/atrisk")

        commitment_id = uuid4()
        context = {
            "current_commitment": {
                "id": commitment_id,
                "deliverable": "Send quarterly report",
                "status": "in_progress",
                "stakeholder_name": "Finance Team",
            }
        }

        result = handler.execute(cmd, context)

        # Should ask why the commitment is at risk
        assert "why" in result.message.lower() or "reason" in result.message.lower()
        assert result.panel_update is not None
        assert result.panel_update["workflow_step"] == "reason"

    def test_atrisk_filters_only_active_commitments_in_selection(self) -> None:
        """Test: /atrisk only shows pending/in_progress commitments for selection."""
        from jdo.commands.handlers import AtRiskHandler

        handler = AtRiskHandler()
        cmd = ParsedCommand(CommandType.ATRISK, [], "/atrisk")

        context = {
            "available_commitments": [
                {"id": uuid4(), "deliverable": "Active one", "status": "pending"},
                {"id": uuid4(), "deliverable": "Completed one", "status": "completed"},
                {"id": uuid4(), "deliverable": "Active two", "status": "in_progress"},
                {"id": uuid4(), "deliverable": "Abandoned one", "status": "abandoned"},
            ]
        }

        result = handler.execute(cmd, context)

        # Panel should only show active commitments
        assert result.panel_update is not None
        assert len(result.panel_update["items"]) == 2  # Only pending and in_progress


class TestCleanupHandler:
    """Tests for the /cleanup command handler."""

    def test_cleanup_without_commitment_prompts_for_selection(self) -> None:
        """Test: /cleanup without commitment context prompts for selection."""
        from jdo.commands.handlers import CleanupHandler

        handler = CleanupHandler()
        cmd = ParsedCommand(CommandType.CLEANUP, [], "/cleanup")

        context = {}

        result = handler.execute(cmd, context)

        assert "select" in result.message.lower() or "commitment" in result.message.lower()
        assert result.panel_update is None

    def test_cleanup_without_cleanup_plan_suggests_atrisk(self) -> None:
        """Test: /cleanup on commitment without cleanup plan suggests /atrisk."""
        from jdo.commands.handlers import CleanupHandler

        handler = CleanupHandler()
        cmd = ParsedCommand(CommandType.CLEANUP, [], "/cleanup")

        context = {
            "current_commitment": {
                "id": uuid4(),
                "deliverable": "Send report",
                "status": "pending",
            }
        }

        result = handler.execute(cmd, context)

        assert "doesn't have a cleanup plan" in result.message.lower()
        assert "/atrisk" in result.message

    def test_cleanup_shows_cleanup_plan_details(self) -> None:
        """Test: /cleanup shows cleanup plan details."""
        from jdo.commands.handlers import CleanupHandler

        handler = CleanupHandler()
        cmd = ParsedCommand(CommandType.CLEANUP, [], "/cleanup")

        context = {
            "current_commitment": {
                "id": uuid4(),
                "deliverable": "Send report",
                "status": "at_risk",
            },
            "cleanup_plan": {
                "id": uuid4(),
                "status": "planned",
                "impact_description": "Client may lose trust",
                "mitigation_actions": ["Email weekly update", "Offer discount"],
                "notification_task_completed": False,
            },
        }

        result = handler.execute(cmd, context)

        assert "cleanup plan" in result.message.lower()
        assert "planned" in result.message.lower()
        assert "client may lose trust" in result.message.lower()
        assert result.panel_update is not None
        assert result.panel_update["mode"] == "cleanup"

    def test_cleanup_shows_notification_status(self) -> None:
        """Test: /cleanup shows notification completion status."""
        from jdo.commands.handlers import CleanupHandler

        handler = CleanupHandler()
        cmd = ParsedCommand(CommandType.CLEANUP, [], "/cleanup")

        context = {
            "current_commitment": {
                "id": uuid4(),
                "deliverable": "Send report",
                "status": "at_risk",
            },
            "cleanup_plan": {
                "id": uuid4(),
                "status": "in_progress",
                "impact_description": "Delay affects project timeline",
                "mitigation_actions": [],
                "notification_task_completed": True,
            },
        }

        result = handler.execute(cmd, context)

        assert "notification sent" in result.message.lower()
        assert "yes" in result.message.lower()

    def test_cleanup_shows_mitigation_actions(self) -> None:
        """Test: /cleanup shows mitigation actions list."""
        from jdo.commands.handlers import CleanupHandler

        handler = CleanupHandler()
        cmd = ParsedCommand(CommandType.CLEANUP, [], "/cleanup")

        context = {
            "current_commitment": {
                "id": uuid4(),
                "deliverable": "Send report",
                "status": "at_risk",
            },
            "cleanup_plan": {
                "id": uuid4(),
                "status": "in_progress",
                "impact_description": "Delay",
                "mitigation_actions": ["Action 1", "Action 2", "Action 3"],
                "notification_task_completed": True,
            },
        }

        result = handler.execute(cmd, context)

        assert "mitigation" in result.message.lower()
        assert "1. Action 1" in result.message
        assert "2. Action 2" in result.message
        assert "3. Action 3" in result.message


class TestIntegrityHandler:
    """Tests for the /integrity command handler."""

    def test_integrity_shows_empty_dashboard_for_new_user(self) -> None:
        """Test: /integrity shows A+ for new user with no history."""
        from jdo.commands.handlers import IntegrityHandler

        handler = IntegrityHandler()
        cmd = ParsedCommand(CommandType.INTEGRITY, [], "/integrity")

        context = {}  # No metrics available

        result = handler.execute(cmd, context)

        assert "A+" in result.message
        assert "clean slate" in result.message.lower()
        assert result.panel_update is not None
        assert result.panel_update["mode"] == "integrity"
        assert result.panel_update["data"]["is_empty"] is True

    def test_integrity_shows_dashboard_with_metrics(self) -> None:
        """Test: /integrity shows dashboard with actual metrics."""
        from jdo.commands.handlers import IntegrityHandler

        handler = IntegrityHandler()
        cmd = ParsedCommand(CommandType.INTEGRITY, [], "/integrity")

        context = {
            "integrity_metrics": {
                "letter_grade": "B+",
                "composite_score": 88.5,
                "on_time_rate": 0.9,
                "notification_timeliness": 0.85,
                "cleanup_completion_rate": 0.8,
                "current_streak_weeks": 3,
                "total_completed": 20,
                "total_on_time": 18,
                "total_at_risk": 2,
                "total_abandoned": 0,
            }
        }

        result = handler.execute(cmd, context)

        assert "B+" in result.message
        assert "88.5%" in result.message or "88.5" in result.message
        assert "90%" in result.message  # on_time_rate * 100
        assert "3 week" in result.message.lower()
        assert result.panel_update is not None
        assert result.panel_update["data"]["grade_color"] == "blue"

    def test_integrity_shows_all_metrics(self) -> None:
        """Test: /integrity shows all four main metrics."""
        from jdo.commands.handlers import IntegrityHandler

        handler = IntegrityHandler()
        cmd = ParsedCommand(CommandType.INTEGRITY, [], "/integrity")

        context = {
            "integrity_metrics": {
                "letter_grade": "A-",
                "composite_score": 91.0,
                "on_time_rate": 0.95,
                "notification_timeliness": 0.9,
                "cleanup_completion_rate": 0.85,
                "current_streak_weeks": 5,
                "total_completed": 50,
                "total_on_time": 47,
                "total_at_risk": 3,
                "total_abandoned": 1,
            }
        }

        result = handler.execute(cmd, context)

        # Check all metrics are shown
        assert "on-time delivery" in result.message.lower()
        assert "notification" in result.message.lower()
        assert "cleanup" in result.message.lower()
        assert "streak" in result.message.lower()

    def test_integrity_shows_grade_with_color(self) -> None:
        """Test: /integrity shows grade with appropriate color code."""
        from jdo.commands.handlers import IntegrityHandler

        handler = IntegrityHandler()
        cmd = ParsedCommand(CommandType.INTEGRITY, [], "/integrity")

        # Test various grades and their colors
        grade_color_tests = [
            ("A+", "green"),
            ("A", "green"),
            ("A-", "green"),
            ("B+", "blue"),
            ("B", "blue"),
            ("B-", "blue"),
            ("C+", "yellow"),
            ("C", "yellow"),
            ("C-", "yellow"),
            ("D+", "red"),
            ("D", "red"),
            ("D-", "red"),
            ("F", "red"),
        ]

        for grade, expected_color in grade_color_tests:
            context = {
                "integrity_metrics": {
                    "letter_grade": grade,
                    "composite_score": 50.0,
                    "on_time_rate": 0.5,
                    "notification_timeliness": 0.5,
                    "cleanup_completion_rate": 0.5,
                    "current_streak_weeks": 0,
                    "total_completed": 10,
                    "total_on_time": 5,
                    "total_at_risk": 2,
                    "total_abandoned": 1,
                }
            }

            result = handler.execute(cmd, context)

            assert result.panel_update is not None
            assert result.panel_update["data"]["grade_color"] == expected_color, (
                f"Grade {grade} should have color {expected_color}"
            )

    def test_integrity_shows_history_stats_when_present(self) -> None:
        """Test: /integrity shows history stats when there are at-risk or abandoned."""
        from jdo.commands.handlers import IntegrityHandler

        handler = IntegrityHandler()
        cmd = ParsedCommand(CommandType.INTEGRITY, [], "/integrity")

        context = {
            "integrity_metrics": {
                "letter_grade": "B",
                "composite_score": 85.0,
                "on_time_rate": 0.8,
                "notification_timeliness": 0.9,
                "cleanup_completion_rate": 0.75,
                "current_streak_weeks": 2,
                "total_completed": 30,
                "total_on_time": 24,
                "total_at_risk": 5,
                "total_abandoned": 2,
            }
        }

        result = handler.execute(cmd, context)

        # Should show history section
        assert "history" in result.message.lower()
        assert "30" in result.message  # total_completed
        assert "at-risk" in result.message.lower() or "at_risk" in result.message.lower()


class TestIntegrityCommandRegistration:
    """Tests for integrity command registration in the handler registry."""

    def test_atrisk_handler_is_registered(self) -> None:
        """Test: AtRiskHandler is registered for ATRISK command type."""
        from jdo.commands.handlers import AtRiskHandler, get_handler

        handler = get_handler(CommandType.ATRISK)
        assert isinstance(handler, AtRiskHandler)

    def test_cleanup_handler_is_registered(self) -> None:
        """Test: CleanupHandler is registered for CLEANUP command type."""
        from jdo.commands.handlers import CleanupHandler, get_handler

        handler = get_handler(CommandType.CLEANUP)
        assert isinstance(handler, CleanupHandler)

    def test_integrity_handler_is_registered(self) -> None:
        """Test: IntegrityHandler is registered for INTEGRITY command type."""
        from jdo.commands.handlers import IntegrityHandler, get_handler

        handler = get_handler(CommandType.INTEGRITY)
        assert isinstance(handler, IntegrityHandler)


class TestHelpHandlerIntegrityCommands:
    """Tests for /help with integrity commands."""

    def test_help_lists_atrisk_command(self) -> None:
        """Test: /help lists /atrisk command."""
        from jdo.commands.handlers import HelpHandler

        handler = HelpHandler()
        cmd = ParsedCommand(CommandType.HELP, [], "/help")

        result = handler.execute(cmd, {})

        assert "/atrisk" in result.message

    def test_help_lists_cleanup_command(self) -> None:
        """Test: /help lists /cleanup command."""
        from jdo.commands.handlers import HelpHandler

        handler = HelpHandler()
        cmd = ParsedCommand(CommandType.HELP, [], "/help")

        result = handler.execute(cmd, {})

        assert "/cleanup" in result.message

    def test_help_lists_integrity_command(self) -> None:
        """Test: /help lists /integrity command."""
        from jdo.commands.handlers import HelpHandler

        handler = HelpHandler()
        cmd = ParsedCommand(CommandType.HELP, [], "/help")

        result = handler.execute(cmd, {})

        assert "/integrity" in result.message

    def test_help_atrisk_shows_details(self) -> None:
        """Test: /help atrisk shows command details."""
        from jdo.commands.handlers import HelpHandler

        handler = HelpHandler()
        cmd = ParsedCommand(CommandType.HELP, ["atrisk"], "/help atrisk")

        result = handler.execute(cmd, {})

        assert "at-risk" in result.message.lower() or "atrisk" in result.message.lower()
        assert "honor" in result.message.lower() or "workflow" in result.message.lower()

    def test_help_cleanup_shows_details(self) -> None:
        """Test: /help cleanup shows command details."""
        from jdo.commands.handlers import HelpHandler

        handler = HelpHandler()
        cmd = ParsedCommand(CommandType.HELP, ["cleanup"], "/help cleanup")

        result = handler.execute(cmd, {})

        assert "cleanup" in result.message.lower()
        assert "impact" in result.message.lower() or "mitigation" in result.message.lower()

    def test_help_integrity_shows_details(self) -> None:
        """Test: /help integrity shows command details."""
        from jdo.commands.handlers import HelpHandler

        handler = HelpHandler()
        cmd = ParsedCommand(CommandType.HELP, ["integrity"], "/help integrity")

        result = handler.execute(cmd, {})

        assert "integrity" in result.message.lower()
        assert "grade" in result.message.lower() or "score" in result.message.lower()


# ============================================================
# Phase 9: /abandon Command Tests (D3 & D4)
# ============================================================


class TestAbandonHandler:
    """Tests for the /abandon command handler."""

    def test_abandon_without_commitment_prompts_for_selection(self) -> None:
        """Test: /abandon without commitment context prompts for selection."""
        from jdo.commands.handlers import AbandonHandler

        handler = AbandonHandler()
        cmd = ParsedCommand(CommandType.ABANDON, [], "/abandon")

        context = {
            "available_commitments": [
                {"id": uuid4(), "deliverable": "Send report", "status": "pending"},
                {"id": uuid4(), "deliverable": "Review docs", "status": "in_progress"},
            ]
        }

        result = handler.execute(cmd, context)

        assert "which" in result.message.lower() or "abandon" in result.message.lower()
        assert result.panel_update is not None
        assert result.panel_update["mode"] == "list"

    def test_abandon_without_commitments_shows_error(self) -> None:
        """Test: /abandon without any commitments shows appropriate error."""
        from jdo.commands.handlers import AbandonHandler

        handler = AbandonHandler()
        cmd = ParsedCommand(CommandType.ABANDON, [], "/abandon")

        context = {}  # No commitments at all

        result = handler.execute(cmd, context)

        assert "no active commitments" in result.message.lower()
        assert result.panel_update is None

    def test_abandon_on_completed_commitment_shows_error(self) -> None:
        """Test: /abandon on completed commitment shows error."""
        from jdo.commands.handlers import AbandonHandler

        handler = AbandonHandler()
        cmd = ParsedCommand(CommandType.ABANDON, [], "/abandon")

        context = {
            "current_commitment": {
                "id": uuid4(),
                "deliverable": "Send report",
                "status": "completed",
            }
        }

        result = handler.execute(cmd, context)

        assert "completed" in result.message.lower()
        assert "cannot be abandoned" in result.message.lower()

    def test_abandon_on_already_abandoned_commitment_shows_error(self) -> None:
        """Test: /abandon on already abandoned commitment shows error."""
        from jdo.commands.handlers import AbandonHandler

        handler = AbandonHandler()
        cmd = ParsedCommand(CommandType.ABANDON, [], "/abandon")

        context = {
            "current_commitment": {
                "id": uuid4(),
                "deliverable": "Send report",
                "status": "abandoned",
            }
        }

        result = handler.execute(cmd, context)

        assert "already abandoned" in result.message.lower()

    def test_abandon_on_pending_commitment_without_stakeholder_confirms(self) -> None:
        """Test: /abandon on pending commitment without stakeholder asks for confirmation."""
        from jdo.commands.handlers import AbandonHandler

        handler = AbandonHandler()
        cmd = ParsedCommand(CommandType.ABANDON, [], "/abandon")

        context = {
            "current_commitment": {
                "id": uuid4(),
                "deliverable": "Personal task",
                "status": "pending",
                # No stakeholder_name
            }
        }

        result = handler.execute(cmd, context)

        assert "abandon" in result.message.lower()
        assert "personal task" in result.message.lower()
        assert result.needs_confirmation is True
        assert result.panel_update is not None
        assert result.panel_update["action"] == "abandon"

    def test_abandon_on_pending_commitment_with_stakeholder_prompts_atrisk_first(
        self,
    ) -> None:
        """Test: D4 - /abandon on commitment with stakeholder prompts to mark at-risk first."""
        from jdo.commands.handlers import AbandonHandler

        handler = AbandonHandler()
        cmd = ParsedCommand(CommandType.ABANDON, [], "/abandon")

        context = {
            "current_commitment": {
                "id": uuid4(),
                "deliverable": "Send quarterly report",
                "status": "pending",
                "stakeholder_name": "Finance Team",
            }
        }

        result = handler.execute(cmd, context)

        # D4: Should prompt to mark at-risk first
        assert "finance team" in result.message.lower()
        assert "at-risk" in result.message.lower() or "atrisk" in result.message.lower()
        assert "recommend" in result.message.lower() or "would you like" in result.message.lower()
        assert result.panel_update is not None
        assert result.panel_update["mode"] == "abandon_prompt"
        assert result.panel_update["prompt_type"] == "atrisk_first"

    def test_abandon_on_in_progress_commitment_with_stakeholder_prompts_atrisk_first(
        self,
    ) -> None:
        """Test: D4 - /abandon on in_progress with stakeholder prompts mark at-risk."""
        from jdo.commands.handlers import AbandonHandler

        handler = AbandonHandler()
        cmd = ParsedCommand(CommandType.ABANDON, [], "/abandon")

        context = {
            "current_commitment": {
                "id": uuid4(),
                "deliverable": "Deliver presentation",
                "status": "in_progress",
                "stakeholder_name": "Client",
            }
        }

        result = handler.execute(cmd, context)

        # D4: Should prompt to mark at-risk first
        assert "client" in result.message.lower()
        assert "at-risk" in result.message.lower() or "atrisk" in result.message.lower()

    def test_abandon_at_risk_with_incomplete_notification_warns_user(self) -> None:
        """Test: D3 - /abandon on at-risk with incomplete notification warns user."""
        from jdo.commands.handlers import AbandonHandler

        handler = AbandonHandler()
        cmd = ParsedCommand(CommandType.ABANDON, [], "/abandon")

        commitment_id = uuid4()
        context = {
            "current_commitment": {
                "id": commitment_id,
                "deliverable": "Send quarterly report",
                "status": "at_risk",
                "stakeholder_name": "Finance Team",
            },
            "cleanup_plan": {
                "id": uuid4(),
                "status": "planned",
            },
            "notification_task": {
                "id": uuid4(),
                "status": "pending",  # Not completed
                "is_notification_task": True,
            },
        }

        result = handler.execute(cmd, context)

        # D3: Should warn about incomplete notification
        assert "haven't notified" in result.message.lower()
        assert "finance team" in result.message.lower()
        assert "integrity score" in result.message.lower()
        assert "skipped" in result.message.lower()
        assert result.panel_update is not None
        assert result.panel_update["mode"] == "abandon_warning"
        assert result.panel_update["warning_type"] == "notification_incomplete"
        assert result.needs_confirmation is True
        assert result.draft_data is not None
        assert result.draft_data["skip_notification"] is True

    def test_abandon_at_risk_with_completed_notification_confirms(self) -> None:
        """Test: /abandon on at-risk with completed notification asks for simple confirmation."""
        from jdo.commands.handlers import AbandonHandler

        handler = AbandonHandler()
        cmd = ParsedCommand(CommandType.ABANDON, [], "/abandon")

        context = {
            "current_commitment": {
                "id": uuid4(),
                "deliverable": "Send quarterly report",
                "status": "at_risk",
                "stakeholder_name": "Finance Team",
            },
            "cleanup_plan": {
                "id": uuid4(),
                "status": "in_progress",
            },
            "notification_task": {
                "id": uuid4(),
                "status": "completed",  # Completed
                "is_notification_task": True,
            },
        }

        result = handler.execute(cmd, context)

        # Should allow abandonment without warning
        assert "notified" in result.message.lower()
        assert "finance team" in result.message.lower()
        assert result.needs_confirmation is True
        # No warning about skipping
        assert "skipped" not in result.message.lower()

    def test_abandon_at_risk_no_notification_task_allows_abandon(self) -> None:
        """Test: /abandon on at-risk without notification task allows abandonment."""
        from jdo.commands.handlers import AbandonHandler

        handler = AbandonHandler()
        cmd = ParsedCommand(CommandType.ABANDON, [], "/abandon")

        context = {
            "current_commitment": {
                "id": uuid4(),
                "deliverable": "Send quarterly report",
                "status": "at_risk",
                "stakeholder_name": "Finance Team",
            },
            "cleanup_plan": {
                "id": uuid4(),
                "status": "planned",
            },
            # No notification_task in context
        }

        result = handler.execute(cmd, context)

        # Should allow abandonment (no notification task to check)
        assert result.needs_confirmation is True

    def test_abandon_filters_only_active_commitments_in_selection(self) -> None:
        """Test: /abandon only shows active commitments for selection."""
        from jdo.commands.handlers import AbandonHandler

        handler = AbandonHandler()
        cmd = ParsedCommand(CommandType.ABANDON, [], "/abandon")

        context = {
            "available_commitments": [
                {"id": uuid4(), "deliverable": "Active one", "status": "pending"},
                {"id": uuid4(), "deliverable": "Completed one", "status": "completed"},
                {"id": uuid4(), "deliverable": "At risk one", "status": "at_risk"},
                {"id": uuid4(), "deliverable": "Abandoned one", "status": "abandoned"},
            ]
        }

        result = handler.execute(cmd, context)

        # Panel should only show active commitments (pending, in_progress, at_risk)
        assert result.panel_update is not None
        assert len(result.panel_update["items"]) == 2  # pending and at_risk

    def test_abandon_selection_shows_at_risk_indicator(self) -> None:
        """Test: /abandon selection list shows at-risk indicator."""
        from jdo.commands.handlers import AbandonHandler

        handler = AbandonHandler()
        cmd = ParsedCommand(CommandType.ABANDON, [], "/abandon")

        context = {
            "available_commitments": [
                {"id": uuid4(), "deliverable": "Normal commitment", "status": "pending"},
                {"id": uuid4(), "deliverable": "At risk commitment", "status": "at_risk"},
            ]
        }

        result = handler.execute(cmd, context)

        # At-risk item should have indicator in message
        assert "at_risk" in result.message.lower() or "⚠️" in result.message


class TestAbandonHandlerRegistration:
    """Tests for abandon command registration in the handler registry."""

    def test_abandon_handler_is_registered(self) -> None:
        """Test: AbandonHandler is registered for ABANDON command type."""
        from jdo.commands.handlers import AbandonHandler, get_handler

        handler = get_handler(CommandType.ABANDON)
        assert isinstance(handler, AbandonHandler)


class TestHelpHandlerAbandonCommand:
    """Tests for /help with abandon command."""

    def test_help_lists_abandon_command(self) -> None:
        """Test: /help lists /abandon command."""
        from jdo.commands.handlers import HelpHandler

        handler = HelpHandler()
        cmd = ParsedCommand(CommandType.HELP, [], "/help")

        result = handler.execute(cmd, {})

        assert "/abandon" in result.message


# ============================================================
# HoursHandler Tests
# ============================================================


class TestHoursHandler:
    """Tests for the /hours command handler."""

    def test_hours_shows_prompt_when_no_args(self) -> None:
        """Test: /hours with no args shows current status and prompt."""
        from jdo.commands.handlers import HoursHandler

        handler = HoursHandler()
        cmd = ParsedCommand(CommandType.HOURS, [], "/hours")

        result = handler.execute(cmd, {})

        assert "Available Hours" in result.message
        assert "How many hours" in result.message
        assert result.needs_confirmation is False

    def test_hours_shows_current_when_set(self) -> None:
        """Test: /hours shows current available hours when set."""
        from jdo.commands.handlers import HoursHandler

        handler = HoursHandler()
        cmd = ParsedCommand(CommandType.HOURS, [], "/hours")

        context = {
            "available_hours_remaining": 4.0,
            "allocated_hours": 2.5,
        }

        result = handler.execute(cmd, context)

        assert "4.0 hours" in result.message
        assert "2.5 hours" in result.message
        assert "Remaining capacity: 1.5" in result.message

    def test_hours_shows_over_allocation_warning(self) -> None:
        """Test: /hours warns when over-allocated."""
        from jdo.commands.handlers import HoursHandler

        handler = HoursHandler()
        cmd = ParsedCommand(CommandType.HOURS, [], "/hours")

        context = {
            "available_hours_remaining": 2.0,
            "allocated_hours": 4.0,
        }

        result = handler.execute(cmd, context)

        assert "OVER-ALLOCATED" in result.message
        assert "2.0 hours" in result.message

    def test_hours_sets_hours_from_arg(self) -> None:
        """Test: /hours 4 sets available hours."""
        from jdo.commands.handlers import HoursHandler

        handler = HoursHandler()
        cmd = ParsedCommand(CommandType.HOURS, ["4"], "/hours 4")

        result = handler.execute(cmd, {})

        assert "Setting available hours" in result.message
        assert "4h" in result.message
        assert result.panel_update is not None
        assert result.panel_update["action"] == "set_hours"
        assert result.panel_update["hours"] == 4.0

    def test_hours_parses_various_formats(self) -> None:
        """Test: /hours parses various time formats."""
        from jdo.commands.handlers import HoursHandler

        handler = HoursHandler()

        # Test "2.5" format
        cmd = ParsedCommand(CommandType.HOURS, ["2.5"], "/hours 2.5")
        result = handler.execute(cmd, {})
        assert result.panel_update is not None
        assert result.panel_update["hours"] == 2.5

        # Test "90min" format
        cmd = ParsedCommand(CommandType.HOURS, ["90min"], "/hours 90min")
        result = handler.execute(cmd, {})
        assert result.panel_update is not None
        assert result.panel_update["hours"] == 1.5

        # Test "1h" format
        cmd = ParsedCommand(CommandType.HOURS, ["1h"], "/hours 1h")
        result = handler.execute(cmd, {})
        assert result.panel_update is not None
        assert result.panel_update["hours"] == 1.0

    def test_hours_invalid_input_shows_error(self) -> None:
        """Test: /hours with invalid input shows error."""
        from jdo.commands.handlers import HoursHandler

        handler = HoursHandler()
        cmd = ParsedCommand(CommandType.HOURS, ["abc"], "/hours abc")

        result = handler.execute(cmd, {})

        assert "Could not parse" in result.message
        assert result.panel_update is None

    def test_hours_warns_when_setting_below_allocated(self) -> None:
        """Test: /hours warns when setting below allocated hours."""
        from jdo.commands.handlers import HoursHandler

        handler = HoursHandler()
        cmd = ParsedCommand(CommandType.HOURS, ["2"], "/hours 2")

        context = {
            "allocated_hours": 4.0,
        }

        result = handler.execute(cmd, context)

        assert "Setting available hours" in result.message
        assert "already allocated" in result.message
        assert "over your available time" in result.message


class TestHoursHandlerRegistration:
    """Tests for HoursHandler registration."""

    def test_hours_handler_registered(self) -> None:
        """Test: HoursHandler is registered in handler registry."""
        from jdo.commands.handlers import HoursHandler, get_handler

        handler = get_handler(CommandType.HOURS)
        assert isinstance(handler, HoursHandler)


class TestHelpHandlerHoursCommand:
    """Tests for /help with hours command."""

    def test_help_lists_hours_command(self) -> None:
        """Test: /help lists /hours command."""
        from jdo.commands.handlers import HelpHandler

        handler = HelpHandler()
        cmd = ParsedCommand(CommandType.HELP, [], "/help")

        result = handler.execute(cmd, {})

        assert "/hours" in result.message

    def test_help_hours_shows_detailed_help(self) -> None:
        """Test: /help hours shows detailed help."""
        from jdo.commands.handlers import HelpHandler

        handler = HelpHandler()
        cmd = ParsedCommand(CommandType.HOURS, ["hours"], "/help hours")

        result = handler.execute(cmd, {"args": ["hours"]})

        # Execute with args to get specific help
        cmd = ParsedCommand(CommandType.HELP, ["hours"], "/help hours")
        result = handler.execute(cmd, {})

        assert "time coaching" in result.message.lower() or "/hours" in result.message


# ============================================================
# D8: /recover Command Tests (Recovery Flow)
# ============================================================


class TestRecoverHandler:
    """Tests for the /recover command handler."""

    def test_recover_without_commitment_shows_error(self) -> None:
        """Test: /recover without commitment context shows error."""
        from jdo.commands.handlers import RecoverHandler

        handler = RecoverHandler()
        cmd = ParsedCommand(CommandType.RECOVER, [], "/recover")

        context = {}  # No commitment

        result = handler.execute(cmd, context)

        assert "no commitment" in result.message.lower()
        assert result.panel_update is None

    def test_recover_on_non_at_risk_commitment_shows_error(self) -> None:
        """Test: /recover on non at-risk commitment shows error."""
        from jdo.commands.handlers import RecoverHandler

        handler = RecoverHandler()
        cmd = ParsedCommand(CommandType.RECOVER, [], "/recover")

        context = {
            "current_commitment": {
                "id": uuid4(),
                "deliverable": "In progress task",
                "status": "in_progress",
            }
        }

        result = handler.execute(cmd, context)

        assert "not at-risk" in result.message.lower()
        assert "in_progress" in result.message.lower()

    def test_recover_on_pending_commitment_shows_error(self) -> None:
        """Test: /recover on pending commitment shows error."""
        from jdo.commands.handlers import RecoverHandler

        handler = RecoverHandler()
        cmd = ParsedCommand(CommandType.RECOVER, [], "/recover")

        context = {
            "current_commitment": {
                "id": uuid4(),
                "deliverable": "Pending task",
                "status": "pending",
            }
        }

        result = handler.execute(cmd, context)

        assert "not at-risk" in result.message.lower()

    def test_recover_on_completed_commitment_shows_error(self) -> None:
        """Test: /recover on completed commitment shows error."""
        from jdo.commands.handlers import RecoverHandler

        handler = RecoverHandler()
        cmd = ParsedCommand(CommandType.RECOVER, [], "/recover")

        context = {
            "current_commitment": {
                "id": uuid4(),
                "deliverable": "Done task",
                "status": "completed",
            }
        }

        result = handler.execute(cmd, context)

        assert "not at-risk" in result.message.lower()


class TestRecoverHandlerRegistration:
    """Tests for RecoverHandler registration."""

    def test_recover_handler_registered(self) -> None:
        """Test: RecoverHandler is registered in handler registry."""
        from jdo.commands.handlers import RecoverHandler, get_handler

        handler = get_handler(CommandType.RECOVER)
        assert isinstance(handler, RecoverHandler)


class TestHelpHandlerRecoverCommand:
    """Tests for /help with recover command."""

    def test_help_lists_recover_command(self) -> None:
        """Test: /help lists /recover command."""
        from jdo.commands.handlers import HelpHandler

        handler = HelpHandler()
        cmd = ParsedCommand(CommandType.HELP, [], "/help")

        result = handler.execute(cmd, {})

        assert "/recover" in result.message

    def test_help_recover_shows_detailed_help(self) -> None:
        """Test: /help recover shows detailed help."""
        from jdo.commands.handlers import HelpHandler

        handler = HelpHandler()
        cmd = ParsedCommand(CommandType.HELP, ["recover"], "/help recover")

        result = handler.execute(cmd, {})

        assert "recover" in result.message.lower()
        assert "at-risk" in result.message.lower()
        assert "in-progress" in result.message.lower() or "in_progress" in result.message.lower()
