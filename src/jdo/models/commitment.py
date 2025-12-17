"""Commitment SQLModel entity."""

from datetime import date, datetime, time
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey, Uuid
from sqlmodel import Field, SQLModel

from jdo.models.base import utc_now


class CommitmentStatus(str, Enum):
    """Status of a commitment."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


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
    milestone_id: UUID | None = Field(default=None, foreign_key="milestones.id")
    recurring_commitment_id: UUID | None = Field(
        default=None,
        sa_column=Column(
            Uuid(as_uuid=True),
            ForeignKey("recurring_commitments.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    due_date: date
    due_time: time = Field(default_factory=default_due_time)
    timezone: str = Field(default="America/New_York")
    status: CommitmentStatus = Field(default=CommitmentStatus.PENDING)
    completed_at: datetime | None = Field(default=None)
    notes: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @property
    def is_recurring(self) -> bool:
        """Check if this commitment was spawned from a recurring commitment.

        Returns:
            True if linked to a RecurringCommitment, False otherwise.
        """
        return self.recurring_commitment_id is not None

    def is_orphan(self) -> bool:
        """Check if this commitment is an orphan.

        A commitment is considered orphan if it has neither a goal_id nor a
        milestone_id. Orphan commitments should be surfaced for user attention.

        Returns:
            True if orphan (no goal_id AND no milestone_id), False otherwise.
        """
        return self.goal_id is None and self.milestone_id is None
