"""Tests for utility handlers module."""

from __future__ import annotations

import pytest

from jdo.commands.handlers.utility_handlers import (
    CancelHandler,
    EditHandler,
    HelpHandler,
    HoursHandler,
    ShowHandler,
    TriageHandler,
    TypeHandler,
    ViewHandler,
)
from jdo.commands.parser import CommandType, ParsedCommand
from jdo.models.draft import EntityType


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


class TestShowHandler:
    """Tests for ShowHandler."""

    def test_show_with_no_args_shows_help(self) -> None:
        """Test that /show with no args shows help."""
        handler = ShowHandler()
        cmd = make_command("show")
        context: dict[str, object] = {}

        result = handler.execute(cmd, context)

        assert result.panel_update is None
        assert "Usage: /show" in result.message
        assert "Available types:" in result.message

    def test_show_with_unknown_arg_shows_help(self) -> None:
        """Test that /show with unknown arg shows help."""
        handler = ShowHandler()
        cmd = make_command("show", ["unknown"])
        context: dict[str, object] = {}

        result = handler.execute(cmd, context)

        assert result.panel_update is None
        assert "Usage: /show" in result.message

    def test_show_goals(self) -> None:
        """Test /show goals."""
        handler = ShowHandler()
        cmd = make_command("show", ["goals"])
        context: dict[str, object] = {"goals": [{"id": 1, "title": "Test Goal"}]}

        result = handler.execute(cmd, context)

        assert result.message == "Showing 1 goals."
        assert result.panel_update is not None
        assert result.panel_update["entity_type"] == "goal"
        assert result.panel_update["mode"] == "list"

    def test_show_commitments(self) -> None:
        """Test /show commitments."""
        handler = ShowHandler()
        cmd = make_command("show", ["commitments"])
        context: dict[str, object] = {"commitments": [{"id": 1, "deliverable": "Test"}]}

        result = handler.execute(cmd, context)

        assert result.message == "Showing 1 commitments."
        assert result.panel_update is not None
        assert result.panel_update["entity_type"] == "commitment"

    def test_show_tasks(self) -> None:
        """Test /show tasks."""
        handler = ShowHandler()
        cmd = make_command("show", ["tasks"])
        context: dict[str, object] = {"tasks": [{"id": 1, "description": "Task 1"}]}

        result = handler.execute(cmd, context)

        assert result.message == "Showing 1 tasks."
        assert result.panel_update is not None
        assert result.panel_update["entity_type"] == "task"

    def test_show_visions(self) -> None:
        """Test /show visions."""
        handler = ShowHandler()
        cmd = make_command("show", ["visions"])
        context: dict[str, object] = {"visions": [{"id": 1, "title": "Vision"}]}

        result = handler.execute(cmd, context)

        assert result.message == "Showing 1 visions."
        assert result.panel_update is not None
        assert result.panel_update["entity_type"] == "vision"

    def test_show_milestones(self) -> None:
        """Test /show milestones."""
        handler = ShowHandler()
        cmd = make_command("show", ["milestones"])
        context: dict[str, object] = {"milestones": [{"id": 1, "title": "Milestone"}]}

        result = handler.execute(cmd, context)

        assert result.message == "Showing 1 milestones."
        assert result.panel_update is not None
        assert result.panel_update["entity_type"] == "milestone"

    def test_show_recurring(self) -> None:
        """Test /show recurring."""
        handler = ShowHandler()
        cmd = make_command("show", ["recurring"])
        context: dict[str, object] = {"recurring": [{"id": 1, "pattern": "daily"}]}

        result = handler.execute(cmd, context)

        assert result.message == "Showing 1 recurring."
        assert result.panel_update is not None
        assert result.panel_update["entity_type"] == "recurring_commitment"

    def test_show_stakeholders(self) -> None:
        """Test /show stakeholders."""
        handler = ShowHandler()
        cmd = make_command("show", ["stakeholders"])
        context: dict[str, object] = {"stakeholders": [{"id": 1, "name": "Alice"}]}

        result = handler.execute(cmd, context)

        assert result.message == "Showing 1 stakeholders."
        assert result.panel_update is not None
        assert result.panel_update["entity_type"] == "stakeholder"

    def test_show_orphans_with_data(self) -> None:
        """Test /show orphans with orphan commitments."""
        handler = ShowHandler()
        cmd = make_command("show", ["orphans"])
        context: dict[str, object] = {"orphan_commitments": [{"id": 1}]}

        result = handler.execute(cmd, context)

        assert "1 orphan commitment(s)" in result.message
        assert result.panel_update is not None
        assert result.panel_update["entity_type"] == "commitment"

    def test_show_orphans_empty(self) -> None:
        """Test /show orphans when no orphans exist."""
        handler = ShowHandler()
        cmd = make_command("show", ["orphans"])
        context: dict[str, object] = {"orphan_commitments": []}

        result = handler.execute(cmd, context)

        assert "No orphan commitments found" in result.message

    def test_show_orphan_goals_with_data(self) -> None:
        """Test /show orphan-goals with orphan goals."""
        handler = ShowHandler()
        cmd = make_command("show", ["orphan-goals"])
        context: dict[str, object] = {"orphan_goals": [{"id": 1}]}

        result = handler.execute(cmd, context)

        assert "1 goal(s)" in result.message
        assert result.panel_update is not None
        assert result.panel_update["entity_type"] == "goal"

    def test_show_orphan_goals_empty(self) -> None:
        """Test /show orphan-goals when no orphan goals exist."""
        handler = ShowHandler()
        cmd = make_command("show", ["orphan-goals"])
        context: dict[str, object] = {"orphan_goals": []}

        result = handler.execute(cmd, context)

        assert "No orphan goals found" in result.message

    def test_show_hierarchy(self) -> None:
        """Test /show hierarchy."""
        handler = ShowHandler()
        cmd = make_command("show", ["hierarchy"])
        context: dict[str, object] = {"goals": []}

        result = handler.execute(cmd, context)

        assert "hierarchy tree view" in result.message
        assert result.panel_update is not None
        assert result.panel_update["mode"] == "hierarchy"

    def test_show_empty_list_shows_message(self) -> None:
        """Test that empty lists show appropriate message."""
        handler = ShowHandler()
        cmd = make_command("show", ["goals"])
        context: dict[str, object] = {}

        result = handler.execute(cmd, context)

        assert result.message == "No goals found."


class TestHelpHandler:
    """Tests for HelpHandler."""

    def test_help_specific_command(self) -> None:
        """Test /help with specific command."""
        handler = HelpHandler()
        cmd = make_command("help", ["commit"])
        context: dict[str, object] = {}

        result = handler.execute(cmd, context)

        assert "commit" in result.message.lower()
        assert "deliverable" in result.message

    def test_help_unknown_command(self) -> None:
        """Test /help with unknown command shows general help."""
        handler = HelpHandler()
        cmd = make_command("help", ["unknowncmd"])
        context: dict[str, object] = {}

        result = handler.execute(cmd, context)

        assert "Available commands" in result.message

    def test_help_general(self) -> None:
        """Test /help without arguments."""
        handler = HelpHandler()
        cmd = make_command("help")
        context: dict[str, object] = {}

        result = handler.execute(cmd, context)

        assert "Available commands" in result.message
        assert "/commit" in result.message
        assert "/goal" in result.message
        assert "/help" in result.message


class TestViewHandler:
    """Tests for ViewHandler."""

    def test_view_with_object_data(self) -> None:
        """Test /view with valid object data."""
        handler = ViewHandler()
        cmd = make_command("view", ["123"])
        context: dict[str, object] = {
            "object_data": {
                "entity_type": "commitment",
                "id": "123",
                "deliverable": "Test",
            }
        }

        result = handler.execute(cmd, context)

        assert "Viewing commitment details" in result.message
        assert result.panel_update is not None
        assert result.panel_update["mode"] == "view"
        assert result.panel_update["entity_type"] == "commitment"

    def test_view_without_object_data(self) -> None:
        """Test /view without object data."""
        handler = ViewHandler()
        cmd = make_command("view", ["123"])
        context: dict[str, object] = {}

        result = handler.execute(cmd, context)

        assert "Could not find" in result.message
        assert result.panel_update is None

    def test_view_with_missing_entity_type(self) -> None:
        """Test /view when entity type is missing."""
        handler = ViewHandler()
        cmd = make_command("view", ["123"])
        context: dict[str, object] = {"object_data": {"id": "123"}}

        result = handler.execute(cmd, context)

        assert "Viewing item details" in result.message


class TestCancelHandler:
    """Tests for CancelHandler."""

    def test_cancel_with_draft(self) -> None:
        """Test /cancel with active draft."""
        handler = CancelHandler()
        cmd = make_command("cancel")
        context: dict[str, object] = {"current_draft": {"entity_type": "commitment"}}

        result = handler.execute(cmd, context)

        assert "Cancelled commitment draft" in result.message

    def test_cancel_without_draft(self) -> None:
        """Test /cancel without active draft."""
        handler = CancelHandler()
        cmd = make_command("cancel")
        context: dict[str, object] = {}

        result = handler.execute(cmd, context)

        assert "No active draft to cancel" in result.message


class TestEditHandler:
    """Tests for EditHandler."""

    def test_edit_with_object(self) -> None:
        """Test /edit with selected object."""
        handler = EditHandler()
        cmd = make_command("edit")
        context: dict[str, object] = {"current_object": {"entity_type": "commitment", "id": "123"}}

        result = handler.execute(cmd, context)

        assert "Editing commitment" in result.message
        assert result.panel_update is not None
        assert result.panel_update["mode"] == "draft"
        assert result.needs_confirmation is False

    def test_edit_without_object(self) -> None:
        """Test /edit without selected object."""
        handler = EditHandler()
        cmd = make_command("edit")
        context: dict[str, object] = {}

        result = handler.execute(cmd, context)

        assert "No item selected" in result.message
        assert result.panel_update is None


class TestTypeHandler:
    """Tests for TypeHandler."""

    def test_type_without_args(self) -> None:
        """Test /type without arguments."""
        handler = TypeHandler()
        cmd = make_command("type")
        context: dict[str, object] = {"current_draft": {}}

        result = handler.execute(cmd, context)

        assert "Usage: /type" in result.message

    def test_type_unknown_value(self) -> None:
        """Test /type with 'unknown' as value."""
        handler = TypeHandler()
        cmd = make_command("type", ["unknown"])
        context: dict[str, object] = {"current_draft": {}}

        result = handler.execute(cmd, context)

        assert "Type must be one of" in result.message

    def test_type_without_draft(self) -> None:
        """Test /type without active draft."""
        handler = TypeHandler()
        cmd = make_command("type", ["commitment"])
        context: dict[str, object] = {}

        result = handler.execute(cmd, context)

        assert "No active draft" in result.message

    def test_type_commitment(self) -> None:
        """Test /type commitment."""
        handler = TypeHandler()
        cmd = make_command("type", ["commitment"])
        context: dict[str, object] = {"current_draft": {"raw_text": "Test"}}

        result = handler.execute(cmd, context)

        assert "Set draft type to 'commitment'" in result.message
        assert result.needs_confirmation is True


class TestHoursHandler:
    """Tests for HoursHandler."""

    def test_hours_with_value(self) -> None:
        """Test /hours with numeric value."""
        handler = HoursHandler()
        cmd = make_command("hours", ["4"])
        context: dict[str, object] = {"allocated_hours": 2.0}

        result = handler.execute(cmd, context)

        assert "Setting available hours to" in result.message
        assert result.draft_data is not None
        assert result.draft_data["available_hours"] == 4.0

    def test_hours_with_decimal(self) -> None:
        """Test /hours with decimal value."""
        handler = HoursHandler()
        cmd = make_command("hours", ["2.5"])
        context: dict[str, object] = {}

        result = handler.execute(cmd, context)

        assert "Setting available hours to" in result.message
        assert "2h 30m" in result.message

    def test_hours_with_time_format(self) -> None:
        """Test /hours with time format like '90min'."""
        handler = HoursHandler()
        cmd = make_command("hours", ["90min"])
        context: dict[str, object] = {}

        result = handler.execute(cmd, context)

        assert "Setting available hours to" in result.message
        assert "1h 30m" in result.message

    def test_hours_invalid_format(self) -> None:
        """Test /hours with invalid format."""
        handler = HoursHandler()
        cmd = make_command("hours", ["invalid"])
        context: dict[str, object] = {}

        result = handler.execute(cmd, context)

        assert "Could not parse" in result.message

    def test_hours_without_args_shows_prompt(self) -> None:
        """Test /hours without arguments shows current status."""
        handler = HoursHandler()
        cmd = make_command("hours")
        context: dict[str, object] = {"available_hours_remaining": 6.0, "allocated_hours": 2.0}

        result = handler.execute(cmd, context)

        assert "Available Hours" in result.message
        assert "Current available" in result.message

    def test_hours_without_hours_set(self) -> None:
        """Test /hours when no hours have been set."""
        handler = HoursHandler()
        cmd = make_command("hours")
        context: dict[str, object] = {"allocated_hours": 2.0}

        result = handler.execute(cmd, context)

        assert "Available hours not set" in result.message

    def test_hours_overallocated_warning(self) -> None:
        """Test /hours shows warning when overallocated."""
        handler = HoursHandler()
        cmd = make_command("hours", ["2"])
        context: dict[str, object] = {"allocated_hours": 5.0}

        result = handler.execute(cmd, context)

        assert "over your available time" in result.message


class TestTriageHandler:
    """Tests for TriageHandler."""

    def test_triage_no_items(self) -> None:
        """Test /triage when no items to triage."""
        handler = TriageHandler()
        cmd = make_command("triage")
        context: dict[str, object] = {"triage_items": []}

        result = handler.execute(cmd, context)

        assert "No items to triage" in result.message

    def test_triage_complete(self) -> None:
        """Test /triage when all items processed."""
        handler = TriageHandler()
        cmd = make_command("triage")
        context: dict[str, object] = {"triage_items": [{"id": 1}], "triage_index": 1}

        result = handler.execute(cmd, context)

        assert "Triage complete" in result.message

    def test_triage_first_item_no_analysis(self) -> None:
        """Test /triage first item triggers analysis."""
        handler = TriageHandler()
        cmd = make_command("triage")
        context: dict[str, object] = {
            "triage_items": [{"id": 1, "raw_text": "Test item"}],
            "triage_index": 0,
        }

        result = handler.execute(cmd, context)

        assert "Triage item 1 of 1" in result.message
        assert "Analyzing" in result.message
        assert result.panel_update is not None
        assert result.panel_update["needs_analysis"] is True

    def test_triage_with_analysis_confident(self) -> None:
        """Test /triage shows analysis when confident."""
        handler = TriageHandler()
        cmd = make_command("triage")
        context: dict[str, object] = {
            "triage_items": [{"id": 1, "raw_text": "Test item"}],
            "triage_index": 0,
            "triage_analysis": {
                "is_confident": True,
                "classification": {
                    "suggested_type": "commitment",
                    "confidence": 0.9,
                    "reasoning": "Test reasoning",
                },
            },
        }

        result = handler.execute(cmd, context)

        assert "Suggested type: commitment" in result.message
        assert "90% confident" in result.message

    def test_triage_with_analysis_not_confident(self) -> None:
        """Test /triage shows question when not confident."""
        handler = TriageHandler()
        cmd = make_command("triage")
        context: dict[str, object] = {
            "triage_items": [{"id": 1, "raw_text": "Test item"}],
            "triage_index": 0,
            "triage_analysis": {
                "is_confident": False,
                "question": {"question": "What type of item is this?"},
            },
        }

        result = handler.execute(cmd, context)

        assert "Question" in result.message
        assert "commitment" in result.message
