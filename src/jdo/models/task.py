"""Task SQLModel entity."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, field_validator
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class TaskStatus(str, Enum):
    """Status of a task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class ActualHoursCategory(str, Enum):
    """Category for actual hours vs estimate comparison.

    Used for 5-point scale to record how actual time compared to estimate.
    """

    MUCH_SHORTER = "much_shorter"  # <50% of estimate
    SHORTER = "shorter"  # 50-85% of estimate
    ON_TARGET = "on_target"  # 85-115% of estimate
    LONGER = "longer"  # 115-150% of estimate
    MUCH_LONGER = "much_longer"  # >150% of estimate

    @property
    def multiplier(self) -> float:
        """Get the multiplier for accuracy calculation.

        Returns midpoint of the range for variance calculation.
        """
        multipliers = {
            ActualHoursCategory.MUCH_SHORTER: 0.25,  # Midpoint of 0-50%
            ActualHoursCategory.SHORTER: 0.675,  # Midpoint of 50-85%
            ActualHoursCategory.ON_TARGET: 1.0,  # Midpoint of 85-115%
            ActualHoursCategory.LONGER: 1.325,  # Midpoint of 115-150%
            ActualHoursCategory.MUCH_LONGER: 2.0,  # >150%, use 200%
        }
        return multipliers[self]


class EstimationConfidence(str, Enum):
    """Confidence level for time estimates."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


class SubTask(BaseModel):
    """An embedded sub-task within a Task.

    SubTasks are stored as JSON within the Task record, not as a separate table.
    """

    description: str
    completed: bool = False


class Task(SQLModel, table=True):
    """A task within a commitment.

    Tasks represent scoped work items required to fulfill a commitment.
    Each task must have a clear scope defining what "done" means.

    Note: sub_tasks is stored as JSON (list of dicts) in the database.
    Use get_sub_tasks() to get SubTask objects.
    """

    __tablename__ = "tasks"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    commitment_id: UUID = Field(foreign_key="commitments.id")
    title: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    # Store as list of dicts in JSON column
    sub_tasks: list[dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    order: int
    is_notification_task: bool = Field(default=False)
    # Time estimation fields
    estimated_hours: float | None = Field(default=None)
    actual_hours_category: ActualHoursCategory | None = Field(default=None)
    estimation_confidence: EstimationConfidence | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("sub_tasks", mode="before")
    @classmethod
    def serialize_sub_tasks(cls, v: Any) -> list[dict[str, Any]]:  # noqa: ANN401
        """Convert SubTask objects to dicts for JSON storage."""
        if v is None:
            return []
        result = []
        for item in v:
            if isinstance(item, SubTask):
                result.append(item.model_dump())
            elif isinstance(item, dict):
                result.append(item)
            else:
                result.append(item)
        return result

    def get_sub_tasks(self) -> list[SubTask]:
        """Get sub_tasks as SubTask objects."""
        return [SubTask(**st) for st in self.sub_tasks]

    def set_sub_tasks(self, sub_tasks: list[SubTask]) -> None:
        """Set sub_tasks from SubTask objects."""
        self.sub_tasks = [st.model_dump() for st in sub_tasks]
