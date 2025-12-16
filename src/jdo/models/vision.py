"""Vision SQLModel entity."""

from datetime import UTC, date, datetime, timedelta
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


class VisionStatus(str, Enum):
    """Status of a vision."""

    ACTIVE = "active"
    ACHIEVED = "achieved"
    EVOLVED = "evolved"
    ABANDONED = "abandoned"


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


def today_date() -> date:
    """Get today's date in UTC."""
    return datetime.now(UTC).date()


def default_review_date() -> date:
    """Default review date 90 days from now."""
    return today_date() + timedelta(days=90)


class Vision(SQLModel, table=True):
    """A vivid, inspiring picture of the future.

    Visions are the top of the MPI planning hierarchy. They represent
    long-term (3-5+ years) outcomes that ignite passion and guide all
    goals and commitments. Visions are reviewed quarterly.
    """

    __tablename__ = "visions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(min_length=1)
    narrative: str = Field(min_length=1)
    timeframe: str | None = Field(default=None)
    metrics: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    why_it_matters: str | None = Field(default=None)
    status: VisionStatus = Field(default=VisionStatus.ACTIVE)
    next_review_date: date = Field(default_factory=default_review_date)
    last_reviewed_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def is_due_for_review(self) -> bool:
        """Check if vision is due for quarterly review.

        Returns:
            True if next_review_date <= today, False otherwise.
        """
        return self.next_review_date <= today_date()

    def complete_review(self) -> None:
        """Mark the vision as reviewed.

        Sets last_reviewed_at to now and next_review_date to 90 days from now.
        """
        self.last_reviewed_at = utc_now()
        self.next_review_date = today_date() + timedelta(days=90)
        self.updated_at = utc_now()
