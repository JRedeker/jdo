"""Integrity summary widget for NavSidebar.

Displays a compact view of the user's integrity grade and score,
always visible below the navigation menu.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.text import Text
from textual.reactive import reactive
from textual.widgets import Static

if TYPE_CHECKING:
    from jdo.models.integrity_metrics import IntegrityMetrics


class IntegritySummary(Static):
    """Compact integrity display for the sidebar.

    Shows:
    - Letter grade (A+, B-, etc.)
    - Composite score (0-100)
    - Overall trend indicator

    Attributes:
        grade: Current letter grade.
        score: Composite score (0-100).
        trend: Overall trend direction.
    """

    DEFAULT_CSS = """
    IntegritySummary {
        height: auto;
        width: 100%;
        padding: 1 1;
        border-top: solid $primary;
        margin-top: 1;
    }

    IntegritySummary.-collapsed {
        padding: 1 0;
    }

    IntegritySummary .integrity-label {
        color: $text-muted;
    }

    IntegritySummary .grade-a {
        color: $success;
    }

    IntegritySummary .grade-b {
        color: $primary;
    }

    IntegritySummary .grade-c {
        color: $warning;
    }

    IntegritySummary .grade-d {
        color: $error;
    }

    IntegritySummary .grade-f {
        color: $error;
        text-style: bold;
    }

    IntegritySummary .trend-up {
        color: $success;
    }

    IntegritySummary .trend-down {
        color: $error;
    }

    IntegritySummary .trend-stable {
        color: $text-muted;
    }
    """

    grade: reactive[str] = reactive(default="--")
    score: reactive[float] = reactive(default=0.0)
    trend: reactive[str | None] = reactive(default=None)
    collapsed: reactive[bool] = reactive(default=False)

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the integrity summary widget.

        Args:
            name: Widget name.
            id: Widget ID.
            classes: CSS classes.
        """
        super().__init__(name=name, id=id, classes=classes)

    def render(self) -> Text:
        """Render the integrity summary."""
        text = Text()

        if self.collapsed:
            # Collapsed: just show grade
            text.append(self.grade, style=self._grade_style())
        else:
            # Expanded: show full summary
            text.append("Integrity ", style="dim")
            text.append(self.grade, style=self._grade_style())
            text.append(f" ({self.score:.0f})", style="dim")

            if self.trend:
                text.append(" ")
                text.append(self.trend, style=self._trend_style())

        return text

    def _grade_style(self) -> str:
        """Get style for the current grade."""
        if self.grade.startswith("A"):
            return "bold green"
        if self.grade.startswith("B"):
            return "bold blue"
        if self.grade.startswith("C"):
            return "bold yellow"
        if self.grade.startswith("D"):
            return "bold red"
        if self.grade == "F":
            return "bold red reverse"
        return "dim"

    def _trend_style(self) -> str:
        """Get style for the trend indicator."""
        if self.trend == "↑":
            return "green"
        if self.trend == "↓":
            return "red"
        return "dim"

    def update_metrics(self, metrics: IntegrityMetrics) -> None:
        """Update the display with new metrics.

        Args:
            metrics: The integrity metrics to display.
        """
        self.grade = metrics.letter_grade
        self.score = metrics.composite_score
        self.trend = metrics.trend_indicator(metrics.overall_trend)
        self.refresh()

    def set_collapsed(self, collapsed: bool) -> None:
        """Set the collapsed display state.

        Args:
            collapsed: Whether to show collapsed (compact) view.
        """
        self.collapsed = collapsed
        if collapsed:
            self.add_class("-collapsed")
        else:
            self.remove_class("-collapsed")
        self.refresh()

    def watch_grade(self, _old: str, _new: str) -> None:
        """React to grade changes."""
        self.refresh()

    def watch_score(self, _old: float, _new: float) -> None:
        """React to score changes."""
        self.refresh()

    def watch_trend(self, _old: str | None, _new: str | None) -> None:
        """React to trend changes."""
        self.refresh()
