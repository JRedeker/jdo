"""Tests for the integrity formatters module."""

from io import StringIO
from unittest.mock import MagicMock

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from jdo.models.integrity_metrics import IntegrityMetrics, TrendDirection
from jdo.output.integrity import (
    GRADE_COLORS,
    TREND_STYLES,
    format_grade,
    format_grade_summary,
    format_integrity_dashboard,
    format_integrity_plain,
    format_metric_row,
    format_metrics_table,
    format_trend,
    get_grade_color,
)


def make_metrics(**kwargs) -> IntegrityMetrics:
    """Create IntegrityMetrics with defaults for testing.

    Args:
        **kwargs: Override any IntegrityMetrics field.

    Returns:
        IntegrityMetrics with sensible defaults for testing.
    """
    defaults = {
        "on_time_rate": 1.0,
        "notification_timeliness": 1.0,
        "cleanup_completion_rate": 1.0,
        "current_streak_weeks": 0,
        "total_completed": 10,
        "total_on_time": 10,
        "total_at_risk": 0,
        "total_abandoned": 0,
        "estimation_accuracy": 1.0,
        "tasks_with_estimates": 0,
        "on_time_trend": None,
        "notification_trend": None,
        "cleanup_trend": None,
        "overall_trend": None,
    }
    defaults.update(kwargs)
    return IntegrityMetrics(**defaults)


def render_to_string(renderable) -> str:
    """Render a Rich renderable to plain text string for testing."""
    console = Console(file=StringIO(), force_terminal=True, width=120)
    console.print(renderable)
    return console.file.getvalue()


class TestGetGradeColor:
    """Tests for grade color mapping."""

    def test_a_grades_are_green(self):
        """A grades return green."""
        assert get_grade_color("A+") == "green"
        assert get_grade_color("A") == "green"
        assert get_grade_color("A-") == "green"

    def test_b_grades_are_blue(self):
        """B grades return blue."""
        assert get_grade_color("B+") == "blue"
        assert get_grade_color("B") == "blue"
        assert get_grade_color("B-") == "blue"

    def test_c_grades_are_yellow(self):
        """C grades return yellow."""
        assert get_grade_color("C+") == "yellow"
        assert get_grade_color("C") == "yellow"
        assert get_grade_color("C-") == "yellow"

    def test_d_grades_are_red(self):
        """D grades return red."""
        assert get_grade_color("D+") == "red"
        assert get_grade_color("D") == "red"
        assert get_grade_color("D-") == "red"

    def test_f_grade_is_red(self):
        """F grade returns red."""
        assert get_grade_color("F") == "red"

    def test_unknown_grade_returns_default(self):
        """Unknown grade returns default."""
        assert get_grade_color("X") == "default"


class TestFormatTrend:
    """Tests for trend indicator formatting."""

    def test_none_trend_returns_empty_text(self):
        """None trend returns empty Text."""
        result = format_trend(None)
        assert isinstance(result, Text)
        assert str(result) == ""

    def test_up_trend_shows_arrow(self):
        """Up trend shows up arrow."""
        result = format_trend(TrendDirection.UP)
        assert "↑" in str(result)

    def test_down_trend_shows_arrow(self):
        """Down trend shows down arrow."""
        result = format_trend(TrendDirection.DOWN)
        assert "↓" in str(result)

    def test_stable_trend_shows_arrow(self):
        """Stable trend shows right arrow."""
        result = format_trend(TrendDirection.STABLE)
        assert "→" in str(result)


class TestFormatGrade:
    """Tests for grade display formatting."""

    def test_returns_panel(self):
        """Grade display returns a Panel."""
        panel = format_grade("A+")
        assert isinstance(panel, Panel)

    def test_panel_contains_grade(self):
        """Panel contains the grade text."""
        panel = format_grade("B-")
        content = str(panel.renderable)
        assert "B-" in content

    def test_panel_has_title(self):
        """Panel has 'Integrity Grade' title."""
        panel = format_grade("A")
        assert "Integrity Grade" in str(panel.title)


class TestFormatMetricRow:
    """Tests for metric row formatting."""

    def test_returns_text(self):
        """Metric row returns Text."""
        result = format_metric_row("Test", 0.95)
        assert isinstance(result, Text)

    def test_percentage_format(self):
        """Percentage values are formatted as %."""
        result = format_metric_row("On-time", 0.95)
        assert "95%" in str(result)

    def test_high_value_is_green(self):
        """High percentage values use green."""
        result = format_metric_row("Test", 0.95)
        # Check that green style is applied
        assert any(span.style == "green" for span in result.spans)

    def test_medium_value_is_yellow(self):
        """Medium percentage values use yellow."""
        result = format_metric_row("Test", 0.75)
        assert any(span.style == "yellow" for span in result.spans)

    def test_low_value_is_red(self):
        """Low percentage values use red."""
        result = format_metric_row("Test", 0.50)
        assert any(span.style == "red" for span in result.spans)

    def test_non_percentage_format(self):
        """Non-percentage values are formatted as-is."""
        result = format_metric_row("Streak", 5, is_percentage=False)
        assert "5" in str(result)

    def test_trend_is_included(self):
        """Trend indicator is included when provided."""
        result = format_metric_row("Test", 0.95, trend=TrendDirection.UP)
        assert "↑" in str(result)


class TestFormatMetricsTable:
    """Tests for metrics table formatting."""

    def test_returns_table(self):
        """Metrics table returns a Table."""
        metrics = make_metrics()
        table = format_metrics_table(metrics)
        assert isinstance(table, Table)

    def test_shows_core_metrics(self):
        """Table shows on-time, notification, cleanup, streak."""
        metrics = make_metrics()
        table = format_metrics_table(metrics)
        # Table should have rows (can't easily inspect row content directly)
        assert table.row_count >= 4

    def test_shows_estimation_accuracy_when_sufficient_data(self):
        """Table shows estimation accuracy when tasks_with_estimates >= 5."""
        metrics = make_metrics(
            tasks_with_estimates=10,
            estimation_accuracy=0.85,
        )
        table = format_metrics_table(metrics)
        # Should have 5 rows: on-time, notification, cleanup, estimation, streak
        assert table.row_count == 5

    def test_hides_estimation_accuracy_when_insufficient_data(self):
        """Table hides estimation accuracy when tasks_with_estimates < 5."""
        metrics = make_metrics(
            tasks_with_estimates=3,
            estimation_accuracy=0.85,
        )
        table = format_metrics_table(metrics)
        # Should have 4 rows: on-time, notification, cleanup, streak
        assert table.row_count == 4


class TestFormatIntegrityDashboard:
    """Tests for complete integrity dashboard formatting."""

    def test_returns_panel(self):
        """Dashboard returns a Panel."""
        metrics = make_metrics()
        panel = format_integrity_dashboard(metrics)
        assert isinstance(panel, Panel)

    def test_contains_grade(self):
        """Dashboard contains the letter grade."""
        metrics = make_metrics()  # Perfect scores = A+
        panel = format_integrity_dashboard(metrics)
        content = render_to_string(panel)
        assert "A" in content

    def test_contains_score(self):
        """Dashboard contains the numeric score."""
        metrics = make_metrics()
        panel = format_integrity_dashboard(metrics)
        content = render_to_string(panel)
        assert "/100" in content

    def test_contains_summary(self):
        """Dashboard contains summary statistics."""
        metrics = make_metrics(total_on_time=8, total_completed=10)
        panel = format_integrity_dashboard(metrics)
        content = render_to_string(panel)
        assert "8/10" in content

    def test_shows_at_risk_count_if_nonzero(self):
        """Dashboard shows at-risk count when > 0."""
        metrics = make_metrics(total_at_risk=2)
        panel = format_integrity_dashboard(metrics)
        content = render_to_string(panel)
        assert "2 at-risk" in content

    def test_shows_abandoned_count_if_nonzero(self):
        """Dashboard shows abandoned count when > 0."""
        metrics = make_metrics(total_abandoned=1)
        panel = format_integrity_dashboard(metrics)
        content = render_to_string(panel)
        assert "1 abandoned" in content

    def test_shows_affecting_commitments_if_provided(self):
        """Dashboard shows affecting commitments when provided."""
        metrics = make_metrics()

        # Create mock affecting commitment
        mock_commitment = MagicMock()
        mock_commitment.deliverable = "Send report to boss"

        mock_affecting = MagicMock()
        mock_affecting.commitment = mock_commitment
        mock_affecting.reason = "completed late"

        panel = format_integrity_dashboard(metrics, affecting=[mock_affecting])
        content = render_to_string(panel)
        assert "Send report" in content
        assert "completed late" in content

    def test_shows_overall_trend_if_available(self):
        """Dashboard shows overall trend when available."""
        metrics = make_metrics(overall_trend=TrendDirection.UP)
        panel = format_integrity_dashboard(metrics)
        content = render_to_string(panel)
        assert "Improving" in content or "↑" in content


class TestFormatIntegrityPlain:
    """Tests for plain text integrity formatting."""

    def test_returns_string(self):
        """Plain format returns string."""
        metrics = make_metrics()
        result = format_integrity_plain(metrics)
        assert isinstance(result, str)

    def test_contains_grade(self):
        """Plain format contains grade."""
        metrics = make_metrics()
        result = format_integrity_plain(metrics)
        assert "A" in result  # Perfect metrics = A+

    def test_contains_score(self):
        """Plain format contains score."""
        metrics = make_metrics()
        result = format_integrity_plain(metrics)
        assert "/100" in result

    def test_contains_metrics(self):
        """Plain format contains all metrics."""
        metrics = make_metrics()
        result = format_integrity_plain(metrics)
        assert "On-time delivery" in result
        assert "Notification timeliness" in result
        assert "Cleanup completion" in result
        assert "streak" in result

    def test_contains_summary_counts(self):
        """Plain format contains summary counts."""
        metrics = make_metrics(
            total_on_time=8,
            total_completed=10,
            total_at_risk=2,
            total_abandoned=1,
        )
        result = format_integrity_plain(metrics)
        assert "8/10" in result
        assert "2 marked at-risk" in result
        assert "1 abandoned" in result

    def test_shows_estimation_accuracy_when_sufficient_data(self):
        """Plain format shows estimation accuracy when available."""
        metrics = make_metrics(
            tasks_with_estimates=10,
            estimation_accuracy=0.85,
        )
        result = format_integrity_plain(metrics)
        assert "Estimation accuracy" in result


class TestFormatGradeSummary:
    """Tests for one-line grade summary."""

    def test_returns_string(self):
        """Summary returns string."""
        result = format_grade_summary("A+", 98.5)
        assert isinstance(result, str)

    def test_contains_grade_and_score(self):
        """Summary contains grade and score."""
        result = format_grade_summary("B+", 87.3)
        assert "B+" in result
        assert "87" in result


class TestGradeColorsConstant:
    """Tests for GRADE_COLORS constant."""

    def test_all_letter_grades_have_colors(self):
        """All possible letter grades have colors defined."""
        expected_grades = [
            "A+",
            "A",
            "A-",
            "B+",
            "B",
            "B-",
            "C+",
            "C",
            "C-",
            "D+",
            "D",
            "D-",
            "F",
        ]
        for grade in expected_grades:
            assert grade in GRADE_COLORS


class TestTrendStylesConstant:
    """Tests for TREND_STYLES constant."""

    def test_all_directions_have_styles(self):
        """All trend directions have styles defined."""
        for direction in TrendDirection:
            assert direction.value in TREND_STYLES

    def test_styles_have_symbol_and_color(self):
        """Each style has symbol and color."""
        for symbol, color in TREND_STYLES.values():
            assert symbol in ("↑", "↓", "→")
            assert color in ("green", "red", "dim")
