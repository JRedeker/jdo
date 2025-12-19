"""Tests for IntegrityMetrics dataclass - TDD Red phase."""

from __future__ import annotations

import pytest

from jdo.models.integrity_metrics import IntegrityMetrics, TrendDirection


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
    """Tests for composite_score property (v2 formula with estimation_accuracy)."""

    def test_composite_score_weights(self) -> None:
        """Composite score weights (v2): on_time=0.35, timeliness=0.25, cleanup=0.25, etc."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=1.0,
            cleanup_completion_rate=1.0,
            current_streak_weeks=0,
            total_completed=10,
            total_on_time=10,
            total_at_risk=0,
            total_abandoned=0,
            estimation_accuracy=1.0,
        )
        # 1.0*0.35 + 1.0*0.25 + 1.0*0.25 + 1.0*0.10 + 0 = 0.95 * 100 = 95
        assert metrics.composite_score == 95.0

    def test_composite_score_with_streak_bonus(self) -> None:
        """streak_bonus = min(weeks * 2, 5) / 100 (max 5%)."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=1.0,
            cleanup_completion_rate=1.0,
            current_streak_weeks=3,  # 3 * 2 = 6, capped at 5 / 100 = 0.05
            total_completed=10,
            total_on_time=10,
            total_at_risk=0,
            total_abandoned=0,
            estimation_accuracy=1.0,
        )
        # 1.0*0.35 + 1.0*0.25 + 1.0*0.25 + 1.0*0.10 + 0.05 = 1.0 * 100 = 100
        assert metrics.composite_score == 100.0

    def test_composite_score_streak_bonus_capped_at_5(self) -> None:
        """Streak bonus caps at 5% (3+ weeks)."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=1.0,
            cleanup_completion_rate=1.0,
            current_streak_weeks=10,  # 10 * 2 = 20, capped at 5
            total_completed=10,
            total_on_time=10,
            total_at_risk=0,
            total_abandoned=0,
            estimation_accuracy=1.0,
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
        """Mixed metrics calculate correctly (v2 formula)."""
        metrics = IntegrityMetrics(
            on_time_rate=0.8,  # 0.8 * 0.35 = 0.28
            notification_timeliness=0.6,  # 0.6 * 0.25 = 0.15
            cleanup_completion_rate=0.7,  # 0.7 * 0.25 = 0.175
            current_streak_weeks=2,  # 2 * 2 = 4 / 100 = 0.04
            total_completed=10,
            total_on_time=8,
            total_at_risk=3,
            total_abandoned=1,
            estimation_accuracy=0.9,  # 0.9 * 0.10 = 0.09
        )
        # 0.28 + 0.15 + 0.175 + 0.09 + 0.04 = 0.735 * 100 = 73.5
        assert metrics.composite_score == pytest.approx(73.5)


class TestLetterGrade:
    """Tests for letter_grade property (v2 formula)."""

    def test_grade_a_plus(self) -> None:
        """97-100 = A+ (perfect score with streak)."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=1.0,
            cleanup_completion_rate=1.0,
            current_streak_weeks=3,  # Max 5% bonus
            total_completed=10,
            total_on_time=10,
            total_at_risk=0,
            total_abandoned=0,
            estimation_accuracy=1.0,
        )
        # 0.35 + 0.25 + 0.25 + 0.10 + 0.05 = 1.0 * 100 = 100
        assert metrics.letter_grade == "A+"

    def test_grade_a(self) -> None:
        """93-96 = A."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,  # 0.35
            notification_timeliness=1.0,  # 0.25
            cleanup_completion_rate=1.0,  # 0.25
            current_streak_weeks=0,  # 0.0
            total_completed=10,
            total_on_time=10,
            total_at_risk=0,
            total_abandoned=0,
            estimation_accuracy=1.0,  # 0.10
        )
        # 0.35 + 0.25 + 0.25 + 0.10 + 0 = 0.95 * 100 = 95
        assert metrics.letter_grade == "A"

    def test_grade_a_minus(self) -> None:
        """90-92 = A-."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,  # 0.35
            notification_timeliness=1.0,  # 0.25
            cleanup_completion_rate=1.0,  # 0.25
            current_streak_weeks=0,  # 0.0
            total_completed=10,
            total_on_time=10,
            total_at_risk=0,
            total_abandoned=0,
            estimation_accuracy=0.5,  # 0.05
        )
        # 0.35 + 0.25 + 0.25 + 0.05 + 0 = 0.90 * 100 = 90
        assert metrics.letter_grade == "A-"

    def test_grade_b_plus(self) -> None:
        """87-89 = B+."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,  # 0.35
            notification_timeliness=1.0,  # 0.25
            cleanup_completion_rate=1.0,  # 0.25
            current_streak_weeks=0,  # 0.0
            total_completed=20,
            total_on_time=20,
            total_at_risk=0,
            total_abandoned=0,
            estimation_accuracy=0.2,  # 0.02
        )
        # 0.35 + 0.25 + 0.25 + 0.02 + 0 = 0.87 * 100 = 87
        assert metrics.letter_grade == "B+"

    def test_grade_b(self) -> None:
        """83-86 = B."""
        metrics = IntegrityMetrics(
            on_time_rate=0.90,  # 0.315
            notification_timeliness=1.0,  # 0.25
            cleanup_completion_rate=1.0,  # 0.25
            current_streak_weeks=0,  # 0.0
            total_completed=10,
            total_on_time=9,
            total_at_risk=0,
            total_abandoned=0,
            estimation_accuracy=0.2,  # 0.02
        )
        # 0.315 + 0.25 + 0.25 + 0.02 = 0.835 * 100 = 83.5
        assert metrics.letter_grade == "B"

    def test_grade_b_minus(self) -> None:
        """80-82 = B-."""
        metrics = IntegrityMetrics(
            on_time_rate=0.80,  # 0.28
            notification_timeliness=1.0,  # 0.25
            cleanup_completion_rate=1.0,  # 0.25
            current_streak_weeks=0,
            total_completed=20,
            total_on_time=16,
            total_at_risk=0,
            total_abandoned=0,
            estimation_accuracy=0.2,  # 0.02
        )
        # 0.28 + 0.25 + 0.25 + 0.02 = 0.80 * 100 = 80
        assert metrics.letter_grade == "B-"

    def test_grade_c_plus(self) -> None:
        """77-79 = C+."""
        metrics = IntegrityMetrics(
            on_time_rate=0.80,  # 0.28
            notification_timeliness=0.88,  # 0.22
            cleanup_completion_rate=1.0,  # 0.25
            current_streak_weeks=0,
            total_completed=10,
            total_on_time=8,
            total_at_risk=0,
            total_abandoned=0,
            estimation_accuracy=0.2,  # 0.02
        )
        # 0.28 + 0.22 + 0.25 + 0.02 = 0.77 * 100 = 77
        assert metrics.letter_grade == "C+"

    def test_grade_c(self) -> None:
        """73-76 = C."""
        metrics = IntegrityMetrics(
            on_time_rate=0.80,  # 0.28
            notification_timeliness=0.80,  # 0.20
            cleanup_completion_rate=1.0,  # 0.25
            current_streak_weeks=0,
            total_completed=20,
            total_on_time=16,
            total_at_risk=0,
            total_abandoned=0,
            estimation_accuracy=0.0,  # 0.0
        )
        # 0.28 + 0.20 + 0.25 + 0.0 = 0.73 * 100 = 73
        assert metrics.letter_grade == "C"

    def test_grade_c_minus(self) -> None:
        """70-72 = C-."""
        metrics = IntegrityMetrics(
            on_time_rate=0.80,  # 0.28
            notification_timeliness=0.68,  # 0.17
            cleanup_completion_rate=1.0,  # 0.25
            current_streak_weeks=0,
            total_completed=10,
            total_on_time=8,
            total_at_risk=0,
            total_abandoned=0,
            estimation_accuracy=0.0,  # 0.0
        )
        # 0.28 + 0.17 + 0.25 + 0.0 = 0.70 * 100 = 70
        assert metrics.letter_grade == "C-"

    def test_grade_d_plus(self) -> None:
        """67-69 = D+."""
        metrics = IntegrityMetrics(
            on_time_rate=0.80,  # 0.28
            notification_timeliness=0.60,  # 0.15
            cleanup_completion_rate=0.96,  # 0.24
            current_streak_weeks=0,
            total_completed=10,
            total_on_time=8,
            total_at_risk=0,
            total_abandoned=0,
            estimation_accuracy=0.0,  # 0.0
        )
        # 0.28 + 0.15 + 0.24 + 0 = 0.67 * 100 = 67
        assert metrics.letter_grade == "D+"

    def test_grade_d(self) -> None:
        """63-66 = D."""
        metrics = IntegrityMetrics(
            on_time_rate=0.80,  # 0.28
            notification_timeliness=0.40,  # 0.10
            cleanup_completion_rate=1.0,  # 0.25
            current_streak_weeks=0,
            total_completed=20,
            total_on_time=16,
            total_at_risk=0,
            total_abandoned=0,
            estimation_accuracy=0.0,  # 0.0
        )
        # 0.28 + 0.10 + 0.25 + 0 = 0.63 * 100 = 63
        assert metrics.letter_grade == "D"

    def test_grade_d_minus(self) -> None:
        """60-62 = D-."""
        metrics = IntegrityMetrics(
            on_time_rate=0.80,  # 0.28
            notification_timeliness=0.28,  # 0.07
            cleanup_completion_rate=1.0,  # 0.25
            current_streak_weeks=0,
            total_completed=10,
            total_on_time=8,
            total_at_risk=0,
            total_abandoned=0,
            estimation_accuracy=0.0,  # 0.0
        )
        # 0.28 + 0.07 + 0.25 + 0 = 0.60 * 100 = 60
        assert metrics.letter_grade == "D-"

    def test_grade_f(self) -> None:
        """<60 = F."""
        metrics = IntegrityMetrics(
            on_time_rate=0.50,  # 0.175
            notification_timeliness=0.50,  # 0.125
            cleanup_completion_rate=0.50,  # 0.125
            current_streak_weeks=0,
            total_completed=10,
            total_on_time=5,
            total_at_risk=5,
            total_abandoned=5,
            estimation_accuracy=0.0,  # 0.0
        )
        # 0.175 + 0.125 + 0.125 + 0 = 0.425 * 100 = 42.5
        assert metrics.letter_grade == "F"

    def test_new_user_a(self) -> None:
        """New user with no history = A (95 without streak)."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=1.0,
            cleanup_completion_rate=1.0,
            current_streak_weeks=0,
            total_completed=0,
            total_on_time=0,
            total_at_risk=0,
            total_abandoned=0,
            estimation_accuracy=1.0,  # Default
        )
        # 0.35 + 0.25 + 0.25 + 0.10 + 0 = 0.95 * 100 = 95 = A
        assert metrics.letter_grade == "A"

    def test_new_user_with_streak_a_plus(self) -> None:
        """New user maintains A+ with reliability streak (3+ weeks)."""
        metrics = IntegrityMetrics(
            on_time_rate=1.0,
            notification_timeliness=1.0,
            cleanup_completion_rate=1.0,
            current_streak_weeks=3,  # 3 weeks = max 5% bonus
            total_completed=0,
            total_on_time=0,
            total_at_risk=0,
            total_abandoned=0,
            estimation_accuracy=1.0,
        )
        # 0.35 + 0.25 + 0.25 + 0.10 + 0.05 = 1.0 * 100 = 100 = A+
        assert metrics.letter_grade == "A+"


class TestTrendDirection:
    """Tests for TrendDirection enum and trend fields."""

    def test_trend_direction_enum_values(self) -> None:
        """TrendDirection has up, down, stable values."""
        assert TrendDirection.UP.value == "up"
        assert TrendDirection.DOWN.value == "down"
        assert TrendDirection.STABLE.value == "stable"

    def test_metrics_with_trends(self) -> None:
        """IntegrityMetrics can store trend fields."""
        metrics = IntegrityMetrics(
            on_time_rate=0.85,
            notification_timeliness=0.75,
            cleanup_completion_rate=0.90,
            current_streak_weeks=3,
            total_completed=20,
            total_on_time=17,
            total_at_risk=5,
            total_abandoned=2,
            on_time_trend=TrendDirection.UP,
            notification_trend=TrendDirection.DOWN,
            cleanup_trend=TrendDirection.STABLE,
            overall_trend=TrendDirection.UP,
        )

        assert metrics.on_time_trend == TrendDirection.UP
        assert metrics.notification_trend == TrendDirection.DOWN
        assert metrics.cleanup_trend == TrendDirection.STABLE
        assert metrics.overall_trend == TrendDirection.UP

    def test_metrics_trends_default_to_none(self) -> None:
        """Trend fields default to None when not provided."""
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

        assert metrics.on_time_trend is None
        assert metrics.notification_trend is None
        assert metrics.cleanup_trend is None
        assert metrics.overall_trend is None

    def test_trend_indicator_up(self) -> None:
        """trend_indicator returns ↑ for UP direction."""
        assert IntegrityMetrics.trend_indicator(TrendDirection.UP) == "↑"

    def test_trend_indicator_down(self) -> None:
        """trend_indicator returns ↓ for DOWN direction."""
        assert IntegrityMetrics.trend_indicator(TrendDirection.DOWN) == "↓"

    def test_trend_indicator_stable(self) -> None:
        """trend_indicator returns → for STABLE direction."""
        assert IntegrityMetrics.trend_indicator(TrendDirection.STABLE) == "→"

    def test_trend_indicator_none(self) -> None:
        """trend_indicator returns empty string for None."""
        assert IntegrityMetrics.trend_indicator(None) == ""
