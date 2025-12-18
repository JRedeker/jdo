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
