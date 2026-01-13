"""Dashboard panel formatters for REPL.

Provides multi-panel dashboard display with commitments, goals, and status bar.
Uses Rich Table.grid() + Panel for automatic column alignment.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table

if TYPE_CHECKING:
    pass

# Panel dimensions
DASHBOARD_WIDTH = 100

# Maximum items to display
MAX_COMMITMENTS = 5
MAX_GOALS = 3

# Progress bar configuration
PROGRESS_BAR_WIDTH = 20

# Progress bar color thresholds
PROGRESS_HIGH_THRESHOLD = 0.8  # >= 80% is green
PROGRESS_MEDIUM_THRESHOLD = 0.5  # >= 50% is yellow, < 50% is red

# Display level thresholds
COMPACT_COMMITMENT_THRESHOLD = 2  # <= 2 commitments uses compact display


class DisplayLevel(Enum):
    """Dashboard display density levels."""

    MINIMAL = "minimal"  # Status bar only
    COMPACT = "compact"  # Commitments + status bar (no goals)
    STANDARD = "standard"  # Commitments + status bar
    FULL = "full"  # All three panels


@dataclass
class DashboardCommitment:
    """Commitment data for dashboard display."""

    deliverable: str
    stakeholder: str
    due_display: str  # "Today 5pm", "Tomorrow", "OVERDUE (2d)"
    status: str  # "overdue", "at_risk", "in_progress", "pending"
    is_overdue: bool = False


@dataclass
class DashboardGoal:
    """Goal data for dashboard display."""

    title: str
    progress_percent: float  # 0.0 to 1.0
    progress_text: str  # "3/4 done", "review due"
    needs_review: bool = False


@dataclass
class DashboardIntegrity:
    """Integrity metrics for status bar."""

    grade: str  # "A-"
    score: int  # 91
    trend: str  # "up", "down", "stable"
    streak_weeks: int  # 3


@dataclass
class DashboardData:
    """Complete dashboard data."""

    commitments: list[DashboardCommitment]
    goals: list[DashboardGoal]
    integrity: DashboardIntegrity | None
    triage_count: int


# Status icons (Unicode circles for consistent width)
STATUS_ICONS = {
    "overdue": "[red]●[/]",
    "at_risk": "[yellow]●[/]",
    "in_progress": "[blue]●[/]",
    "completed": "[green]●[/]",
    "pending": "[dim]○[/]",
}


def format_progress_bar(percent: float, width: int = PROGRESS_BAR_WIDTH) -> str:
    """Create a colored progress bar.

    Args:
        percent: Progress from 0.0 to 1.0.
        width: Total bar width in characters.

    Returns:
        Rich-styled progress bar string.
    """
    # Clamp percent to valid range
    percent = max(0.0, min(1.0, percent))

    filled = int(percent * width)
    empty = width - filled

    # Color based on progress
    if percent >= PROGRESS_HIGH_THRESHOLD:
        color = "green"
    elif percent >= PROGRESS_MEDIUM_THRESHOLD:
        color = "yellow"
    else:
        color = "red"

    return f"[{color}]{'█' * filled}[/][dim]{'░' * empty}[/]"


def format_commitments_panel(
    commitments: list[DashboardCommitment],
    active_count: int | None = None,
    at_risk_count: int | None = None,
) -> Panel:
    """Format commitments using Table.grid for automatic alignment.

    Args:
        commitments: List of commitment data for display.
        active_count: Total active commitments (for title).
        at_risk_count: Number at-risk (for title).

    Returns:
        Rich Panel containing formatted commitments.
    """
    # Grid handles column alignment automatically
    grid = Table.grid(padding=(0, 2), expand=True)
    grid.add_column("icon", width=1)
    grid.add_column("deliverable", ratio=2)
    grid.add_column("stakeholder", width=18)
    grid.add_column("due", width=18, justify="right")

    for c in commitments:
        icon = STATUS_ICONS.get(c.status, STATUS_ICONS["pending"])
        due_style = f"[red]{c.due_display}[/]" if c.is_overdue else c.due_display

        grid.add_row(icon, c.deliverable, c.stakeholder, due_style)

    # Build title
    if active_count is not None:
        at_risk_part = f", {at_risk_count} at-risk" if at_risk_count else ""
        title = f"[bold]📋 Commitments ({active_count} active{at_risk_part})[/]"
    else:
        title = "[bold]📋 Commitments[/]"

    return Panel(
        grid,
        title=title,
        title_align="left",
        box=box.ROUNDED,
        width=DASHBOARD_WIDTH,
        padding=(1, 2),
    )


def format_goals_panel(
    goals: list[DashboardGoal],
    active_count: int | None = None,
) -> Panel:
    """Format goals with progress bars using Table.grid.

    Args:
        goals: List of goal data for display.
        active_count: Total active goals (for title).

    Returns:
        Rich Panel containing formatted goals.
    """
    grid = Table.grid(padding=(0, 2), expand=True)
    grid.add_column("title", ratio=2)
    grid.add_column("progress", width=PROGRESS_BAR_WIDTH)
    grid.add_column("percent", width=6, justify="right")
    grid.add_column("status", width=12, justify="right")

    for g in goals:
        bar = format_progress_bar(g.progress_percent, width=PROGRESS_BAR_WIDTH)
        percent = f"{int(g.progress_percent * 100)}%"

        # Style status text
        status_text = g.progress_text
        if g.needs_review:
            status_text = f"[yellow]{status_text} ⚠[/]"

        grid.add_row(g.title, bar, percent, status_text)

    # Build title
    if active_count is not None:
        title = f"[bold]🎯 Goals ({active_count} active)[/]"
    else:
        title = "[bold]🎯 Goals[/]"

    return Panel(
        grid,
        title=title,
        title_align="left",
        box=box.ROUNDED,
        width=DASHBOARD_WIDTH,
        padding=(1, 2),
    )


def format_status_bar(
    integrity: DashboardIntegrity | None,
    triage_count: int,
) -> Panel:
    """Format status bar with 3 centered sections.

    Args:
        integrity: Integrity metrics (grade, score, trend, streak).
        triage_count: Number of items in triage queue.

    Returns:
        Rich Panel containing status bar.
    """
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="center", ratio=1)

    if integrity:
        # Integrity with trend arrow
        trend_display = {
            "up": "[green]↑[/]",
            "down": "[red]↓[/]",
            "stable": "[dim]→[/]",
        }.get(integrity.trend, "[dim]→[/]")

        grade_color = {
            "A": "green",
            "B": "blue",
            "C": "yellow",
        }.get(integrity.grade[0] if integrity.grade else "", "red")

        integrity_text = (
            f"📊 Integrity: [{grade_color}]{integrity.grade}[/] "
            f"({integrity.score}%) {trend_display}"
        )
        streak_text = f"🔥 Streak: {integrity.streak_weeks} weeks"
    else:
        integrity_text = "[dim]📊 Integrity: --[/]"
        streak_text = "[dim]🔥 Streak: --[/]"

    triage_text = f"📥 Triage: {triage_count}"

    grid.add_row(integrity_text, streak_text, triage_text)

    return Panel(
        grid,
        box=box.ROUNDED,
        width=DASHBOARD_WIDTH,
        padding=(0, 2),
    )


def _determine_display_level(data: DashboardData) -> DisplayLevel:
    """Determine appropriate display level based on data.

    Args:
        data: Dashboard data.

    Returns:
        Display level enum value.
    """
    commitment_count = len(data.commitments)
    goal_count = len(data.goals)

    if commitment_count == 0 and goal_count == 0:
        return DisplayLevel.MINIMAL
    if commitment_count <= COMPACT_COMMITMENT_THRESHOLD and goal_count == 0:
        return DisplayLevel.COMPACT
    if goal_count == 0:
        return DisplayLevel.STANDARD
    return DisplayLevel.FULL


def format_dashboard(data: DashboardData) -> Group | None:
    """Format complete dashboard from data.

    Determines display level and assembles appropriate panels.

    Args:
        data: Complete dashboard data.

    Returns:
        Rich Group of panels, or None if nothing to display.
    """
    level = _determine_display_level(data)

    if level == DisplayLevel.MINIMAL:
        # Status bar only (or nothing if no integrity data)
        if data.integrity or data.triage_count > 0:
            return Group(format_status_bar(data.integrity, data.triage_count))
        return None

    panels: list[Panel] = []

    # Commitments panel
    if data.commitments:
        at_risk_count = sum(1 for c in data.commitments if c.status in ("overdue", "at_risk"))
        panels.append(
            format_commitments_panel(
                data.commitments,
                active_count=len(data.commitments),
                at_risk_count=at_risk_count,
            )
        )

    # Goals panel (only in FULL mode)
    if level == DisplayLevel.FULL and data.goals:
        panels.append(
            format_goals_panel(
                data.goals,
                active_count=len(data.goals),
            )
        )

    # Status bar
    panels.append(format_status_bar(data.integrity, data.triage_count))

    return Group(*panels) if panels else None
