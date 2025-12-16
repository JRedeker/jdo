"""Milestone SQLModel entity."""

from datetime import UTC, date, datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class MilestoneStatus(str, Enum):
    """Status of a milestone."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    MISSED = "missed"


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


class Milestone(SQLModel, table=True):
    """A concrete checkpoint with a specific target date.

    Milestones break down aspirational Goals into achievable chunks.
    Every Milestone belongs to a Goal, and Commitments can optionally
    link to Milestones for structured progress tracking.
    """

    __tablename__ = "milestones"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    goal_id: UUID = Field(foreign_key="goals.id")
    title: str = Field(min_length=1)
    description: str | None = Field(default=None)
    target_date: date
    status: MilestoneStatus = Field(default=MilestoneStatus.PENDING)
    completed_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def start(self) -> None:
        """Start working on this milestone.

        Transitions status from pending to in_progress.
        """
        self.status = MilestoneStatus.IN_PROGRESS
        self.updated_at = utc_now()

    def complete(self) -> None:
        """Mark this milestone as completed.

        Sets completed_at timestamp and transitions status to completed.
        Works from pending, in_progress, or missed state (late completion).
        """
        self.status = MilestoneStatus.COMPLETED
        self.completed_at = utc_now()
        self.updated_at = utc_now()

    def mark_missed(self) -> None:
        """Mark this milestone as missed.

        Used when target_date passes without completion.
        """
        self.status = MilestoneStatus.MISSED
        self.updated_at = utc_now()

    def is_overdue(self) -> bool:
        """Check if this milestone is overdue.

        A milestone is overdue if:
        - target_date has passed AND
        - status is pending or in_progress (not completed or already missed)

        Returns:
            True if overdue, False otherwise.
        """
        if self.status in (MilestoneStatus.COMPLETED, MilestoneStatus.MISSED):
            return False
        return self.target_date < datetime.now(UTC).date()
