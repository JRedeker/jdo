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


class TestRecurringCommitmentExtraction:
    """Tests for extracting recurring commitment fields from conversation."""

    def test_extracted_recurring_has_deliverable_template(self) -> None:
        """Extracted recurring commitment includes deliverable_template field."""
        from jdo.ai.extraction import ExtractedRecurringCommitment

        recurring = ExtractedRecurringCommitment(
            deliverable_template="Weekly status report",
            stakeholder_name="Manager",
            recurrence_type="weekly",
            days_of_week=[0],  # Monday
        )

        assert recurring.deliverable_template == "Weekly status report"

    def test_extracted_recurring_has_stakeholder_name(self) -> None:
        """Extracted recurring commitment includes stakeholder_name field."""
        from jdo.ai.extraction import ExtractedRecurringCommitment

        recurring = ExtractedRecurringCommitment(
            deliverable_template="Weekly status report",
            stakeholder_name="Manager",
            recurrence_type="weekly",
            days_of_week=[0],
        )

        assert recurring.stakeholder_name == "Manager"

    def test_extracted_recurring_has_recurrence_type(self) -> None:
        """Extracted recurring commitment includes recurrence_type field."""
        from jdo.ai.extraction import ExtractedRecurringCommitment

        recurring = ExtractedRecurringCommitment(
            deliverable_template="Daily standup",
            stakeholder_name="Team",
            recurrence_type="daily",
        )

        assert recurring.recurrence_type == "daily"

    def test_extracted_recurring_weekly_has_days_of_week(self) -> None:
        """Weekly recurring can specify days_of_week."""
        from jdo.ai.extraction import ExtractedRecurringCommitment

        recurring = ExtractedRecurringCommitment(
            deliverable_template="Team sync",
            stakeholder_name="Team",
            recurrence_type="weekly",
            days_of_week=[0, 2, 4],  # Mon, Wed, Fri
        )

        assert recurring.days_of_week == [0, 2, 4]

    def test_extracted_recurring_monthly_has_day_of_month(self) -> None:
        """Monthly recurring can specify day_of_month."""
        from jdo.ai.extraction import ExtractedRecurringCommitment

        recurring = ExtractedRecurringCommitment(
            deliverable_template="Monthly report",
            stakeholder_name="Finance",
            recurrence_type="monthly",
            day_of_month=15,
        )

        assert recurring.day_of_month == 15

    def test_extracted_recurring_monthly_has_week_of_month(self) -> None:
        """Monthly recurring can specify week_of_month pattern."""
        from jdo.ai.extraction import ExtractedRecurringCommitment

        recurring = ExtractedRecurringCommitment(
            deliverable_template="Monthly report",
            stakeholder_name="Finance",
            recurrence_type="monthly",
            week_of_month=2,  # 2nd week
            days_of_week=[1],  # Tuesday
        )

        assert recurring.week_of_month == 2
        assert recurring.days_of_week == [1]

    def test_extracted_recurring_yearly_has_month_of_year(self) -> None:
        """Yearly recurring can specify month_of_year."""
        from jdo.ai.extraction import ExtractedRecurringCommitment

        recurring = ExtractedRecurringCommitment(
            deliverable_template="Annual review",
            stakeholder_name="HR",
            recurrence_type="yearly",
            month_of_year=12,
            day_of_month=15,
        )

        assert recurring.month_of_year == 12
        assert recurring.day_of_month == 15

    def test_extracted_recurring_has_interval(self) -> None:
        """Extracted recurring can have interval for 'every other' patterns."""
        from jdo.ai.extraction import ExtractedRecurringCommitment

        recurring = ExtractedRecurringCommitment(
            deliverable_template="Bi-weekly report",
            stakeholder_name="Manager",
            recurrence_type="weekly",
            interval=2,
            days_of_week=[0],
        )

        assert recurring.interval == 2

    def test_extracted_recurring_interval_defaults_to_one(self) -> None:
        """Interval defaults to 1 if not specified."""
        from jdo.ai.extraction import ExtractedRecurringCommitment

        recurring = ExtractedRecurringCommitment(
            deliverable_template="Weekly report",
            stakeholder_name="Manager",
            recurrence_type="weekly",
            days_of_week=[0],
        )

        assert recurring.interval == 1

    def test_extracted_recurring_has_optional_due_time(self) -> None:
        """Extracted recurring can include optional due_time."""
        from jdo.ai.extraction import ExtractedRecurringCommitment

        recurring = ExtractedRecurringCommitment(
            deliverable_template="Morning standup",
            stakeholder_name="Team",
            recurrence_type="daily",
            due_time=time(9, 0),
        )

        assert recurring.due_time == time(9, 0)

    async def test_extract_recurring_commitment_returns_structured_data(self) -> None:
        """extract_recurring_commitment returns ExtractedRecurringCommitment from conversation."""
        from jdo.ai.extraction import (
            ExtractedRecurringCommitment,
            extract_recurring_commitment,
        )

        conversation = [
            {
                "role": "user",
                "content": "I need to send a weekly status report to my manager every Monday",
            },
        ]

        # Mock the agent to return a structured recurring commitment
        with patch("jdo.ai.extraction.create_extraction_agent") as mock_create:
            mock_agent = MagicMock()
            mock_result = MagicMock()
            mock_result.output = ExtractedRecurringCommitment(
                deliverable_template="Weekly status report",
                stakeholder_name="Manager",
                recurrence_type="weekly",
                days_of_week=[0],
            )
            mock_agent.run = AsyncMock(return_value=mock_result)
            mock_create.return_value = mock_agent

            result = await extract_recurring_commitment(conversation)

            assert isinstance(result, ExtractedRecurringCommitment)
            assert result.deliverable_template == "Weekly status report"
            assert result.recurrence_type == "weekly"
            assert result.days_of_week == [0]

    def test_recurring_missing_fields_returns_list(self) -> None:
        """get_missing_fields works for recurring commitments too."""
        from jdo.ai.extraction import ExtractedRecurringCommitment, get_missing_fields

        partial = {"deliverable_template": "Weekly report"}

        missing = get_missing_fields(partial, ExtractedRecurringCommitment)

        assert "stakeholder_name" in missing
        assert "recurrence_type" in missing
