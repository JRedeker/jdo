"""IntegrityMetrics dataclass for calculating and displaying integrity scores."""

from __future__ import annotations

from dataclasses import dataclass

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

    @property
    def composite_score(self) -> float:
        """Calculate composite integrity score (0-100).

        Formula:
        - on_time_rate: 40% weight
        - notification_timeliness: 25% weight
        - cleanup_completion_rate: 25% weight
        - streak_bonus: 10% weight (capped at 10%)

        Returns:
            Score from 0-100.
        """
        streak_bonus = min(self.current_streak_weeks * 2, 10) / 100
        return (
            self.on_time_rate * 0.40
            + self.notification_timeliness * 0.25
            + self.cleanup_completion_rate * 0.25
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
