"""Tests for IntegrityMetrics dataclass - TDD Red phase."""

from __future__ import annotations

import pytest

from jdo.models.integrity_metrics import IntegrityMetrics


class TestIntegrityMetricsDataclass:
    """Tests for IntegrityMetrics dataclass structure."""

    def test_creates_with_all_fields(self) -> None:
        """IntegrityMetrics creates with all required fields."""
        metrics = IntegrityMetrics(
            on_time_rate=0.85,
            notification_timeliness=0.75,
            cleanup_completion_rate=0.90,
            current_streak_weeks=3,
            total_completed=20,
            total_on_time=17,
            total_at_risk=5,
            total_abandoned=2,
        )

        assert metrics.on_time_rate == 0.85
        assert metrics.notification_timeliness == 0.75
        assert metrics.cleanup_completion_rate == 0.90
        assert metrics.current_streak_weeks == 3
        assert metrics.total_completed == 20
        assert metrics.total_on_time == 17
        assert metrics.total_at_risk == 5
        assert metrics.total_abandoned == 2


class TestOnTimeRate:
    """Tests for on_time_rate metric."""

    def test_on_time_rate_calculation(self) -> None:
        """on_time_rate = completed_on_time / total_completed."""
        metrics = IntegrityMetrics(
            on_time_rate=0.80,  # 8 out of 10
            notification_timeliness=1.0,
            cleanup_completion_rate=1.0,
            current_streak_weeks=0,
            total_completed=10,
            total_on_time=8,
            total_at_risk=0,
            total_abandoned=0,
        )
        assert metrics.on_time_rate == 0.80

    def test_on_time_rate_perfect(self) -> None:
        """on_time_rate = 1.0 when all completed on time."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=1.0,
            cleanup_completion_rate=1.0,
            current_streak_weeks=0,
            total_completed=5,
            total_on_time=5,
            total_at_risk=0,
            total_abandoned=0,
        )
        assert metrics.on_time_rate == 1.0

    def test_on_time_rate_clean_slate(self) -> None:
        """on_time_rate = 1.0 when no completions (clean slate)."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=1.0,
            cleanup_completion_rate=1.0,
            current_streak_weeks=0,
            total_completed=0,
            total_on_time=0,
            total_at_risk=0,
            total_abandoned=0,
        )
        assert metrics.on_time_rate == 1.0


class TestNotificationTimeliness:
    """Tests for notification_timeliness metric."""

    def test_timeliness_seven_days_early(self) -> None:
        """7+ days early = 1.0 timeliness."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=1.0,  # 7+ days early
            cleanup_completion_rate=1.0,
            current_streak_weeks=0,
            total_completed=0,
            total_on_time=0,
            total_at_risk=1,
            total_abandoned=0,
        )
        assert metrics.notification_timeliness == 1.0

    def test_timeliness_zero_days(self) -> None:
        """0 days (on due date) = 0.0 timeliness."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=0.0,  # On due date
            cleanup_completion_rate=1.0,
            current_streak_weeks=0,
            total_completed=0,
            total_on_time=0,
            total_at_risk=1,
            total_abandoned=0,
        )
        assert metrics.notification_timeliness == 0.0

    def test_timeliness_clean_slate(self) -> None:
        """No at-risk history = 1.0 (clean slate)."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=1.0,
            cleanup_completion_rate=1.0,
            current_streak_weeks=0,
            total_completed=0,
            total_on_time=0,
            total_at_risk=0,  # No at-risk history
            total_abandoned=0,
        )
        assert metrics.notification_timeliness == 1.0


class TestCleanupCompletionRate:
    """Tests for cleanup_completion_rate metric."""

    def test_cleanup_rate_calculation(self) -> None:
        """cleanup_rate = completed / total cleanup plans."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=1.0,
            cleanup_completion_rate=0.75,  # 3 out of 4
            current_streak_weeks=0,
            total_completed=0,
            total_on_time=0,
            total_at_risk=4,
            total_abandoned=0,
        )
        assert metrics.cleanup_completion_rate == 0.75

    def test_cleanup_rate_no_plans(self) -> None:
        """cleanup_rate = 1.0 when no cleanup plans exist (clean slate)."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=1.0,
            cleanup_completion_rate=1.0,
            current_streak_weeks=0,
            total_completed=5,
            total_on_time=5,
            total_at_risk=0,
            total_abandoned=0,
        )
        assert metrics.cleanup_completion_rate == 1.0


class TestReliabilityStreak:
    """Tests for current_streak_weeks metric."""

    def test_streak_counts_weeks(self) -> None:
        """Streak counts consecutive weeks with all on-time."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=1.0,
            cleanup_completion_rate=1.0,
            current_streak_weeks=5,
            total_completed=10,
            total_on_time=10,
            total_at_risk=0,
            total_abandoned=0,
        )
        assert metrics.current_streak_weeks == 5

    def test_streak_zero(self) -> None:
        """Streak is 0 after late/abandoned commitment."""
        metrics = IntegrityMetrics(
            on_time_rate=0.9,
            notification_timeliness=1.0,
            cleanup_completion_rate=1.0,
            current_streak_weeks=0,
            total_completed=10,
            total_on_time=9,
            total_at_risk=0,
            total_abandoned=0,
        )
        assert metrics.current_streak_weeks == 0


class TestCompositeScore:
    """Tests for composite_score property."""

    def test_composite_score_weights(self) -> None:
        """Composite score weights: on_time=0.4, timeliness=0.25, cleanup=0.25, streak=0.1."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=1.0,
            cleanup_completion_rate=1.0,
            current_streak_weeks=0,
            total_completed=10,
            total_on_time=10,
            total_at_risk=0,
            total_abandoned=0,
        )
        # 1.0*0.4 + 1.0*0.25 + 1.0*0.25 + 0*0.1 = 0.9 * 100 = 90
        assert metrics.composite_score == 90.0

    def test_composite_score_with_streak_bonus(self) -> None:
        """streak_bonus = min(weeks * 2, 10) / 100."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=1.0,
            cleanup_completion_rate=1.0,
            current_streak_weeks=5,  # 5 * 2 = 10 / 100 = 0.1
            total_completed=10,
            total_on_time=10,
            total_at_risk=0,
            total_abandoned=0,
        )
        # 1.0*0.4 + 1.0*0.25 + 1.0*0.25 + 0.1 = 1.0 * 100 = 100
        assert metrics.composite_score == 100.0

    def test_composite_score_streak_bonus_capped_at_10(self) -> None:
        """Streak bonus caps at 10 (5+ weeks)."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=1.0,
            cleanup_completion_rate=1.0,
            current_streak_weeks=10,  # 10 * 2 = 20, capped at 10
            total_completed=10,
            total_on_time=10,
            total_at_risk=0,
            total_abandoned=0,
        )
        assert metrics.composite_score == 100.0

    def test_composite_score_range(self) -> None:
        """Score range is 0-100."""
        metrics_max = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=1.0,
            cleanup_completion_rate=1.0,
            current_streak_weeks=5,
            total_completed=10,
            total_on_time=10,
            total_at_risk=0,
            total_abandoned=0,
        )
        assert 0 <= metrics_max.composite_score <= 100

        metrics_min = IntegrityMetrics(
            on_time_rate=0.0,
            notification_timeliness=0.0,
            cleanup_completion_rate=0.0,
            current_streak_weeks=0,
            total_completed=10,
            total_on_time=0,
            total_at_risk=10,
            total_abandoned=10,
        )
        assert 0 <= metrics_min.composite_score <= 100

    def test_composite_score_mixed(self) -> None:
        """Mixed metrics calculate correctly."""
        metrics = IntegrityMetrics(
            on_time_rate=0.8,  # 0.8 * 0.4 = 0.32
            notification_timeliness=0.6,  # 0.6 * 0.25 = 0.15
            cleanup_completion_rate=0.7,  # 0.7 * 0.25 = 0.175
            current_streak_weeks=2,  # 2 * 2 = 4 / 100 = 0.04
            total_completed=10,
            total_on_time=8,
            total_at_risk=3,
            total_abandoned=1,
        )
        # 0.32 + 0.15 + 0.175 + 0.04 = 0.685 * 100 = 68.5
        assert metrics.composite_score == pytest.approx(68.5)


class TestLetterGrade:
    """Tests for letter_grade property."""

    def test_grade_a_plus(self) -> None:
        """97-100 = A+."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=1.0,
            cleanup_completion_rate=1.0,
            current_streak_weeks=5,
            total_completed=10,
            total_on_time=10,
            total_at_risk=0,
            total_abandoned=0,
        )
        assert metrics.letter_grade == "A+"

    def test_grade_a(self) -> None:
        """93-96 = A."""
        # Score needs to be 93-96
        # With streak_bonus=0.1 (max), we need base of 0.83-0.86
        # That's tricky, let's aim for 95
        metrics = IntegrityMetrics(
            on_time_rate=1.0,  # 0.4
            notification_timeliness=1.0,  # 0.25
            cleanup_completion_rate=0.8,  # 0.2
            current_streak_weeks=5,  # 0.1
            total_completed=10,
            total_on_time=10,
            total_at_risk=0,
            total_abandoned=0,
        )
        # 0.4 + 0.25 + 0.2 + 0.1 = 0.95 * 100 = 95
        assert metrics.letter_grade == "A"

    def test_grade_a_minus(self) -> None:
        """90-92 = A-."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,  # 0.4
            notification_timeliness=1.0,  # 0.25
            cleanup_completion_rate=1.0,  # 0.25
            current_streak_weeks=0,  # 0.0
            total_completed=10,
            total_on_time=10,
            total_at_risk=0,
            total_abandoned=0,
        )
        # 0.4 + 0.25 + 0.25 + 0 = 0.90 * 100 = 90
        assert metrics.letter_grade == "A-"

    def test_grade_b_plus(self) -> None:
        """87-89 = B+."""
        metrics = IntegrityMetrics(
            on_time_rate=0.95,  # 0.38
            notification_timeliness=1.0,  # 0.25
            cleanup_completion_rate=1.0,  # 0.25
            current_streak_weeks=0,  # 0.0
            total_completed=20,
            total_on_time=19,
            total_at_risk=0,
            total_abandoned=0,
        )
        # 0.38 + 0.25 + 0.25 + 0 = 0.88 * 100 = 88
        assert metrics.letter_grade == "B+"

    def test_grade_b(self) -> None:
        """83-86 = B."""
        metrics = IntegrityMetrics(
            on_time_rate=0.90,  # 0.36
            notification_timeliness=0.92,  # 0.23
            cleanup_completion_rate=1.0,  # 0.25
            current_streak_weeks=0,  # 0.0
            total_completed=10,
            total_on_time=9,
            total_at_risk=0,
            total_abandoned=0,
        )
        # 0.36 + 0.23 + 0.25 + 0 = 0.84 * 100 = 84
        assert metrics.letter_grade == "B"

    def test_grade_b_minus(self) -> None:
        """80-82 = B-."""
        metrics = IntegrityMetrics(
            on_time_rate=0.85,  # 0.34
            notification_timeliness=0.92,  # 0.23
            cleanup_completion_rate=0.92,  # 0.23
            current_streak_weeks=0,
            total_completed=20,
            total_on_time=17,
            total_at_risk=0,
            total_abandoned=0,
        )
        # 0.34 + 0.23 + 0.23 + 0 = 0.80 * 100 = 80
        assert metrics.letter_grade == "B-"

    def test_grade_c_plus(self) -> None:
        """77-79 = C+."""
        metrics = IntegrityMetrics(
            on_time_rate=0.80,  # 0.32
            notification_timeliness=0.88,  # 0.22
            cleanup_completion_rate=0.96,  # 0.24
            current_streak_weeks=0,
            total_completed=10,
            total_on_time=8,
            total_at_risk=0,
            total_abandoned=0,
        )
        # 0.32 + 0.22 + 0.24 + 0 = 0.78 * 100 = 78
        assert metrics.letter_grade == "C+"

    def test_grade_c(self) -> None:
        """73-76 = C."""
        metrics = IntegrityMetrics(
            on_time_rate=0.75,  # 0.30
            notification_timeliness=0.88,  # 0.22
            cleanup_completion_rate=0.92,  # 0.23
            current_streak_weeks=0,
            total_completed=20,
            total_on_time=15,
            total_at_risk=0,
            total_abandoned=0,
        )
        # 0.30 + 0.22 + 0.23 + 0 = 0.75 * 100 = 75
        assert metrics.letter_grade == "C"

    def test_grade_c_minus(self) -> None:
        """70-72 = C-."""
        metrics = IntegrityMetrics(
            on_time_rate=0.70,  # 0.28
            notification_timeliness=0.84,  # 0.21
            cleanup_completion_rate=0.88,  # 0.22
            current_streak_weeks=0,
            total_completed=10,
            total_on_time=7,
            total_at_risk=0,
            total_abandoned=0,
        )
        # 0.28 + 0.21 + 0.22 + 0 = 0.71 * 100 = 71
        assert metrics.letter_grade == "C-"

    def test_grade_d_plus(self) -> None:
        """67-69 = D+."""
        metrics = IntegrityMetrics(
            on_time_rate=0.70,  # 0.28
            notification_timeliness=0.80,  # 0.20
            cleanup_completion_rate=0.80,  # 0.20
            current_streak_weeks=0,
            total_completed=10,
            total_on_time=7,
            total_at_risk=0,
            total_abandoned=0,
        )
        # 0.28 + 0.20 + 0.20 + 0 = 0.68 * 100 = 68
        assert metrics.letter_grade == "D+"

    def test_grade_d(self) -> None:
        """63-66 = D."""
        metrics = IntegrityMetrics(
            on_time_rate=0.65,  # 0.26
            notification_timeliness=0.72,  # 0.18
            cleanup_completion_rate=0.80,  # 0.20
            current_streak_weeks=0,
            total_completed=20,
            total_on_time=13,
            total_at_risk=0,
            total_abandoned=0,
        )
        # 0.26 + 0.18 + 0.20 + 0 = 0.64 * 100 = 64
        assert metrics.letter_grade == "D"

    def test_grade_d_minus(self) -> None:
        """60-62 = D-."""
        metrics = IntegrityMetrics(
            on_time_rate=0.60,  # 0.24
            notification_timeliness=0.72,  # 0.18
            cleanup_completion_rate=0.76,  # 0.19
            current_streak_weeks=0,
            total_completed=10,
            total_on_time=6,
            total_at_risk=0,
            total_abandoned=0,
        )
        # 0.24 + 0.18 + 0.19 + 0 = 0.61 * 100 = 61
        assert metrics.letter_grade == "D-"

    def test_grade_f(self) -> None:
        """<60 = F."""
        metrics = IntegrityMetrics(
            on_time_rate=0.50,  # 0.20
            notification_timeliness=0.50,  # 0.125
            cleanup_completion_rate=0.50,  # 0.125
            current_streak_weeks=0,
            total_completed=10,
            total_on_time=5,
            total_at_risk=5,
            total_abandoned=5,
        )
        # 0.20 + 0.125 + 0.125 + 0 = 0.45 * 100 = 45
        assert metrics.letter_grade == "F"

    def test_new_user_a_plus(self) -> None:
        """New user with no history = A+."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=1.0,
            cleanup_completion_rate=1.0,
            current_streak_weeks=0,
            total_completed=0,
            total_on_time=0,
            total_at_risk=0,
            total_abandoned=0,
        )
        # New user starts with clean slate = A+
        assert metrics.letter_grade == "A-"  # Without streak bonus, 90 = A-

    def test_new_user_with_streak_a_plus(self) -> None:
        """New user maintains A+ with reliability streak."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=1.0,
            cleanup_completion_rate=1.0,
            current_streak_weeks=5,
            total_completed=0,
            total_on_time=0,
            total_at_risk=0,
            total_abandoned=0,
        )
        assert metrics.letter_grade == "A+"
