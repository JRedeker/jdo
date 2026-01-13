"""Rich output formatters for Integrity Dashboard.

Provides formatting for integrity metrics, grade display, and trends.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.align import Align
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from jdo.integrity.service import AffectingCommitment
    from jdo.models.integrity_metrics import IntegrityMetrics, TrendDirection

# Thresholds for coloring metric percentages
THRESHOLD_GREEN = 90  # >= 90% is green
THRESHOLD_YELLOW = 70  # >= 70% is yellow, below is red
THRESHOLD_ESTIMATION_GREEN = 80  # Estimation accuracy thresholds
THRESHOLD_ESTIMATION_YELLOW = 60
THRESHOLD_STREAK_GREEN = 4  # >= 4 weeks shows green
MIN_TASKS_FOR_ESTIMATION = 5  # Minimum tasks to show estimation accuracy

# Grade colors based on letter grade
GRADE_COLORS: dict[str, str] = {
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

# Trend indicators with colors
TREND_STYLES: dict[str, tuple[str, str]] = {
    "up": ("↑", "green"),
    "down": ("↓", "red"),
    "stable": ("→", "dim"),
}


def get_grade_color(grade: str) -> str:
    """Get the color for a letter grade.

    Args:
        grade: The letter grade (e.g., "A+", "B-", "F").

    Returns:
        The Rich color name.
    """
    return GRADE_COLORS.get(grade, "default")


def format_trend(trend: TrendDirection | None) -> Text:
    """Format a trend indicator with color.

    Args:
        trend: The trend direction or None.

    Returns:
        Rich Text with colored trend indicator.
    """
    if trend is None:
        return Text("")

    trend_value = trend.value if hasattr(trend, "value") else str(trend)
    symbol, color = TREND_STYLES.get(trend_value, ("", "default"))
    return Text(f" {symbol}", style=color)


def format_grade(grade: str) -> Panel:
    """Format a letter grade as a large, centered display.

    Args:
        grade: The letter grade (e.g., "A+", "B-", "F").

    Returns:
        Rich Panel with large grade display.
    """
    color = get_grade_color(grade)
    grade_text = Text(grade, style=f"bold {color}")
    centered = Align.center(grade_text)

    return Panel(
        centered,
        title="Integrity Grade",
        border_style=color,
        padding=(1, 4),
    )


def format_metric_row(
    label: str,
    value: float,
    trend: TrendDirection | None = None,
    *,
    is_percentage: bool = True,
) -> Text:
    """Format a single metric row with label, value, and optional trend.

    Args:
        label: The metric label.
        value: The metric value (0.0-1.0 for percentages).
        trend: Optional trend direction.
        is_percentage: Whether to format as percentage.

    Returns:
        Rich Text with formatted metric.
    """
    result = Text()
    result.append(f"{label}: ", style="bold")

    if is_percentage:
        pct = value * 100
        # Color based on value
        if pct >= THRESHOLD_GREEN:
            color = "green"
        elif pct >= THRESHOLD_YELLOW:
            color = "yellow"
        else:
            color = "red"
        result.append(f"{pct:.0f}%", style=color)
    else:
        result.append(str(value))

    if trend is not None:
        result.append_text(format_trend(trend))

    return result


def format_metrics_table(metrics: IntegrityMetrics) -> Table:
    """Format integrity metrics as a table.

    Args:
        metrics: The IntegrityMetrics dataclass.

    Returns:
        Rich Table with metrics.
    """
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    table.add_column("Trend", justify="left", width=3)

    # On-time rate
    on_time_pct = metrics.on_time_rate * 100
    on_time_color = (
        "green"
        if on_time_pct >= THRESHOLD_GREEN
        else "yellow"
        if on_time_pct >= THRESHOLD_YELLOW
        else "red"
    )
    on_time_trend = format_trend(metrics.on_time_trend)
    table.add_row(
        "On-time delivery",
        Text(f"{on_time_pct:.0f}%", style=on_time_color),
        on_time_trend,
    )

    # Notification timeliness
    notif_pct = metrics.notification_timeliness * 100
    notif_color = (
        "green"
        if notif_pct >= THRESHOLD_GREEN
        else "yellow"
        if notif_pct >= THRESHOLD_YELLOW
        else "red"
    )
    notif_trend = format_trend(metrics.notification_trend)
    table.add_row(
        "Notification timeliness",
        Text(f"{notif_pct:.0f}%", style=notif_color),
        notif_trend,
    )

    # Cleanup completion
    cleanup_pct = metrics.cleanup_completion_rate * 100
    cleanup_color = (
        "green"
        if cleanup_pct >= THRESHOLD_GREEN
        else "yellow"
        if cleanup_pct >= THRESHOLD_YELLOW
        else "red"
    )
    cleanup_trend = format_trend(metrics.cleanup_trend)
    table.add_row(
        "Cleanup completion",
        Text(f"{cleanup_pct:.0f}%", style=cleanup_color),
        cleanup_trend,
    )

    # Estimation accuracy (only show if there's data)
    if metrics.tasks_with_estimates >= MIN_TASKS_FOR_ESTIMATION:
        est_pct = metrics.estimation_accuracy * 100
        est_color = (
            "green"
            if est_pct >= THRESHOLD_ESTIMATION_GREEN
            else "yellow"
            if est_pct >= THRESHOLD_ESTIMATION_YELLOW
            else "red"
        )
        table.add_row(
            "Estimation accuracy",
            Text(f"{est_pct:.0f}%", style=est_color),
            Text(""),
        )

    # Streak
    streak_color = "green" if metrics.current_streak_weeks >= THRESHOLD_STREAK_GREEN else "default"
    streak_text = (
        f"{metrics.current_streak_weeks} week{'s' if metrics.current_streak_weeks != 1 else ''}"
    )
    table.add_row(
        "Current streak",
        Text(streak_text, style=streak_color),
        Text(""),
    )

    return table


def format_integrity_dashboard(
    metrics: IntegrityMetrics,
    affecting: list[AffectingCommitment] | None = None,
) -> Panel:
    """Format the complete integrity dashboard.

    Args:
        metrics: The IntegrityMetrics dataclass.
        affecting: Optional list of commitments affecting the score.

    Returns:
        Rich Panel with grade, metrics, and optional affecting commitments.
    """
    # Build content as a group of renderables
    parts: list = []

    # Large grade display
    grade = metrics.letter_grade
    color = get_grade_color(grade)
    grade_text = Text()
    grade_text.append(grade, style=f"bold {color}")
    grade_text.append(f"  ({metrics.composite_score:.0f}/100)", style="dim")
    parts.append(Align.center(grade_text))
    parts.append(Text(""))  # Spacer

    # Metrics table
    parts.append(format_metrics_table(metrics))

    # Summary stats
    parts.append(Text(""))  # Spacer
    summary = Text()
    summary.append("Summary: ", style="bold")
    summary.append(f"{metrics.total_on_time}/{metrics.total_completed} on-time")
    if metrics.total_at_risk > 0:
        summary.append(f", {metrics.total_at_risk} at-risk")
    if metrics.total_abandoned > 0:
        summary.append(f", {metrics.total_abandoned} abandoned", style="red")
    parts.append(summary)

    # Affecting commitments (if any)
    if affecting:
        parts.append(Text(""))  # Spacer
        parts.append(Text("Recent issues:", style="bold yellow"))
        for ac in affecting[:3]:  # Show max 3
            issue_text = Text("  - ")
            issue_text.append(ac.commitment.deliverable[:40], style="default")
            issue_text.append(f" ({ac.reason})", style="dim")
            parts.append(issue_text)

    # Overall trend
    if metrics.overall_trend is not None:
        parts.append(Text(""))  # Spacer
        trend_text = Text()
        trend_text.append("Trend: ", style="bold")
        trend_value = (
            metrics.overall_trend.value
            if hasattr(metrics.overall_trend, "value")
            else str(metrics.overall_trend)
        )
        if trend_value == "up":
            trend_text.append("Improving ", style="green")
            trend_text.append("↑", style="green")
        elif trend_value == "down":
            trend_text.append("Declining ", style="red")
            trend_text.append("↓", style="red")
        else:
            trend_text.append("Stable ", style="dim")
            trend_text.append("→", style="dim")
        parts.append(trend_text)

    return Panel(
        Group(*parts),
        title="[bold]Integrity Dashboard[/bold]",
        border_style=color,
        padding=(1, 2),
    )


def format_integrity_plain(metrics: IntegrityMetrics) -> str:
    """Format integrity metrics as plain text for AI tools.

    Args:
        metrics: The IntegrityMetrics dataclass.

    Returns:
        Plain text representation.
    """
    lines = [
        "Integrity Score",
        "=" * 20,
        f"Grade: {metrics.letter_grade} ({metrics.composite_score:.0f}/100)",
        "",
        "Metrics:",
        f"  On-time delivery: {metrics.on_time_rate * 100:.0f}%",
        f"  Notification timeliness: {metrics.notification_timeliness * 100:.0f}%",
        f"  Cleanup completion: {metrics.cleanup_completion_rate * 100:.0f}%",
        f"  Current streak: {metrics.current_streak_weeks} weeks",
    ]

    if metrics.tasks_with_estimates >= MIN_TASKS_FOR_ESTIMATION:
        lines.append(f"  Estimation accuracy: {metrics.estimation_accuracy * 100:.0f}%")

    lines.extend(
        [
            "",
            "Summary:",
            f"  {metrics.total_on_time}/{metrics.total_completed} commitments on-time",
            f"  {metrics.total_at_risk} marked at-risk",
            f"  {metrics.total_abandoned} abandoned",
        ]
    )

    return "\n".join(lines)


def format_grade_summary(grade: str, score: float) -> str:
    """Format a one-line grade summary.

    Args:
        grade: The letter grade.
        score: The composite score (0-100).

    Returns:
        Short summary string.
    """
    return f"Integrity: {grade} ({score:.0f}/100)"
