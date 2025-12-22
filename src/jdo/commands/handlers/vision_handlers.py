"""Vision command handler implementations."""

from __future__ import annotations

from typing import Any

from jdo.commands.handlers.base import CommandHandler, HandlerResult
from jdo.commands.parser import ParsedCommand


class VisionHandler(CommandHandler):
    """Handler for /vision command - manages visions."""

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute /vision command.

        Args:
            cmd: The parsed command.
            context: Context with available visions.

        Returns:
            HandlerResult with appropriate panel and message.
        """
        args = cmd.args

        # /vision new - start creation flow
        if args and args[0] == "new":
            return self._start_creation_flow(context)

        # /vision review - list visions due for review
        if args and args[0] == "review":
            return self._show_review_list(context)

        # /vision (no args) - list all visions
        return self._show_vision_list(context)

    def _show_vision_list(self, context: dict[str, Any]) -> HandlerResult:
        """Show list of all visions."""
        visions = context.get("available_visions", [])

        if not visions:
            message = "You don't have any visions yet. Use /vision new to create one."
        else:
            message = f"Found {len(visions)} vision(s). Select one to view details."

        return HandlerResult(
            message=message,
            panel_update={
                "mode": "list",
                "entity_type": "vision",
                "items": visions,
            },
            draft_data=None,
            needs_confirmation=False,
        )

    def _start_creation_flow(self, context: dict[str, Any]) -> HandlerResult:
        """Start the vision creation flow."""
        extracted = context.get("extracted", {})

        draft_data = {
            "title": extracted.get("title", ""),
            "narrative": extracted.get("narrative", ""),
            "metrics": extracted.get("metrics", []),
        }

        message = (
            "Let's create a new vision. Describe your ideal future state - "
            "paint a vivid picture of what success looks like. What narrative "
            "best captures where you want to be?"
        )

        return HandlerResult(
            message=message,
            panel_update={
                "mode": "draft",
                "entity_type": "vision",
                "data": draft_data,
            },
            draft_data=draft_data,
            needs_confirmation=False,
        )

    def _show_review_list(self, context: dict[str, Any]) -> HandlerResult:
        """Show visions due for review."""
        visions_due = context.get("visions_due_for_review", [])

        if not visions_due:
            message = "No visions are due for review. Great job staying on top of things!"
        else:
            message = f"You have {len(visions_due)} vision(s) due for review."

        return HandlerResult(
            message=message,
            panel_update={
                "mode": "list",
                "entity_type": "vision",
                "items": visions_due,
            },
            draft_data=None,
            needs_confirmation=False,
        )
