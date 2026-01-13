"""Rich output formatters for Milestones.

Provides consistent formatting for milestone lists, details, and proposals.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from jdo.output.formatters import format_date, format_empty_list

if TYPE_CHECKING:
    from jdo.models.milestone import Milestone, MilestoneStatus

# Status colors for milestones
MILESTONE_STATUS_COLORS: dict[str, str] = {
    "pending": "default",
    "in_progress": "blue",
    "completed": "green",
    "missed": "red",
}


def get_milestone_status_color(status: str | MilestoneStatus) -> str:
    """Get the color for a milestone status value.

    Args:
        status: The status string or enum value.

    Returns:
        The Rich color name.
    """
    status_str = status.value if hasattr(status, "value") else str(status)
    return MILESTONE_STATUS_COLORS.get(status_str.lower(), "default")


def format_milestone_list(milestones: list[Milestone]) -> Table:
    """Format a list of milestones as a Rich table.

    Args:
        milestones: List of milestone objects.

    Returns:
        Rich Table ready for display.
    """
    table = Table(title="Milestones", box=box.ROUNDED)
    table.add_column("ID", style="dim", width=6)
    table.add_column("Title", width=30)
    table.add_column("Target Date", width=12)
    table.add_column("Status", width=12)
    table.add_column("Goal", width=15)

    for m in milestones:
        status_color = get_milestone_status_color(m.status)
        status_text = Text(m.status.value if hasattr(m.status, "value") else str(m.status))
        if status_color != "default":
            status_text.stylize(status_color)

        # Get goal title if available
        goal_title = "N/A"
        if hasattr(m, "goal") and m.goal:
            goal_title = m.goal.title[:15] if m.goal.title else "N/A"

        table.add_row(
            str(m.id)[:6] if m.id else "N/A",
            m.title[:30] if m.title else "N/A",
            format_date(m.target_date),
            status_text,
            goal_title,
        )

    return table


def format_milestone_detail(milestone: Milestone) -> Panel:
    """Format a single milestone for detailed view.

    Args:
        milestone: The milestone to display.

    Returns:
        Rich Panel with milestone details.
    """
    status_color = get_milestone_status_color(milestone.status)
    status_value = (
        milestone.status.value if hasattr(milestone.status, "value") else str(milestone.status)
    )

    content = Text()
    content.append("Title: ", style="bold")
    content.append(f"{milestone.title or 'N/A'}\n")
    content.append("Target Date: ", style="bold")
    content.append(f"{format_date(milestone.target_date)}\n")
    content.append("Status: ", style="bold")
    content.append(status_value, style=status_color)

    if milestone.description:
        content.append("\n\nDescription:\n", style="bold")
        content.append(milestone.description)

    if hasattr(milestone, "goal") and milestone.goal:
        content.append("\n\nGoal: ", style="bold")
        content.append(milestone.goal.title or "N/A")

    if milestone.completed_at:
        content.append("\nCompleted: ", style="bold")
        content.append(format_date(milestone.completed_at))

    return Panel(content, title=f"Milestone #{str(milestone.id)[:6] if milestone.id else 'Draft'}")


def format_milestone_proposal(
    title: str,
    target_date: str,
    *,
    description: str | None = None,
    goal_title: str | None = None,
) -> Panel:
    """Format a milestone proposal for confirmation.

    Args:
        title: The milestone title.
        target_date: When this should be achieved.
        description: What this milestone represents (optional).
        goal_title: Title of parent goal (optional).

    Returns:
        Rich Panel with proposal details and confirmation prompt.
    """
    content = Text()
    content.append("Title: ", style="bold")
    content.append(f"{title}\n")
    content.append("Target Date: ", style="bold")
    content.append(f"{target_date}\n")

    if description:
        content.append("Description: ", style="bold")
        content.append(f"{description}\n")

    if goal_title:
        content.append("Goal: ", style="bold")
        content.append(f"{goal_title}\n")

    content.append("\n")
    content.append("Does this look right?", style="dim italic")
    content.append(" (yes/no/refine)", style="dim")

    return Panel(content, title="[cyan]New Milestone[/cyan]", border_style="cyan")


def format_milestone_list_plain(milestones: list[dict[str, Any]]) -> str:
    """Format a list of milestone dicts as plain text for AI tools.

    Args:
        milestones: List of milestone dictionaries.

    Returns:
        Plain text representation.
    """
    if not milestones:
        return format_empty_list("milestone")

    lines = ["Milestones:", ""]
    for m in milestones:
        status = m.get("status", "unknown")
        lines.append(f"- {m.get('title', 'N/A')}")
        lines.append(f"  Target: {m.get('target_date', 'N/A')} | Status: {status}")
        if m.get("description"):
            lines.append(f"  {m['description'][:60]}...")
        lines.append("")

    return "\n".join(lines)
