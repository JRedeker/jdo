"""Goal SQLModel entity."""

from datetime import UTC, date, datetime
from enum import Enum
from typing import Self
from uuid import UUID, uuid4

from pydantic import model_validator
from sqlmodel import Field, SQLModel


class GoalStatus(str, Enum):
    """Status of a goal."""

    ACTIVE = "active"
    ON_HOLD = "on_hold"
    ACHIEVED = "achieved"
    ABANDONED = "abandoned"


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


# Valid review intervals
VALID_REVIEW_INTERVALS = {7, 30, 90}


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
