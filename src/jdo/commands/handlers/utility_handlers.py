"""Utility command handler implementations.

Includes handlers for help, show, view, cancel, edit, type, hours, list,
review, and triage commands.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from loguru import logger
from rich import box
from rich.console import Console
from rich.table import Table
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select

from jdo.ai.time_parsing import format_hours, parse_time_input
from jdo.commands.handlers.base import CommandHandler, HandlerResult
from jdo.commands.parser import ParsedCommand
from jdo.db.navigation import NavigationService
from jdo.db.session import get_visions_due_for_review
from jdo.models.commitment import Commitment, CommitmentStatus
from jdo.models.draft import EntityType
from jdo.models.goal import Goal
from jdo.models.vision import Vision
from jdo.output.formatters import (
    MAX_LIST_SHORTCUTS,
    format_commitment_list,
    format_empty_list,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlmodel import Session as DBSession

    from jdo.repl.session import Session

# Console instance for Rich output
console = Console()


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

        # General help grouped by category
        lines = [
            "[bold]JDO Commands[/bold]",
            "",
            "[cyan]Creating & Managing[/cyan]",
            "  /commit (/c)  - Create a new commitment",
            "  /goal         - Create a new goal",
            "  /task         - Add a task to a commitment",
            "  /vision       - Manage visions",
            "  /milestone    - Manage milestones",
            "  /recurring    - Manage recurring commitments",
            "",
            "[cyan]Navigation[/cyan]",
            "  /list (/l)    - List entities (commitments, goals, visions)",
            "  /view (/v)    - View a specific item by ID",
            "  /1 - /5       - Quick select from last list",
            "  /show         - Display entity lists by type",
            "",
            "[cyan]Commitment Status[/cyan]",
            "  /complete     - Mark item as completed",
            "  /atrisk       - Mark commitment as at-risk",
            "  /recover      - Recover at-risk commitment",
            "  /abandon      - Mark commitment as abandoned",
            "  /cleanup      - View/update cleanup plan",
            "",
            "[cyan]Productivity[/cyan]",
            "  /triage       - Process captured items",
            "  /hours        - Set available hours for time coaching",
            "  /integrity    - Show integrity dashboard",
            "",
            "[cyan]Other[/cyan]",
            "  /help (/h)    - Show this help",
            "  /cancel       - Cancel current draft",
            "",
            "[dim]Shortcuts: /c=commit, /l=list, /v=view, /h=help[/dim]",
            "[dim]Type /help <command> for details on a specific command.[/dim]",
        ]
        return HandlerResult(
            message="\n".join(lines),
            panel_update=None,
            draft_data=None,
            needs_confirmation=False,
        )


class ListHandler(CommandHandler):
    """Handler for /list command - lists entities (commitments, goals, visions).

    Uses db_session from context to query entities directly and
    renders output using Rich formatters.
    """

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute /list command.

        Args:
            cmd: The parsed command with optional entity type arg.
            context: Context with db_session.

        Returns:
            HandlerResult with list message.
        """
        db_session: DBSession | None = context.get("db_session")
        if db_session is None:
            return HandlerResult(
                message="Database session not available.",
                error=True,
            )

        entity_type = cmd.args[0].lower().strip() if cmd.args else "commitments"

        if entity_type in ("commitment", "commitments"):
            return self._list_commitments(db_session, context)
        if entity_type in ("goal", "goals"):
            return self._list_goals(db_session, context)
        if entity_type in ("vision", "visions"):
            return self._list_visions(db_session, context)

        return HandlerResult(
            message=f"Unknown entity type: {entity_type}",
            suggestions=["/list commitments", "/list goals", "/list visions"],
            error=True,
        )

    def _list_commitments(self, db_session: DBSession, context: dict[str, Any]) -> HandlerResult:
        """List all active commitments."""
        # Get active commitments (not completed or abandoned)
        active_statuses = [
            CommitmentStatus.PENDING,
            CommitmentStatus.IN_PROGRESS,
            CommitmentStatus.AT_RISK,
        ]
        statement = select(Commitment).where(Commitment.status.in_(active_statuses))
        commitments = list(db_session.exec(statement).all())

        # Update session's last_list_items for /1, /2 shortcuts
        session: Session | None = context.get("session")
        if session is not None:
            session.set_last_list_items([("commitment", c.id) for c in commitments[:5]])

        if not commitments:
            console.print(format_empty_list("commitment"))
            return HandlerResult(
                message="",  # Already printed via console
                clear_context=True,
            )

        table = format_commitment_list(commitments, show_shortcuts=True)
        console.print(table)
        console.print(f"[dim]{len(commitments)} active commitment(s)[/dim]")
        return HandlerResult(
            message="",  # Already printed via console
            clear_context=True,
        )

    def _list_goals(self, db_session: DBSession, context: dict[str, Any]) -> HandlerResult:
        """List all goals."""
        goals = NavigationService.get_goals_list(db_session)

        # Update session's last_list_items for /1, /2 shortcuts
        session: Session | None = context.get("session")
        if session is not None and goals:
            from uuid import UUID  # noqa: PLC0415

            session.set_last_list_items([("goal", UUID(g["id"])) for g in goals[:5]])

        if not goals:
            console.print(format_empty_list("goal"))
            return HandlerResult(
                message="",
                clear_context=True,
            )

        table = Table(title="Goals", box=box.ROUNDED)
        table.add_column("", style="cyan", width=4)  # Shortcut column
        table.add_column("ID", style="dim", width=6)
        table.add_column("Title", width=30)
        table.add_column("Status", width=12)

        for idx, g in enumerate(goals):
            shortcut = f"[bold cyan]/[{idx + 1}][/bold cyan]" if idx < MAX_LIST_SHORTCUTS else ""
            table.add_row(
                shortcut,
                g["id"][:6],
                g["title"][:30] if g["title"] else "N/A",
                g["status"],
            )

        console.print(table)
        console.print(f"[dim]{len(goals)} goal(s)[/dim]")
        if goals:
            console.print("[dim]Use /1, /2, etc. to view details[/dim]")
        return HandlerResult(
            message="",
            clear_context=True,
        )

    def _list_visions(self, db_session: DBSession, context: dict[str, Any]) -> HandlerResult:
        """List all visions."""
        visions = NavigationService.get_visions_list(db_session)

        # Update session's last_list_items for /1, /2 shortcuts
        session: Session | None = context.get("session")
        if session is not None and visions:
            from uuid import UUID  # noqa: PLC0415

            session.set_last_list_items([("vision", UUID(v["id"])) for v in visions[:5]])

        if not visions:
            console.print(format_empty_list("vision"))
            return HandlerResult(
                message="",
                clear_context=True,
            )

        table = Table(title="Visions", box=box.ROUNDED)
        table.add_column("", style="cyan", width=4)  # Shortcut column
        table.add_column("ID", style="dim", width=6)
        table.add_column("Title", width=30)
        table.add_column("Timeframe", width=15)
        table.add_column("Status", width=12)

        for idx, v in enumerate(visions):
            shortcut = f"[bold cyan]/[{idx + 1}][/bold cyan]" if idx < MAX_LIST_SHORTCUTS else ""
            table.add_row(
                shortcut,
                v["id"][:6],
                v["title"][:30] if v["title"] else "N/A",
                v.get("timeframe", "N/A") or "N/A",
                v["status"],
            )

        console.print(table)
        console.print(f"[dim]{len(visions)} vision(s)[/dim]")
        if visions:
            console.print("[dim]Use /1, /2, etc. to view details[/dim]")
        return HandlerResult(
            message="",
            clear_context=True,
        )


class ReviewHandler(CommandHandler):
    """Handler for /review command - reviews visions due for quarterly review.

    Uses db_session from context to query visions and update review dates.
    """

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:  # noqa: ARG002
        """Execute /review command.

        Args:
            cmd: The parsed command.
            context: Context with db_session and session.

        Returns:
            HandlerResult with review info.
        """
        db_session: DBSession | None = context.get("db_session")
        session: Session | None = context.get("session")

        if db_session is None:
            return HandlerResult(
                message="Database session not available.",
                error=True,
            )

        try:
            visions_due = get_visions_due_for_review(db_session)
        except (OSError, SQLAlchemyError) as e:
            logger.warning(f"Failed to get visions due for review: {e}")
            return HandlerResult(
                message="Error loading visions. Please try again.",
                error=True,
            )

        if not visions_due:
            return HandlerResult(
                message="No visions are due for review.",
            )

        # Get the first vision that hasn't been reviewed this session
        vision = visions_due[0]

        # Display vision details
        console.print()
        console.print(f"[bold magenta]Vision: {vision.title}[/bold magenta]")
        console.print()
        console.print(f"[bold]Narrative:[/bold] {vision.narrative}")
        if vision.timeframe:
            console.print(f"[bold]Timeframe:[/bold] {vision.timeframe}")
        if vision.why_it_matters:
            console.print(f"[bold]Why it matters:[/bold] {vision.why_it_matters}")
        if vision.metrics:
            console.print("[bold]Success metrics:[/bold]")
            for metric in vision.metrics:
                console.print(f"  - {metric}")
        console.print()

        # Mark as reviewed
        vision.complete_review()
        db_session.add(vision)
        db_session.commit()

        # Remove from snoozed set if present
        if session is not None:
            session.snoozed_vision_ids.discard(vision.id)

        console.print(
            f"[green]Vision reviewed! Next review scheduled for {vision.next_review_date}.[/green]"
        )

        # Check if there are more visions to review
        remaining = len(visions_due) - 1
        if remaining > 0:
            console.print(
                f"[dim]You have {remaining} more vision(s) due for review. "
                f"Type /review to continue.[/dim]"
            )

        return HandlerResult(
            message="",  # Already printed via console
        )


class ViewHandler(CommandHandler):
    """Handler for /view command - shows entity details.

    Supports:
    - /view <id> - view by full or partial UUID
    - /view 1, /view 2 - view by list shortcut (from last_list_items)
    - /1, /2 - aliases for /view 1, /view 2
    """

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute /view command.

        Args:
            cmd: The parsed command with entity ID or shortcut number.
            context: Context with db_session and session.

        Returns:
            HandlerResult with entity details or error.
        """
        db_session: DBSession | None = context.get("db_session")
        session: Session | None = context.get("session")

        if db_session is None:
            return HandlerResult(
                message="Database session not available.",
                error=True,
            )

        if not cmd.args:
            return HandlerResult(
                message="Usage: /view <id> or /view 1-5",
                suggestions=["/list", "/view abc123"],
                error=True,
            )

        id_arg = cmd.args[0]

        # Check if it's a shortcut number (1-5)
        if id_arg.isdigit():
            shortcut_num = int(id_arg)
            return self._view_by_shortcut(shortcut_num, session, db_session)

        # Otherwise, look up by partial ID
        return self._view_by_id(id_arg, session, db_session)

    def _view_by_shortcut(
        self,
        shortcut_num: int,
        session: Session | None,
        db_session: DBSession,
    ) -> HandlerResult:
        """View entity by list shortcut number."""
        if session is None:
            return HandlerResult(
                message="Session not available.",
                error=True,
            )

        if not session.last_list_items:
            return HandlerResult(
                message="No list to select from. Use /list first.",
                suggestions=["/list"],
                error=True,
            )

        if shortcut_num < 1 or shortcut_num > len(session.last_list_items):
            max_num = min(5, len(session.last_list_items))
            return HandlerResult(
                message=f"No item {shortcut_num}. Use /1 through /{max_num}.",
                suggestions=["/list"],
                error=True,
            )

        entity_type, entity_id = session.last_list_items[shortcut_num - 1]
        return self._lookup_and_display(entity_type, entity_id, session, db_session)

    def _view_by_id(
        self,
        partial_id: str,
        session: Session | None,
        db_session: DBSession,
    ) -> HandlerResult:
        """View entity by full or partial UUID."""
        from uuid import UUID  # noqa: PLC0415

        from jdo.models import Commitment, Goal, Vision  # noqa: PLC0415

        partial_id = partial_id.lower().strip()

        # Try each entity type
        for model, entity_type in [
            (Commitment, "commitment"),
            (Goal, "goal"),
            (Vision, "vision"),
        ]:
            try:
                # Try exact UUID match first
                try:
                    full_uuid = UUID(partial_id)
                    entity = db_session.get(model, full_uuid)
                    if entity:
                        return self._display_entity(entity, entity_type, session, db_session)
                except ValueError:
                    pass  # Not a valid UUID, try partial match

                # Try partial ID match (first 6+ chars)
                entities = list(db_session.exec(select(model)).all())
                matches = [e for e in entities if str(e.id).lower().startswith(partial_id)]

                if len(matches) == 1:
                    return self._display_entity(matches[0], entity_type, session, db_session)
                if len(matches) > 1:
                    # Ambiguous - show options
                    options = [f"{str(e.id)[:8]}" for e in matches[:5]]
                    opts_str = ", ".join(options)
                    msg = f"Multiple {entity_type}s match '{partial_id}': {opts_str}"
                    return HandlerResult(
                        message=msg,
                        suggestions=[f"/view {options[0]}"],
                        error=True,
                    )
            except (OSError, SQLAlchemyError) as e:
                logger.warning(f"Error looking up {entity_type}: {e}")
                continue

        return HandlerResult(
            message=f"No entity found matching '{partial_id}'.",
            suggestions=["/list"],
            error=True,
        )

    def _lookup_and_display(
        self,
        entity_type: str,
        entity_id: UUID,
        session: Session | None,
        db_session: DBSession,
    ) -> HandlerResult:
        """Look up entity by type and ID, then display."""
        from jdo.models import Commitment, Goal, Vision  # noqa: PLC0415

        model_map = {
            "commitment": Commitment,
            "goal": Goal,
            "vision": Vision,
        }

        model = model_map.get(entity_type)
        if model is None:
            return HandlerResult(
                message=f"Unknown entity type: {entity_type}",
                error=True,
            )

        try:
            entity = db_session.get(model, entity_id)
            if entity is None:
                return HandlerResult(
                    message=f"{entity_type.title()} not found.",
                    suggestions=["/list"],
                    error=True,
                )
            return self._display_entity(entity, entity_type, session, db_session)
        except (OSError, SQLAlchemyError) as e:
            logger.warning(f"Error looking up {entity_type}: {e}")
            return HandlerResult(
                message=f"Error loading {entity_type}.",
                error=True,
            )

    def _display_entity(
        self,
        entity: Commitment | Goal | Vision,
        entity_type: str,
        session: Session | None,
        db_session: DBSession,  # noqa: ARG002
    ) -> HandlerResult:
        """Display entity details and update context."""
        from jdo.repl.session import EntityContext  # noqa: PLC0415

        entity_id = entity.id
        short_id = str(entity_id)[:6]

        # Get display name based on entity type
        if entity_type == "commitment":
            display_name = entity.deliverable[:30] if entity.deliverable else "Untitled"
            self._print_commitment_details(entity)
        elif entity_type == "goal":
            display_name = entity.title[:30] if entity.title else "Untitled"
            self._print_goal_details(entity)
        elif entity_type == "vision":
            display_name = entity.title[:30] if entity.title else "Untitled"
            self._print_vision_details(entity)
        else:
            display_name = short_id

        # Update session context
        if session is not None:
            session.entity_context.set(
                entity_type=entity_type,
                entity_id=entity_id,
                short_id=short_id,
                display_name=display_name,
            )

        # Build entity context for HandlerResult
        context = EntityContext(
            entity_type=entity_type,
            entity_id=entity_id,
            short_id=short_id,
            display_name=display_name,
        )

        return HandlerResult(
            message="",  # Already printed via console
            entity_context=context,
        )

    def _print_commitment_details(self, commitment: Commitment) -> None:
        """Print commitment details using Rich."""
        from rich.panel import Panel  # noqa: PLC0415

        lines = [
            f"[bold]Deliverable:[/bold] {commitment.deliverable}",
            f"[bold]Status:[/bold] {commitment.status.value}",
            f"[bold]Due:[/bold] {commitment.due_date}",
        ]
        if commitment.due_time:
            lines.append(f"[bold]Time:[/bold] {commitment.due_time}")

        panel = Panel(
            "\n".join(lines),
            title=f"[cyan]Commitment {str(commitment.id)[:6]}[/cyan]",
            border_style="cyan",
        )
        console.print(panel)

    def _print_goal_details(self, goal: Goal) -> None:
        """Print goal details using Rich."""
        from rich.panel import Panel  # noqa: PLC0415

        lines = [
            f"[bold]Title:[/bold] {goal.title}",
            f"[bold]Status:[/bold] {goal.status.value}",
        ]
        if goal.problem_statement:
            lines.append(f"[bold]Problem:[/bold] {goal.problem_statement[:100]}...")
        if goal.solution_vision:
            lines.append(f"[bold]Vision:[/bold] {goal.solution_vision[:100]}...")

        panel = Panel(
            "\n".join(lines),
            title=f"[green]Goal {str(goal.id)[:6]}[/green]",
            border_style="green",
        )
        console.print(panel)

    def _print_vision_details(self, vision: Vision) -> None:
        """Print vision details using Rich."""
        from rich.panel import Panel  # noqa: PLC0415

        lines = [
            f"[bold]Title:[/bold] {vision.title}",
            f"[bold]Status:[/bold] {vision.status.value}",
        ]
        if vision.narrative:
            lines.append(f"[bold]Narrative:[/bold] {vision.narrative[:100]}...")
        if vision.timeframe:
            lines.append(f"[bold]Timeframe:[/bold] {vision.timeframe}")

        panel = Panel(
            "\n".join(lines),
            title=f"[magenta]Vision {str(vision.id)[:6]}[/magenta]",
            border_style="magenta",
        )
        console.print(panel)


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
