"""Commitment SQLModel entity."""

from datetime import UTC, date, datetime, time
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class CommitmentStatus(str, Enum):
    """Status of a commitment."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


def default_due_time() -> time:
    """Default due time of 9:00 AM."""
    return time(9, 0)


class Commitment(SQLModel, table=True):
    """A commitment made to a stakeholder.

    Commitments answer: "What (deliverable) to who (stakeholder) by when (due date)."
    They must have a clear deliverable, stakeholder, and due date.
    """

    __tablename__ = "commitments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    deliverable: str = Field(min_length=1)
    stakeholder_id: UUID = Field(foreign_key="stakeholders.id")
    goal_id: UUID | None = Field(default=None, foreign_key="goals.id")
    due_date: date
    due_time: time = Field(default_factory=default_due_time)
    timezone: str = Field(default="America/New_York")
    status: CommitmentStatus = Field(default=CommitmentStatus.PENDING)
    completed_at: datetime | None = Field(default=None)
    notes: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
