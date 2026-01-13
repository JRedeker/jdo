"""Main REPL loop for conversational CLI.

Provides a prompt_toolkit-based REPL with streaming AI responses,
session state management, and hybrid input handling.
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Callable
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
from jdo.db.session import (
    get_dashboard_commitments,
    get_dashboard_goals,
    get_triage_count,
    get_visions_due_for_review,
)
from jdo.models.commitment import Commitment, CommitmentStatus
from jdo.models.goal import Goal
from jdo.models.vision import Vision
from jdo.output.dashboard import (
    DashboardCommitment,
    DashboardData,
    DashboardGoal,
    DashboardIntegrity,
    format_dashboard,
)
from jdo.output.formatters import (
    format_commitment_list,
    format_commitment_proposal,
    format_empty_list,
)
from jdo.repl.session import PendingDraft, Session
from jdo.utils.datetime import today_date, utc_now

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
[bold red]No AI API credentials configured.[/bold red]

To use JDO, configure your credentials with: [cyan]jdo auth[/cyan]

Or set the OPENAI_API_KEY or OPENROUTER_API_KEY environment variable.

See /help for more information.
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
    # Show animated thinking spinner
    status = console.status("[dim]Thinking...[/dim]", spinner="dots")
    status.start()

    response_text = ""
    first_chunk = True
    live = None

    try:
        async with asyncio.timeout(AI_STREAM_TIMEOUT_SECONDS):
            async for chunk in stream_response(
                agent,
                user_input,
                deps,
                message_history=session.message_history,
            ):
                if first_chunk:
                    # Stop spinner BEFORE starting Live (avoid nesting)
                    status.stop()
                    live = Live("", console=console, refresh_per_second=10, transient=False)
                    live.start()
                    first_chunk = False

                response_text += chunk
                # Render as Markdown during streaming
                try:
                    live.update(Markdown(response_text))
                except (ValueError, TypeError, AttributeError) as e:
                    logger.debug(f"Markdown rendering error, falling back to plain text: {e}")
                    live.update(Text(response_text))

        # Stop live display if it was started
        if live:
            live.stop()

    except TimeoutError:
        console.print("[yellow]The AI took too long to respond. Please try again.[/yellow]")
        return ""
    except (OSError, ConnectionError) as e:
        # Handle network-related errors specifically
        console.print(f"[red]Error communicating with AI: {e}[/red]")
        return ""
    finally:
        # Always ensure spinner is stopped
        if first_chunk:
            status.stop()
        if live:
            live.stop()

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
        _handle_complete(args, session, db_session)
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
    except ValueError as e:
        logger.warning("Commitment extraction failed: {}", e)
        console.print(f"[red]Could not extract commitment details: {e}[/red]")
        console.print("[dim]Try being more specific, e.g.: 'report to Sarah by Friday'[/dim]")
    except Exception as e:
        logger.error("Unexpected error during commitment extraction: {}", exc_info=e)
        console.print("[red]Could not extract commitment details. Please try again.[/red]")


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
        except (OSError, SQLAlchemyError) as e:
            logger.error(f"Failed to create commitment: {e}")
            console.print("[red]Error creating commitment. Please try again.[/red]")
            return True
        else:
            console.print(
                f"[green]Created commitment #{str(commitment.id)[:6]}: "
                f"{commitment.deliverable}[/green]"
            )
            # Update cached dashboard data after entity creation
            _update_dashboard_cache(session, db_session)
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
[cyan]/complete <id>[/cyan]           - Mark a commitment as complete
[cyan]/review[/cyan]                  - Review visions due for quarterly review

[bold]Examples:[/bold]
  /commit "send report to Sarah by Friday"
  /list goals
  /complete abc123

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


def _handle_complete(args: str, session: Session, db_session: DBSession) -> None:
    """Handle /complete command - mark a commitment as complete.

    Args:
        args: Optional commitment ID or partial match text.
        session: REPL session state.
        db_session: Database session.
    """
    if not args:
        console.print("[yellow]Usage: /complete <commitment_id>[/yellow]")
        console.print('[dim]Example: /complete 123abc or /complete "send report"[/dim]')
        console.print("[dim]Run /list to see active commitments.[/dim]")
        return

    # Get active commitments
    active_statuses = [
        CommitmentStatus.PENDING,
        CommitmentStatus.IN_PROGRESS,
        CommitmentStatus.AT_RISK,
    ]
    statement = select(Commitment).where(Commitment.status.in_(active_statuses))
    commitments = list(db_session.exec(statement).all())

    if not commitments:
        console.print("[dim]No active commitments to complete.[/dim]")
        return

    # Try to find matching commitment by ID
    target_commitment = None
    partial_id = args.strip().lower()

    for commitment in commitments:
        # Match by partial ID (first 6+ chars)
        commitment_id_str = str(commitment.id)[:6].lower()
        if commitment_id_str == partial_id[:6]:
            target_commitment = commitment
            break

        # Match by deliverable text (substring match, case-insensitive)
        if partial_id in commitment.deliverable.lower():
            target_commitment = commitment
            break

    if not target_commitment:
        console.print(f"[yellow]No commitment found matching '{args}'[/yellow]")
        console.print("[dim]Run /list to see active commitments.[/dim]")
        return

    # Mark as complete
    target_commitment.status = CommitmentStatus.COMPLETED
    target_commitment.completed_at = utc_now()
    db_session.add(target_commitment)
    db_session.commit()

    logger.info(
        f"Completed commitment: {target_commitment.deliverable} (id={target_commitment.id})"
    )

    console.print(f"[green]Completed commitment: {target_commitment.deliverable}[/green]")

    # Update cached dashboard data after entity completion
    _update_dashboard_cache(session, db_session)


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

    table = Table(title="Goals", box=box.ROUNDED)
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

    table = Table(title="Visions", box=box.ROUNDED)
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


def _get_active_commitment_count(db_session: DBSession) -> int:
    """Get count of active commitments for toolbar.

    Args:
        db_session: Database session.

    Returns:
        Count of active commitments.
    """
    active_statuses = [
        CommitmentStatus.PENDING,
        CommitmentStatus.IN_PROGRESS,
        CommitmentStatus.AT_RISK,
    ]
    statement = select(Commitment).where(Commitment.status.in_(active_statuses))
    return len(list(db_session.exec(statement).all()))


def _update_dashboard_cache(session: Session, db_session: DBSession) -> None:
    """Update session cache with current dashboard data.

    Args:
        session: REPL session state.
        db_session: Database session.
    """
    from jdo.repl.session import DashboardCacheUpdate  # noqa: PLC0415

    # Fetch dashboard data from database
    commitments = get_dashboard_commitments(db_session)
    goals = get_dashboard_goals(db_session)
    triage_count = get_triage_count(db_session)

    # Update session cache
    update = DashboardCacheUpdate(
        commitments=commitments,
        goals=goals,
        triage_count=triage_count,
        # Integrity data placeholder - implement when IntegrityService is ready
        integrity_grade="",
        integrity_score=0,
        integrity_trend="stable",
        streak_weeks=0,
    )
    session.update_dashboard_cache(update)


def _build_dashboard_data(session: Session) -> DashboardData:
    """Build dashboard data from session cache.

    Args:
        session: REPL session state with cached dashboard data.

    Returns:
        DashboardData ready for formatting.
    """
    # Convert cached dicts to dataclasses
    commitments = [
        DashboardCommitment(
            deliverable=c["deliverable"],
            stakeholder=c["stakeholder"],
            due_display=c["due_display"],
            status=c["status"],
            is_overdue=c.get("is_overdue", False),
        )
        for c in session.cached_dashboard_commitments
    ]

    goals = [
        DashboardGoal(
            title=g["title"],
            progress_percent=g["progress_percent"],
            progress_text=g["progress_text"],
            needs_review=g.get("needs_review", False),
        )
        for g in session.cached_dashboard_goals
    ]

    # Build integrity data if available
    integrity = None
    if session.cached_integrity_grade:
        integrity = DashboardIntegrity(
            grade=session.cached_integrity_grade,
            score=session.cached_integrity_score,
            trend=session.cached_integrity_trend,
            streak_weeks=session.cached_streak_weeks,
        )

    return DashboardData(
        commitments=commitments,
        goals=goals,
        integrity=integrity,
        triage_count=session.cached_triage_count,
    )


def _show_dashboard(session: Session) -> None:
    """Display dashboard panels using cached session data.

    Args:
        session: REPL session state with cached dashboard data.
    """
    data = _build_dashboard_data(session)
    dashboard = format_dashboard(data)
    if dashboard:
        console.print(dashboard)


def _initialize_agent() -> Agent[JDODependencies, str]:
    """Initialize database, check credentials, and create AI agent.

    Returns:
        The created AI agent.

    Raises:
        SystemExit: If credentials are not configured.
    """
    create_db_and_tables()

    if not check_credentials():
        console.print(NO_CREDENTIALS_MESSAGE)
        sys.exit(1)

    return create_agent()


def _setup_session_state(
    db_session: DBSession,
) -> tuple[Session, JDODependencies]:
    """Setup session state and dependencies.

    Args:
        db_session: Database session.

    Returns:
        Tuple of (session state, agent dependencies).
    """
    deps = JDODependencies(session=db_session)
    session = Session()

    # Initialize dashboard cache with full data
    _update_dashboard_cache(session, db_session)

    return session, deps


def _create_toolbar_callback(session: Session) -> Callable[[], str]:
    """Create toolbar text callback using cached session values.

    Args:
        session: Session state with cached counts.

    Returns:
        Function that generates toolbar text.
    """

    def get_toolbar_text() -> str:
        draft_indicator = " [draft]" if session.has_pending_draft else ""
        return (
            f" {session.cached_commitment_count} active | "
            f"{session.cached_triage_count} triage{draft_indicator}"
        )

    return get_toolbar_text


def _create_prompt_session(
    get_toolbar_text: Callable[[], str],
) -> PromptSession[str]:
    """Create prompt session with history, auto-completion, and toolbar.

    Args:
        get_toolbar_text: Callback function for toolbar text.

    Returns:
        Configured prompt session.
    """
    completer = WordCompleter(SLASH_COMMANDS, ignore_case=True)
    return PromptSession(
        history=InMemoryHistory(),
        message="> ",
        completer=completer,
        complete_while_typing=False,
        bottom_toolbar=get_toolbar_text,
        refresh_interval=1.0,
    )


async def _main_repl_loop(
    prompt_session: PromptSession[str],
    session: Session,
    db_session: DBSession,
    agent: Agent[JDODependencies, str],
    deps: JDODependencies,
) -> None:
    """Run the main REPL loop processing user input.

    Args:
        prompt_session: Prompt session for getting user input.
        session: Current session state.
        db_session: Database session.
        agent: The PydanticAI agent.
        deps: Agent dependencies.
    """
    # Show initial dashboard before first prompt
    _show_dashboard(session)

    while True:
        try:
            user_input = await prompt_session.prompt_async()

            if not user_input or not user_input.strip():
                continue

            user_input = user_input.strip()

            if not await _process_user_input(user_input, session, db_session, agent, deps):
                break

            # Show dashboard before next prompt
            _show_dashboard(session)

        except KeyboardInterrupt:
            console.print("\n[dim]Input cancelled.[/dim]")
            continue
        except EOFError:
            console.print(GOODBYE_MESSAGE)
            break


# Slash commands for auto-completion
SLASH_COMMANDS = [
    "/help",
    "/list",
    "/list commitments",
    "/list goals",
    "/list visions",
    "/commit",
    "/complete",
    "/review",
]


async def repl_loop() -> None:
    """Main REPL loop.

    Handles user input, routes to AI or slash commands, and manages session state.
    """
    agent = _initialize_agent()

    with get_session() as db_session:
        session, deps = _setup_session_state(db_session)

        get_toolbar_text = _create_toolbar_callback(session)
        prompt_session = _create_prompt_session(get_toolbar_text)

        _show_startup_guidance(db_session, session)

        await _main_repl_loop(prompt_session, session, db_session, agent, deps)


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
