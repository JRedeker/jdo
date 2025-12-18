"""Tests for AI triage classification module."""

from unittest.mock import MagicMock, patch

from jdo.ai.triage import (
    CLASSIFIABLE_TYPES,
    CONFIDENCE_THRESHOLD,
    ClarifyingQuestion,
    TriageAnalysis,
    TriageClassification,
    classify_triage_item,
)
from jdo.models.draft import EntityType


class TestTriageClassification:
    """Tests for TriageClassification model."""

    def test_has_required_fields(self):
        """TriageClassification has all required fields."""
        classification = TriageClassification(
            suggested_type="commitment",
            confidence=0.9,
            detected_stakeholder="Sarah",
            detected_date="Friday",
            reasoning="Contains deliverable, stakeholder, and date",
        )

        assert classification.suggested_type == "commitment"
        assert classification.confidence == 0.9
        assert classification.detected_stakeholder == "Sarah"
        assert classification.detected_date == "Friday"
        assert "deliverable" in classification.reasoning

    def test_optional_fields_can_be_none(self):
        """Stakeholder and date are optional."""
        classification = TriageClassification(
            suggested_type="task",
            confidence=0.8,
            reasoning="Simple action item",
        )

        assert classification.detected_stakeholder is None
        assert classification.detected_date is None


class TestClarifyingQuestion:
    """Tests for ClarifyingQuestion model."""

    def test_has_question_field(self):
        """ClarifyingQuestion has question field."""
        question = ClarifyingQuestion(question="Is this a task or a commitment?")
        assert question.question == "Is this a task or a commitment?"


class TestTriageAnalysis:
    """Tests for TriageAnalysis dataclass."""

    def test_is_confident_with_high_confidence(self):
        """is_confident returns True when confidence >= threshold."""
        classification = TriageClassification(
            suggested_type="commitment",
            confidence=0.85,
            reasoning="Clear commitment pattern",
        )
        analysis = TriageAnalysis(
            raw_text="Send report to Sarah by Friday",
            classification=classification,
            question=None,
        )

        assert analysis.is_confident is True

    def test_is_confident_with_low_confidence(self):
        """is_confident returns False when confidence < threshold."""
        classification = TriageClassification(
            suggested_type="task",
            confidence=0.5,
            reasoning="Unclear what this is",
        )
        analysis = TriageAnalysis(
            raw_text="Something to do",
            classification=classification,
            question=ClarifyingQuestion(question="What type is this?"),
        )

        assert analysis.is_confident is False

    def test_is_confident_with_no_classification(self):
        """is_confident returns False when no classification."""
        analysis = TriageAnalysis(
            raw_text="Vague text",
            classification=None,
            question=ClarifyingQuestion(question="What do you mean?"),
        )

        assert analysis.is_confident is False

    def test_suggested_entity_type_returns_enum(self):
        """suggested_entity_type returns EntityType when confident."""
        classification = TriageClassification(
            suggested_type="commitment",
            confidence=0.9,
            reasoning="Clear commitment",
        )
        analysis = TriageAnalysis(
            raw_text="Test",
            classification=classification,
            question=None,
        )

        assert analysis.suggested_entity_type == EntityType.COMMITMENT

    def test_suggested_entity_type_none_when_not_confident(self):
        """suggested_entity_type returns None when not confident."""
        classification = TriageClassification(
            suggested_type="task",
            confidence=0.4,
            reasoning="Not sure",
        )
        analysis = TriageAnalysis(
            raw_text="Test",
            classification=classification,
            question=None,
        )

        assert analysis.suggested_entity_type is None


class TestConstants:
    """Tests for module constants."""

    def test_confidence_threshold_value(self):
        """CONFIDENCE_THRESHOLD is 0.7."""
        assert CONFIDENCE_THRESHOLD == 0.7

    def test_classifiable_types_excludes_unknown(self):
        """CLASSIFIABLE_TYPES excludes UNKNOWN."""
        assert EntityType.UNKNOWN not in CLASSIFIABLE_TYPES

    def test_classifiable_types_includes_all_others(self):
        """CLASSIFIABLE_TYPES includes all standard types."""
        assert EntityType.COMMITMENT in CLASSIFIABLE_TYPES
        assert EntityType.GOAL in CLASSIFIABLE_TYPES
        assert EntityType.TASK in CLASSIFIABLE_TYPES
        assert EntityType.VISION in CLASSIFIABLE_TYPES
        assert EntityType.MILESTONE in CLASSIFIABLE_TYPES


class TestClassifyTriageItem:
    """Tests for classify_triage_item function with mocked AI."""

    def test_returns_confident_classification(self):
        """Returns TriageAnalysis with classification when AI is confident."""
        mock_classification = TriageClassification(
            suggested_type="commitment",
            confidence=0.9,
            detected_stakeholder="Manager",
            detected_date="Monday",
            reasoning="Contains delivery commitment with deadline",
        )

        mock_result = MagicMock()
        mock_result.output = mock_classification

        with (
            patch("jdo.ai.triage._get_triage_agent") as mock_get_agent,
            patch("jdo.ai.triage.get_settings") as mock_settings,
        ):
            mock_settings.return_value.ai_provider = "test"
            mock_settings.return_value.ai_model = "test-model"
            mock_agent = MagicMock()
            mock_agent.run_sync.return_value = mock_result
            mock_get_agent.return_value = mock_agent

            result = classify_triage_item("Send weekly report to manager by Monday")

        assert result.is_confident is True
        assert result.classification is not None
        assert result.classification.suggested_type == "commitment"
        assert result.question is None

    def test_returns_question_when_low_confidence(self):
        """Returns TriageAnalysis with question when AI confidence is low."""
        mock_classification = TriageClassification(
            suggested_type="task",
            confidence=0.4,
            reasoning="Could be task or commitment, unclear",
        )

        mock_result = MagicMock()
        mock_result.output = mock_classification

        with (
            patch("jdo.ai.triage._get_triage_agent") as mock_get_agent,
            patch("jdo.ai.triage.get_settings") as mock_settings,
        ):
            mock_settings.return_value.ai_provider = "test"
            mock_settings.return_value.ai_model = "test-model"
            mock_agent = MagicMock()
            mock_agent.run_sync.return_value = mock_result
            mock_get_agent.return_value = mock_agent

            result = classify_triage_item("Do the thing")

        assert result.is_confident is False
        assert result.classification is not None  # Still available
        assert result.question is not None  # But also has a question

    def test_returns_ai_generated_question(self):
        """Returns AI-generated question when AI returns ClarifyingQuestion."""
        mock_question = ClarifyingQuestion(
            question="Is this something you need to deliver to someone, or a personal goal?"
        )

        mock_result = MagicMock()
        mock_result.output = mock_question

        with (
            patch("jdo.ai.triage._get_triage_agent") as mock_get_agent,
            patch("jdo.ai.triage.get_settings") as mock_settings,
        ):
            mock_settings.return_value.ai_provider = "test"
            mock_settings.return_value.ai_model = "test-model"
            mock_agent = MagicMock()
            mock_agent.run_sync.return_value = mock_result
            mock_get_agent.return_value = mock_agent

            result = classify_triage_item("Improve things")

        assert result.classification is None
        assert result.question is not None
        assert "deliver" in result.question.question
