"""CleanupPlan SQLModel entity for integrity protocol."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from jdo.utils.datetime import utc_now


class CleanupPlanStatus(str, Enum):
    """Status of a cleanup plan for at-risk/abandoned commitments."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class CleanupPlan(SQLModel, table=True):
    """A cleanup plan for when a commitment is at-risk or abandoned.

    CleanupPlans track the recovery workflow when a commitment can't be met:
    - Impact description (what harm does missing this cause?)
    - Mitigation actions (what will you do about it?)
    - Notification task reference (must complete to progress cleanup)
    - Status tracking through the cleanup lifecycle

    This implements MPI's Honor-Your-Word protocol: Notify, then Clean Up.
    """

    __tablename__ = "cleanup_plans"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    commitment_id: UUID = Field(foreign_key="commitments.id")
    impact_description: str | None = Field(default=None)
    mitigation_actions: list[str] = Field(default=[], sa_column=Column(JSON))
    notification_task_id: UUID | None = Field(default=None, foreign_key="tasks.id")
    status: CleanupPlanStatus = Field(default=CleanupPlanStatus.PLANNED)
    completed_at: datetime | None = Field(default=None)
    skipped_reason: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
