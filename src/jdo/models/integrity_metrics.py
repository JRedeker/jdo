"""IntegrityMetrics dataclass for calculating and displaying integrity scores."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# Grade thresholds: (min_score, grade)
# Ordered from highest to lowest for efficient lookup
GRADE_THRESHOLDS: list[tuple[int, str]] = [
    (97, "A+"),
    (93, "A"),
    (90, "A-"),
    (87, "B+"),
    (83, "B"),
    (80, "B-"),
    (77, "C+"),
    (73, "C"),
    (70, "C-"),
    (67, "D+"),
    (63, "D"),
    (60, "D-"),
]

# Threshold for determining trend direction (5% change is significant)
TREND_THRESHOLD = 0.05


class TrendDirection(str, Enum):
    """Direction of metric change compared to previous period."""

    UP = "up"  # Improving
    DOWN = "down"  # Declining
    STABLE = "stable"  # No significant change


@dataclass
class IntegrityMetrics:
    """Calculated integrity metrics from commitment history.

    This dataclass represents a snapshot of a user's integrity metrics,
    calculated from their commitment history. It provides:
    - Individual metrics (on_time_rate, notification_timeliness, etc.)
    - Composite score calculation
    - Letter grade conversion

    Metrics follow MPI's Honor-Your-Word protocol:
    - On-time delivery shows commitment reliability
    - Notification timeliness shows early warning behavior
    - Cleanup completion shows follow-through on recovery
    - Streak reflects sustained reliability
    - Estimation accuracy shows calibrated time planning
    """

    # Primary metrics (0.0-1.0 scale)
    on_time_rate: float
    notification_timeliness: float
    cleanup_completion_rate: float
    current_streak_weeks: int

    # Supporting data for display
    total_completed: int
    total_on_time: int
    total_at_risk: int
    total_abandoned: int

    # Estimation accuracy: 1.0 = perfect estimates, 0.0 = wildly inaccurate
    # Defaults to 1.0 for users with insufficient history
    estimation_accuracy: float = 1.0
    # Number of completed tasks with both estimate and actual_hours_category
    tasks_with_estimates: int = 0

    # Trend indicators (compared to previous 30-day period)
    on_time_trend: TrendDirection | None = None
    notification_trend: TrendDirection | None = None
    cleanup_trend: TrendDirection | None = None
    overall_trend: TrendDirection | None = None

    @property
    def composite_score(self) -> float:
        """Calculate composite integrity score (0-100).

        Formula (v2 with estimation accuracy):
        - on_time_rate: 35% weight (was 40%)
        - notification_timeliness: 25% weight
        - cleanup_completion_rate: 25% weight
        - estimation_accuracy: 10% weight (NEW)
        - streak_bonus: 5% max (was 10%)

        Returns:
            Score from 0-100.
        """
        # Streak bonus: max 5% (2% per week, capped at 5%)
        streak_bonus = min(self.current_streak_weeks * 2, 5) / 100
        return (
            self.on_time_rate * 0.35
            + self.notification_timeliness * 0.25
            + self.cleanup_completion_rate * 0.25
            + self.estimation_accuracy * 0.10
            + streak_bonus
        ) * 100

    @property
    def letter_grade(self) -> str:
        """Convert composite score to letter grade.

        Grading scale:
        - A+: 97-100
        - A:  93-96
        - A-: 90-92
        - B+: 87-89
        - B:  83-86
        - B-: 80-82
        - C+: 77-79
        - C:  73-76
        - C-: 70-72
        - D+: 67-69
        - D:  63-66
        - D-: 60-62
        - F:  < 60

        Returns:
            Letter grade string (e.g., "A+", "B-", "F").
        """
        score = self.composite_score
        for threshold, grade in GRADE_THRESHOLDS:
            if score >= threshold:
                return grade
        return "F"

    @staticmethod
    def trend_indicator(trend: TrendDirection | None) -> str:
        """Get display indicator for a trend direction.

        Args:
            trend: The trend direction or None.

        Returns:
            Arrow symbol: ↑ for up, ↓ for down, → for stable, empty for None.
        """
        if trend is None:
            return ""
        indicators = {
            TrendDirection.UP: "↑",
            TrendDirection.DOWN: "↓",
            TrendDirection.STABLE: "→",
        }
        return indicators.get(trend, "")
