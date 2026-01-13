"""Main REPL loop for conversational CLI.

Provides a prompt_toolkit-based REPL with streaming AI responses,
session state management, and hybrid input handling.
"""

from __future__ import annotations

import asyncio
import sys
from typing import TYPE_CHECKING

from loguru import logger
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from rich import box
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select

from jdo.ai.agent import JDODependencies, create_agent, get_model_identifier
from jdo.ai.context import stream_response
from jdo.ai.extraction import extract_commitment
from jdo.ai.timeout import AI_STREAM_TIMEOUT_SECONDS
from jdo.auth.api import is_authenticated
from jdo.config import get_settings
from jdo.db import create_db_and_tables, get_session
from jdo.db.navigation import NavigationService
from jdo.db.persistence import PersistenceService
from jdo.db.session import get_triage_count, get_visions_due_for_review
from jdo.models.commitment import Commitment, CommitmentStatus
from jdo.models.goal import Goal
from jdo.models.vision import Vision
from jdo.output.formatters import (
    format_commitment_list,
    format_commitment_proposal,
    format_empty_list,
)
from jdo.repl.session import PendingDraft, Session
from jdo.utils.datetime import today_date

if TYPE_CHECKING:
    from pydantic_ai import Agent
    from sqlmodel import Session as DBSession

# Console instance for Rich output
console = Console()

# Welcome message shown on REPL start
WELCOME_MESSAGE = """\
[bold cyan]JDO[/bold cyan] - Just Do One thing at a time

I'm your commitment tracking assistant. Tell me what you need to do,
and I'll help you track it.

[dim]Type 'exit' or 'quit' to leave. Press Ctrl+C to cancel input.[/dim]
"""

# Goodbye message shown on REPL exit
GOODBYE_MESSAGE = "[dim]Goodbye! Keep your commitments.[/dim]"

# First-run guidance message for new users
FIRST_RUN_MESSAGE = """\
[bold cyan]Welcome to JDO![/bold cyan]

I'm your commitment tracking assistant. I help you make and keep promises
to the people who matter.

[bold]Try saying something like:[/bold]
  "I need to send the report to Sarah by Friday"
  "Show my commitments"
  "Create a goal to improve my health"

[dim]Type /help for available commands.[/dim]
"""

# Error message when no AI credentials are configured
NO_CREDENTIALS_MESSAGE = """\
[bold red]No AI credentials configured.[/bold red]

To use JDO, you need to configure an AI provider. Set one of:
  - OPENAI_API_KEY environment variable
  - OPENROUTER_API_KEY environment variable
"""


def check_credentials() -> bool:
    """Check if AI credentials are configured.

    Returns:
        True if credentials are available, False otherwise.
    """
    settings = get_settings()
    return is_authenticated(settings.ai_provider)


def _is_first_run(db_session: DBSession) -> bool:
    """Check if this is a first-run (no entities in database).

    Args:
        db_session: Database session.

    Returns:
        True if no commitments, goals, or visions exist.
    """
    # Check for any commitments
    commitment_count = db_session.exec(select(Commitment).limit(1)).first()
    if commitment_count:
        return False

    # Check for any goals
    goal_count = db_session.exec(select(Goal).limit(1)).first()
    if goal_count:
        return False

    # Check for any visions
    vision_count = db_session.exec(select(Vision).limit(1)).first()
    return vision_count is None


def _get_at_risk_commitments(db_session: DBSession) -> list[Commitment]:
    """Get commitments that are at-risk or overdue.

    Args:
        db_session: Database session.

    Returns:
        List of at-risk or overdue commitments.
    """
    today = today_date()

    # Get commitments that are at-risk status OR overdue (past due date but not completed)
    statement = select(Commitment).where(
        Commitment.status.in_(
            [
                CommitmentStatus.AT_RISK,
                CommitmentStatus.PENDING,
                CommitmentStatus.IN_PROGRESS,
            ]
        ),
        Commitment.due_date <= today,
    )
    return list(db_session.exec(statement).all())


# Maximum title length for vision review notice (including "..." suffix)
_VISION_TITLE_MAX_LENGTH = 40
_VISION_TITLE_TRUNCATE_AT = 37  # Leave room for "..."


def _get_vision_review_message(
    db_session: DBSession, session: Session
) -> tuple[str | None, list[Vision]]:
    """Get vision review message and list of due visions.

    Args:
        db_session: Database session.
        session: REPL session state for tracking snoozed visions.

    Returns:
        Tuple of (message or None, list of visions to snooze).
    """
    try:
        visions_due = get_visions_due_for_review(db_session)
    except (OSError, SQLAlchemyError) as e:
        logger.warning(f"Failed to check visions due for review: {e}")
        return None, []

    # Filter out already-snoozed visions
    visions_due = [v for v in visions_due if v.id not in session.snoozed_vision_ids]

    if not visions_due:
        return None, []

    if len(visions_due) == 1:
        vision = visions_due[0]
        title = vision.title
        if len(title) > _VISION_TITLE_MAX_LENGTH:
            title = title[:_VISION_TITLE_TRUNCATE_AT] + "..."
        message = (
            f"[magenta]Your vision '{title}' is due for review. "
            f"Type /review to reflect on it.[/magenta]"
        )
    else:
        message = (
            f"[magenta]You have {len(visions_due)} visions due for review. "
            f"Type /review to start.[/magenta]"
        )

    logger.debug(f"Displayed vision review notice for {len(visions_due)} vision(s)")
    return message, visions_due


def _show_startup_guidance(db_session: DBSession, session: Session) -> None:
    """Show proactive guidance messages at startup.

    Checks for:
    - First-run (new user)
    - At-risk/overdue commitments
    - Items in triage queue
    - Visions due for review

    Args:
        db_session: Database session.
        session: REPL session state for tracking snoozed visions.
    """
    # Check for first-run
    if _is_first_run(db_session):
        console.print(FIRST_RUN_MESSAGE)
        return

    # Show regular welcome
    console.print(WELCOME_MESSAGE)

    messages = []

    # Check for at-risk commitments
    at_risk = _get_at_risk_commitments(db_session)
    if len(at_risk) == 1:
        c = at_risk[0]
        messages.append(
            f"[yellow]You have 1 commitment that needs attention: "
            f'"{c.deliverable[:30]}..."[/yellow]'
        )
    elif at_risk:
        messages.append(
            f"[yellow]You have {len(at_risk)} commitments that need attention.[/yellow]"
        )

    # Check for triage items
    triage_count = get_triage_count(db_session)
    if triage_count == 1:
        messages.append("[cyan]You have 1 item to triage.[/cyan]")
    elif triage_count > 1:
        messages.append(f"[cyan]You have {triage_count} items to triage.[/cyan]")

    # Check for visions due for review
    vision_message, visions_to_snooze = _get_vision_review_message(db_session, session)
    if vision_message:
        messages.append(vision_message)
        # Mark displayed visions as snoozed for this session
        for vision in visions_to_snooze:
            session.snoozed_vision_ids.add(vision.id)

    # Print messages
    if messages:
        console.print()
        for msg in messages:
            console.print(msg)
        console.print()


async def process_ai_input(
    user_input: str,
    agent: Agent[JDODependencies, str],
    deps: JDODependencies,
    session: Session,
) -> str:
    """Process user input through the AI agent with streaming.

    Args:
        user_input: The user's input text.
        agent: The PydanticAI agent.
        deps: Agent dependencies.
        session: Current session state.

    Returns:
        The complete AI response text.
    """
    # Show thinking indicator
    console.print("[dim]Thinking...[/dim]", end="")

    response_text = ""
    first_chunk = True

    try:
        async with asyncio.timeout(AI_STREAM_TIMEOUT_SECONDS):
            output = Text()
            with Live(output, console=console, refresh_per_second=10, transient=False) as live:
                async for chunk in stream_response(
                    agent,
                    user_input,
                    deps,
                    message_history=session.message_history,
                ):
                    if first_chunk:
                        # Clear "Thinking..." on first token
                        console.print("\r" + " " * 20 + "\r", end="")
                        first_chunk = False
                    output.append(chunk)
                    response_text += chunk
                    live.update(output)

        # If we never got any chunks, clear the thinking indicator
        if first_chunk:
            console.print("\r" + " " * 20 + "\r", end="")

    except TimeoutError:
        if first_chunk:
            console.print("\r" + " " * 20 + "\r", end="")
        console.print("[yellow]The AI took too long to respond. Please try again.[/yellow]")
        return ""
    except (OSError, ConnectionError) as e:
        # Handle network-related errors specifically
        if first_chunk:
            console.print("\r" + " " * 20 + "\r", end="")
        console.print(f"[red]Error communicating with AI: {e}[/red]")
        return ""

    console.print()  # Newline after response
    return response_text


async def handle_slash_command(
    user_input: str,
    session: Session,
    db_session: DBSession,
) -> bool:
    """Handle slash commands (bypass AI for queries, use AI for extraction).

    Args:
        user_input: The user's input starting with '/'.
        session: Current session state for pending drafts.
        db_session: Database session for queries.

    Returns:
        True if command was handled, False if unknown command.
    """
    parts = user_input[1:].split(maxsplit=1)
    command = parts[0].lower() if parts else ""
    args = parts[1] if len(parts) > 1 else ""

    if command == "help":
        _handle_help()
        return True

    if command == "list":
        _handle_list(args, db_session)
        return True

    if command == "commit":
        await _handle_commit(args, session, db_session)
        return True

    if command == "complete":
        # TODO: Implement complete command
        console.print("[yellow]Complete command not yet implemented in REPL.[/yellow]")
        console.print("[dim]For now, say 'mark commitment X as complete'.[/dim]")
        return True

    if command == "review":
        _handle_review(session, db_session)
        return True

    console.print(
        f"[yellow]Unknown command: /{command}. Type /help for available commands.[/yellow]"
    )
    return True


async def _handle_commit(args: str, session: Session, _db_session: DBSession) -> None:
    """Handle /commit command.

    Args:
        args: The commitment description text.
        session: Session state for pending draft.
        _db_session: Database session (reserved for future direct DB operations).
    """
    del _db_session  # Reserved for future direct DB operations
    if not args:
        console.print("[yellow]Usage: /commit <description>[/yellow]")
        console.print('[dim]Example: /commit "send report to Sarah by Friday"[/dim]')
        return

    # Strip quotes if present
    text = args.strip("\"'")

    console.print("[dim]Extracting commitment details...[/dim]")

    try:
        # Use AI extraction to parse the commitment
        model = get_model_identifier()
        messages = [{"role": "user", "content": text}]
        extracted = await extract_commitment(messages, model)

        # Store as pending draft for confirmation
        session.set_pending_draft(
            action="create",
            entity_type="commitment",
            data={
                "deliverable": extracted.deliverable,
                "stakeholder": extracted.stakeholder_name,
                "due_date": extracted.due_date.isoformat(),
                "due_time": extracted.due_time.isoformat() if extracted.due_time else None,
            },
        )

        # Show proposal
        panel = format_commitment_proposal(
            deliverable=extracted.deliverable,
            stakeholder=extracted.stakeholder_name,
            due_date=extracted.due_date,
            due_time=extracted.due_time.strftime("%H:%M") if extracted.due_time else None,
        )
        console.print(panel)

    except TimeoutError:
        console.print("[red]AI extraction timed out. Please try again.[/red]")
    except (ValueError, KeyError) as e:
        console.print(f"[red]Could not extract commitment details: {e}[/red]")
        console.print("[dim]Try being more specific, e.g.: 'report to Sarah by Friday'[/dim]")


def _handle_confirmation(
    user_input: str,
    session: Session,
    db_session: DBSession,
) -> bool:
    """Handle confirmation responses for pending drafts.

    Args:
        user_input: The user's response (yes/no/refinement).
        session: Session state with pending draft.
        db_session: Database session.

    Returns:
        True if confirmation was handled, False if no pending draft.
    """
    draft = session.pending_draft
    if draft is None:
        return False

    lower_input = user_input.lower().strip()

    # Check for affirmative responses
    if lower_input in ("yes", "y", "correct", "do it", "looks good", "ok", "okay"):
        return _confirm_draft(draft, session, db_session)

    # Check for negative responses
    if lower_input in ("no", "n", "cancel", "never mind", "nope"):
        session.clear_pending_draft()
        console.print("[dim]Cancelled.[/dim]")
        return True

    # Otherwise, treat as refinement - let AI handle it
    return False


def _confirm_draft(
    draft: PendingDraft,
    session: Session,
    db_session: DBSession,
) -> bool:
    """Execute a confirmed draft.

    Args:
        draft: The pending draft to execute.
        session: Session state.
        db_session: Database session.

    Returns:
        True if executed successfully.
    """
    if draft.entity_type == "commitment":
        try:
            persistence = PersistenceService(db_session)
            commitment = persistence.save_commitment(draft.data)
            db_session.commit()
        except Exception as e:  # noqa: BLE001 - catch-all for database errors
            console.print(f"[red]Error creating commitment: {e}[/red]")
            return True
        else:
            console.print(
                f"[green]Created commitment #{str(commitment.id)[:6]}: "
                f"{commitment.deliverable}[/green]"
            )
            session.clear_pending_draft()
            return True

    console.print(f"[yellow]Unknown draft type: {draft.entity_type}[/yellow]")
    session.clear_pending_draft()
    return True


def _handle_help() -> None:
    """Display help message."""
    console.print(
        """[bold]Available Commands:[/bold]

[cyan]/help[/cyan]                    - Show this help message
[cyan]/list[/cyan]                    - List commitments (default)
[cyan]/list commitments[/cyan]        - List all commitments
[cyan]/list goals[/cyan]              - List all goals
[cyan]/list visions[/cyan]            - List all visions
[cyan]/commit "..."[/cyan]            - Create a new commitment
[cyan]/review[/cyan]                  - Review visions due for quarterly review
[cyan]/complete[/cyan]                - Mark an item as complete (coming soon)

[bold]Examples:[/bold]
  /commit "send report to Sarah by Friday"
  /list goals

[dim]Or just type naturally - I understand plain English![/dim]
"""
    )


def _handle_review(session: Session, db_session: DBSession) -> None:
    """Handle /review command - review visions due for quarterly review.

    Args:
        session: REPL session state.
        db_session: Database session.
    """
    try:
        visions_due = get_visions_due_for_review(db_session)
    except (OSError, SQLAlchemyError) as e:
        logger.warning(f"Failed to get visions due for review: {e}")
        console.print("[red]Error loading visions. Please try again.[/red]")
        return

    if not visions_due:
        console.print("[dim]No visions are due for review.[/dim]")
        return

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


def _handle_list(args: str, db_session: DBSession) -> None:
    """Handle /list command.

    Args:
        args: Optional entity type to list.
        db_session: Database session.
    """
    entity_type = args.lower().strip() if args else "commitments"

    if entity_type in ("commitment", "commitments"):
        _list_commitments(db_session)
    elif entity_type in ("goal", "goals"):
        _list_goals(db_session)
    elif entity_type in ("vision", "visions"):
        _list_visions(db_session)
    else:
        console.print(f"[yellow]Unknown entity type: {entity_type}[/yellow]")
        console.print("[dim]Try: /list commitments, /list goals, or /list visions[/dim]")


def _list_commitments(db_session: DBSession) -> None:
    """List all commitments."""
    # Get active commitments (not completed or abandoned)
    active_statuses = [
        CommitmentStatus.PENDING,
        CommitmentStatus.IN_PROGRESS,
        CommitmentStatus.AT_RISK,
    ]
    statement = select(Commitment).where(Commitment.status.in_(active_statuses))
    commitments = list(db_session.exec(statement).all())

    if not commitments:
        console.print(format_empty_list("commitment"))
        return

    table = format_commitment_list(commitments)
    console.print(table)
    console.print(f"[dim]{len(commitments)} active commitment(s)[/dim]")


def _list_goals(db_session: DBSession) -> None:
    """List all goals."""
    goals = NavigationService.get_goals_list(db_session)

    if not goals:
        console.print(format_empty_list("goal"))
        return

    table = Table(title="Goals")
    table.add_column("ID", style="dim", width=6)
    table.add_column("Title", width=30)
    table.add_column("Status", width=12)

    for g in goals:
        table.add_row(
            g["id"][:6],
            g["title"][:30] if g["title"] else "N/A",
            g["status"],
        )

    console.print(table)
    console.print(f"[dim]{len(goals)} goal(s)[/dim]")


def _list_visions(db_session: DBSession) -> None:
    """List all visions."""
    visions = NavigationService.get_visions_list(db_session)

    if not visions:
        console.print(format_empty_list("vision"))
        return

    table = Table(title="Visions")
    table.add_column("ID", style="dim", width=6)
    table.add_column("Title", width=30)
    table.add_column("Timeframe", width=15)
    table.add_column("Status", width=12)

    for v in visions:
        table.add_row(
            v["id"][:6],
            v["title"][:30] if v["title"] else "N/A",
            v.get("timeframe", "N/A") or "N/A",
            v["status"],
        )

    console.print(table)
    console.print(f"[dim]{len(visions)} vision(s)[/dim]")


async def _process_user_input(
    user_input: str,
    session: Session,
    db_session: DBSession,
    agent: Agent[JDODependencies, str],
    deps: JDODependencies,
) -> bool:
    """Process a single user input.

    Args:
        user_input: The user's input text.
        session: Current session state.
        db_session: Database session.
        agent: The PydanticAI agent.
        deps: Agent dependencies.

    Returns:
        True to continue the loop, False to exit.
    """
    # Handle exit commands
    if user_input.lower() in ("exit", "quit"):
        console.print(GOODBYE_MESSAGE)
        return False

    # Handle slash commands (bypass AI for queries)
    if user_input.startswith("/"):
        await handle_slash_command(user_input, session, db_session)
        return True

    # Check for pending confirmation
    if session.has_pending_draft and _handle_confirmation(user_input, session, db_session):
        return True

    # Add user message to history
    session.add_user_message(user_input)

    # Process through AI
    response = await process_ai_input(user_input, agent, deps, session)

    # Add assistant response to history
    if response:
        session.add_assistant_message(response)

    return True


async def repl_loop() -> None:
    """Main REPL loop.

    Handles user input, routes to AI or slash commands, and manages session state.
    """
    # Initialize database
    create_db_and_tables()

    # Check for AI credentials
    if not check_credentials():
        console.print(NO_CREDENTIALS_MESSAGE)
        return

    # Create AI agent and dependencies
    agent = create_agent()
    with get_session() as db_session:
        deps = JDODependencies(session=db_session)
        session = Session()

        # Create prompt session with history
        prompt_session: PromptSession[str] = PromptSession(
            history=InMemoryHistory(),
            message="> ",
        )

        # Show startup guidance (first-run, at-risk, triage, vision review reminders)
        _show_startup_guidance(db_session, session)

        while True:
            try:
                # Get user input
                user_input = await prompt_session.prompt_async()

                # Handle empty/whitespace input
                if not user_input or not user_input.strip():
                    continue

                user_input = user_input.strip()

                # Process input and check if we should continue
                if not await _process_user_input(user_input, session, db_session, agent, deps):
                    break

            except KeyboardInterrupt:
                # Ctrl+C cancels current input, doesn't exit
                console.print("\n[dim]Input cancelled.[/dim]")
                continue
            except EOFError:
                # Ctrl+D exits
                console.print(GOODBYE_MESSAGE)
                break


def run_repl() -> None:
    """Run the REPL loop.

    Entry point for the REPL, handles async execution.
    """
    try:
        asyncio.run(repl_loop())
    except KeyboardInterrupt:
        # Handle Ctrl+C during startup
        console.print("\n[dim]Interrupted.[/dim]")
        sys.exit(0)
