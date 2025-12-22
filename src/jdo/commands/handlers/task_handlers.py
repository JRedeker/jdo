"""Task command handler implementations."""

from __future__ import annotations

from typing import Any, ClassVar

from jdo.ai.time_parsing import format_hours
from jdo.commands.handlers.base import CommandHandler, HandlerResult
from jdo.commands.parser import ParsedCommand


class TaskHandler(CommandHandler):
    """Handler for /task command - creates tasks for commitments."""

    def __init__(self) -> None:
        """Initialize the task handler."""
        self._current_draft: dict[str, Any] | None = None

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:  # noqa: ARG002
        """Execute /task command.

        Args:
            cmd: The parsed command.
            context: Context with conversation and extracted data.

        Returns:
            HandlerResult with draft panel and message.
        """
        commitment_id = context.get("current_commitment_id")
        available_commitments = context.get("available_commitments", [])

        # Require commitment context
        if not commitment_id:
            if available_commitments:
                return self._prompt_for_commitment_selection(available_commitments)
            return HandlerResult(
                message=(
                    "Tasks need to be linked to a commitment. "
                    "Please create a commitment first with /commit, or "
                    "select an existing commitment to add tasks to."
                ),
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        extracted = context.get("extracted", {})

        # Try to extract from conversation if not pre-extracted
        if not extracted and context.get("conversation"):
            extracted = self._extract_from_conversation(context["conversation"])

        # Build draft data
        draft_data = {
            "title": extracted.get("title", ""),
            "scope": extracted.get("scope", ""),
            "commitment_id": commitment_id,
            "estimated_hours": extracted.get("estimated_hours"),
        }

        self._current_draft = draft_data

        # Build response message
        if not draft_data["title"]:
            message = "What task would you like to add to this commitment?"
            needs_confirmation = False
        else:
            message = f"I'll add this task: {draft_data['title']}"
            needs_confirmation = True

        return HandlerResult(
            message=message,
            panel_update={
                "mode": "draft",
                "entity_type": "task",
                "data": draft_data,
            },
            draft_data=draft_data,
            needs_confirmation=needs_confirmation,
        )

    def _prompt_for_commitment_selection(self, commitments: list[dict[str, Any]]) -> HandlerResult:
        """Prompt user to select a commitment."""
        lines = ["Which commitment would you like to add a task to?", ""]
        for i, c in enumerate(commitments, 1):
            lines.append(f"  {i}. {c.get('deliverable') or 'Untitled'}")
        lines.append("")
        lines.append("Enter a number to select a commitment.")
        return HandlerResult(
            message="\n".join(lines),
            panel_update={
                "mode": "list",
                "entity_type": "commitment",
                "items": commitments,
            },
            draft_data=None,
            needs_confirmation=False,
        )

    def _extract_from_conversation(self, conversation: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract task fields from conversation."""
        extracted: dict[str, Any] = {}

        for msg in conversation:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                # Basic keyword detection (placeholder for AI)
                if "first" in content.lower() or "need to" in content.lower():
                    extracted["title"] = content[:100]

        return extracted


class CompleteHandler(CommandHandler):
    """Handler for /complete command - marks items complete.

    For tasks with time estimates, prompts for actual hours comparison
    using a 5-point scale before completing.
    """

    # Actual hours category options for display
    _HOURS_OPTIONS: ClassVar[list[tuple[str, str, str]]] = [
        ("1", "much_shorter", "Much shorter than estimated (<50%)"),
        ("2", "shorter", "Shorter than estimated (50-85%)"),
        ("3", "on_target", "On target (85-115%)"),
        ("4", "longer", "Longer than estimated (115-150%)"),
        ("5", "much_longer", "Much longer than estimated (>150%)"),
    ]

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:  # noqa: ARG002
        """Execute /complete command.

        Args:
            cmd: The parsed command.
            context: Context with current object.

        Returns:
            HandlerResult asking for confirmation or hours input.
        """
        current_object = context.get("current_object")

        if not current_object:
            return HandlerResult(
                message="No item selected to complete. Use /show or /view to select an item first.",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        entity_type = current_object.get("entity_type") or "item"
        title = current_object.get("deliverable") or current_object.get("title") or "this item"

        # For tasks with time estimates, prompt for actual hours comparison
        if entity_type == "task" and current_object.get("estimated_hours") is not None:
            return self._prompt_for_actual_hours(current_object, title)

        return HandlerResult(
            message=f"Mark '{title}' as completed?",
            panel_update={
                "mode": "view",
                "entity_type": entity_type,
                "data": current_object,
            },
            draft_data=None,
            needs_confirmation=True,
        )

    def _prompt_for_actual_hours(self, task_data: dict[str, Any], title: str) -> HandlerResult:
        """Prompt for actual hours comparison when completing a task.

        Args:
            task_data: The task data dict.
            title: Task title for display.

        Returns:
            HandlerResult with hours prompt.
        """
        estimated = task_data.get("estimated_hours", 0)
        estimated_str = format_hours(estimated) if estimated else "unknown"

        lines = [
            f"Completing: {title}",
            f"Estimated: {estimated_str}",
            "",
            "How did actual time compare to your estimate?",
            "",
        ]

        for num, _code, label in self._HOURS_OPTIONS:
            lines.append(f"  [{num}] {label}")

        lines.append("")
        lines.append("Enter 1-5, or 'skip' to complete without recording:")

        return HandlerResult(
            message="\n".join(lines),
            panel_update={
                "mode": "complete_task",
                "entity_type": "task",
                "data": task_data,
                "workflow_step": "actual_hours",
            },
            draft_data={
                "task_id": task_data.get("id"),
                "estimated_hours": estimated,
                "actual_hours_category": None,
            },
            needs_confirmation=False,
        )
