"""Milestone command handler implementations."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from jdo.commands.handlers.base import CommandHandler, HandlerResult
from jdo.commands.parser import ParsedCommand


class MilestoneHandler(CommandHandler):
    """Handler for /milestone command - manages milestones."""

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute /milestone command."""
        args = cmd.args
        goal_id = context.get("current_goal_id")

        if args and args[0] == "new":
            if not goal_id:
                return HandlerResult(
                    message=(
                        "Milestones need to be linked to a goal. "
                        "Please select a goal first with /show goals."
                    ),
                    panel_update=None,
                    draft_data=None,
                    needs_confirmation=False,
                )
            return self._start_creation_flow(context, goal_id)

        return self._show_milestone_list(context)

    def _show_milestone_list(self, context: dict[str, Any]) -> HandlerResult:
        """Show list of milestones for current goal."""
        milestones = context.get("milestones_for_goal", context.get("milestones", []))
        goal_id = context.get("current_goal_id")

        if not goal_id:
            message = "Select a goal first to see its milestones. Use /show goals."
        elif not milestones:
            message = "No milestones for this goal yet. Use /milestone new to create one."
        else:
            message = f"Found {len(milestones)} milestone(s) for this goal."

        return HandlerResult(
            message=message,
            panel_update={
                "mode": "list",
                "entity_type": "milestone",
                "items": milestones,
            },
            draft_data=None,
            needs_confirmation=False,
        )

    def _start_creation_flow(self, context: dict[str, Any], goal_id: UUID | str) -> HandlerResult:
        """Start the milestone creation flow."""
        extracted = context.get("extracted", {})

        draft_data = {
            "title": extracted.get("title", ""),
            "target_date": extracted.get("target_date"),
            "goal_id": goal_id,
        }

        if draft_data["title"] and not draft_data["target_date"]:
            message = (
                f"When should '{draft_data['title']}' be completed? Please provide a target date."
            )
        elif not draft_data["title"]:
            message = "What milestone would you like to set for this goal?"
        else:
            title = draft_data["title"]
            target = draft_data["target_date"]
            message = f"I'll create milestone '{title}' targeting {target}."

        return HandlerResult(
            message=message,
            panel_update={
                "mode": "draft",
                "entity_type": "milestone",
                "data": draft_data,
            },
            draft_data=draft_data,
            needs_confirmation=bool(draft_data["title"] and draft_data["target_date"]),
        )
