"""Tests for the triage formatters module."""

from io import StringIO
from unittest.mock import MagicMock

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from jdo.output.triage import (
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    ENTITY_TYPE_COLORS,
    format_confidence,
    format_triage_item,
    format_triage_item_plain,
    format_triage_progress,
    format_triage_queue_status,
    format_triage_summary,
    get_entity_type_color,
)


def render_to_string(renderable) -> str:
    """Render a Rich renderable to plain text string for testing."""
    console = Console(file=StringIO(), force_terminal=True, width=120)
    console.print(renderable)
    return console.file.getvalue()


def make_mock_draft(raw_text: str = "Test captured text"):
    """Create a mock Draft object for testing."""
    draft = MagicMock()
    draft.partial_data = {"raw_text": raw_text}
    return draft


def make_mock_analysis(
    suggested_type: str = "commitment",
    confidence: float = 0.95,
    reasoning: str = "Test reasoning",
    detected_stakeholder: str | None = None,
    detected_date: str | None = None,
    question: str | None = None,
):
    """Create a mock TriageAnalysis for testing."""
    analysis = MagicMock()

    # Classification
    classification = MagicMock()
    classification.suggested_type = suggested_type
    classification.confidence = confidence
    classification.reasoning = reasoning
    classification.detected_stakeholder = detected_stakeholder
    classification.detected_date = detected_date
    analysis.classification = classification

    # Confidence check
    analysis.is_confident = confidence >= CONFIDENCE_MEDIUM

    # Question (if low confidence or requested)
    if question:
        question_mock = MagicMock()
        question_mock.question = question
        analysis.question = question_mock
    else:
        analysis.question = None

    return analysis


class TestGetEntityTypeColor:
    """Tests for entity type color mapping."""

    def test_commitment_is_blue(self):
        """Commitment type returns blue."""
        assert get_entity_type_color("commitment") == "blue"

    def test_goal_is_green(self):
        """Goal type returns green."""
        assert get_entity_type_color("goal") == "green"

    def test_task_is_cyan(self):
        """Task type returns cyan."""
        assert get_entity_type_color("task") == "cyan"

    def test_vision_is_magenta(self):
        """Vision type returns magenta."""
        assert get_entity_type_color("vision") == "magenta"

    def test_milestone_is_yellow(self):
        """Milestone type returns yellow."""
        assert get_entity_type_color("milestone") == "yellow"

    def test_unknown_is_dim(self):
        """Unknown type returns dim."""
        assert get_entity_type_color("unknown") == "dim"

    def test_case_insensitive(self):
        """Color lookup is case insensitive."""
        assert get_entity_type_color("COMMITMENT") == "blue"
        assert get_entity_type_color("Goal") == "green"

    def test_invalid_returns_default(self):
        """Invalid type returns default."""
        assert get_entity_type_color("invalid_type") == "default"


class TestFormatConfidence:
    """Tests for confidence formatting."""

    def test_returns_text(self):
        """Format returns Rich Text."""
        result = format_confidence(0.95)
        assert isinstance(result, Text)

    def test_high_confidence_shows_high_label(self):
        """High confidence (>=90%) shows High label."""
        result = format_confidence(0.95)
        content = str(result)
        assert "95%" in content
        assert "High" in content

    def test_medium_confidence_shows_medium_label(self):
        """Medium confidence (70-89%) shows Medium label."""
        result = format_confidence(0.75)
        content = str(result)
        assert "75%" in content
        assert "Medium" in content

    def test_low_confidence_shows_low_label(self):
        """Low confidence (<70%) shows Low label."""
        result = format_confidence(0.50)
        content = str(result)
        assert "50%" in content
        assert "Low" in content


class TestFormatTriageProgress:
    """Tests for triage progress indicator formatting."""

    def test_returns_text(self):
        """Progress returns Rich Text."""
        result = format_triage_progress(1, 5)
        assert isinstance(result, Text)

    def test_shows_current_and_total(self):
        """Progress shows current and total."""
        result = format_triage_progress(3, 10)
        content = str(result)
        assert "3" in content
        assert "10" in content
        assert "of" in content

    def test_single_item(self):
        """Single item shows 1 of 1."""
        result = format_triage_progress(1, 1)
        content = str(result)
        assert "1" in content


class TestFormatTriageItem:
    """Tests for triage item panel formatting."""

    def test_returns_panel(self):
        """Format returns a Panel."""
        draft = make_mock_draft()
        panel = format_triage_item(draft)
        assert isinstance(panel, Panel)

    def test_shows_original_text(self):
        """Panel shows the original captured text."""
        draft = make_mock_draft("Buy groceries for dinner party")
        panel = format_triage_item(draft)
        content = render_to_string(panel)
        assert "Buy groceries" in content

    def test_shows_progress_indicator(self):
        """Panel shows progress when multiple items."""
        draft = make_mock_draft()
        panel = format_triage_item(draft, current=2, total=5)
        content = render_to_string(panel)
        assert "2" in content
        assert "5" in content

    def test_shows_analyzing_when_no_analysis(self):
        """Panel shows 'Analyzing...' when no analysis provided."""
        draft = make_mock_draft()
        panel = format_triage_item(draft, analysis=None)
        content = render_to_string(panel)
        assert "Analyzing" in content

    def test_shows_suggested_type_from_analysis(self):
        """Panel shows suggested type from analysis."""
        draft = make_mock_draft()
        analysis = make_mock_analysis(suggested_type="commitment")
        panel = format_triage_item(draft, analysis=analysis)
        content = render_to_string(panel)
        assert "Commitment" in content

    def test_shows_confidence_from_analysis(self):
        """Panel shows confidence from analysis."""
        draft = make_mock_draft()
        analysis = make_mock_analysis(confidence=0.85)
        panel = format_triage_item(draft, analysis=analysis)
        content = render_to_string(panel)
        assert "85%" in content

    def test_shows_reasoning_from_analysis(self):
        """Panel shows reasoning from analysis."""
        draft = make_mock_draft()
        analysis = make_mock_analysis(reasoning="Contains deadline and deliverable")
        panel = format_triage_item(draft, analysis=analysis)
        content = render_to_string(panel)
        assert "deadline" in content or "deliverable" in content

    def test_shows_detected_stakeholder(self):
        """Panel shows detected stakeholder if present."""
        draft = make_mock_draft()
        analysis = make_mock_analysis(detected_stakeholder="Sarah")
        panel = format_triage_item(draft, analysis=analysis)
        content = render_to_string(panel)
        assert "Sarah" in content

    def test_shows_detected_date(self):
        """Panel shows detected date if present."""
        draft = make_mock_draft()
        analysis = make_mock_analysis(detected_date="Friday")
        panel = format_triage_item(draft, analysis=analysis)
        content = render_to_string(panel)
        assert "Friday" in content

    def test_shows_question_when_low_confidence(self):
        """Panel shows clarifying question when confidence is low."""
        draft = make_mock_draft()
        analysis = make_mock_analysis(
            confidence=0.50,
            question="Is this a commitment or just a task?",
        )
        analysis.is_confident = False  # Override
        panel = format_triage_item(draft, analysis=analysis)
        content = render_to_string(panel)
        assert "commitment or just a task" in content

    def test_shows_action_options(self):
        """Panel shows action options."""
        draft = make_mock_draft()
        analysis = make_mock_analysis()
        panel = format_triage_item(draft, analysis=analysis)
        content = render_to_string(panel)
        # Should show some options
        assert "Accept" in content or "y" in content


class TestFormatTriageSummary:
    """Tests for triage summary panel formatting."""

    def test_returns_panel(self):
        """Summary returns a Panel."""
        panel = format_triage_summary(5, 5, {"commitment": 3, "task": 2})
        assert isinstance(panel, Panel)

    def test_shows_complete_message(self):
        """Summary shows completion message."""
        panel = format_triage_summary(5, 5, {})
        content = render_to_string(panel)
        assert "Complete" in content

    def test_shows_processed_count(self):
        """Summary shows processed count."""
        panel = format_triage_summary(3, 5, {})
        content = render_to_string(panel)
        assert "3" in content
        assert "5" in content

    def test_shows_created_entities(self):
        """Summary shows created entity counts."""
        panel = format_triage_summary(5, 5, {"commitment": 2, "goal": 1})
        content = render_to_string(panel)
        assert "2" in content
        assert "commitment" in content.lower()
        assert "1" in content
        assert "goal" in content.lower()

    def test_shows_no_items_created_when_empty(self):
        """Summary shows 'No items created' when dict is empty."""
        panel = format_triage_summary(5, 5, {})
        content = render_to_string(panel)
        assert "No items created" in content


class TestFormatTriageItemPlain:
    """Tests for plain text triage item formatting."""

    def test_returns_string(self):
        """Plain format returns string."""
        draft = make_mock_draft()
        result = format_triage_item_plain(draft)
        assert isinstance(result, str)

    def test_contains_original_text(self):
        """Plain format contains original text."""
        draft = make_mock_draft("Send report to boss")
        result = format_triage_item_plain(draft)
        assert "Send report to boss" in result

    def test_contains_analysis_when_provided(self):
        """Plain format contains analysis details."""
        draft = make_mock_draft()
        analysis = make_mock_analysis(
            suggested_type="commitment",
            confidence=0.95,
            reasoning="Has deliverable and deadline",
        )
        result = format_triage_item_plain(draft, analysis)
        assert "commitment" in result
        assert "95%" in result
        assert "deliverable" in result

    def test_contains_question_when_present(self):
        """Plain format contains clarifying question."""
        draft = make_mock_draft()
        analysis = make_mock_analysis(
            confidence=0.50,
            question="What type is this?",
        )
        result = format_triage_item_plain(draft, analysis)
        assert "What type is this?" in result


class TestFormatTriageQueueStatus:
    """Tests for triage queue status formatting."""

    def test_zero_items(self):
        """Zero items returns 'No items to triage'."""
        result = format_triage_queue_status(0)
        assert "No items" in result

    def test_one_item(self):
        """One item returns singular message."""
        result = format_triage_queue_status(1)
        assert "1 item" in result
        assert "items" not in result  # Should be singular

    def test_multiple_items(self):
        """Multiple items returns plural message."""
        result = format_triage_queue_status(5)
        assert "5 items" in result


class TestEntityTypeColorsConstant:
    """Tests for ENTITY_TYPE_COLORS constant."""

    def test_all_entity_types_have_colors(self):
        """All expected entity types have colors defined."""
        expected_types = ["commitment", "goal", "task", "vision", "milestone", "unknown"]
        for entity_type in expected_types:
            assert entity_type in ENTITY_TYPE_COLORS
