"""Rich output formatters for Goals.

Provides consistent formatting for goal lists, details, and proposals.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from jdo.output.formatters import format_date, format_empty_list

if TYPE_CHECKING:
    from jdo.models.goal import Goal, GoalStatus

# Status colors for goals
GOAL_STATUS_COLORS: dict[str, str] = {
    "active": "green",
    "on_hold": "yellow",
    "achieved": "cyan",
    "abandoned": "red",
}


def get_goal_status_color(status: str | GoalStatus) -> str:
    """Get the color for a goal status value.

    Args:
        status: The status string or enum value.

    Returns:
        The Rich color name.
    """
    status_str = status.value if hasattr(status, "value") else str(status)
    return GOAL_STATUS_COLORS.get(status_str.lower(), "default")


def format_goal_list(goals: list[Goal]) -> Table:
    """Format a list of goals as a Rich table.

    Args:
        goals: List of goal objects.

    Returns:
        Rich Table ready for display.
    """
    table = Table(title="Goals")
    table.add_column("ID", style="dim", width=6)
    table.add_column("Title", width=30)
    table.add_column("Status", width=12)
    table.add_column("Vision", width=15)

    for g in goals:
        status_color = get_goal_status_color(g.status)
        status_text = Text(g.status.value if hasattr(g.status, "value") else str(g.status))
        if status_color != "default":
            status_text.stylize(status_color)

        # Get vision title if linked
        vision_title = "N/A"
        if hasattr(g, "vision") and g.vision:
            vision_title = g.vision.title[:15] if g.vision.title else "N/A"

        table.add_row(
            str(g.id)[:6] if g.id else "N/A",
            g.title[:30] if g.title else "N/A",
            status_text,
            vision_title,
        )

    return table


def format_goal_detail(goal: Goal) -> Panel:
    """Format a single goal for detailed view.

    Args:
        goal: The goal to display.

    Returns:
        Rich Panel with goal details.
    """
    status_color = get_goal_status_color(goal.status)
    status_value = goal.status.value if hasattr(goal.status, "value") else str(goal.status)

    content = Text()
    content.append("Title: ", style="bold")
    content.append(f"{goal.title or 'N/A'}\n")
    content.append("Problem: ", style="bold")
    content.append(f"{goal.problem_statement or 'N/A'}\n")
    content.append("Solution Vision: ", style="bold")
    content.append(f"{goal.solution_vision or 'N/A'}\n")
    content.append("Status: ", style="bold")
    content.append(status_value, style=status_color)

    if goal.motivation:
        content.append("\nMotivation: ", style="bold")
        content.append(goal.motivation)

    if goal.next_review_date:
        content.append("\nNext Review: ", style="bold")
        content.append(format_date(goal.next_review_date))

    return Panel(content, title=f"Goal #{str(goal.id)[:6] if goal.id else 'Draft'}")


def format_goal_proposal(
    title: str,
    problem_statement: str,
    solution_vision: str,
    *,
    motivation: str | None = None,
    vision_title: str | None = None,
) -> Panel:
    """Format a goal proposal for confirmation.

    Args:
        title: The goal title.
        problem_statement: What problem this goal solves.
        solution_vision: What success looks like.
        motivation: Why this matters (optional).
        vision_title: Title of linked vision (optional).

    Returns:
        Rich Panel with proposal details and confirmation prompt.
    """
    content = Text()
    content.append("Title: ", style="bold")
    content.append(f"{title}\n")
    content.append("Problem: ", style="bold")
    content.append(f"{problem_statement}\n")
    content.append("Solution: ", style="bold")
    content.append(f"{solution_vision}\n")

    if motivation:
        content.append("Motivation: ", style="bold")
        content.append(f"{motivation}\n")

    if vision_title:
        content.append("Linked Vision: ", style="bold")
        content.append(f"{vision_title}\n")

    content.append("\n")
    content.append("Does this look right?", style="dim italic")
    content.append(" (yes/no/refine)", style="dim")

    return Panel(content, title="[cyan]New Goal[/cyan]", border_style="cyan")


def format_goal_list_plain(goals: list[dict]) -> str:
    """Format a list of goal dicts as plain text for AI tools.

    Args:
        goals: List of goal dictionaries.

    Returns:
        Plain text representation.
    """
    if not goals:
        return format_empty_list("goal")

    lines = ["Goals:", ""]
    for g in goals:
        status = g.get("status", "unknown")
        lines.append(f"- {g.get('title', 'N/A')}")
        lines.append(f"  Problem: {g.get('problem_statement', 'N/A')[:60]}...")
        lines.append(f"  Status: {status}")
        lines.append("")

    return "\n".join(lines)
