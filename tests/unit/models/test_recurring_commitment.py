"""Tests for RecurringCommitment SQLModel - TDD Red phase."""

from datetime import date, time
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlmodel import SQLModel


class TestRecurringCommitmentModel:
    """Tests for RecurringCommitment model structure."""

    def test_inherits_from_sqlmodel_with_table_true(self) -> None:
        """RecurringCommitment inherits from SQLModel with table=True."""
        from jdo.models.recurring_commitment import RecurringCommitment

        assert issubclass(RecurringCommitment, SQLModel)
        assert hasattr(RecurringCommitment, "__tablename__")

    def test_has_tablename_recurring_commitments(self) -> None:
        """RecurringCommitment has tablename 'recurring_commitments'."""
        from jdo.models.recurring_commitment import RecurringCommitment

        assert RecurringCommitment.__tablename__ == "recurring_commitments"

    def test_has_required_fields(self) -> None:
        """RecurringCommitment has all required fields."""
        from jdo.models.recurring_commitment import RecurringCommitment

        fields = RecurringCommitment.model_fields
        assert "id" in fields
        assert "deliverable_template" in fields
        assert "stakeholder_id" in fields
        assert "goal_id" in fields
        assert "due_time" in fields
        assert "timezone" in fields
        assert "recurrence_type" in fields
        assert "interval" in fields
        assert "days_of_week" in fields
        assert "day_of_month" in fields
        assert "week_of_month" in fields
        assert "month_of_year" in fields
        assert "end_type" in fields
        assert "end_after_count" in fields
        assert "end_by_date" in fields
        assert "task_templates" in fields
        assert "notes" in fields
        assert "status" in fields
        assert "last_generated_date" in fields
        assert "instances_generated" in fields
        assert "created_at" in fields
        assert "updated_at" in fields


class TestRecurrenceTypeEnum:
    """Tests for RecurrenceType enum."""

    def test_has_required_values(self) -> None:
        """RecurrenceType has daily, weekly, monthly, yearly."""
        from jdo.models.recurring_commitment import RecurrenceType

        assert RecurrenceType.DAILY.value == "daily"
        assert RecurrenceType.WEEKLY.value == "weekly"
        assert RecurrenceType.MONTHLY.value == "monthly"
        assert RecurrenceType.YEARLY.value == "yearly"


class TestEndTypeEnum:
    """Tests for EndType enum."""

    def test_has_required_values(self) -> None:
        """EndType has never, after_count, by_date."""
        from jdo.models.recurring_commitment import EndType

        assert EndType.NEVER.value == "never"
        assert EndType.AFTER_COUNT.value == "after_count"
        assert EndType.BY_DATE.value == "by_date"


class TestRecurringCommitmentStatusEnum:
    """Tests for RecurringCommitmentStatus enum."""

    def test_has_required_values(self) -> None:
        """RecurringCommitmentStatus has active, paused."""
        from jdo.models.recurring_commitment import RecurringCommitmentStatus

        assert RecurringCommitmentStatus.ACTIVE.value == "active"
        assert RecurringCommitmentStatus.PAUSED.value == "paused"


class TestRecurringCommitmentValidation:
    """Tests for RecurringCommitment field validation."""

    def test_creates_with_required_fields(self) -> None:
        """Create recurring commitment with required fields."""
        from jdo.models.recurring_commitment import (
            RecurrenceType,
            RecurringCommitment,
            RecurringCommitmentStatus,
        )

        stakeholder_id = uuid4()
        recurring = RecurringCommitment(
            deliverable_template="Weekly status report",
            stakeholder_id=stakeholder_id,
            recurrence_type=RecurrenceType.WEEKLY,
            days_of_week=[0],  # Monday
        )

        assert recurring.deliverable_template == "Weekly status report"
        assert recurring.stakeholder_id == stakeholder_id
        assert recurring.recurrence_type == RecurrenceType.WEEKLY
        assert recurring.status == RecurringCommitmentStatus.ACTIVE
        assert isinstance(recurring.id, UUID)

    def test_requires_non_empty_deliverable_template(self) -> None:
        """Reject empty deliverable_template."""
        from jdo.models.recurring_commitment import (
            RecurrenceType,
            RecurringCommitment,
        )

        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            RecurringCommitment.model_validate(
                {
                    "deliverable_template": "",
                    "stakeholder_id": str(uuid4()),
                    "recurrence_type": "daily",
                }
            )

    def test_requires_stakeholder_id(self) -> None:
        """Reject missing stakeholder_id."""
        from jdo.models.recurring_commitment import (
            RecurrenceType,
            RecurringCommitment,
        )

        with pytest.raises(ValidationError):
            RecurringCommitment.model_validate(
                {
                    "deliverable_template": "Test",
                    "recurrence_type": "daily",
                }
            )

    def test_requires_recurrence_type(self) -> None:
        """Reject missing recurrence_type."""
        from jdo.models.recurring_commitment import RecurringCommitment

        with pytest.raises(ValidationError):
            RecurringCommitment.model_validate(
                {
                    "deliverable_template": "Test",
                    "stakeholder_id": str(uuid4()),
                }
            )

    def test_status_defaults_to_active(self) -> None:
        """Status defaults to active."""
        from jdo.models.recurring_commitment import (
            RecurrenceType,
            RecurringCommitment,
            RecurringCommitmentStatus,
        )

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
        )

        assert recurring.status == RecurringCommitmentStatus.ACTIVE

    def test_auto_generates_id_created_at_updated_at(self) -> None:
        """Auto-generates id, created_at, updated_at."""
        from jdo.models.recurring_commitment import (
            RecurrenceType,
            RecurringCommitment,
        )

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
        )

        assert isinstance(recurring.id, UUID)
        assert recurring.created_at is not None
        assert recurring.updated_at is not None


class TestWeeklyPatternValidation:
    """Tests for weekly recurrence pattern validation."""

    def test_days_of_week_accepts_valid_integers(self) -> None:
        """days_of_week accepts list of 0-6 integers."""
        from jdo.models.recurring_commitment import (
            RecurrenceType,
            RecurringCommitment,
        )

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.WEEKLY,
            days_of_week=[0, 2, 4],  # Mon, Wed, Fri
        )

        assert recurring.days_of_week == [0, 2, 4]

    def test_days_of_week_rejects_values_outside_range(self) -> None:
        """days_of_week rejects values outside 0-6."""
        from jdo.models.recurring_commitment import RecurringCommitment

        with pytest.raises(ValueError, match="days_of_week values must be 0-6"):
            RecurringCommitment.model_validate(
                {
                    "deliverable_template": "Test",
                    "stakeholder_id": str(uuid4()),
                    "recurrence_type": "weekly",
                    "days_of_week": [7],  # Invalid
                }
            )

    def test_weekly_requires_at_least_one_day(self) -> None:
        """Weekly recurrence requires at least one day."""
        from jdo.models.recurring_commitment import RecurringCommitment

        with pytest.raises(ValueError, match="Weekly recurrence requires at least one day"):
            RecurringCommitment.model_validate(
                {
                    "deliverable_template": "Test",
                    "stakeholder_id": str(uuid4()),
                    "recurrence_type": "weekly",
                    "days_of_week": [],
                }
            )

    def test_weekly_without_days_of_week_raises_error(self) -> None:
        """Weekly recurrence without days_of_week raises error."""
        from jdo.models.recurring_commitment import RecurringCommitment

        with pytest.raises(ValueError, match="Weekly recurrence requires days_of_week"):
            RecurringCommitment.model_validate(
                {
                    "deliverable_template": "Test",
                    "stakeholder_id": str(uuid4()),
                    "recurrence_type": "weekly",
                }
            )


class TestMonthlyPatternValidation:
    """Tests for monthly recurrence pattern validation."""

    def test_day_of_month_accepts_valid_values(self) -> None:
        """day_of_month accepts 1-31."""
        from jdo.models.recurring_commitment import (
            RecurrenceType,
            RecurringCommitment,
        )

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.MONTHLY,
            day_of_month=15,
        )

        assert recurring.day_of_month == 15

    def test_day_of_month_rejects_values_outside_range(self) -> None:
        """day_of_month rejects values outside 1-31."""
        from jdo.models.recurring_commitment import RecurringCommitment

        with pytest.raises(ValueError, match="day_of_month must be 1-31"):
            RecurringCommitment.model_validate(
                {
                    "deliverable_template": "Test",
                    "stakeholder_id": str(uuid4()),
                    "recurrence_type": "monthly",
                    "day_of_month": 32,
                }
            )

    def test_week_of_month_with_day_of_week(self) -> None:
        """week_of_month accepts 1-5 with day_of_week."""
        from jdo.models.recurring_commitment import (
            RecurrenceType,
            RecurringCommitment,
        )

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.MONTHLY,
            week_of_month=2,
            days_of_week=[4],  # 2nd Friday
        )

        assert recurring.week_of_month == 2
        assert recurring.days_of_week == [4]

    def test_monthly_requires_day_of_month_or_week_pattern(self) -> None:
        """Monthly requires either day_of_month OR (week_of_month + day_of_week)."""
        from jdo.models.recurring_commitment import RecurringCommitment

        with pytest.raises(ValueError, match="Monthly recurrence requires"):
            RecurringCommitment.model_validate(
                {
                    "deliverable_template": "Test",
                    "stakeholder_id": str(uuid4()),
                    "recurrence_type": "monthly",
                }
            )

    def test_week_of_month_accepts_negative_for_last(self) -> None:
        """week_of_month accepts -1 for last week."""
        from jdo.models.recurring_commitment import (
            RecurrenceType,
            RecurringCommitment,
        )

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.MONTHLY,
            week_of_month=-1,
            days_of_week=[4],  # Last Friday
        )

        assert recurring.week_of_month == -1


class TestEndConditionValidation:
    """Tests for end condition validation."""

    def test_end_type_never_has_no_constraints(self) -> None:
        """end_type=never has no end constraints."""
        from jdo.models.recurring_commitment import (
            EndType,
            RecurrenceType,
            RecurringCommitment,
        )

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            end_type=EndType.NEVER,
        )

        assert recurring.end_type == EndType.NEVER
        assert recurring.end_after_count is None
        assert recurring.end_by_date is None

    def test_end_type_after_count_requires_positive_count(self) -> None:
        """end_type=after_count requires end_after_count > 0."""
        from jdo.models.recurring_commitment import (
            EndType,
            RecurrenceType,
            RecurringCommitment,
        )

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            end_type=EndType.AFTER_COUNT,
            end_after_count=10,
        )

        assert recurring.end_after_count == 10

    def test_end_type_after_count_without_count_raises_error(self) -> None:
        """end_type=after_count without end_after_count raises error."""
        from jdo.models.recurring_commitment import RecurringCommitment

        with pytest.raises(ValueError, match="end_after_count required"):
            RecurringCommitment.model_validate(
                {
                    "deliverable_template": "Test",
                    "stakeholder_id": str(uuid4()),
                    "recurrence_type": "daily",
                    "end_type": "after_count",
                }
            )

    def test_end_type_by_date_requires_end_by_date(self) -> None:
        """end_type=by_date requires end_by_date."""
        from jdo.models.recurring_commitment import (
            EndType,
            RecurrenceType,
            RecurringCommitment,
        )

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            end_type=EndType.BY_DATE,
            end_by_date=date(2025, 12, 31),
        )

        assert recurring.end_by_date == date(2025, 12, 31)

    def test_end_type_by_date_without_date_raises_error(self) -> None:
        """end_type=by_date without end_by_date raises error."""
        from jdo.models.recurring_commitment import RecurringCommitment

        with pytest.raises(ValueError, match="end_by_date required"):
            RecurringCommitment.model_validate(
                {
                    "deliverable_template": "Test",
                    "stakeholder_id": str(uuid4()),
                    "recurrence_type": "daily",
                    "end_type": "by_date",
                }
            )


class TestYearlyPatternValidation:
    """Tests for yearly recurrence pattern validation."""

    def test_yearly_with_month_and_day(self) -> None:
        """Yearly pattern with month_of_year and day_of_month."""
        from jdo.models.recurring_commitment import (
            RecurrenceType,
            RecurringCommitment,
        )

        recurring = RecurringCommitment(
            deliverable_template="Annual review",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.YEARLY,
            month_of_year=3,  # March
            day_of_month=15,
        )

        assert recurring.month_of_year == 3
        assert recurring.day_of_month == 15

    def test_yearly_requires_month_of_year(self) -> None:
        """Yearly recurrence requires month_of_year."""
        from jdo.models.recurring_commitment import RecurringCommitment

        with pytest.raises(ValueError, match="Yearly recurrence requires month_of_year"):
            RecurringCommitment.model_validate(
                {
                    "deliverable_template": "Test",
                    "stakeholder_id": str(uuid4()),
                    "recurrence_type": "yearly",
                    "day_of_month": 15,
                }
            )

    def test_month_of_year_rejects_invalid_values(self) -> None:
        """month_of_year rejects values outside 1-12."""
        from jdo.models.recurring_commitment import RecurringCommitment

        with pytest.raises(ValueError, match="month_of_year must be 1-12"):
            RecurringCommitment.model_validate(
                {
                    "deliverable_template": "Test",
                    "stakeholder_id": str(uuid4()),
                    "recurrence_type": "yearly",
                    "month_of_year": 13,
                    "day_of_month": 15,
                }
            )


class TestDefaultValues:
    """Tests for default field values."""

    def test_timezone_defaults_to_est(self) -> None:
        """timezone defaults to America/New_York."""
        from jdo.models.recurring_commitment import (
            RecurrenceType,
            RecurringCommitment,
        )

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
        )

        assert recurring.timezone == "America/New_York"

    def test_interval_defaults_to_one(self) -> None:
        """interval defaults to 1."""
        from jdo.models.recurring_commitment import (
            RecurrenceType,
            RecurringCommitment,
        )

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
        )

        assert recurring.interval == 1

    def test_end_type_defaults_to_never(self) -> None:
        """end_type defaults to never."""
        from jdo.models.recurring_commitment import (
            EndType,
            RecurrenceType,
            RecurringCommitment,
        )

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
        )

        assert recurring.end_type == EndType.NEVER

    def test_instances_generated_defaults_to_zero(self) -> None:
        """instances_generated defaults to 0."""
        from jdo.models.recurring_commitment import (
            RecurrenceType,
            RecurringCommitment,
        )

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
        )

        assert recurring.instances_generated == 0

    def test_task_templates_defaults_to_empty_list(self) -> None:
        """task_templates defaults to empty list."""
        from jdo.models.recurring_commitment import (
            RecurrenceType,
            RecurringCommitment,
        )

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
        )

        assert recurring.task_templates == []


class TestTaskTemplate:
    """Tests for TaskTemplate Pydantic model."""

    def test_creates_with_required_fields(self) -> None:
        """Create TaskTemplate with required fields."""
        from jdo.models.recurring_commitment import TaskTemplate

        template = TaskTemplate(
            title="Gather data",
            scope="Collect data from departments",
            order=1,
        )

        assert template.title == "Gather data"
        assert template.scope == "Collect data from departments"
        assert template.order == 1
        assert template.sub_tasks == []

    def test_requires_non_empty_title(self) -> None:
        """TaskTemplate requires non-empty title."""
        from jdo.models.recurring_commitment import TaskTemplate

        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            TaskTemplate.model_validate(
                {
                    "title": "",
                    "scope": "Valid scope",
                    "order": 1,
                }
            )

    def test_requires_non_empty_scope(self) -> None:
        """TaskTemplate requires non-empty scope."""
        from jdo.models.recurring_commitment import TaskTemplate

        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            TaskTemplate.model_validate(
                {
                    "title": "Valid title",
                    "scope": "",
                    "order": 1,
                }
            )

    def test_requires_order(self) -> None:
        """TaskTemplate requires order."""
        from jdo.models.recurring_commitment import TaskTemplate

        with pytest.raises(ValidationError):
            TaskTemplate.model_validate(
                {
                    "title": "Valid title",
                    "scope": "Valid scope",
                }
            )

    def test_sub_tasks_defaults_to_empty_list(self) -> None:
        """TaskTemplate sub_tasks defaults to empty list."""
        from jdo.models.recurring_commitment import TaskTemplate

        template = TaskTemplate(
            title="Test",
            scope="Test scope",
            order=1,
        )

        assert template.sub_tasks == []

    def test_accepts_sub_tasks(self) -> None:
        """TaskTemplate accepts sub_tasks list."""
        from jdo.models.recurring_commitment import SubTaskTemplate, TaskTemplate

        template = TaskTemplate(
            title="Test",
            scope="Test scope",
            order=1,
            sub_tasks=[
                SubTaskTemplate(description="Step 1"),
                SubTaskTemplate(description="Step 2"),
            ],
        )

        assert len(template.sub_tasks) == 2
        assert template.sub_tasks[0].description == "Step 1"
        assert template.sub_tasks[1].description == "Step 2"

    def test_recurring_commitment_stores_task_templates(self) -> None:
        """RecurringCommitment stores task_templates as JSON."""
        from jdo.models.recurring_commitment import (
            RecurrenceType,
            RecurringCommitment,
            TaskTemplate,
        )

        templates = [
            TaskTemplate(title="Task 1", scope="Scope 1", order=1),
            TaskTemplate(title="Task 2", scope="Scope 2", order=2),
        ]

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            task_templates=[t.model_dump() for t in templates],
        )

        assert len(recurring.task_templates) == 2
        assert recurring.task_templates[0]["title"] == "Task 1"
        assert recurring.task_templates[1]["title"] == "Task 2"

    def test_get_task_templates_helper(self) -> None:
        """RecurringCommitment.get_task_templates returns TaskTemplate objects."""
        from jdo.models.recurring_commitment import (
            RecurrenceType,
            RecurringCommitment,
            TaskTemplate,
        )

        templates = [
            TaskTemplate(title="Task 1", scope="Scope 1", order=1),
            TaskTemplate(title="Task 2", scope="Scope 2", order=2),
        ]

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            task_templates=[t.model_dump() for t in templates],
        )

        parsed = recurring.get_task_templates()
        assert len(parsed) == 2
        assert isinstance(parsed[0], TaskTemplate)
        assert parsed[0].title == "Task 1"
        assert parsed[1].scope == "Scope 2"


class TestRecurringCommitmentPersistence:
    """Tests for RecurringCommitment database persistence."""

    def test_save_and_retrieve(self, tmp_path: Path) -> None:
        """Save recurring commitment via session and retrieve by id."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.models.recurring_commitment import (
            RecurrenceType,
            RecurringCommitment,
        )
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Create stakeholder first
            stakeholder = Stakeholder(name="Test Person", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            # Create recurring commitment
            recurring = RecurringCommitment(
                deliverable_template="Weekly report",
                stakeholder_id=stakeholder_id,
                recurrence_type=RecurrenceType.WEEKLY,
                days_of_week=[0],  # Monday
            )
            recurring_id = recurring.id

            with get_session() as session:
                session.add(recurring)

            # Retrieve
            with get_session() as session:
                result = session.exec(
                    select(RecurringCommitment).where(RecurringCommitment.id == recurring_id)
                ).first()

                assert result is not None
                assert result.deliverable_template == "Weekly report"
                assert result.stakeholder_id == stakeholder_id

        reset_engine()
