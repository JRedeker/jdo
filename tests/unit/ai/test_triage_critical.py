"""Tests for AI triage functionality."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from jdo.ai.triage import (
    CONFIDENCE_THRESHOLD,
    ClarifyingQuestion,
    TriageAnalysis,
    TriageClassification,
    classify_triage_item,
)


class TestTriageClassification:
    """Tests for TriageClassification model."""

    def test_classification_creation(self) -> None:
        """TriageClassification can be created with required fields."""
        classification = TriageClassification(
            suggested_type="commitment",
            confidence=0.9,
            reasoning="Test reasoning",
        )

        assert classification.suggested_type == "commitment"
        assert classification.confidence == 0.9
        assert classification.reasoning == "Test reasoning"
        assert classification.detected_stakeholder is None
        assert classification.detected_date is None

    def test_classification_with_optional_fields(self) -> None:
        """TriageClassification accepts optional fields."""
        classification = TriageClassification(
            suggested_type="goal",
            confidence=0.75,
            reasoning="Test reasoning",
            detected_stakeholder="Alice",
            detected_date="2024-01-15",
        )

        assert classification.detected_stakeholder == "Alice"
        assert classification.detected_date == "2024-01-15"

    def test_confidence_bounds(self) -> None:
        """TriageClassification enforces confidence bounds."""
        with pytest.raises(ValidationError):
            TriageClassification(
                suggested_type="task",
                confidence=1.5,
                reasoning="Invalid confidence",
            )

        with pytest.raises(ValidationError):
            TriageClassification(
                suggested_type="task",
                confidence=-0.1,
                reasoning="Invalid confidence",
            )


class TestClarifyingQuestion:
    """Tests for ClarifyingQuestion model."""

    def test_question_creation(self) -> None:
        """ClarifyingQuestion can be created."""
        question = ClarifyingQuestion(question="What type of item is this?")

        assert question.question == "What type of item is this?"


class TestTriageAnalysis:
    """Tests for TriageAnalysis dataclass."""

    def test_analysis_with_classification(self) -> None:
        """TriageAnalysis with classification has expected properties."""
        classification = TriageClassification(
            suggested_type="commitment",
            confidence=0.85,
            reasoning="Clear commitment detected",
        )
        analysis = TriageAnalysis(
            raw_text="Send report to Sarah by Friday",
            classification=classification,
            question=None,
        )

        assert analysis.raw_text == "Send report to Sarah by Friday"
        assert analysis.classification is classification
        assert analysis.question is None
        assert analysis.is_confident is True
        assert analysis.suggested_entity_type.value == "commitment"

    def test_analysis_with_question(self) -> None:
        """TriageAnalysis with question has expected properties."""
        question = ClarifyingQuestion(question="I'm not sure. Is this a commitment or a task?")
        analysis = TriageAnalysis(
            raw_text="Do the thing",
            classification=None,
            question=question,
        )

        assert analysis.is_confident is False
        assert analysis.suggested_entity_type is None

    def test_is_confident_threshold(self) -> None:
        """is_confident respects confidence threshold."""
        high_conf = TriageClassification(
            suggested_type="task",
            confidence=0.8,
            reasoning="Clear task",
        )
        low_conf = TriageClassification(
            suggested_type="task",
            confidence=0.6,
            reasoning="Unclear",
        )

        high_analysis = TriageAnalysis(
            raw_text="Task",
            classification=high_conf,
            question=None,
        )
        low_analysis = TriageAnalysis(
            raw_text="Task",
            classification=low_conf,
            question=None,
        )

        assert high_analysis.is_confident is True
        assert low_analysis.is_confident is False


class TestClassifyTriageItem:
    """Tests for classify_triage_item function."""

    def test_returns_triage_analysis(self) -> None:
        """classify_triage_item returns TriageAnalysis."""
        with patch("jdo.ai.triage._get_triage_agent") as mock_agent:
            mock_agent.return_value.run_sync.return_value.output = TriageClassification(
                suggested_type="commitment",
                confidence=0.9,
                reasoning="Clear commitment",
            )

            result = classify_triage_item("I need to send the report by Friday")

            assert isinstance(result, TriageAnalysis)
            assert result.raw_text == "I need to send the report by Friday"

    def test_handles_clarifying_question(self) -> None:
        """classify_triage_item handles clarifying question output."""
        with patch("jdo.ai.triage._get_triage_agent") as mock_agent:
            mock_agent.return_value.run_sync.return_value.output = ClarifyingQuestion(
                question="Could you clarify what type of item this is?"
            )

            result = classify_triage_item("Help me with something")

            assert isinstance(result, TriageAnalysis)
            assert result.question is not None


class TestConfidenceThreshold:
    """Tests for CONFIDENCE_THRESHOLD constant."""

    def test_threshold_value(self) -> None:
        """CONFIDENCE_THRESHOLD is 0.7."""
        assert CONFIDENCE_THRESHOLD == 0.7
