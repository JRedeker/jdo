"""Tests for PersistenceService.

Tests entity creation from draft data with mock session.
"""

from __future__ import annotations

from datetime import date, time
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from jdo.db.persistence import PersistenceService, ValidationError
from jdo.models import (
    Commitment,
    Goal,
    Milestone,
    RecurringCommitment,
    Stakeholder,
    StakeholderType,
    Task,
    Vision,
)
from jdo.models.recurring_commitment import RecurrenceType


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock database session."""
    session = MagicMock()
    session.exec.return_value.first.return_value = None  # No existing entities
    session.exec.return_value.one.return_value = 0  # Zero count for tasks
    return session


@pytest.fixture
def service(mock_session: MagicMock) -> PersistenceService:
    """Create PersistenceService with mock session."""
    return PersistenceService(mock_session)


class TestGetOrCreateStakeholder:
    """Tests for get_or_create_stakeholder method."""

    def test_creates_new_stakeholder_when_not_found(
        self, service: PersistenceService, mock_session: MagicMock
    ) -> None:
        """New stakeholder is created when name not found."""
        # Mock no existing stakeholder
        mock_session.exec.return_value.first.return_value = None

        stakeholder = service.get_or_create_stakeholder("Sarah")

        assert stakeholder.name == "Sarah"
        assert stakeholder.type == StakeholderType.PERSON
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    def test_returns_existing_stakeholder(
        self, service: PersistenceService, mock_session: MagicMock
    ) -> None:
        """Existing stakeholder is returned when found."""
        existing = Stakeholder(name="Sarah", type=StakeholderType.PERSON)
        mock_session.exec.return_value.first.return_value = existing

        result = service.get_or_create_stakeholder("Sarah")

        assert result is existing
        # Should not add new entity
        mock_session.add.assert_not_called()

    def test_case_insensitive_matching(
        self, service: PersistenceService, mock_session: MagicMock
    ) -> None:
        """Matching is case-insensitive."""
        existing = Stakeholder(name="SARAH", type=StakeholderType.PERSON)
        mock_session.exec.return_value.first.return_value = existing

        result = service.get_or_create_stakeholder("sarah")

        assert result is existing
        mock_session.add.assert_not_called()

    def test_raises_for_empty_name(self, service: PersistenceService) -> None:
        """ValidationError is raised for empty name."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            service.get_or_create_stakeholder("")

    def test_raises_for_whitespace_name(self, service: PersistenceService) -> None:
        """ValidationError is raised for whitespace-only name."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            service.get_or_create_stakeholder("   ")

    def test_trims_whitespace(self, service: PersistenceService, mock_session: MagicMock) -> None:
        """Whitespace is trimmed from name."""
        mock_session.exec.return_value.first.return_value = None

        stakeholder = service.get_or_create_stakeholder("  Sarah  ")

        assert stakeholder.name == "Sarah"


class TestSaveCommitment:
    """Tests for save_commitment method."""

    def test_saves_commitment_with_required_fields(
        self, service: PersistenceService, mock_session: MagicMock
    ) -> None:
        """Commitment is saved with required fields."""
        mock_session.exec.return_value.first.return_value = None

        draft_data = {
            "deliverable": "Send quarterly report",
            "stakeholder": "Finance",
            "due_date": date(2025, 12, 20),
        }

        commitment = service.save_commitment(draft_data)

        assert commitment.deliverable == "Send quarterly report"
        assert commitment.due_date == date(2025, 12, 20)
        assert commitment.due_time == time(9, 0)  # Default
        mock_session.add.assert_called()
        mock_session.flush.assert_called()

    def test_saves_commitment_with_optional_fields(
        self, service: PersistenceService, mock_session: MagicMock
    ) -> None:
        """Commitment is saved with optional fields."""
        mock_session.exec.return_value.first.return_value = None
        goal_id = uuid4()
        milestone_id = uuid4()

        draft_data = {
            "deliverable": "Send quarterly report",
            "stakeholder": "Finance",
            "due_date": "2025-12-20",
            "due_time": time(15, 0),
            "goal_id": goal_id,
            "milestone_id": milestone_id,
        }

        commitment = service.save_commitment(draft_data)

        assert commitment.due_time == time(15, 0)
        assert commitment.goal_id == goal_id
        assert commitment.milestone_id == milestone_id

    def test_parses_date_string(self, service: PersistenceService, mock_session: MagicMock) -> None:
        """Date string is parsed correctly."""
        mock_session.exec.return_value.first.return_value = None

        draft_data = {
            "deliverable": "Test",
            "stakeholder": "Test",
            "due_date": "2025-12-20",
        }

        commitment = service.save_commitment(draft_data)

        assert commitment.due_date == date(2025, 12, 20)

    def test_raises_for_invalid_due_time(self, service: PersistenceService) -> None:
        """Invalid due_time raises ValidationError."""
        draft_data = {
            "deliverable": "Test",
            "stakeholder": "Test",
            "due_date": "2025-12-20",
            "due_time": "not-a-time",
        }

        with pytest.raises(ValidationError, match="Invalid time format"):
            service.save_commitment(draft_data)

    def test_raises_for_missing_deliverable(self, service: PersistenceService) -> None:
        """ValidationError is raised for missing deliverable."""
        draft_data = {
            "stakeholder": "Finance",
            "due_date": date(2025, 12, 20),
        }

        with pytest.raises(ValidationError, match="deliverable"):
            service.save_commitment(draft_data)

    def test_raises_for_missing_stakeholder(self, service: PersistenceService) -> None:
        """ValidationError is raised for missing stakeholder."""
        draft_data = {
            "deliverable": "Test",
            "due_date": date(2025, 12, 20),
        }

        with pytest.raises(ValidationError, match="stakeholder"):
            service.save_commitment(draft_data)

    def test_raises_for_missing_due_date(self, service: PersistenceService) -> None:
        """ValidationError is raised for missing due_date."""
        draft_data = {
            "deliverable": "Test",
            "stakeholder": "Test",
        }

        with pytest.raises(ValidationError, match="due_date"):
            service.save_commitment(draft_data)


class TestSaveGoal:
    """Tests for save_goal method."""

    def test_saves_goal_with_required_fields(
        self, service: PersistenceService, mock_session: MagicMock
    ) -> None:
        """Goal is saved with required fields."""
        draft_data = {
            "title": "Improve productivity",
            "problem_statement": "Team is slow",
            "solution_vision": "Fast and efficient team",
        }

        goal = service.save_goal(draft_data)

        assert goal.title == "Improve productivity"
        assert goal.problem_statement == "Team is slow"
        assert goal.solution_vision == "Fast and efficient team"
        mock_session.add.assert_called_once()

    def test_saves_goal_with_optional_fields(
        self, service: PersistenceService, mock_session: MagicMock
    ) -> None:
        """Goal is saved with optional fields."""
        vision_id = uuid4()

        draft_data = {
            "title": "Improve productivity",
            "problem_statement": "Team is slow",
            "solution_vision": "Fast team",
            "motivation": "Better outcomes",
            "vision_id": vision_id,
        }

        goal = service.save_goal(draft_data)

        assert goal.motivation == "Better outcomes"
        assert goal.vision_id == vision_id

    def test_raises_for_missing_title(self, service: PersistenceService) -> None:
        """ValidationError is raised for missing title."""
        draft_data = {
            "problem_statement": "Test",
            "solution_vision": "Test",
        }

        with pytest.raises(ValidationError, match="title"):
            service.save_goal(draft_data)


class TestSaveTask:
    """Tests for save_task method."""

    def test_saves_task_with_required_fields(
        self, service: PersistenceService, mock_session: MagicMock
    ) -> None:
        """Task is saved with required fields."""
        commitment_id = uuid4()
        mock_session.exec.return_value.one.return_value = 0

        draft_data = {
            "title": "Gather data",
            "commitment_id": commitment_id,
        }

        task = service.save_task(draft_data)

        assert task.title == "Gather data"
        assert task.scope == "Gather data"  # Defaults to title
        assert task.commitment_id == commitment_id
        assert task.order == 0

    def test_saves_task_with_scope(
        self, service: PersistenceService, mock_session: MagicMock
    ) -> None:
        """Task is saved with custom scope."""
        commitment_id = uuid4()
        mock_session.exec.return_value.one.return_value = 0

        draft_data = {
            "title": "Gather data",
            "scope": "Collect all Q4 metrics from analytics",
            "commitment_id": commitment_id,
        }

        task = service.save_task(draft_data)

        assert task.scope == "Collect all Q4 metrics from analytics"

    def test_auto_increments_order(
        self, service: PersistenceService, mock_session: MagicMock
    ) -> None:
        """Order is auto-incremented based on existing tasks."""
        commitment_id = uuid4()
        mock_session.exec.return_value.one.return_value = 3  # 3 existing tasks

        draft_data = {
            "title": "New task",
            "commitment_id": commitment_id,
        }

        task = service.save_task(draft_data)

        assert task.order == 3

    def test_raises_for_missing_commitment_id(self, service: PersistenceService) -> None:
        """ValidationError is raised for missing commitment_id."""
        draft_data = {
            "title": "Test",
        }

        with pytest.raises(ValidationError, match="commitment_id"):
            service.save_task(draft_data)


class TestSaveMilestone:
    """Tests for save_milestone method."""

    def test_saves_milestone_with_required_fields(
        self, service: PersistenceService, mock_session: MagicMock
    ) -> None:
        """Milestone is saved with required fields."""
        goal_id = uuid4()

        draft_data = {
            "title": "Phase 1 Complete",
            "goal_id": goal_id,
            "target_date": date(2025, 12, 31),
        }

        milestone = service.save_milestone(draft_data)

        assert milestone.title == "Phase 1 Complete"
        assert milestone.goal_id == goal_id
        assert milestone.target_date == date(2025, 12, 31)

    def test_saves_milestone_with_description(
        self, service: PersistenceService, mock_session: MagicMock
    ) -> None:
        """Milestone is saved with description."""
        goal_id = uuid4()

        draft_data = {
            "title": "Phase 1 Complete",
            "goal_id": goal_id,
            "target_date": date(2025, 12, 31),
            "description": "All core features implemented",
        }

        milestone = service.save_milestone(draft_data)

        assert milestone.description == "All core features implemented"

    def test_raises_for_missing_goal_id(self, service: PersistenceService) -> None:
        """ValidationError is raised for missing goal_id."""
        draft_data = {
            "title": "Test",
            "target_date": date(2025, 12, 31),
        }

        with pytest.raises(ValidationError, match="goal_id"):
            service.save_milestone(draft_data)


class TestSaveVision:
    """Tests for save_vision method."""

    def test_saves_vision_with_required_fields(
        self, service: PersistenceService, mock_session: MagicMock
    ) -> None:
        """Vision is saved with required fields."""
        draft_data = {
            "title": "2026 Company Vision",
            "narrative": "We will be the market leader in our space",
        }

        vision = service.save_vision(draft_data)

        assert vision.title == "2026 Company Vision"
        assert vision.narrative == "We will be the market leader in our space"

    def test_saves_vision_with_optional_fields(
        self, service: PersistenceService, mock_session: MagicMock
    ) -> None:
        """Vision is saved with optional fields."""
        draft_data = {
            "title": "2026 Vision",
            "narrative": "Market leader",
            "timeframe": "3-5 years",
            "metrics": ["Revenue $10M", "100 customers"],
            "why_it_matters": "Growth and impact",
        }

        vision = service.save_vision(draft_data)

        assert vision.timeframe == "3-5 years"
        assert vision.metrics == ["Revenue $10M", "100 customers"]
        assert vision.why_it_matters == "Growth and impact"

    def test_raises_for_missing_narrative(self, service: PersistenceService) -> None:
        """ValidationError is raised for missing narrative."""
        draft_data = {
            "title": "Test",
        }

        with pytest.raises(ValidationError, match="narrative"):
            service.save_vision(draft_data)


class TestSaveRecurringCommitment:
    """Tests for save_recurring_commitment method."""

    def test_saves_weekly_recurring(
        self, service: PersistenceService, mock_session: MagicMock
    ) -> None:
        """Weekly recurring commitment is saved."""
        mock_session.exec.return_value.first.return_value = None

        draft_data = {
            "deliverable_template": "Weekly status report",
            "stakeholder_name": "Manager",
            "recurrence_type": "weekly",
            "days_of_week": [0, 4],  # Monday, Friday
        }

        recurring = service.save_recurring_commitment(draft_data)

        assert recurring.deliverable_template == "Weekly status report"
        assert recurring.recurrence_type == RecurrenceType.WEEKLY
        assert recurring.days_of_week == [0, 4]

    def test_saves_monthly_recurring(
        self, service: PersistenceService, mock_session: MagicMock
    ) -> None:
        """Monthly recurring commitment is saved."""
        mock_session.exec.return_value.first.return_value = None

        draft_data = {
            "deliverable_template": "Monthly report",
            "stakeholder_name": "Team",
            "recurrence_type": "monthly",
            "day_of_month": 1,
        }

        recurring = service.save_recurring_commitment(draft_data)

        assert recurring.recurrence_type == RecurrenceType.MONTHLY
        assert recurring.day_of_month == 1

    def test_saves_with_due_time(
        self, service: PersistenceService, mock_session: MagicMock
    ) -> None:
        """Recurring commitment is saved with due time."""
        mock_session.exec.return_value.first.return_value = None

        draft_data = {
            "deliverable_template": "Daily standup",
            "stakeholder_name": "Team",
            "recurrence_type": "daily",
            "due_time": time(9, 30),
        }

        recurring = service.save_recurring_commitment(draft_data)

        assert recurring.due_time == time(9, 30)

    def test_raises_for_invalid_recurrence_type(self, service: PersistenceService) -> None:
        """ValidationError is raised for invalid recurrence type."""
        draft_data = {
            "deliverable_template": "Test",
            "stakeholder_name": "Test",
            "recurrence_type": "invalid",
        }

        with pytest.raises(ValidationError, match="Invalid recurrence_type"):
            service.save_recurring_commitment(draft_data)


class TestHelperMethods:
    """Tests for helper methods."""

    def test_parse_date_from_date_object(self, service: PersistenceService) -> None:
        """Date object is returned as-is."""
        result = service._parse_date(date(2025, 12, 20))
        assert result == date(2025, 12, 20)

    def test_parse_date_from_string(self, service: PersistenceService) -> None:
        """ISO date string is parsed correctly."""
        result = service._parse_date("2025-12-20")
        assert result == date(2025, 12, 20)

    def test_parse_date_invalid_string(self, service: PersistenceService) -> None:
        """Invalid date string raises ValidationError."""
        with pytest.raises(ValidationError, match="Invalid date"):
            service._parse_date("not-a-date")

    def test_parse_time_from_time_object(self, service: PersistenceService) -> None:
        """Time object is returned as-is."""
        result = service._parse_time(time(15, 30))
        assert result == time(15, 30)

    def test_parse_time_from_string(self, service: PersistenceService) -> None:
        """Time string is parsed correctly."""
        result = service._parse_time("15:30")
        assert result == time(15, 30)

    def test_parse_time_returns_none_for_none(self, service: PersistenceService) -> None:
        """None returns None."""
        result = service._parse_time(None)
        assert result is None

    def test_parse_uuid_from_uuid_object(self, service: PersistenceService) -> None:
        """UUID object is returned as-is."""
        uid = uuid4()
        result = service._parse_uuid(uid)
        assert result == uid

    def test_parse_uuid_from_string(self, service: PersistenceService) -> None:
        """UUID string is parsed correctly."""
        uid = uuid4()
        result = service._parse_uuid(str(uid))
        assert result == uid

    def test_parse_uuid_returns_none_for_none(self, service: PersistenceService) -> None:
        """None returns None."""
        result = service._parse_uuid(None)
        assert result is None

    def test_parse_uuid_returns_none_for_invalid(self, service: PersistenceService) -> None:
        """Invalid string returns None."""
        result = service._parse_uuid("not-a-uuid")
        assert result is None
