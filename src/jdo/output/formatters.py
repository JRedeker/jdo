"""Rich output formatters for entities and messages.

Provides consistent formatting for commitments, goals, tasks, and other entities.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from jdo.models.commitment import Commitment, CommitmentStatus

# Shared console instance
console = Console()

# Status colors for commitments
STATUS_COLORS: dict[str, str] = {
    "pending": "default",
    "in_progress": "blue",
    "completed": "green",
    "at_risk": "yellow",
    "abandoned": "red",
}


def get_status_color(status: str | CommitmentStatus) -> str:
    """Get the color for a status value.

    Args:
        status: The status string or enum value.

    Returns:
        The Rich color name.
    """
    status_str = status.value if hasattr(status, "value") else str(status)
    return STATUS_COLORS.get(status_str.lower(), "default")


def format_date(d: date | datetime | None) -> str:
    """Format a date for display.

    Args:
        d: The date to format.

    Returns:
        Formatted date string or "N/A".
    """
    if d is None:
        return "N/A"
    if isinstance(d, datetime):
        return d.strftime("%Y-%m-%d %H:%M")
    return d.strftime("%Y-%m-%d")


def format_commitment_list(commitments: list[Commitment]) -> Table:
    """Format a list of commitments as a Rich table.

    Args:
        commitments: List of commitment objects.

    Returns:
        Rich Table ready for display.
    """
    table = Table(title="Commitments")
    table.add_column("ID", style="dim", width=6)
    table.add_column("Deliverable", width=30)
    table.add_column("Stakeholder", width=15)
    table.add_column("Due", width=12)
    table.add_column("Status", width=12)

    for c in commitments:
        status_color = get_status_color(c.status)
        status_text = Text(c.status.value if hasattr(c.status, "value") else str(c.status))
        if status_color != "default":
            status_text.stylize(status_color)

        # Highlight overdue items
        due_text = format_date(c.due_date)
        today = datetime.now(tz=UTC).date()
        if c.due_date and c.due_date < today:
            due_text = f"[red]{due_text}[/red]"

        table.add_row(
            str(c.id)[:6] if c.id else "N/A",
            c.deliverable[:30] if c.deliverable else "N/A",
            c.stakeholder.name if c.stakeholder else "N/A",
            due_text,
            status_text,
        )

    return table


def format_commitment_detail(commitment: Commitment) -> Panel:
    """Format a single commitment for detailed view.

    Args:
        commitment: The commitment to display.

    Returns:
        Rich Panel with commitment details.
    """
    status_color = get_status_color(commitment.status)
    status_value = (
        commitment.status.value if hasattr(commitment.status, "value") else str(commitment.status)
    )

    content = Text()
    content.append("Deliverable: ", style="bold")
    content.append(f"{commitment.deliverable or 'N/A'}\n")
    content.append("Stakeholder: ", style="bold")
    content.append(f"{commitment.stakeholder.name if commitment.stakeholder else 'N/A'}\n")
    content.append("Due Date: ", style="bold")
    content.append(f"{format_date(commitment.due_date)}\n")
    content.append("Status: ", style="bold")
    content.append(status_value, style=status_color)

    if commitment.goal:
        content.append("\nGoal: ", style="bold")
        content.append(commitment.goal.title or "N/A")

    return Panel(
        content, title=f"Commitment #{str(commitment.id)[:6] if commitment.id else 'Draft'}"
    )


def format_success(message: str) -> None:
    """Print a success message.

    Args:
        message: The message to display.
    """
    console.print(f"[green]{message}[/green]")


def format_error(message: str) -> None:
    """Print an error message.

    Args:
        message: The message to display.
    """
    console.print(f"[red]{message}[/red]")


def format_empty_list(entity_type: str) -> str:
    """Get the empty list message for an entity type.

    Args:
        entity_type: The type of entity (e.g., "commitment", "goal").

    Returns:
        The empty list message.
    """
    messages = {
        "commitment": "No commitments yet. Tell me what you need to do.",
        "goal": "No goals yet. What would you like to achieve?",
        "task": "No tasks yet. Tasks break down commitments into actionable steps.",
        "vision": "No visions yet. What future do you envision?",
        "milestone": "No milestones yet. Milestones help break goals into achievable chunks.",
    }
    return messages.get(entity_type.lower(), f"No {entity_type}s found.")


def format_commitment_proposal(
    deliverable: str,
    stakeholder: str,
    due_date: date | None = None,
    due_time: str | None = None,
    *,
    goal_title: str | None = None,
) -> Panel:
    """Format a commitment proposal for confirmation.

    Args:
        deliverable: The commitment deliverable.
        stakeholder: The stakeholder name.
        due_date: The due date for the commitment.
        due_time: Optional due time string.
        goal_title: Optional goal title to link to.

    Returns:
        Rich Panel with proposal details and confirmation prompt.
    """
    content = Text()
    content.append("Deliverable: ", style="bold")
    content.append(f"{deliverable}\n")
    content.append("Stakeholder: ", style="bold")
    content.append(f"{stakeholder}\n")
    content.append("Due Date: ", style="bold")
    content.append(f"{format_date(due_date)}")
    if due_time:
        content.append(f" at {due_time}")
    content.append("\n")

    if goal_title:
        content.append("Linked Goal: ", style="bold")
        content.append(f"{goal_title}\n")

    content.append("\n")
    content.append("Does this look right?", style="dim italic")
    content.append(" (yes/no/refine)", style="dim")

    return Panel(content, title="[cyan]New Commitment[/cyan]", border_style="cyan")


def format_commitment_list_plain(commitments: list[dict]) -> str:
    """Format a list of commitment dicts as plain text for AI tools.

    This formatter is for AI tool output that doesn't need Rich rendering.

    Args:
        commitments: List of commitment dictionaries with id, deliverable, etc.

    Returns:
        Plain text representation.
    """
    if not commitments:
        return format_empty_list("commitment")

    lines = ["Current Commitments:", ""]
    for c in commitments:
        status = c.get("status", "unknown")
        due = c.get("due_date", "N/A")
        lines.append(f"- {c.get('deliverable', 'N/A')}")
        lines.append(f"  Stakeholder: {c.get('stakeholder_name', 'N/A')}")
        lines.append(f"  Due: {due} | Status: {status}")
        lines.append("")

    return "\n".join(lines)


def format_overdue_commitments_plain(commitments: list[dict]) -> str:
    """Format a list of overdue commitment dicts as plain text.

    Args:
        commitments: List of overdue commitment dictionaries.

    Returns:
        Plain text representation with days overdue emphasized.
    """
    if not commitments:
        return "No overdue commitments found. Great job staying on track!"

    lines = ["OVERDUE Commitments:", ""]
    for c in commitments:
        days = c.get("days_overdue", 0)
        lines.append(f"- {c.get('deliverable', 'N/A')} ({days} days overdue)")
        lines.append(f"  Stakeholder: {c.get('stakeholder_name', 'N/A')}")
        lines.append(
            f"  Was due: {c.get('due_date', 'N/A')} | Status: {c.get('status', 'unknown')}"
        )
        lines.append("")

    return "\n".join(lines)


def format_visions_plain(visions: list[dict]) -> str:
    """Format a list of vision dicts as plain text.

    Args:
        visions: List of vision dictionaries.

    Returns:
        Plain text representation.
    """
    if not visions:
        return format_empty_list("vision")

    lines = ["Visions:", ""]
    for v in visions:
        lines.append(f"- {v.get('title', 'N/A')}")
        if v.get("timeframe"):
            lines.append(f"  Timeframe: {v['timeframe']}")
        if v.get("narrative"):
            lines.append(f"  {v['narrative'][:100]}...")
        if v.get("days_overdue"):
            lines.append(f"  Review overdue: {v['days_overdue']} days")
        lines.append("")

    return "\n".join(lines)


def format_milestones_plain(milestones: list[dict]) -> str:
    """Format a list of milestone dicts as plain text.

    Args:
        milestones: List of milestone dictionaries.

    Returns:
        Plain text representation.
    """
    if not milestones:
        return format_empty_list("milestone")

    lines = ["Milestones:", ""]
    for m in milestones:
        lines.append(f"- {m.get('title', 'N/A')}")
        lines.append(
            f"  Target: {m.get('target_date', 'N/A')} | Status: {m.get('status', 'unknown')}"
        )
        if m.get("description"):
            lines.append(f"  {m['description'][:80]}...")
        lines.append("")

    return "\n".join(lines)
