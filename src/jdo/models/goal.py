"""Goal SQLModel entity."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from enum import Enum
from typing import Self
from uuid import UUID, uuid4

from pydantic import model_validator
from sqlmodel import Field, SQLModel

__all__ = ["INTERVAL_LABELS", "VALID_REVIEW_INTERVALS", "Goal", "GoalProgress", "GoalStatus"]


def today_date() -> date:
    """Get current date in UTC."""
    return datetime.now(UTC).date()


@dataclass
class GoalProgress:
    """Progress summary for a goal's commitments.

    Shows counts of commitments by status, providing visibility into
    how much work is done vs remaining.
    """

    total: int
    completed: int
    in_progress: int
    pending: int
    abandoned: int

    @property
    def completion_rate(self) -> float:
        """Percentage of non-abandoned commitments that are completed.

        Returns:
            Float between 0.0 and 1.0, or 0.0 if no non-abandoned commitments.
        """
        non_abandoned = self.total - self.abandoned
        if non_abandoned == 0:
            return 0.0
        return self.completed / non_abandoned


class GoalStatus(str, Enum):
    """Status of a goal."""

    ACTIVE = "active"
    ON_HOLD = "on_hold"
    ACHIEVED = "achieved"
    ABANDONED = "abandoned"


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


# Valid review intervals and their labels
VALID_REVIEW_INTERVALS = {7, 30, 90}
INTERVAL_LABELS = {
    7: "Weekly",
    30: "Monthly",
    90: "Quarterly",
}


class Goal(SQLModel, table=True):
    """A goal that provides context and direction for commitments.

    Goals represent outcomes with a clear problem statement and solution vision.
    They can be nested under other goals via parent_goal_id.
    """

    __tablename__ = "goals"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(min_length=1)
    problem_statement: str = Field(min_length=1)
    solution_vision: str = Field(min_length=1)
    motivation: str | None = Field(default=None)
    parent_goal_id: UUID | None = Field(default=None, foreign_key="goals.id")
    vision_id: UUID | None = Field(default=None, foreign_key="visions.id")
    status: GoalStatus = Field(default=GoalStatus.ACTIVE)
    next_review_date: date | None = Field(default=None)
    review_interval_days: int | None = Field(default=None)
    last_reviewed_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_review_interval(self) -> Self:
        """Validate review_interval_days is 7, 30, or 90."""
        if (
            self.review_interval_days is not None
            and self.review_interval_days not in VALID_REVIEW_INTERVALS
        ):
            msg = "Review interval must be 7, 30, or 90"
            raise ValueError(msg)
        return self

    def is_due_for_review(self) -> bool:
        """Check if this goal is due for review.

        A goal is due for review when:
        - It has a next_review_date that is today or in the past
        - Its status is ACTIVE

        On-hold, achieved, and abandoned goals are not due for review.

        Returns:
            True if due for review, False otherwise.
        """
        if self.status != GoalStatus.ACTIVE:
            return False
        if self.next_review_date is None:
            return False
        return self.next_review_date <= today_date()

    def complete_review(self) -> None:
        """Complete a review of this goal.

        Updates:
        - last_reviewed_at: Set to current time
        - next_review_date: Calculated from review_interval_days if set, else None
        - updated_at: Set to current time
        """
        now = utc_now()
        self.last_reviewed_at = now
        self.updated_at = now

        if self.review_interval_days is not None:
            self.next_review_date = today_date() + timedelta(days=self.review_interval_days)
        else:
            self.next_review_date = None

    @property
    def interval_label(self) -> str | None:
        """Human-readable label for the review interval.

        Returns:
            'Weekly' for 7 days, 'Monthly' for 30 days,
            'Quarterly' for 90 days, or None if no interval set.
        """
        if self.review_interval_days is None:
            return None
        return INTERVAL_LABELS.get(self.review_interval_days)
