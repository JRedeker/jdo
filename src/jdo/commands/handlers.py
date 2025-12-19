"""Command handlers for TUI commands.

Each handler executes a parsed command and returns a HandlerResult
with a message for the chat and optional panel updates.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from jdo.ai.time_parsing import format_hours, parse_time_input
from jdo.commands.parser import CommandType, ParsedCommand
from jdo.db.persistence import PersistenceService
from jdo.db.session import get_session
from jdo.integrity.service import IntegrityService
from jdo.models.draft import EntityType


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
            # Get velocity for confirmation message
            try:
                with get_session() as session:
                    service = PersistenceService(session)
                    created, completed = service.get_commitment_velocity()
            except Exception:
                # If database queries fail, proceed without guardrails
                created = 0
                completed = 0

            message = self._build_confirmation_message(draft_data, created, completed)
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

    def _build_confirmation_message(
        self,
        draft_data: dict[str, Any],
        velocity_created: int,
        velocity_completed: int,
    ) -> str:
        """Build confirmation message with optional velocity coaching.

        Args:
            draft_data: The draft commitment data.
            velocity_created: Commitments created in past week.
            velocity_completed: Commitments completed in past week.

        Returns:
            Message asking for confirmation with optional coaching notes.
        """
        lines = ["Here's the commitment I'll create:", ""]
        lines.append(f"  Deliverable: {draft_data['deliverable']}")
        lines.append(f"  Stakeholder: {draft_data['stakeholder']}")
        due_time = draft_data.get("due_time")
        due_str = f"  Due: {draft_data['due_date']}"
        if due_time:
            due_str += f" {due_time}"
        lines.append(due_str)

        # Add velocity warning if creating faster than completing
        if velocity_created > velocity_completed:
            lines.append("")
            lines.append(
                f"**Note**: You've created {velocity_created} commitments this week "
                f"but only completed {velocity_completed}. Are you overcommitting?"
            )

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


class CompleteHandler(CommandHandler):
    """Handler for /complete command - marks items complete.

    For tasks with time estimates, prompts for actual hours comparison
    using a 5-point scale before completing.
    """

    # Actual hours category options for display
    _HOURS_OPTIONS = [
        ("1", "much_shorter", "Much shorter than estimated (<50%)"),
        ("2", "shorter", "Shorter than estimated (50-85%)"),
        ("3", "on_target", "On target (85-115%)"),
        ("4", "longer", "Longer than estimated (115-150%)"),
        ("5", "much_longer", "Much longer than estimated (>150%)"),
    ]

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
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


class AtRiskHandler(CommandHandler):
    """Handler for /atrisk command - marks commitment as at-risk.

    Starts the Honor-Your-Word protocol: notify stakeholders, clean up impact.
    """

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute /atrisk command.

        Args:
            cmd: The parsed command.
            context: Context with current commitment data.

        Returns:
            HandlerResult for at-risk workflow.
        """
        current_commitment = context.get("current_commitment")
        available_commitments = context.get("available_commitments", [])

        # Check if we have a commitment in context
        if not current_commitment:
            if available_commitments:
                return self._prompt_for_commitment_selection(available_commitments)
            return HandlerResult(
                message="No active commitments to mark as at-risk. "
                "Create a commitment first with /commit.",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        # Check if already at-risk
        status = current_commitment.get("status", "")
        if status == "at_risk":
            return HandlerResult(
                message="This commitment is already marked at-risk. "
                "Would you like to view the cleanup plan? Use /cleanup.",
                panel_update={
                    "mode": "view",
                    "entity_type": "commitment",
                    "data": current_commitment,
                },
                draft_data=None,
                needs_confirmation=False,
            )

        # Check if commitment is completable (not already completed/abandoned)
        if status in ("completed", "abandoned"):
            return HandlerResult(
                message=f"This commitment is already {status}. "
                "Only pending or in-progress commitments can be marked at-risk.",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        # Start at-risk workflow - prompt for reason
        deliverable = current_commitment.get("deliverable") or "this commitment"
        stakeholder = current_commitment.get("stakeholder_name") or "the stakeholder"

        return HandlerResult(
            message=f"You're about to mark '{deliverable}' as at-risk.\n\n"
            "Why might you miss this commitment? "
            "(This helps draft the notification to the stakeholder)",
            panel_update={
                "mode": "atrisk_workflow",
                "entity_type": "commitment",
                "data": current_commitment,
                "workflow_step": "reason",
            },
            draft_data={
                "commitment_id": current_commitment.get("id"),
                "stakeholder_name": stakeholder,
                "reason": None,
                "impact": None,
                "proposed_resolution": None,
            },
            needs_confirmation=False,
        )

    def _prompt_for_commitment_selection(self, commitments: list[dict[str, Any]]) -> HandlerResult:
        """Prompt user to select which commitment is at-risk."""
        # Filter to only active commitments
        active = [c for c in commitments if c.get("status") in ("pending", "in_progress")]

        if not active:
            return HandlerResult(
                message="No active commitments to mark as at-risk. "
                "All your commitments are either completed or abandoned.",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        lines = ["Which commitment is at risk?", ""]
        for i, c in enumerate(active, 1):
            deliverable = (c.get("deliverable") or "Untitled")[:50]
            due = c.get("due_date") or "No date"
            lines.append(f"  {i}. {deliverable} (due: {due})")
        lines.append("")
        lines.append("Enter a number to select, or describe the commitment.")

        return HandlerResult(
            message="\n".join(lines),
            panel_update={
                "mode": "list",
                "entity_type": "commitment",
                "items": active,
            },
            draft_data=None,
            needs_confirmation=False,
        )


class CleanupHandler(CommandHandler):
    """Handler for /cleanup command - view or update cleanup plan."""

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute /cleanup command.

        Args:
            cmd: The parsed command.
            context: Context with current commitment and cleanup plan data.

        Returns:
            HandlerResult with cleanup plan view or prompt.
        """
        current_commitment = context.get("current_commitment")
        cleanup_plan = context.get("cleanup_plan")

        # Check for commitment context
        if not current_commitment:
            return HandlerResult(
                message="Select a commitment first to view its cleanup plan. "
                "Use /show commitments to see your commitments.",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        status = current_commitment.get("status", "")

        # Check if commitment has a cleanup plan
        if not cleanup_plan:
            if status == "at_risk":
                # At-risk but no cleanup plan - shouldn't happen but handle gracefully
                return HandlerResult(
                    message="This commitment is at-risk but has no cleanup plan. "
                    "This may indicate a data issue. Please try /atrisk again.",
                    panel_update=None,
                    draft_data=None,
                    needs_confirmation=False,
                )
            # Not at-risk, no cleanup plan
            return HandlerResult(
                message="This commitment doesn't have a cleanup plan. "
                "Would you like to mark it as at-risk? Use /atrisk.",
                panel_update={
                    "mode": "view",
                    "entity_type": "commitment",
                    "data": current_commitment,
                },
                draft_data=None,
                needs_confirmation=False,
            )

        # Show cleanup plan
        return self._show_cleanup_plan(current_commitment, cleanup_plan)

    def _show_cleanup_plan(
        self, commitment: dict[str, Any], cleanup_plan: dict[str, Any]
    ) -> HandlerResult:
        """Display cleanup plan details."""
        plan_status = cleanup_plan.get("status", "unknown")
        impact = cleanup_plan.get("impact_description") or "Not specified"
        actions = cleanup_plan.get("mitigation_actions", [])
        notification_complete = cleanup_plan.get("notification_task_completed", False)

        lines = [
            "Cleanup Plan",
            "=" * 40,
            "",
            f"Status: {plan_status}",
            f"Notification sent: {'Yes' if notification_complete else 'No'}",
            "",
            "Impact Description:",
            f"  {impact}",
            "",
            "Mitigation Actions:",
        ]

        if actions:
            for i, action in enumerate(actions, 1):
                lines.append(f"  {i}. {action}")
        else:
            lines.append("  (No mitigation actions defined yet)")

        lines.extend(
            [
                "",
                "You can update this plan by describing changes in the chat.",
                "Example: 'Add mitigation action: follow up weekly until resolved'",
            ]
        )

        return HandlerResult(
            message="\n".join(lines),
            panel_update={
                "mode": "cleanup",
                "entity_type": "cleanup_plan",
                "data": cleanup_plan,
                "commitment": commitment,
            },
            draft_data=None,
            needs_confirmation=False,
        )


class IntegrityHandler(CommandHandler):
    """Handler for /integrity command - shows integrity dashboard."""

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute /integrity command.

        Args:
            cmd: The parsed command.
            context: Context with integrity metrics.

        Returns:
            HandlerResult with integrity dashboard.
        """
        metrics = context.get("integrity_metrics")

        # Handle case where no metrics are available
        if not metrics:
            # New user with clean slate
            return self._show_empty_dashboard()

        return self._show_dashboard(metrics)

    def _show_empty_dashboard(self) -> HandlerResult:
        """Show dashboard for new users with no history."""
        lines = [
            "Integrity Dashboard",
            "=" * 40,
            "",
            "  Grade: A+",
            "",
            "You're starting with a clean slate!",
            "",
            "Keep your commitments to maintain your integrity score.",
            "If you can't meet a commitment, use /atrisk to notify",
            "stakeholders and create a cleanup plan.",
            "",
            "Your score is based on:",
            "  - On-time delivery rate (40%)",
            "  - Notification timeliness (25%)",
            "  - Cleanup completion rate (25%)",
            "  - Reliability streak bonus (10%)",
        ]

        return HandlerResult(
            message="\n".join(lines),
            panel_update={
                "mode": "integrity",
                "entity_type": "integrity_dashboard",
                "data": {
                    "letter_grade": "A+",
                    "composite_score": 100.0,
                    "on_time_rate": 1.0,
                    "notification_timeliness": 1.0,
                    "cleanup_completion_rate": 1.0,
                    "current_streak_weeks": 0,
                    "is_empty": True,
                },
            },
            draft_data=None,
            needs_confirmation=False,
        )

    def _show_dashboard(self, metrics: dict[str, Any]) -> HandlerResult:
        """Show integrity dashboard with metrics."""
        grade = metrics.get("letter_grade", "?")
        score = metrics.get("composite_score", 0)
        on_time = metrics.get("on_time_rate", 0) * 100
        timeliness = metrics.get("notification_timeliness", 0) * 100
        cleanup = metrics.get("cleanup_completion_rate", 0) * 100
        streak = metrics.get("current_streak_weeks", 0)

        # Totals for context
        total_completed = metrics.get("total_completed", 0)
        total_on_time = metrics.get("total_on_time", 0)
        total_at_risk = metrics.get("total_at_risk", 0)
        total_abandoned = metrics.get("total_abandoned", 0)

        # Affecting commitments
        affecting = metrics.get("affecting_commitments", [])

        lines = [
            "Integrity Dashboard",
            "=" * 40,
            "",
            f"  Grade: {grade}  (Score: {score:.1f}%)",
            "",
            "Metrics:",
            f"  On-time delivery:      {on_time:.0f}% ({total_on_time}/{total_completed} on time)",
            f"  Notification timing:   {timeliness:.0f}%",
            f"  Cleanup completion:    {cleanup:.0f}%",
            f"  Reliability streak:    {streak} week(s)",
            "",
        ]

        # Add summary stats
        if total_at_risk > 0 or total_abandoned > 0:
            lines.append("History:")
            lines.append(f"  Total completed: {total_completed}")
            if total_at_risk > 0:
                lines.append(f"  Marked at-risk: {total_at_risk}")
            if total_abandoned > 0:
                lines.append(f"  Abandoned: {total_abandoned}")
            lines.append("")

        # Add affecting commitments
        if affecting:
            lines.append("Recent issues affecting score:")
            for item in affecting:
                deliverable = item.get("deliverable", "Untitled")[:40]
                reason = item.get("reason", "unknown")
                lines.append(f"  • {deliverable} ({reason})")
            lines.append("")

        # Grade color hint for TUI
        grade_colors = {
            "A+": "green",
            "A": "green",
            "A-": "green",
            "B+": "blue",
            "B": "blue",
            "B-": "blue",
            "C+": "yellow",
            "C": "yellow",
            "C-": "yellow",
            "D+": "red",
            "D": "red",
            "D-": "red",
            "F": "red",
        }

        return HandlerResult(
            message="\n".join(lines),
            panel_update={
                "mode": "integrity",
                "entity_type": "integrity_dashboard",
                "data": {
                    **metrics,
                    "grade_color": grade_colors.get(grade, "white"),
                    "affecting_commitments": affecting,
                },
            },
            draft_data=None,
            needs_confirmation=False,
        )


class AbandonHandler(CommandHandler):
    """Handler for /abandon command - marks commitment as abandoned.

    Implements soft enforcement per Honor-Your-Word protocol:
    - If commitment is at_risk and notification task not completed, warns user
    - Offers option to mark at-risk first if stakeholder exists
    - On confirmed abandon, sets CleanupPlan status to skipped if applicable
    """

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute /abandon command.

        Args:
            cmd: The parsed command.
            context: Context with current commitment data.

        Returns:
            HandlerResult with appropriate prompt or confirmation.
        """
        current_commitment = context.get("current_commitment")
        available_commitments = context.get("available_commitments", [])

        # Check if we have a commitment in context
        if not current_commitment:
            return self._handle_no_commitment(available_commitments)

        # Check if already completed or abandoned
        validation_result = self._validate_commitment_status(current_commitment)
        if validation_result:
            return validation_result

        status = current_commitment.get("status") or ""
        deliverable = current_commitment.get("deliverable") or "this commitment"
        stakeholder = current_commitment.get("stakeholder_name") or ""

        # D3: Soft enforcement for at-risk commitments
        if status == "at_risk":
            return self._handle_at_risk_abandon(current_commitment, context)

        # D4: Pre-abandon prompt for commitments with stakeholders
        if stakeholder and status in ("pending", "in_progress"):
            return self._prompt_atrisk_first(current_commitment)

        # Standard abandonment (no stakeholder)
        return HandlerResult(
            message=f"Abandon '{deliverable}'?\n\nThis will mark the commitment as abandoned.",
            panel_update={
                "mode": "view",
                "entity_type": "commitment",
                "data": current_commitment,
                "action": "abandon",
            },
            draft_data=None,
            needs_confirmation=True,
        )

    def _handle_no_commitment(self, available_commitments: list[dict[str, Any]]) -> HandlerResult:
        """Handle case when no commitment is in context."""
        if available_commitments:
            return self._prompt_for_commitment_selection(available_commitments)
        return HandlerResult(
            message="No active commitments to abandon. Create a commitment first with /commit.",
            panel_update=None,
            draft_data=None,
            needs_confirmation=False,
        )

    def _validate_commitment_status(self, commitment: dict[str, Any]) -> HandlerResult | None:
        """Validate commitment can be abandoned. Returns error result or None if valid."""
        status = commitment.get("status", "")
        if status == "completed":
            return HandlerResult(
                message="This commitment is already completed. "
                "Completed commitments cannot be abandoned.",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )
        if status == "abandoned":
            return HandlerResult(
                message="This commitment is already abandoned.",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )
        return None

    def _handle_at_risk_abandon(
        self, commitment: dict[str, Any], context: dict[str, Any]
    ) -> HandlerResult:
        """Handle abandonment of at-risk commitment with soft enforcement.

        Checks if notification task is completed. If not, warns the user
        that abandoning without notification will affect their integrity score.
        """
        deliverable = commitment.get("deliverable") or "this commitment"
        stakeholder = commitment.get("stakeholder_name") or "the stakeholder"
        cleanup_plan = context.get("cleanup_plan")
        notification_task = context.get("notification_task")

        # Check if notification task exists and is incomplete
        notification_incomplete = False
        if notification_task:
            task_status = notification_task.get("status", "")
            notification_incomplete = task_status not in ("completed", "done")

        if notification_incomplete:
            # D3: Warn user about incomplete notification
            return HandlerResult(
                message=f"⚠️ You haven't notified {stakeholder} yet.\n\n"
                f"Abandoning '{deliverable}' without notification will:\n"
                "• Set your cleanup plan status to 'skipped'\n"
                "• Negatively affect your integrity score\n\n"
                "Options:\n"
                "• Type 'yes' to abandon anyway\n"
                "• Type 'notify' to complete notification first\n"
                "• Type 'cancel' to go back",
                panel_update={
                    "mode": "abandon_warning",
                    "entity_type": "commitment",
                    "data": commitment,
                    "cleanup_plan": cleanup_plan,
                    "notification_task": notification_task,
                    "warning_type": "notification_incomplete",
                },
                draft_data={
                    "commitment_id": commitment.get("id"),
                    "skip_notification": True,
                    "skipped_reason": "User abandoned without completing notification",
                },
                needs_confirmation=True,
            )

        # Notification completed, standard at-risk abandonment
        return HandlerResult(
            message=f"Abandon '{deliverable}'?\n\n"
            f"You've notified {stakeholder}. The commitment will be marked as abandoned "
            "and the cleanup plan completed.",
            panel_update={
                "mode": "view",
                "entity_type": "commitment",
                "data": commitment,
                "action": "abandon",
                "cleanup_plan": cleanup_plan,
            },
            draft_data=None,
            needs_confirmation=True,
        )

    def _prompt_atrisk_first(self, commitment: dict[str, Any]) -> HandlerResult:
        """D4: Prompt user to mark at-risk first before abandoning.

        When a commitment has a stakeholder but isn't at-risk yet,
        encourage the user to go through proper notification workflow.
        """
        deliverable = commitment.get("deliverable") or "this commitment"
        stakeholder = commitment.get("stakeholder_name") or "the stakeholder"

        return HandlerResult(
            message=f"'{deliverable}' has a stakeholder ({stakeholder}).\n\n"
            "Would you like to:\n"
            "• Mark at-risk first to notify them? (recommended)\n"
            "• Abandon directly without notification?\n\n"
            "Type 'atrisk' to mark at-risk first, or 'abandon' to abandon directly.",
            panel_update={
                "mode": "abandon_prompt",
                "entity_type": "commitment",
                "data": commitment,
                "prompt_type": "atrisk_first",
            },
            draft_data={
                "commitment_id": commitment.get("id"),
                "stakeholder_name": stakeholder,
            },
            needs_confirmation=False,
        )

    def _prompt_for_commitment_selection(self, commitments: list[dict[str, Any]]) -> HandlerResult:
        """Prompt user to select which commitment to abandon."""
        # Filter to only active commitments
        active = [
            c for c in commitments if c.get("status") in ("pending", "in_progress", "at_risk")
        ]

        if not active:
            return HandlerResult(
                message="No active commitments to abandon. "
                "All your commitments are either completed or already abandoned.",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        lines = ["Which commitment do you want to abandon?", ""]
        for i, c in enumerate(active, 1):
            deliverable = (c.get("deliverable") or "Untitled")[:50]
            status = c.get("status") or "unknown"
            status_indicator = " ⚠️" if status == "at_risk" else ""
            lines.append(f"  {i}. {deliverable} [{status}]{status_indicator}")
        lines.append("")
        lines.append("Enter a number to select, or describe the commitment.")

        return HandlerResult(
            message="\n".join(lines),
            panel_update={
                "mode": "list",
                "entity_type": "commitment",
                "items": active,
                "action": "select_for_abandon",
            },
            draft_data=None,
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

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
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


class RecoverHandler(CommandHandler):
    """Handler for /recover command - recovers at-risk commitment to in_progress.

    Used when the situation has improved and the commitment can be delivered.
    """

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute /recover command.

        Args:
            cmd: The parsed command.
            context: Context with current commitment data.

        Returns:
            HandlerResult for recovery workflow.
        """
        current_commitment = context.get("current_commitment")

        # Check if we have a commitment in context
        if not current_commitment:
            return HandlerResult(
                message="No commitment selected. Use /show commitments to view "
                "your commitments, then select one to recover.",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        # Check if commitment is at-risk
        status = current_commitment.get("status", "")
        if hasattr(status, "value"):
            status = status.value

        if status != "at_risk":
            return HandlerResult(
                message=f"This commitment is not at-risk (current status: {status}). "
                "Only at-risk commitments can be recovered.",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        commitment_id = current_commitment.get("id")
        if not commitment_id:
            return HandlerResult(
                message="Could not identify commitment. Please try again.",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        # Check for notification_resolved argument
        notification_resolved = False
        if cmd.args and cmd.args[0].lower() in ("resolved", "yes", "y"):
            notification_resolved = True

        try:
            with get_session() as session:
                service = IntegrityService()
                result = service.recover_commitment(
                    session=session,
                    commitment_id=commitment_id,
                    notification_resolved=notification_resolved,
                )

                deliverable = result.commitment.deliverable or "Commitment"
                stakeholder = current_commitment.get("stakeholder_name", "stakeholder")

                if result.notification_still_needed:
                    # Prompt user about notification task
                    message = (
                        f"'{deliverable}' has been recovered to in-progress.\n\n"
                        f"You previously marked this as at-risk. "
                        f"Do you still need to notify {stakeholder}, "
                        "or has the situation resolved?\n\n"
                        "Reply with:\n"
                        "  - '/recover resolved' to skip the notification (situation resolved)\n"
                        "  - Keep the notification task to complete it"
                    )
                else:
                    message = (
                        f"'{deliverable}' has been recovered to in-progress.\n\n"
                        "The cleanup plan has been cancelled. "
                        "Great work getting things back on track!"
                    )

                # Build updated commitment data for panel
                updated_data = dict(current_commitment)
                updated_data["status"] = "in_progress"

                return HandlerResult(
                    message=message,
                    panel_update={
                        "mode": "view",
                        "entity_type": "commitment",
                        "data": updated_data,
                    },
                    draft_data=None,
                    needs_confirmation=False,
                )

        except ValueError as e:
            return HandlerResult(
                message=f"Could not recover commitment: {e}",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )
        except Exception as e:
            return HandlerResult(
                message=f"An error occurred: {e}",
                panel_update=None,
                draft_data=None,
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
    CommandType.TRIAGE: TriageHandler,
    CommandType.SHOW: ShowHandler,
    CommandType.HELP: HelpHandler,
    CommandType.VIEW: ViewHandler,
    CommandType.CANCEL: CancelHandler,
    CommandType.COMPLETE: CompleteHandler,
    CommandType.TYPE: TypeHandler,
    CommandType.EDIT: EditHandler,
    CommandType.ATRISK: AtRiskHandler,
    CommandType.CLEANUP: CleanupHandler,
    CommandType.INTEGRITY: IntegrityHandler,
    CommandType.ABANDON: AbandonHandler,
    CommandType.HOURS: HoursHandler,
    CommandType.RECOVER: RecoverHandler,
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
