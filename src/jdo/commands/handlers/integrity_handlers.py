"""Integrity command handler implementations."""

from __future__ import annotations

from typing import Any

from jdo.commands.handlers.base import CommandHandler, HandlerResult
from jdo.commands.parser import ParsedCommand


class IntegrityHandler(CommandHandler):
    """Handler for /integrity command - shows integrity dashboard."""

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:  # noqa: ARG002
        """Execute /integrity command.

        Args:
            cmd: The parsed command.
            context: Context with integrity metrics.

        Returns:
            HandlerResult with integrity dashboard.
        """
        metrics = context.get("integrity_metrics")

        # Handle case where no metrics are available
        if not metrics:
            # New user with clean slate
            return self._show_empty_dashboard()

        return self._show_dashboard(metrics)

    def _show_empty_dashboard(self) -> HandlerResult:
        """Show dashboard for new users with no history."""
        lines = [
            "Integrity Dashboard",
            "=" * 40,
            "",
            "  Grade: A+",
            "",
            "You're starting with a clean slate!",
            "",
            "Keep your commitments to maintain your integrity score.",
            "If you can't meet a commitment, use /atrisk to notify",
            "stakeholders and create a cleanup plan.",
            "",
            "Your score is based on:",
            "  - On-time delivery rate (40%)",
            "  - Notification timeliness (25%)",
            "  - Cleanup completion rate (25%)",
            "  - Reliability streak bonus (10%)",
        ]

        return HandlerResult(
            message="\n".join(lines),
            panel_update={
                "mode": "integrity",
                "entity_type": "integrity_dashboard",
                "data": {
                    "letter_grade": "A+",
                    "composite_score": 100.0,
                    "on_time_rate": 1.0,
                    "notification_timeliness": 1.0,
                    "cleanup_completion_rate": 1.0,
                    "current_streak_weeks": 0,
                    "is_empty": True,
                },
            },
            draft_data=None,
            needs_confirmation=False,
        )

    def _show_dashboard(self, metrics: dict[str, Any]) -> HandlerResult:
        """Show integrity dashboard with metrics."""
        grade = metrics.get("letter_grade", "?")
        score = metrics.get("composite_score", 0)
        on_time = metrics.get("on_time_rate", 0) * 100
        timeliness = metrics.get("notification_timeliness", 0) * 100
        cleanup = metrics.get("cleanup_completion_rate", 0) * 100
        streak = metrics.get("current_streak_weeks", 0)

        # Totals for context
        total_completed = metrics.get("total_completed", 0)
        total_on_time = metrics.get("total_on_time", 0)
        total_at_risk = metrics.get("total_at_risk", 0)
        total_abandoned = metrics.get("total_abandoned", 0)

        # Affecting commitments
        affecting = metrics.get("affecting_commitments", [])

        lines = [
            "Integrity Dashboard",
            "=" * 40,
            "",
            f"  Grade: {grade}  (Score: {score:.1f}%)",
            "",
            "Metrics:",
            f"  On-time delivery:      {on_time:.0f}% ({total_on_time}/{total_completed} on time)",
            f"  Notification timing:   {timeliness:.0f}%",
            f"  Cleanup completion:    {cleanup:.0f}%",
            f"  Reliability streak:    {streak} week(s)",
            "",
        ]

        # Add summary stats
        if total_at_risk > 0 or total_abandoned > 0:
            lines.append("History:")
            lines.append(f"  Total completed: {total_completed}")
            if total_at_risk > 0:
                lines.append(f"  Marked at-risk: {total_at_risk}")
            if total_abandoned > 0:
                lines.append(f"  Abandoned: {total_abandoned}")
            lines.append("")

        # Add affecting commitments
        if affecting:
            lines.append("Recent issues affecting score:")
            for item in affecting:
                deliverable = item.get("deliverable", "Untitled")[:40]
                reason = item.get("reason", "unknown")
                lines.append(f"  • {deliverable} ({reason})")
            lines.append("")

        # Grade color hint for TUI
        grade_colors = {
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

        return HandlerResult(
            message="\n".join(lines),
            panel_update={
                "mode": "integrity",
                "entity_type": "integrity_dashboard",
                "data": {
                    **metrics,
                    "grade_color": grade_colors.get(grade, "white"),
                    "affecting_commitments": affecting,
                },
            },
            draft_data=None,
            needs_confirmation=False,
        )
