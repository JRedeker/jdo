"""Recurring commitment command handler implementations."""

from __future__ import annotations

from typing import Any

from jdo.commands.handlers.base import CommandHandler, HandlerResult
from jdo.commands.parser import ParsedCommand


class RecurringHandler(CommandHandler):
    """Handler for /recurring command - manages recurring commitments."""

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute /recurring command.

        Args:
            cmd: The parsed command.
            context: Context with recurring commitments.

        Returns:
            HandlerResult with appropriate panel and message.
        """
        args = cmd.args

        # /recurring new - start creation flow
        if args and args[0] == "new":
            return self._start_creation_flow(context)

        # /recurring pause <id> - pause a recurring commitment
        if args and args[0] == "pause":
            return self._handle_pause(args[1:], context)

        # /recurring resume <id> - resume a recurring commitment
        if args and args[0] == "resume":
            return self._handle_resume(args[1:], context)

        # /recurring delete <id> - delete a recurring commitment
        if args and args[0] == "delete":
            return self._handle_delete(args[1:], context)

        # /recurring (no args) - list all recurring commitments
        return self._show_recurring_list(context)

    def _show_recurring_list(self, context: dict[str, Any]) -> HandlerResult:
        """Show list of all recurring commitments."""
        recurring_list = context.get("recurring_commitments", [])

        if not recurring_list:
            message = (
                "You don't have any recurring commitments yet. Use /recurring new to create one."
            )
        else:
            message = f"Found {len(recurring_list)} recurring commitment(s)."

        return HandlerResult(
            message=message,
            panel_update={
                "mode": "list",
                "entity_type": "recurring_commitment",
                "items": recurring_list,
            },
            draft_data=None,
            needs_confirmation=False,
        )

    def _start_creation_flow(self, context: dict[str, Any]) -> HandlerResult:
        """Start the recurring commitment creation flow."""
        extracted = context.get("extracted", {})

        draft_data = {
            "deliverable_template": extracted.get("deliverable_template", ""),
            "stakeholder_name": extracted.get("stakeholder_name", ""),
            "recurrence_type": extracted.get("recurrence_type", ""),
            "interval": extracted.get("interval", 1),
            "days_of_week": extracted.get("days_of_week", []),
            "day_of_month": extracted.get("day_of_month"),
            "week_of_month": extracted.get("week_of_month"),
            "month_of_year": extracted.get("month_of_year"),
            "due_time": extracted.get("due_time"),
            "goal_id": extracted.get("goal_id"),
        }

        message = (
            "Let's create a recurring commitment. What do you commit to doing "
            "regularly? (e.g., 'Weekly status report to manager every Monday')"
        )

        return HandlerResult(
            message=message,
            panel_update={
                "mode": "draft",
                "entity_type": "recurring_commitment",
                "data": draft_data,
            },
            draft_data=draft_data,
            needs_confirmation=False,
        )

    def _handle_pause(self, args: list[str], context: dict[str, Any]) -> HandlerResult:  # noqa: ARG002
        """Handle /recurring pause <id> command."""
        if not args:
            return HandlerResult(
                message="Usage: /recurring pause <id>",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        recurring_id = args[0]
        return HandlerResult(
            message=f"Pause recurring commitment {recurring_id}?",
            panel_update={
                "mode": "view",
                "entity_type": "recurring_commitment",
                "action": "pause",
                "target_id": recurring_id,
            },
            draft_data=None,
            needs_confirmation=True,
        )

    def _handle_resume(self, args: list[str], context: dict[str, Any]) -> HandlerResult:  # noqa: ARG002
        """Handle /recurring resume <id> command."""
        if not args:
            return HandlerResult(
                message="Usage: /recurring resume <id>",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        recurring_id = args[0]
        return HandlerResult(
            message=f"Resume recurring commitment {recurring_id}?",
            panel_update={
                "mode": "view",
                "entity_type": "recurring_commitment",
                "action": "resume",
                "target_id": recurring_id,
            },
            draft_data=None,
            needs_confirmation=True,
        )

    def _handle_delete(self, args: list[str], context: dict[str, Any]) -> HandlerResult:  # noqa: ARG002
        """Handle /recurring delete <id> command."""
        if not args:
            return HandlerResult(
                message="Usage: /recurring delete <id>",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        recurring_id = args[0]
        return HandlerResult(
            message=(
                f"Delete recurring commitment {recurring_id}? "
                "(Existing instances will remain but won't be linked.)"
            ),
            panel_update={
                "mode": "view",
                "entity_type": "recurring_commitment",
                "action": "delete",
                "target_id": recurring_id,
            },
            draft_data=None,
            needs_confirmation=True,
        )
