"""Tests for Vision and Milestone AI extraction.

Phase 10.5/10.6: Vision/Milestone AI Prompts for extraction and suggestions.
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch


class TestVisionExtraction:
    """Tests for extracting vision fields from conversation."""

    def test_extracted_vision_has_title(self) -> None:
        """Extracted vision includes title field."""
        from jdo.ai.extraction import ExtractedVision

        vision = ExtractedVision(
            title="Transform customer experience",
            narrative="A world where every customer interaction delights and inspires",
            timeframe="5 years",
        )

        assert vision.title == "Transform customer experience"

    def test_extracted_vision_has_narrative(self) -> None:
        """Extracted vision includes narrative field (vivid description)."""
        from jdo.ai.extraction import ExtractedVision

        vision = ExtractedVision(
            title="Transform customer experience",
            narrative="A world where every customer interaction delights and inspires",
            timeframe="5 years",
        )

        assert "delights" in vision.narrative

    def test_extracted_vision_has_timeframe(self) -> None:
        """Extracted vision includes timeframe field."""
        from jdo.ai.extraction import ExtractedVision

        vision = ExtractedVision(
            title="Transform customer experience",
            narrative="A world where every customer interaction delights",
            timeframe="5 years",
        )

        assert vision.timeframe == "5 years"

    def test_extracted_vision_has_optional_metrics(self) -> None:
        """Extracted vision can include suggested metrics."""
        from jdo.ai.extraction import ExtractedVision

        vision = ExtractedVision(
            title="Transform customer experience",
            narrative="A world where every customer interaction delights",
            metrics=["NPS score > 70", "Customer retention > 95%"],
        )

        assert len(vision.metrics) == 2
        assert "NPS score > 70" in vision.metrics

    def test_extracted_vision_metrics_defaults_empty(self) -> None:
        """Extracted vision metrics defaults to empty list."""
        from jdo.ai.extraction import ExtractedVision

        vision = ExtractedVision(
            title="Transform customer experience",
            narrative="A world where every customer interaction delights",
        )

        assert vision.metrics == []

    def test_extracted_vision_has_optional_why_it_matters(self) -> None:
        """Extracted vision can include why_it_matters field."""
        from jdo.ai.extraction import ExtractedVision

        vision = ExtractedVision(
            title="Transform customer experience",
            narrative="A world where every customer interaction delights",
            why_it_matters="Happy customers drive sustainable growth",
        )

        assert vision.why_it_matters == "Happy customers drive sustainable growth"


class TestMilestoneExtraction:
    """Tests for extracting milestone fields from conversation."""

    def test_extracted_milestone_has_title(self) -> None:
        """Extracted milestone includes title field."""
        from jdo.ai.extraction import ExtractedMilestone

        milestone = ExtractedMilestone(
            title="Launch beta version",
            description="First public release with core features",
            target_date=date(2025, 3, 15),
        )

        assert milestone.title == "Launch beta version"

    def test_extracted_milestone_has_target_date(self) -> None:
        """Extracted milestone includes target_date field."""
        from jdo.ai.extraction import ExtractedMilestone

        milestone = ExtractedMilestone(
            title="Launch beta version",
            target_date=date(2025, 3, 15),
        )

        assert milestone.target_date == date(2025, 3, 15)

    def test_extracted_milestone_has_optional_description(self) -> None:
        """Extracted milestone can include description field."""
        from jdo.ai.extraction import ExtractedMilestone

        milestone = ExtractedMilestone(
            title="Launch beta version",
            description="First public release with core features",
            target_date=date(2025, 3, 15),
        )

        assert milestone.description == "First public release with core features"


class TestVisionExtractionAgent:
    """Tests for the vision extraction agent."""

    async def test_extract_vision_returns_structured_data(self) -> None:
        """extract_vision returns ExtractedVision from conversation."""
        from jdo.ai.extraction import ExtractedVision, extract_vision

        conversation = [
            {
                "role": "user",
                "content": "I want to build a company where every engineer feels empowered",
            },
        ]

        with patch("jdo.ai.extraction.create_extraction_agent") as mock_create:
            mock_agent = MagicMock()
            mock_result = MagicMock()
            mock_result.output = ExtractedVision(
                title="Engineer empowerment",
                narrative="A company where every engineer feels empowered to do their best work",
                timeframe="3 years",
            )
            mock_agent.run = AsyncMock(return_value=mock_result)
            mock_create.return_value = mock_agent

            result = await extract_vision(conversation)

            assert isinstance(result, ExtractedVision)
            assert result.title == "Engineer empowerment"

    async def test_extract_milestone_returns_structured_data(self) -> None:
        """extract_milestone returns ExtractedMilestone from conversation."""
        from jdo.ai.extraction import ExtractedMilestone, extract_milestone

        conversation = [
            {"role": "user", "content": "We need to launch beta by March 15th"},
        ]

        with patch("jdo.ai.extraction.create_extraction_agent") as mock_create:
            mock_agent = MagicMock()
            mock_result = MagicMock()
            mock_result.output = ExtractedMilestone(
                title="Beta launch",
                description="Launch beta version to early adopters",
                target_date=date(2025, 3, 15),
            )
            mock_agent.run = AsyncMock(return_value=mock_result)
            mock_create.return_value = mock_agent

            result = await extract_milestone(conversation)

            assert isinstance(result, ExtractedMilestone)
            assert result.title == "Beta launch"


class TestSuggestionPrompts:
    """Tests for AI-powered suggestions."""

    def test_vision_extraction_prompt_exists(self) -> None:
        """VISION_EXTRACTION_PROMPT is defined."""
        from jdo.ai.extraction import VISION_EXTRACTION_PROMPT

        assert "narrative" in VISION_EXTRACTION_PROMPT.lower()
        assert "vivid" in VISION_EXTRACTION_PROMPT.lower()

    def test_milestone_extraction_prompt_exists(self) -> None:
        """MILESTONE_EXTRACTION_PROMPT is defined."""
        from jdo.ai.extraction import MILESTONE_EXTRACTION_PROMPT

        assert "target_date" in MILESTONE_EXTRACTION_PROMPT.lower()

    def test_suggest_metrics_prompt_exists(self) -> None:
        """SUGGEST_METRICS_PROMPT is defined for suggesting vision metrics."""
        from jdo.ai.extraction import SUGGEST_METRICS_PROMPT

        assert "metrics" in SUGGEST_METRICS_PROMPT.lower()

    def test_suggest_milestones_prompt_exists(self) -> None:
        """SUGGEST_MILESTONES_PROMPT is defined for suggesting goal milestones."""
        from jdo.ai.extraction import SUGGEST_MILESTONES_PROMPT

        assert "milestone" in SUGGEST_MILESTONES_PROMPT.lower()


class TestLinkagePrompts:
    """Tests for vision/milestone linkage prompts."""

    def test_vision_linkage_prompt_exists(self) -> None:
        """VISION_LINKAGE_PROMPT is defined for prompting vision selection."""
        from jdo.ai.extraction import VISION_LINKAGE_PROMPT

        assert "vision" in VISION_LINKAGE_PROMPT.lower()
        assert "goal" in VISION_LINKAGE_PROMPT.lower()

    def test_milestone_linkage_prompt_exists(self) -> None:
        """MILESTONE_LINKAGE_PROMPT is defined for prompting milestone selection."""
        from jdo.ai.extraction import MILESTONE_LINKAGE_PROMPT

        assert "milestone" in MILESTONE_LINKAGE_PROMPT.lower()
        assert "commitment" in MILESTONE_LINKAGE_PROMPT.lower()


class TestMissingVisionMilestoneFields:
    """Tests for detecting missing required fields in vision/milestone."""

    def test_vision_missing_fields_returns_list(self) -> None:
        """get_missing_fields works for visions."""
        from jdo.ai.extraction import ExtractedVision, get_missing_fields

        partial = {"title": "Transform customer experience"}

        missing = get_missing_fields(partial, ExtractedVision)

        assert "narrative" in missing

    def test_vision_all_fields_returns_empty(self) -> None:
        """get_missing_fields returns empty when all vision fields present."""
        from jdo.ai.extraction import ExtractedVision, get_missing_fields

        complete = {
            "title": "Transform customer experience",
            "narrative": "A world where every customer interaction delights",
        }

        missing = get_missing_fields(complete, ExtractedVision)

        assert missing == []

    def test_milestone_missing_fields_returns_list(self) -> None:
        """get_missing_fields works for milestones."""
        from jdo.ai.extraction import ExtractedMilestone, get_missing_fields

        partial = {"title": "Launch beta"}

        missing = get_missing_fields(partial, ExtractedMilestone)

        assert "target_date" in missing

    def test_milestone_all_fields_returns_empty(self) -> None:
        """get_missing_fields returns empty when all milestone fields present."""
        from jdo.ai.extraction import ExtractedMilestone, get_missing_fields

        complete = {
            "title": "Launch beta",
            "target_date": date(2025, 3, 15),
        }

        missing = get_missing_fields(complete, ExtractedMilestone)

        assert missing == []
