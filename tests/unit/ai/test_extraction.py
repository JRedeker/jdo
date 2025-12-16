"""Tests for AI field extraction from natural language.

Phase 10.3/10.4: Field Extraction for commitments, goals, and tasks.
"""

from datetime import date, time
from unittest.mock import AsyncMock, MagicMock, patch

from pydantic import BaseModel
from pydantic_ai.models.test import TestModel


class TestCommitmentExtraction:
    """Tests for extracting commitment fields from conversation."""

    def test_extracted_commitment_has_deliverable(self) -> None:
        """Extracted commitment includes deliverable field."""
        from jdo.ai.extraction import ExtractedCommitment

        commitment = ExtractedCommitment(
            deliverable="Send quarterly report",
            stakeholder_name="Finance Team",
            due_date=date(2025, 12, 20),
        )

        assert commitment.deliverable == "Send quarterly report"

    def test_extracted_commitment_has_stakeholder(self) -> None:
        """Extracted commitment includes stakeholder_name field."""
        from jdo.ai.extraction import ExtractedCommitment

        commitment = ExtractedCommitment(
            deliverable="Send report",
            stakeholder_name="Finance Team",
            due_date=date(2025, 12, 20),
        )

        assert commitment.stakeholder_name == "Finance Team"

    def test_extracted_commitment_has_due_date(self) -> None:
        """Extracted commitment includes due_date field."""
        from jdo.ai.extraction import ExtractedCommitment

        commitment = ExtractedCommitment(
            deliverable="Send report",
            stakeholder_name="Finance Team",
            due_date=date(2025, 12, 20),
        )

        assert commitment.due_date == date(2025, 12, 20)

    def test_extracted_commitment_has_optional_due_time(self) -> None:
        """Extracted commitment can include optional due_time."""
        from jdo.ai.extraction import ExtractedCommitment

        commitment = ExtractedCommitment(
            deliverable="Send report",
            stakeholder_name="Finance Team",
            due_date=date(2025, 12, 20),
            due_time=time(15, 0),
        )

        assert commitment.due_time == time(15, 0)

    def test_extracted_commitment_due_time_defaults_none(self) -> None:
        """Extracted commitment due_time defaults to None."""
        from jdo.ai.extraction import ExtractedCommitment

        commitment = ExtractedCommitment(
            deliverable="Send report",
            stakeholder_name="Finance Team",
            due_date=date(2025, 12, 20),
        )

        assert commitment.due_time is None


class TestGoalExtraction:
    """Tests for extracting goal fields from conversation."""

    def test_extracted_goal_has_title(self) -> None:
        """Extracted goal includes title field."""
        from jdo.ai.extraction import ExtractedGoal

        goal = ExtractedGoal(
            title="Improve customer satisfaction",
            problem_statement="Customer complaints are increasing",
            solution_vision="Happy customers who recommend us",
        )

        assert goal.title == "Improve customer satisfaction"

    def test_extracted_goal_has_problem_statement(self) -> None:
        """Extracted goal includes problem_statement field."""
        from jdo.ai.extraction import ExtractedGoal

        goal = ExtractedGoal(
            title="Improve customer satisfaction",
            problem_statement="Customer complaints are increasing",
            solution_vision="Happy customers who recommend us",
        )

        assert goal.problem_statement == "Customer complaints are increasing"

    def test_extracted_goal_has_solution_vision(self) -> None:
        """Extracted goal includes solution_vision field."""
        from jdo.ai.extraction import ExtractedGoal

        goal = ExtractedGoal(
            title="Improve customer satisfaction",
            problem_statement="Customer complaints are increasing",
            solution_vision="Happy customers who recommend us",
        )

        assert goal.solution_vision == "Happy customers who recommend us"


class TestTaskExtraction:
    """Tests for extracting task fields from conversation."""

    def test_extracted_task_has_title(self) -> None:
        """Extracted task includes title field."""
        from jdo.ai.extraction import ExtractedTask

        task = ExtractedTask(
            title="Draft the report outline",
            scope="Create initial structure with main sections",
        )

        assert task.title == "Draft the report outline"

    def test_extracted_task_has_scope(self) -> None:
        """Extracted task includes scope field."""
        from jdo.ai.extraction import ExtractedTask

        task = ExtractedTask(
            title="Draft the report outline",
            scope="Create initial structure with main sections",
        )

        assert task.scope == "Create initial structure with main sections"


class TestExtractionAgent:
    """Tests for the extraction agent that uses AI to extract fields."""

    def test_create_extraction_agent_returns_agent(self) -> None:
        """create_extraction_agent returns a PydanticAI agent."""
        from pydantic_ai import Agent

        from jdo.ai.extraction import ExtractedCommitment, create_extraction_agent

        agent = create_extraction_agent(
            TestModel(),
            ExtractedCommitment,
            "Extract commitment details",
        )

        assert isinstance(agent, Agent)

    async def test_extract_commitment_returns_structured_data(self) -> None:
        """extract_commitment returns ExtractedCommitment from conversation."""
        from jdo.ai.extraction import ExtractedCommitment, extract_commitment

        conversation = [
            {
                "role": "user",
                "content": "I need to send the quarterly report to finance by Friday 3pm",
            },
        ]

        # Mock the agent to return a structured commitment
        with patch("jdo.ai.extraction.create_extraction_agent") as mock_create:
            mock_agent = MagicMock()
            mock_result = MagicMock()
            mock_result.output = ExtractedCommitment(
                deliverable="Send quarterly report",
                stakeholder_name="Finance",
                due_date=date(2025, 12, 20),
                due_time=time(15, 0),
            )
            mock_agent.run = AsyncMock(return_value=mock_result)
            mock_create.return_value = mock_agent

            result = await extract_commitment(conversation)

            assert isinstance(result, ExtractedCommitment)
            assert result.deliverable == "Send quarterly report"

    async def test_extract_goal_returns_structured_data(self) -> None:
        """extract_goal returns ExtractedGoal from conversation."""
        from jdo.ai.extraction import ExtractedGoal, extract_goal

        conversation = [
            {"role": "user", "content": "I want to improve our customer satisfaction scores"},
        ]

        with patch("jdo.ai.extraction.create_extraction_agent") as mock_create:
            mock_agent = MagicMock()
            mock_result = MagicMock()
            mock_result.output = ExtractedGoal(
                title="Improve customer satisfaction",
                problem_statement="Scores are low",
                solution_vision="High satisfaction scores",
            )
            mock_agent.run = AsyncMock(return_value=mock_result)
            mock_create.return_value = mock_agent

            result = await extract_goal(conversation)

            assert isinstance(result, ExtractedGoal)
            assert result.title == "Improve customer satisfaction"


class TestMissingFieldDetection:
    """Tests for detecting missing required fields."""

    def test_commitment_missing_fields_returns_list(self) -> None:
        """get_missing_fields returns list of missing field names."""
        from jdo.ai.extraction import ExtractedCommitment, get_missing_fields

        # Partial commitment with missing stakeholder
        partial = {"deliverable": "Send report", "due_date": "2025-12-20"}

        missing = get_missing_fields(partial, ExtractedCommitment)

        assert "stakeholder_name" in missing

    def test_commitment_all_fields_returns_empty(self) -> None:
        """get_missing_fields returns empty list when all required fields present."""
        from jdo.ai.extraction import ExtractedCommitment, get_missing_fields

        complete = {
            "deliverable": "Send report",
            "stakeholder_name": "Finance",
            "due_date": "2025-12-20",
        }

        missing = get_missing_fields(complete, ExtractedCommitment)

        assert missing == []

    def test_goal_missing_fields_returns_list(self) -> None:
        """get_missing_fields works for goals too."""
        from jdo.ai.extraction import ExtractedGoal, get_missing_fields

        partial = {"title": "Improve satisfaction"}

        missing = get_missing_fields(partial, ExtractedGoal)

        assert "problem_statement" in missing
        assert "solution_vision" in missing
