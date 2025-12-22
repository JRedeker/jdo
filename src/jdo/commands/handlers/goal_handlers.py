"""Goal command handler implementations."""

from __future__ import annotations

from typing import Any

from jdo.commands.handlers.base import CommandHandler, HandlerResult
from jdo.commands.parser import ParsedCommand


class GoalHandler(CommandHandler):
    """Handler for /goal command - creates goals."""

    def __init__(self) -> None:
        """Initialize the goal handler."""
        self._current_draft: dict[str, Any] | None = None

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:  # noqa: ARG002
        """Execute /goal command.

        Args:
            cmd: The parsed command.
            context: Context with conversation and extracted data.

        Returns:
            HandlerResult with draft panel and message.
        """
        extracted = context.get("extracted", {})

        # Try to extract from conversation if not pre-extracted
        if not extracted and context.get("conversation"):
            extracted = self._extract_from_conversation(context["conversation"])

        # Build draft data
        draft_data = {
            "title": extracted.get("title", ""),
            "problem_statement": extracted.get("problem_statement", ""),
            "solution_vision": extracted.get("solution_vision", ""),
            "motivation": extracted.get("motivation"),
            "vision_id": extracted.get("vision_id"),
        }

        self._current_draft = draft_data

        # Check for missing required fields
        missing_fields = []
        if not draft_data["title"]:
            missing_fields.append("title")
        if not draft_data["problem_statement"]:
            missing_fields.append("problem_statement")
        if not draft_data["solution_vision"]:
            missing_fields.append("solution_vision")

        # Check if we should prompt for vision linkage
        available_visions = context.get("available_visions", [])
        prompt_for_vision = available_visions and not draft_data.get("vision_id")

        # Build response message
        if missing_fields:
            message = self._build_prompt_message(missing_fields)
            needs_confirmation = False
        elif prompt_for_vision:
            message = self._build_vision_prompt(available_visions, draft_data)
            needs_confirmation = False
        else:
            message = self._build_confirmation_message(draft_data)
            needs_confirmation = True

        return HandlerResult(
            message=message,
            panel_update={
                "mode": "draft",
                "entity_type": "goal",
                "data": draft_data,
            },
            draft_data=draft_data,
            needs_confirmation=needs_confirmation,
        )

    def _extract_from_conversation(self, conversation: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract goal fields from conversation."""
        extracted: dict[str, Any] = {}

        for msg in conversation:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                # Basic keyword detection (placeholder for AI)
                if "goal" in content.lower() or "want to" in content.lower():
                    extracted["title"] = content[:100]

        return extracted

    def _build_prompt_message(self, missing_fields: list[str]) -> str:
        """Build a message prompting for missing fields."""
        if "problem_statement" in missing_fields:
            return "What problem are you trying to solve with this goal?"
        if "solution_vision" in missing_fields:
            return "How will things look when you've achieved this goal?"
        if "title" in missing_fields:
            return "What would you like to call this goal?"
        return "I need more information about this goal."

    def _build_vision_prompt(
        self,
        available_visions: list[dict[str, Any]],
        draft_data: dict[str, Any],  # noqa: ARG002
    ) -> str:
        """Build a message prompting for vision linkage."""
        lines = [
            "I see you have some visions defined. Would you like to link this goal to one?",
            "",
        ]
        for i, vision in enumerate(available_visions, 1):
            lines.append(f"  {i}. {vision.get('title') or 'Untitled'}")
        lines.append("")
        lines.append("Enter a number to select, or 'skip' to create without a vision link.")
        return "\n".join(lines)

    def _build_confirmation_message(self, draft_data: dict[str, Any]) -> str:
        """Build a confirmation message with draft summary."""
        lines = ["Here's the goal I'll create:", ""]
        lines.append(f"  Title: {draft_data['title']}")
        lines.append(f"  Problem: {draft_data['problem_statement'][:50]}...")
        lines.append(f"  Vision: {draft_data['solution_vision'][:50]}...")
        lines.append("")
        lines.append("Does this look right? (yes to confirm)")
        return "\n".join(lines)
