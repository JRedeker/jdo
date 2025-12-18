"""Draft SQLModel entity for partial domain object persistence."""

from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


class EntityType(str, Enum):
    """Type of entity being drafted."""

    COMMITMENT = "commitment"
    GOAL = "goal"
    TASK = "task"
    VISION = "vision"
    MILESTONE = "milestone"
    UNKNOWN = "unknown"  # For triage items captured without type


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


class Draft(SQLModel, table=True):
    """A partially created domain object awaiting completion.

    Drafts persist partial data so users can resume creating
    commitments, goals, tasks, visions, or milestones after
    closing the application.

    Only one draft per entity_type is allowed at a time.
    Drafts older than 7 days are flagged for expiration prompt.
    """

    __tablename__ = "drafts"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    entity_type: EntityType
    partial_data: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def is_expired(self) -> bool:
        """Check if this draft is older than 7 days.

        Returns:
            True if draft is MORE than 7 days old (not exactly 7), False otherwise.
        """
        expiration_threshold = datetime.now(UTC) - timedelta(days=7)
        # Use <= to ensure exactly 7 days is NOT expired (strictly more than 7 days)
        return self.created_at < expiration_threshold
