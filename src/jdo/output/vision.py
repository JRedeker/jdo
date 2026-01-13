"""Rich output formatters for Visions.

Provides consistent formatting for vision lists, details, and proposals.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from jdo.output.formatters import format_date, format_empty_list

if TYPE_CHECKING:
    from jdo.models.vision import Vision, VisionStatus

# Status colors for visions
VISION_STATUS_COLORS: dict[str, str] = {
    "active": "green",
    "achieved": "cyan",
    "evolved": "blue",
    "abandoned": "red",
}


def get_vision_status_color(status: str | VisionStatus) -> str:
    """Get the color for a vision status value.

    Args:
        status: The status string or enum value.

    Returns:
        The Rich color name.
    """
    status_str = status.value if hasattr(status, "value") else str(status)
    return VISION_STATUS_COLORS.get(status_str.lower(), "default")


def format_vision_list(visions: list[Vision]) -> Table:
    """Format a list of visions as a Rich table.

    Args:
        visions: List of vision objects.

    Returns:
        Rich Table ready for display.
    """
    table = Table(title="Visions")
    table.add_column("ID", style="dim", width=6)
    table.add_column("Title", width=30)
    table.add_column("Timeframe", width=12)
    table.add_column("Status", width=12)
    table.add_column("Review Due", width=12)

    for v in visions:
        status_color = get_vision_status_color(v.status)
        status_text = Text(v.status.value if hasattr(v.status, "value") else str(v.status))
        if status_color != "default":
            status_text.stylize(status_color)

        # Format review date with overdue highlighting
        review_text = format_date(v.next_review_date) if v.next_review_date else "N/A"

        table.add_row(
            str(v.id)[:6] if v.id else "N/A",
            v.title[:30] if v.title else "N/A",
            v.timeframe[:12] if v.timeframe else "N/A",
            status_text,
            review_text,
        )

    return table


def format_vision_detail(vision: Vision) -> Panel:
    """Format a single vision for detailed view.

    Args:
        vision: The vision to display.

    Returns:
        Rich Panel with vision details.
    """
    status_color = get_vision_status_color(vision.status)
    status_value = vision.status.value if hasattr(vision.status, "value") else str(vision.status)

    content = Text()
    content.append("Title: ", style="bold")
    content.append(f"{vision.title or 'N/A'}\n")
    content.append("Timeframe: ", style="bold")
    content.append(f"{vision.timeframe or 'N/A'}\n")
    content.append("Status: ", style="bold")
    content.append(status_value, style=status_color)
    content.append("\n\n")

    content.append("Narrative:\n", style="bold")
    content.append(f"{vision.narrative or 'N/A'}\n")

    if vision.why_it_matters:
        content.append("\nWhy It Matters:\n", style="bold")
        content.append(vision.why_it_matters)

    if vision.metrics:
        content.append("\n\nMetrics:\n", style="bold")
        for metric in vision.metrics:
            content.append(f"  - {metric}\n")

    if vision.next_review_date:
        content.append("\nNext Review: ", style="bold")
        content.append(format_date(vision.next_review_date))

    return Panel(content, title=f"Vision #{str(vision.id)[:6] if vision.id else 'Draft'}")


def format_vision_proposal(
    title: str,
    narrative: str,
    timeframe: str | None = None,
    *,
    metrics: list[str] | None = None,
    why_it_matters: str | None = None,
) -> Panel:
    """Format a vision proposal for confirmation.

    Args:
        title: The vision title.
        narrative: Vivid description of what success looks like.
        timeframe: When this should be achieved (optional).
        metrics: Measurable indicators of success (optional).
        why_it_matters: Why this vision matters (optional).

    Returns:
        Rich Panel with proposal details and confirmation prompt.
    """
    content = Text()
    content.append("Title: ", style="bold")
    content.append(f"{title}\n")

    if timeframe:
        content.append("Timeframe: ", style="bold")
        content.append(f"{timeframe}\n")

    content.append("\nNarrative:\n", style="bold")
    content.append(f"{narrative}\n")

    if why_it_matters:
        content.append("\nWhy It Matters:\n", style="bold")
        content.append(f"{why_it_matters}\n")

    if metrics:
        content.append("\nSuccess Metrics:\n", style="bold")
        for metric in metrics:
            content.append(f"  - {metric}\n")

    content.append("\n")
    content.append("Does this look right?", style="dim italic")
    content.append(" (yes/no/refine)", style="dim")

    return Panel(content, title="[cyan]New Vision[/cyan]", border_style="cyan")


def format_vision_list_plain(visions: list[dict]) -> str:
    """Format a list of vision dicts as plain text for AI tools.

    Args:
        visions: List of vision dictionaries.

    Returns:
        Plain text representation.
    """
    if not visions:
        return format_empty_list("vision")

    lines = ["Visions:", ""]
    for v in visions:
        status = v.get("status", "unknown")
        lines.append(f"- {v.get('title', 'N/A')}")
        if v.get("timeframe"):
            lines.append(f"  Timeframe: {v['timeframe']}")
        if v.get("narrative"):
            lines.append(f"  {v['narrative'][:80]}...")
        lines.append(f"  Status: {status}")
        if v.get("days_overdue"):
            lines.append(f"  Review overdue: {v['days_overdue']} days")
        lines.append("")

    return "\n".join(lines)
