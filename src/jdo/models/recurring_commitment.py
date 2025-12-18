"""RecurringCommitment SQLModel entity."""

from __future__ import annotations

from datetime import date, datetime, time
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, model_validator
from pydantic import Field as PydanticField
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from jdo.models.base import utc_now

# Constants for validation ranges
MIN_DAY_OF_WEEK = 0
MAX_DAY_OF_WEEK = 6  # Monday=0 to Sunday=6
MIN_DAY_OF_MONTH = 1
MAX_DAY_OF_MONTH = 31
MIN_MONTH_OF_YEAR = 1
MAX_MONTH_OF_YEAR = 12
MIN_WEEK_OF_MONTH = 1
MAX_WEEK_OF_MONTH = 5  # 5 means "last" week
LAST_WEEK_OF_MONTH = -1  # Alternative for "last" week
MAX_INTERVAL = 365  # Reasonable upper bound for interval


class SubTaskTemplate(BaseModel):
    """Template for a sub-task within a TaskTemplate."""

    description: str = PydanticField(min_length=1)


class TaskTemplate(BaseModel):
    """Template for a task within a RecurringCommitment.

    When a Commitment is spawned from a RecurringCommitment,
    TaskTemplates are copied to create new Task instances.
    """

    title: str = PydanticField(min_length=1)
    scope: str = PydanticField(min_length=1)
    order: int
    sub_tasks: list[SubTaskTemplate] = PydanticField(default_factory=list)


class RecurrenceType(str, Enum):
    """Type of recurrence pattern."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class EndType(str, Enum):
    """Type of end condition for recurrence."""

    NEVER = "never"
    AFTER_COUNT = "after_count"
    BY_DATE = "by_date"


class RecurringCommitmentStatus(str, Enum):
    """Status of a recurring commitment."""

    ACTIVE = "active"
    PAUSED = "paused"


class RecurringCommitment(SQLModel, table=True):
    """A recurring commitment template that spawns Commitment instances.

    RecurringCommitments act as templates with recurrence patterns.
    They generate individual Commitment instances on-demand based on
    the schedule defined by the recurrence pattern.
    """

    __tablename__ = "recurring_commitments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    deliverable_template: str = Field(min_length=1)
    stakeholder_id: UUID = Field(foreign_key="stakeholders.id")
    goal_id: UUID | None = Field(default=None, foreign_key="goals.id")

    # Time settings
    due_time: time | None = Field(default=None)
    timezone: str = Field(default="America/New_York")

    # Recurrence pattern
    recurrence_type: RecurrenceType
    interval: int = Field(default=1, ge=1, le=MAX_INTERVAL)

    # Weekly pattern: days 0=Monday to 6=Sunday
    days_of_week: list[int] | None = Field(default=None, sa_column=Column(JSON))

    # Monthly pattern: specific day of month (1-31)
    day_of_month: int | None = Field(default=None)

    # Monthly pattern: week of month (1-5 or -1 for last) with day_of_week
    week_of_month: int | None = Field(default=None)

    # Yearly pattern: month (1-12)
    month_of_year: int | None = Field(default=None)

    # End conditions
    end_type: EndType = Field(default=EndType.NEVER)
    end_after_count: int | None = Field(default=None)
    end_by_date: date | None = Field(default=None)

    # Task templates stored as JSON
    task_templates: list[dict[str, Any]] = Field(default=[], sa_column=Column(JSON))

    # Optional fields
    notes: str | None = Field(default=None)

    # Status and tracking
    status: RecurringCommitmentStatus = Field(default=RecurringCommitmentStatus.ACTIVE)
    last_generated_date: date | None = Field(default=None)
    instances_generated: int = Field(default=0)

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_recurrence_pattern(self) -> RecurringCommitment:
        """Validate recurrence pattern based on recurrence_type."""
        if self.recurrence_type == RecurrenceType.WEEKLY:
            self._validate_weekly_pattern()
        elif self.recurrence_type == RecurrenceType.MONTHLY:
            self._validate_monthly_pattern()
        elif self.recurrence_type == RecurrenceType.YEARLY:
            self._validate_yearly_pattern()

        self._validate_end_conditions()
        self._validate_days_of_week_range()
        self._validate_week_of_month_range()
        self._validate_no_duplicate_days()

        return self

    def _validate_weekly_pattern(self) -> None:
        """Validate weekly recurrence pattern."""
        if self.days_of_week is None:
            msg = "Weekly recurrence requires days_of_week"
            raise ValueError(msg)
        if len(self.days_of_week) == 0:
            msg = "Weekly recurrence requires at least one day"
            raise ValueError(msg)

    def _validate_monthly_pattern(self) -> None:
        """Validate monthly recurrence pattern."""
        has_day_of_month = self.day_of_month is not None
        has_week_pattern = self.week_of_month is not None and self.days_of_week is not None

        if not has_day_of_month and not has_week_pattern:
            msg = "Monthly recurrence requires day_of_month OR (week_of_month + days_of_week)"
            raise ValueError(msg)

        if self.day_of_month is not None and not (
            MIN_DAY_OF_MONTH <= self.day_of_month <= MAX_DAY_OF_MONTH
        ):
            msg = "day_of_month must be 1-31"
            raise ValueError(msg)

    def _validate_yearly_pattern(self) -> None:
        """Validate yearly recurrence pattern."""
        if self.month_of_year is None:
            msg = "Yearly recurrence requires month_of_year"
            raise ValueError(msg)

        if not (MIN_MONTH_OF_YEAR <= self.month_of_year <= MAX_MONTH_OF_YEAR):
            msg = "month_of_year must be 1-12"
            raise ValueError(msg)

        # Yearly also needs either day_of_month or week pattern
        has_day_of_month = self.day_of_month is not None
        has_week_pattern = self.week_of_month is not None and self.days_of_week is not None

        if not has_day_of_month and not has_week_pattern:
            msg = "Yearly recurrence requires day_of_month OR (week_of_month + days_of_week)"
            raise ValueError(msg)

        if self.day_of_month is not None and not (
            MIN_DAY_OF_MONTH <= self.day_of_month <= MAX_DAY_OF_MONTH
        ):
            msg = "day_of_month must be 1-31"
            raise ValueError(msg)

    def _validate_end_conditions(self) -> None:
        """Validate end conditions based on end_type."""
        if self.end_type == EndType.AFTER_COUNT and self.end_after_count is None:
            msg = "end_after_count required when end_type is after_count"
            raise ValueError(msg)

        if self.end_type == EndType.BY_DATE and self.end_by_date is None:
            msg = "end_by_date required when end_type is by_date"
            raise ValueError(msg)

    def _validate_days_of_week_range(self) -> None:
        """Validate days_of_week values are in range 0-6."""
        if self.days_of_week is not None:
            for day in self.days_of_week:
                if not (MIN_DAY_OF_WEEK <= day <= MAX_DAY_OF_WEEK):
                    msg = "days_of_week values must be 0-6"
                    raise ValueError(msg)

    def _validate_week_of_month_range(self) -> None:
        """Validate week_of_month is in valid range (1-5 or -1 for last)."""
        if self.week_of_month is not None:
            valid_values = {1, 2, 3, 4, 5, LAST_WEEK_OF_MONTH}  # 1-5 or -1
            if self.week_of_month not in valid_values:
                msg = "week_of_month must be 1-5 or -1 (for last week)"
                raise ValueError(msg)

    def _validate_no_duplicate_days(self) -> None:
        """Validate days_of_week has no duplicates."""
        if self.days_of_week is not None and len(self.days_of_week) != len(set(self.days_of_week)):
            msg = "days_of_week cannot contain duplicate values"
            raise ValueError(msg)

    def get_task_templates(self) -> list[TaskTemplate]:
        """Get task_templates as TaskTemplate objects."""
        return [TaskTemplate(**t) for t in self.task_templates]

    def set_task_templates(self, templates: list[TaskTemplate]) -> None:
        """Set task_templates from TaskTemplate objects."""
        self.task_templates = [t.model_dump() for t in templates]
