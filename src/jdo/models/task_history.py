"""TaskHistoryEntry SQLModel entity for audit logging."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from jdo.models.task import ActualHoursCategory, TaskStatus


class TaskEventType(str, Enum):
    """Type of task lifecycle event."""

    CREATED = "created"
    STARTED = "started"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    ABANDONED = "abandoned"


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


class TaskHistoryEntry(SQLModel, table=True):
    """Immutable audit log entry for task lifecycle events.

    This model captures task status transitions for AI learning and pattern analysis.
    Entries are never modified or deleted - they form an immutable audit log.

    The commitment_id is denormalized for efficient querying without joins.
    History entries survive task deletion to preserve the learning history.
    """

    __tablename__ = "task_history"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    task_id: UUID = Field(foreign_key="tasks.id", index=True)
    commitment_id: UUID = Field(index=True)  # Denormalized for fast queries
    event_type: TaskEventType
    previous_status: TaskStatus | None = Field(default=None)
    new_status: TaskStatus
    # Snapshot of time estimation at event time
    estimated_hours: float | None = Field(default=None)
    # Only set for completed events
    actual_hours_category: ActualHoursCategory | None = Field(default=None)
    # Optional notes (e.g., skip reason)
    notes: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now, index=True)
