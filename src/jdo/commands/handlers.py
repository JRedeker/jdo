"""Command handlers for TUI commands.

Each handler executes a parsed command and returns a HandlerResult
with a message for the chat and optional panel updates.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from jdo.commands.parser import CommandType, ParsedCommand


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


class CommandHandler(ABC):
    """Base class for command handlers."""

    @abstractmethod
    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute the command and return a result.

        Args:
            cmd: The parsed command to execute.
            context: Context data including conversation history and extracted fields.

        Returns:
            HandlerResult with message and optional panel updates.
        """


class CommitHandler(CommandHandler):
    """Handler for /commit command - creates commitments."""

    def __init__(self) -> None:
        """Initialize the commit handler."""
        self._current_draft: dict[str, Any] | None = None

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute /commit command.

        Args:
            cmd: The parsed command.
            context: Context with conversation and extracted data.

        Returns:
            HandlerResult with draft panel and message.
        """
        # Check for pre-extracted data
        extracted = context.get("extracted", {})

        # Try to extract from conversation if not pre-extracted
        if not extracted and context.get("conversation"):
            extracted = self._extract_from_conversation(context["conversation"])

        # Build draft data
        draft_data = {
            "deliverable": extracted.get("deliverable", ""),
            "stakeholder": extracted.get("stakeholder", ""),
            "due_date": extracted.get("due_date"),
            "due_time": extracted.get("due_time"),
            "goal_id": extracted.get("goal_id"),
            "milestone_id": extracted.get("milestone_id"),
        }

        self._current_draft = draft_data

        # Check for missing required fields
        missing_fields = []
        if not draft_data["deliverable"]:
            missing_fields.append("deliverable")
        if not draft_data["stakeholder"]:
            missing_fields.append("stakeholder")
        if not draft_data["due_date"]:
            missing_fields.append("due_date")

        # Build response message
        if missing_fields:
            message = self._build_prompt_message(missing_fields, draft_data)
            needs_confirmation = False
        else:
            message = self._build_confirmation_message(draft_data)
            needs_confirmation = True

        return HandlerResult(
            message=message,
            panel_update={
                "mode": "draft",
                "entity_type": "commitment",
                "data": draft_data,
            },
            draft_data=draft_data,
            needs_confirmation=needs_confirmation,
        )

    def cancel(self) -> HandlerResult:
        """Cancel the current draft.

        Returns:
            HandlerResult indicating cancellation.
        """
        self._current_draft = None
        return HandlerResult(
            message="Draft cancelled. What would you like to do next?",
            panel_update={"mode": "list", "entity_type": "commitment", "items": []},
            draft_data=None,
            needs_confirmation=False,
        )

    def _extract_from_conversation(self, conversation: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract commitment fields from conversation.

        This is a placeholder for AI extraction. In the full implementation,
        this would use the AI agent to extract structured data.

        Args:
            conversation: List of conversation messages.

        Returns:
            Dict with extracted fields.
        """
        # Simple placeholder extraction - real implementation uses AI
        extracted: dict[str, Any] = {}

        for msg in conversation:
            if msg.get("role") == "user":
                content = msg.get("content", "").lower()
                # Basic keyword detection (placeholder for AI)
                if "send" in content or "deliver" in content or "report" in content:
                    extracted["deliverable"] = msg.get("content", "")[:100]

        return extracted

    def _build_prompt_message(self, missing_fields: list[str], draft_data: dict[str, Any]) -> str:
        """Build a message prompting for missing fields.

        Args:
            missing_fields: List of field names that are missing.
            draft_data: Current draft data.

        Returns:
            Message prompting for missing information.
        """
        prompts = []

        if "deliverable" in missing_fields:
            prompts.append("What will you deliver?")
        if "stakeholder" in missing_fields:
            prompts.append("Who are you making this commitment to?")
        if "due_date" in missing_fields:
            prompts.append("When is it due?")

        return "I need a bit more information to create this commitment. " + " ".join(prompts)

    def _build_confirmation_message(self, draft_data: dict[str, Any]) -> str:
        """Build a confirmation message with draft summary.

        Args:
            draft_data: The draft data to summarize.

        Returns:
            Message asking for confirmation.
        """
        lines = ["Here's the commitment I'll create:", ""]
        lines.append(f"  Deliverable: {draft_data['deliverable']}")
        lines.append(f"  Stakeholder: {draft_data['stakeholder']}")
        lines.append(f"  Due: {draft_data['due_date']} {draft_data.get('due_time', '')}")
        lines.append("")
        lines.append("Does this look right? (yes to confirm, or tell me what to change)")

        return "\n".join(lines)


class GoalHandler(CommandHandler):
    """Handler for /goal command - creates goals."""

    def __init__(self) -> None:
        """Initialize the goal handler."""
        self._current_draft: dict[str, Any] | None = None

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
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
        self, available_visions: list[dict[str, Any]], draft_data: dict[str, Any]
    ) -> str:
        """Build a message prompting for vision linkage."""
        lines = [
            "I see you have some visions defined. Would you like to link this goal to one?",
            "",
        ]
        for i, vision in enumerate(available_visions, 1):
            lines.append(f"  {i}. {vision.get('title', 'Untitled')}")
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


class TaskHandler(CommandHandler):
    """Handler for /task command - creates tasks for commitments."""

    def __init__(self) -> None:
        """Initialize the task handler."""
        self._current_draft: dict[str, Any] | None = None

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
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
                message="Tasks need to be linked to a commitment. "
                "Please create a commitment first with /commit, or "
                "select an existing commitment to add tasks to.",
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
            lines.append(f"  {i}. {c.get('deliverable', 'Untitled')}")
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


class MilestoneHandler(CommandHandler):
    """Handler for /milestone command - manages milestones."""

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute /milestone command.

        Args:
            cmd: The parsed command.
            context: Context with goal and milestones.

        Returns:
            HandlerResult with appropriate panel and message.
        """
        args = cmd.args
        goal_id = context.get("current_goal_id")

        # /milestone new - start creation flow
        if args and args[0] == "new":
            if not goal_id:
                return HandlerResult(
                    message="Milestones need to be linked to a goal. "
                    "Please select a goal first with /show goals.",
                    panel_update=None,
                    draft_data=None,
                    needs_confirmation=False,
                )
            return self._start_creation_flow(context, goal_id)

        # /milestone (no args) - list milestones for current goal
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

    def _start_creation_flow(self, context: dict[str, Any], goal_id: Any) -> HandlerResult:
        """Start the milestone creation flow."""
        extracted = context.get("extracted", {})

        draft_data = {
            "title": extracted.get("title", ""),
            "target_date": extracted.get("target_date"),
            "goal_id": goal_id,
        }

        # Prompt for target date if missing
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


class ShowHandler(CommandHandler):
    """Handler for /show command - displays lists of entities."""

    # Map show arguments to entity types
    _ENTITY_MAP: dict[str, str] = {
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

        message = f"Showing {len(items)} {entity_arg}."
        if not items:
            message = f"No {entity_arg} found."

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

    _COMMAND_HELP: dict[str, str] = {
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
    }

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
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
            "  /show       - Display entity lists",
            "  /view       - View a specific item",
            "  /complete   - Mark item as completed",
            "  /cancel     - Cancel current draft",
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

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
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

        entity_type = object_data.get("entity_type", "item")

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

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute /cancel command.

        Args:
            cmd: The parsed command.
            context: Context with current draft.

        Returns:
            HandlerResult indicating cancellation.
        """
        current_draft = context.get("current_draft")

        if current_draft:
            entity_type = current_draft.get("entity_type", "draft")
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


class CompleteHandler(CommandHandler):
    """Handler for /complete command - marks items complete."""

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute /complete command.

        Args:
            cmd: The parsed command.
            context: Context with current object.

        Returns:
            HandlerResult asking for confirmation.
        """
        current_object = context.get("current_object")

        if not current_object:
            return HandlerResult(
                message="No item selected to complete. Use /show or /view to select an item first.",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        entity_type = current_object.get("entity_type", "item")
        title = current_object.get("deliverable") or current_object.get("title", "this item")

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

    def _handle_pause(self, args: list[str], context: dict[str, Any]) -> HandlerResult:
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

    def _handle_resume(self, args: list[str], context: dict[str, Any]) -> HandlerResult:
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

    def _handle_delete(self, args: list[str], context: dict[str, Any]) -> HandlerResult:
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


class EditHandler(CommandHandler):
    """Handler for /edit command - enables editing via conversation."""

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
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

        entity_type = current_object.get("entity_type", "item")

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


# Handler registry
_HANDLERS: dict[CommandType, type[CommandHandler]] = {
    CommandType.COMMIT: CommitHandler,
    CommandType.GOAL: GoalHandler,
    CommandType.TASK: TaskHandler,
    CommandType.VISION: VisionHandler,
    CommandType.MILESTONE: MilestoneHandler,
    CommandType.RECURRING: RecurringHandler,
    CommandType.SHOW: ShowHandler,
    CommandType.HELP: HelpHandler,
    CommandType.VIEW: ViewHandler,
    CommandType.CANCEL: CancelHandler,
    CommandType.COMPLETE: CompleteHandler,
    CommandType.EDIT: EditHandler,
}

# Cache handler instances
_handler_instances: dict[CommandType, CommandHandler] = {}


def get_handler(command_type: CommandType) -> CommandHandler | None:
    """Get the handler for a command type.

    Args:
        command_type: The type of command to get a handler for.

    Returns:
        Handler instance or None for MESSAGE type.
    """
    if command_type == CommandType.MESSAGE:
        return None

    if command_type not in _handler_instances:
        handler_class = _HANDLERS.get(command_type)
        if handler_class:
            _handler_instances[command_type] = handler_class()

    return _handler_instances.get(command_type)
