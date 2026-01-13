"""Rich output formatters for Tasks.

Provides consistent formatting for task lists, details, and proposals.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from jdo.output.formatters import format_empty_list

if TYPE_CHECKING:
    from jdo.models.task import Task, TaskStatus

# Status colors for tasks
TASK_STATUS_COLORS: dict[str, str] = {
    "pending": "default",
    "in_progress": "blue",
    "completed": "green",
    "skipped": "dim",
}


def get_task_status_color(status: str | TaskStatus) -> str:
    """Get the color for a task status value.

    Args:
        status: The status string or enum value.

    Returns:
        The Rich color name.
    """
    status_str = status.value if hasattr(status, "value") else str(status)
    return TASK_STATUS_COLORS.get(status_str.lower(), "default")


def format_task_list(tasks: list[Task]) -> Table:
    """Format a list of tasks as a Rich table.

    Args:
        tasks: List of task objects.

    Returns:
        Rich Table ready for display.
    """
    table = Table(title="Tasks", box=box.ROUNDED)
    table.add_column("ID", style="dim", width=6)
    table.add_column("Title", width=30)
    table.add_column("Status", width=12)
    table.add_column("Est. Hours", width=10)
    table.add_column("Commitment", width=15)

    for t in tasks:
        status_color = get_task_status_color(t.status)
        status_text = Text(t.status.value if hasattr(t.status, "value") else str(t.status))
        if status_color != "default":
            status_text.stylize(status_color)

        # Format estimated hours
        est_hours = f"{t.estimated_hours:.1f}h" if t.estimated_hours else "N/A"

        # Get commitment deliverable if available
        commitment_text = "N/A"
        if hasattr(t, "commitment") and t.commitment:
            commitment_text = t.commitment.deliverable[:15] if t.commitment.deliverable else "N/A"

        table.add_row(
            str(t.id)[:6] if t.id else "N/A",
            t.title[:30] if t.title else "N/A",
            status_text,
            est_hours,
            commitment_text,
        )

    return table


def format_task_detail(task: Task) -> Panel:
    """Format a single task for detailed view.

    Args:
        task: The task to display.

    Returns:
        Rich Panel with task details.
    """
    status_color = get_task_status_color(task.status)
    status_value = task.status.value if hasattr(task.status, "value") else str(task.status)

    content = Text()
    content.append("Title: ", style="bold")
    content.append(f"{task.title or 'N/A'}\n")
    content.append("Scope: ", style="bold")
    content.append(f"{task.scope or 'N/A'}\n")
    content.append("Status: ", style="bold")
    content.append(status_value, style=status_color)

    if task.estimated_hours:
        content.append("\nEstimated Hours: ", style="bold")
        content.append(f"{task.estimated_hours:.1f}h")

        if task.actual_hours_category:
            actual_value = (
                task.actual_hours_category.value
                if hasattr(task.actual_hours_category, "value")
                else str(task.actual_hours_category)
            )
            content.append(f" (Actual: {actual_value})")

    if task.estimation_confidence:
        conf_value = (
            task.estimation_confidence.value
            if hasattr(task.estimation_confidence, "value")
            else str(task.estimation_confidence)
        )
        content.append("\nConfidence: ", style="bold")
        content.append(conf_value)

    if hasattr(task, "commitment") and task.commitment:
        content.append("\n\nCommitment: ", style="bold")
        content.append(task.commitment.deliverable or "N/A")

    # Show subtasks if any
    if task.sub_tasks:
        content.append("\n\nSubtasks:\n", style="bold")
        for sub in task.sub_tasks:
            check = "[x]" if sub.get("completed", False) else "[ ]"
            content.append(f"  {check} {sub.get('description', 'N/A')}\n")

    return Panel(content, title=f"Task #{str(task.id)[:6] if task.id else 'Draft'}")


def format_task_proposal(
    title: str,
    scope: str,
    *,
    estimated_hours: float | None = None,
    commitment_deliverable: str | None = None,
) -> Panel:
    """Format a task proposal for confirmation.

    Args:
        title: The task title.
        scope: What specifically needs to be done.
        estimated_hours: Time estimate in hours (optional).
        commitment_deliverable: Parent commitment deliverable (optional).

    Returns:
        Rich Panel with proposal details and confirmation prompt.
    """
    content = Text()
    content.append("Title: ", style="bold")
    content.append(f"{title}\n")
    content.append("Scope: ", style="bold")
    content.append(f"{scope}\n")

    if estimated_hours:
        content.append("Estimated Hours: ", style="bold")
        content.append(f"{estimated_hours:.1f}h\n")

    if commitment_deliverable:
        content.append("Commitment: ", style="bold")
        content.append(f"{commitment_deliverable}\n")

    content.append("\n")
    content.append("Does this look right?", style="dim italic")
    content.append(" (yes/no/refine)", style="dim")

    return Panel(content, title="[cyan]New Task[/cyan]", border_style="cyan")


def format_task_list_plain(tasks: list[dict[str, Any]]) -> str:
    """Format a list of task dicts as plain text for AI tools.

    Args:
        tasks: List of task dictionaries.

    Returns:
        Plain text representation.
    """
    if not tasks:
        return format_empty_list("task")

    lines = ["Tasks:", ""]
    for t in tasks:
        status = t.get("status", "unknown")
        est = f"{t.get('estimated_hours', 0):.1f}h" if t.get("estimated_hours") else "N/A"
        lines.append(f"- {t.get('title', 'N/A')}")
        lines.append(f"  Scope: {t.get('scope', 'N/A')[:50]}...")
        lines.append(f"  Status: {status} | Est: {est}")
        lines.append("")

    return "\n".join(lines)
