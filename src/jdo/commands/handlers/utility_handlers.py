"""Utility command handler implementations.

Includes handlers for help, show, view, cancel, edit, type, hours, and triage commands.
"""

from __future__ import annotations

from typing import Any, ClassVar

from jdo.ai.time_parsing import format_hours, parse_time_input
from jdo.commands.handlers.base import CommandHandler, HandlerResult
from jdo.commands.parser import ParsedCommand
from jdo.models.draft import EntityType


class ShowHandler(CommandHandler):
    """Handler for /show command - displays lists of entities."""

    # Map show arguments to entity types
    _ENTITY_MAP: ClassVar[dict[str, str]] = {
        "goals": "goal",
        "commitments": "commitment",
        "tasks": "task",
        "visions": "vision",
        "milestones": "milestone",
        "recurring": "recurring_commitment",
        "stakeholders": "stakeholder",
        "orphans": "orphan",
        "hierarchy": "hierarchy",
        "orphan-goals": "orphan-goals",
    }

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute /show command.

        Args:
            cmd: The parsed command with entity type argument.
            context: Context with entity lists.

        Returns:
            HandlerResult with list panel and message.
        """
        if not cmd.args:
            return self._show_help()

        entity_arg = cmd.args[0].lower()

        if entity_arg not in self._ENTITY_MAP:
            return self._show_help()

        entity_type = self._ENTITY_MAP[entity_arg]

        # Special handling for orphans
        if entity_type == "orphan":
            return self._show_orphans(context)

        # Special handling for hierarchy
        if entity_type == "hierarchy":
            return self._show_hierarchy(context)

        # Special handling for orphan-goals
        if entity_type == "orphan-goals":
            return self._show_orphan_goals(context)

        # Get items from context
        items = context.get(entity_arg, context.get(f"{entity_type}s", []))

        message = f"No {entity_arg} found." if not items else f"Showing {len(items)} {entity_arg}."

        return HandlerResult(
            message=message,
            panel_update={
                "mode": "list",
                "entity_type": entity_type,
                "items": items,
            },
            draft_data=None,
            needs_confirmation=False,
        )

    def _show_orphans(self, context: dict[str, Any]) -> HandlerResult:
        """Show orphan commitments (not linked to goals/milestones)."""
        orphans = context.get("orphan_commitments", [])

        if orphans:
            message = f"Found {len(orphans)} orphan commitment(s) not linked to any goal."
        else:
            message = "No orphan commitments found. All commitments are linked!"

        return HandlerResult(
            message=message,
            panel_update={
                "mode": "list",
                "entity_type": "commitment",
                "items": orphans,
            },
            draft_data=None,
            needs_confirmation=False,
        )

    def _show_hierarchy(self, context: dict[str, Any]) -> HandlerResult:
        """Show full hierarchy tree view."""
        return HandlerResult(
            message="Showing hierarchy tree view.",
            panel_update={
                "mode": "hierarchy",
                "entity_type": "hierarchy",
                "data": context,
            },
            draft_data=None,
            needs_confirmation=False,
        )

    def _show_orphan_goals(self, context: dict[str, Any]) -> HandlerResult:
        """Show goals not linked to any vision."""
        orphan_goals = context.get("orphan_goals", [])

        if orphan_goals:
            message = f"Found {len(orphan_goals)} goal(s) not linked to any vision."
        else:
            message = "No orphan goals found. All goals are linked to visions!"

        return HandlerResult(
            message=message,
            panel_update={
                "mode": "list",
                "entity_type": "goal",
                "items": orphan_goals,
            },
            draft_data=None,
            needs_confirmation=False,
        )

    def _show_help(self) -> HandlerResult:
        """Show available /show options."""
        lines = [
            "Usage: /show <type>",
            "",
            "Available types:",
            "  goals        - Show all goals",
            "  commitments  - Show all commitments",
            "  tasks        - Show tasks for current commitment",
            "  visions      - Show all visions",
            "  milestones   - Show milestones for current goal",
            "  recurring    - Show recurring commitments",
            "  stakeholders - Show all stakeholders",
            "  orphans      - Show unlinked commitments",
            "  orphan-goals - Show goals without a vision",
            "  hierarchy    - Show full hierarchy tree",
        ]
        return HandlerResult(
            message="\n".join(lines),
            panel_update=None,
            draft_data=None,
            needs_confirmation=False,
        )


class HelpHandler(CommandHandler):
    """Handler for /help command - shows command help."""

    _COMMAND_HELP: ClassVar[dict[str, str]] = {
        "commit": (
            "/commit - Create a new commitment\n\n"
            "A commitment has:\n"
            "  - deliverable: What you're committing to deliver\n"
            "  - stakeholder: Who you're making the commitment to\n"
            "  - due_date: When it's due\n"
            "  - due_time: Specific time (optional, defaults to 9am)\n\n"
            "Example: Just describe your commitment in the chat, then type /commit"
        ),
        "goal": (
            "/goal - Create a new goal\n\n"
            "A goal has:\n"
            "  - title: Short name for the goal\n"
            "  - problem_statement: What problem you're solving\n"
            "  - solution_vision: What success looks like\n\n"
            "Goals help organize related commitments."
        ),
        "task": (
            "/task - Add a task to the current commitment\n\n"
            "Tasks break down commitments into smaller steps."
        ),
        "vision": (
            "/vision - Manage visions\n\n"
            "Commands:\n"
            "  /vision        - List all visions\n"
            "  /vision new    - Create a new vision\n"
            "  /vision review - Show visions due for review"
        ),
        "milestone": (
            "/milestone - Manage milestones\n\n"
            "Commands:\n"
            "  /milestone      - List milestones for current goal\n"
            "  /milestone new  - Create a new milestone"
        ),
        "recurring": (
            "/recurring - Manage recurring commitments\n\n"
            "Commands:\n"
            "  /recurring          - List all recurring commitments\n"
            "  /recurring new      - Create a new recurring commitment\n"
            "  /recurring pause    - Pause a recurring commitment\n"
            "  /recurring resume   - Resume a paused recurring commitment\n"
            "  /recurring delete   - Delete a recurring commitment"
        ),
        "show": (
            "/show <type> - Display lists\n\n"
            "Types: goals, commitments, tasks, visions, milestones, recurring, "
            "stakeholders, orphans"
        ),
        "triage": (
            "/triage - Process captured items\n\n"
            "Starts the triage workflow to classify captured items.\n"
            'Use `jdo capture "text"` from the command line to capture ideas.\n\n'
            "During triage:\n"
            "  [a] Accept - create with suggested type\n"
            "  [c] Change - choose a different type\n"
            "  [d] Delete - remove the item\n"
            "  [s] Skip - come back later\n"
            "  [q] Quit - exit triage"
        ),
        "atrisk": (
            "/atrisk - Mark commitment as at-risk\n\n"
            "Starts the Honor-Your-Word protocol when you might miss a commitment.\n\n"
            "The workflow:\n"
            "  1. Explain why the commitment is at risk\n"
            "  2. Describe the impact on stakeholders\n"
            "  3. Propose a resolution or new timeline\n"
            "  4. AI drafts a notification message\n"
            "  5. A notification task is created at position 0\n\n"
            "Completing the notification task maintains your integrity score."
        ),
        "cleanup": (
            "/cleanup - View or update cleanup plan\n\n"
            "Shows the cleanup plan for an at-risk or abandoned commitment.\n\n"
            "The cleanup plan includes:\n"
            "  - Impact description\n"
            "  - Mitigation actions\n"
            "  - Notification status\n"
            "  - Plan status\n\n"
            "Update by describing changes in the chat:\n"
            '  "Add mitigation: follow up weekly"'
        ),
        "integrity": (
            "/integrity - Show integrity dashboard\n\n"
            "Displays your integrity metrics:\n"
            "  - Overall letter grade (A+ to F)\n"
            "  - On-time delivery rate (40% of score)\n"
            "  - Notification timeliness (25% of score)\n"
            "  - Cleanup completion rate (25% of score)\n"
            "  - Reliability streak bonus (10% of score)\n\n"
            "New users start with an A+ (clean slate)."
        ),
        "abandon": (
            "/abandon - Mark commitment as abandoned\n\n"
            "Abandons a commitment you can no longer complete.\n\n"
            "Soft enforcement rules:\n"
            "  - If commitment has a stakeholder, suggests marking at-risk first\n"
            "  - If commitment is at-risk with incomplete notification, warns about "
            "integrity impact\n"
            "  - Allows override after showing warning\n\n"
            "Abandoning without notifying stakeholders affects your integrity score."
        ),
        "hours": (
            "/hours [amount] - Set available hours for time coaching\n\n"
            "Set how many hours you have remaining today to work on tasks.\n"
            "This enables AI coaching about time allocation.\n\n"
            "Usage:\n"
            "  /hours        - Show current hours and prompt for input\n"
            "  /hours 4      - Set 4 hours available\n"
            "  /hours 2.5    - Set 2.5 hours available\n"
            "  /hours 90min  - Set 90 minutes (1.5 hours) available\n\n"
            "The AI will warn you when task estimates exceed available time."
        ),
        "recover": (
            "/recover - Recover an at-risk commitment\n\n"
            "Moves an at-risk commitment back to in-progress status.\n"
            "Use this when the situation has improved and you can deliver.\n\n"
            "The workflow:\n"
            "  1. Select an at-risk commitment (or have one in context)\n"
            "  2. Run /recover to change status to in_progress\n"
            "  3. Cleanup plan is cancelled automatically\n"
            "  4. If notification task is pending, you'll be asked:\n"
            "     - '/recover resolved' to skip notification\n"
            "     - Keep the task to complete it\n\n"
            "This is the happy path when things get back on track."
        ),
    }

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:  # noqa: ARG002
        """Execute /help command.

        Args:
            cmd: The parsed command with optional command name.
            context: Context (not used).

        Returns:
            HandlerResult with help text.
        """
        if cmd.args:
            command_name = cmd.args[0].lower()
            if command_name in self._COMMAND_HELP:
                return HandlerResult(
                    message=self._COMMAND_HELP[command_name],
                    panel_update=None,
                    draft_data=None,
                    needs_confirmation=False,
                )

        # General help
        lines = [
            "Available commands:",
            "",
            "  /commit     - Create a new commitment",
            "  /goal       - Create a new goal",
            "  /task       - Add a task to a commitment",
            "  /vision     - Manage visions",
            "  /milestone  - Manage milestones",
            "  /recurring  - Manage recurring commitments",
            "  /triage     - Process captured items",
            "  /show       - Display entity lists",
            "  /view       - View a specific item",
            "  /complete   - Mark item as completed",
            "  /abandon    - Mark commitment as abandoned",
            "  /cancel     - Cancel current draft",
            "  /atrisk     - Mark commitment as at-risk",
            "  /recover    - Recover at-risk commitment",
            "  /cleanup    - View/update cleanup plan",
            "  /integrity  - Show integrity dashboard",
            "  /hours      - Set available hours for time coaching",
            "  /help       - Show this help",
            "",
            "Type /help <command> for more details on a specific command.",
        ]
        return HandlerResult(
            message="\n".join(lines),
            panel_update=None,
            draft_data=None,
            needs_confirmation=False,
        )


class ViewHandler(CommandHandler):
    """Handler for /view command - shows entity details."""

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:  # noqa: ARG002
        """Execute /view command.

        Args:
            cmd: The parsed command with entity ID.
            context: Context with object_data.

        Returns:
            HandlerResult with view panel.
        """
        object_data = context.get("object_data")

        if not object_data:
            return HandlerResult(
                message="Could not find the requested item.",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        entity_type = object_data.get("entity_type") or "item"

        return HandlerResult(
            message=f"Viewing {entity_type} details.",
            panel_update={
                "mode": "view",
                "entity_type": entity_type,
                "data": object_data,
            },
            draft_data=None,
            needs_confirmation=False,
        )


class CancelHandler(CommandHandler):
    """Handler for /cancel command - discards current draft."""

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:  # noqa: ARG002
        """Execute /cancel command.

        Args:
            cmd: The parsed command.
            context: Context with current draft.

        Returns:
            HandlerResult indicating cancellation.
        """
        current_draft = context.get("current_draft")

        if current_draft:
            entity_type = current_draft.get("entity_type") or "draft"
            message = f"Cancelled {entity_type} draft. What would you like to do next?"
        else:
            message = "No active draft to cancel."

        return HandlerResult(
            message=message,
            panel_update={
                "mode": "list",
                "entity_type": "commitment",
                "items": [],
            },
            draft_data=None,
            needs_confirmation=False,
        )


class EditHandler(CommandHandler):
    """Handler for /edit command - enables editing via conversation."""

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:  # noqa: ARG002
        """Execute /edit command.

        Args:
            cmd: The parsed command.
            context: Context with current object.

        Returns:
            HandlerResult for edit mode.
        """
        current_object = context.get("current_object")

        if not current_object:
            return HandlerResult(
                message="No item selected to edit. Use /show or /view to select an item first.",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        entity_type = current_object.get("entity_type") or "item"

        return HandlerResult(
            message=f"Editing {entity_type}. What would you like to change?",
            panel_update={
                "mode": "draft",
                "entity_type": entity_type,
                "data": current_object,
            },
            draft_data=current_object,
            needs_confirmation=False,
        )


class TypeHandler(CommandHandler):
    """Handler for /type command - assigns a true entity type.

    This is used as a gate before refinement: a draft must have a true type
    before it can be edited or confirmed.
    """

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute /type <entity_type>.

        Args:
            cmd: Parsed command with args.
            context: Context with current draft.

        Returns:
            HandlerResult asking for confirmation.
        """
        if not cmd.args:
            return HandlerResult(
                message=(
                    "Usage: /type <commitment|goal|task|vision|milestone>\n"
                    "Example: /type commitment"
                ),
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        type_str = cmd.args[0].lower().strip()
        try:
            entity_type = EntityType(type_str)
        except ValueError:
            return HandlerResult(
                message=(
                    f"Unknown type: {type_str}. "
                    "Use one of: commitment, goal, task, vision, milestone."
                ),
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        if entity_type == EntityType.UNKNOWN:
            return HandlerResult(
                message="Type must be one of commitment, goal, task, vision, or milestone.",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        current_draft = context.get("current_draft")
        if not current_draft:
            return HandlerResult(
                message="No active draft to type.",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        # Ask for confirmation before setting type.
        return HandlerResult(
            message=f"Set draft type to '{entity_type.value}'? (y/n)",
            panel_update={
                "mode": "draft",
                "entity_type": entity_type.value,
                "data": current_draft,
            },
            draft_data=current_draft,
            needs_confirmation=True,
        )


class HoursHandler(CommandHandler):
    """Handler for /hours command - sets available hours for time coaching.

    The available hours represent how many hours the user has remaining
    to work on tasks today. This enables AI coaching about over-allocation.
    """

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute /hours command.

        Args:
            cmd: The parsed command with optional hours argument.
            context: Context with current available hours.

        Returns:
            HandlerResult with updated hours info.
        """
        args = cmd.args

        # If hours provided as argument, set them directly
        if args:
            return self._set_hours(args[0], context)

        # Otherwise, show current status and prompt for input
        return self._show_hours_prompt(context)

    def _show_hours_prompt(self, context: dict[str, Any]) -> HandlerResult:
        """Show current hours and prompt for update."""
        current_hours = context.get("available_hours_remaining")
        allocated_hours = context.get("allocated_hours", 0.0)

        lines = ["Available Hours"]
        lines.append("=" * 40)
        lines.append("")

        if current_hours is not None:
            lines.append(f"Current available: {current_hours:.1f} hours")
            lines.append(f"Currently allocated: {allocated_hours:.1f} hours")
            remaining = current_hours - allocated_hours
            if remaining < 0:
                lines.append(f"OVER-ALLOCATED by {abs(remaining):.1f} hours")
            else:
                lines.append(f"Remaining capacity: {remaining:.1f} hours")
        else:
            lines.append("Available hours not set.")
            lines.append(f"Currently allocated: {allocated_hours:.1f} hours")

        lines.append("")
        lines.append("How many hours do you have remaining today?")
        lines.append("Example: /hours 4 or just type a number like '3.5'")

        return HandlerResult(
            message="\n".join(lines),
            panel_update={
                "mode": "hours",
                "entity_type": "time_context",
                "data": {
                    "available_hours": current_hours,
                    "allocated_hours": allocated_hours,
                },
            },
            draft_data=None,
            needs_confirmation=False,
        )

    def _set_hours(self, hours_input: str, context: dict[str, Any]) -> HandlerResult:
        """Parse and set available hours."""
        parsed = parse_time_input(hours_input)

        if parsed is None:
            return HandlerResult(
                message=f"Could not parse '{hours_input}' as a time. "
                "Try formats like '4', '3.5', '2 hours', or '90 min'.",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        hours = parsed.hours
        allocated = context.get("allocated_hours", 0.0)

        lines = [f"Setting available hours to {format_hours(hours)}."]

        if hours < allocated:
            over_by = allocated - hours
            lines.append("")
            lines.append(f"Note: You're already allocated {format_hours(allocated)}, ")
            lines.append(f"which is {format_hours(over_by)} over your available time.")
            lines.append("Consider deferring some tasks or adjusting estimates.")

        return HandlerResult(
            message="\n".join(lines),
            panel_update={
                "mode": "hours_set",
                "entity_type": "time_context",
                "data": {
                    "available_hours": hours,
                    "allocated_hours": allocated,
                },
                "action": "set_hours",
                "hours": hours,
            },
            draft_data={"available_hours": hours},
            needs_confirmation=False,
        )


class TriageHandler(CommandHandler):
    """Handler for /triage command - processes captured items.

    Triage workflow:
    1. Get next item from triage queue (FIFO order)
    2. AI analyzes and suggests entity type
    3. User confirms, changes type, deletes, or skips
    4. Repeat until queue empty or user exits
    """

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:  # noqa: ARG002
        """Execute /triage command.

        Args:
            cmd: The parsed command.
            context: Context with triage items and state.

        Returns:
            HandlerResult with triage item display and options.
        """
        # Get triage items from context (populated by chat screen)
        triage_items = context.get("triage_items", [])
        current_index = context.get("triage_index", 0)

        if not triage_items:
            return HandlerResult(
                message='No items to triage. Use `jdo capture "text"` to capture ideas.',
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        if current_index >= len(triage_items):
            return HandlerResult(
                message="Triage complete! All items have been processed.",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        # Get current triage item
        current_item = triage_items[current_index]

        # Get AI analysis from context (populated by chat screen)
        analysis = context.get("triage_analysis")

        if analysis is None:
            # First time viewing this item - show it and trigger analysis
            return self._show_item_for_analysis(current_item, current_index, len(triage_items))

        # Show AI analysis with options
        return self._show_analysis_with_options(
            current_item, analysis, current_index, len(triage_items)
        )

    def _show_item_for_analysis(
        self, item: dict[str, Any], index: int, total: int
    ) -> HandlerResult:
        """Show triage item and indicate analysis is needed.

        Args:
            item: The triage item data.
            index: Current item index.
            total: Total number of items.

        Returns:
            HandlerResult indicating analysis is needed.
        """
        raw_text = item.get("raw_text") or "Unknown"

        lines = [
            f"Triage item {index + 1} of {total}:",
            "",
            f'  "{raw_text}"',
            "",
            "Analyzing...",
        ]

        return HandlerResult(
            message="\n".join(lines),
            panel_update={
                "mode": "triage",
                "item": item,
                "index": index,
                "total": total,
                "needs_analysis": True,
            },
            draft_data=None,
            needs_confirmation=False,
        )

    def _show_analysis_with_options(
        self,
        item: dict[str, Any],
        analysis: dict[str, Any],
        index: int,
        total: int,
    ) -> HandlerResult:
        """Show AI analysis and available actions.

        Args:
            item: The triage item data.
            analysis: AI analysis results.
            index: Current item index.
            total: Total number of items.

        Returns:
            HandlerResult with analysis and options.
        """
        raw_text = item.get("raw_text") or "Unknown"

        lines = [
            f"Triage item {index + 1} of {total}:",
            "",
            f'  "{raw_text}"',
            "",
        ]

        # Check if we have a confident classification
        if analysis.get("is_confident"):
            classification = analysis.get("classification") or {}
            suggested_type = classification.get("suggested_type") or "unknown"
            confidence = classification.get("confidence") or 0
            reasoning = classification.get("reasoning") or ""
            stakeholder = classification.get("detected_stakeholder")
            date_info = classification.get("detected_date")

            lines.append(f"Suggested type: {suggested_type} ({confidence:.0%} confident)")
            lines.append(f"Reasoning: {reasoning}")

            if stakeholder:
                lines.append(f"Detected stakeholder: {stakeholder}")
            if date_info:
                lines.append(f"Detected date: {date_info}")

            lines.append("")
            lines.append("Options:")
            lines.append("  [a] Accept - create as " + suggested_type)
            lines.append("  [c] Change type - choose a different type")
            lines.append("  [d] Delete - remove this item")
            lines.append("  [s] Skip - come back later")
            lines.append("  [q] Quit - exit triage")
        else:
            # Low confidence or question
            question = analysis.get("question") or {}
            question_text = question.get("question") or "What type of item is this?"

            lines.append(f"Question: {question_text}")
            lines.append("")
            lines.append("Options:")
            lines.append("  [1] commitment  [2] goal  [3] task")
            lines.append("  [4] vision      [5] milestone")
            lines.append("  [d] Delete      [s] Skip  [q] Quit")

        return HandlerResult(
            message="\n".join(lines),
            panel_update={
                "mode": "triage",
                "item": item,
                "analysis": analysis,
                "index": index,
                "total": total,
            },
            draft_data=None,
            needs_confirmation=False,
        )
