"""Cleanup utilities for UAT.

Provides functions to clean up test data created during UAT runs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from loguru import logger
from sqlmodel import Session, select

from jdo.models import Commitment, Goal, Milestone, Stakeholder, Task, Vision


@dataclass
class EntityCounts:
    """Counts of entities in the database."""

    visions: int = 0
    goals: int = 0
    milestones: int = 0
    stakeholders: int = 0
    commitments: int = 0
    tasks: int = 0

    @property
    def total(self) -> int:
        """Total number of entities."""
        return (
            self.visions
            + self.goals
            + self.milestones
            + self.stakeholders
            + self.commitments
            + self.tasks
        )

    def __str__(self) -> str:
        """Format as string."""
        return (
            f"Visions: {self.visions}, Goals: {self.goals}, "
            f"Milestones: {self.milestones}, Stakeholders: {self.stakeholders}, "
            f"Commitments: {self.commitments}, Tasks: {self.tasks}"
        )


def get_entity_counts(session: Session) -> EntityCounts:
    """Get counts of all entities in the database.

    Args:
        session: Database session.

    Returns:
        EntityCounts with current counts.
    """
    return EntityCounts(
        visions=len(session.exec(select(Vision)).all()),
        goals=len(session.exec(select(Goal)).all()),
        milestones=len(session.exec(select(Milestone)).all()),
        stakeholders=len(session.exec(select(Stakeholder)).all()),
        commitments=len(session.exec(select(Commitment)).all()),
        tasks=len(session.exec(select(Task)).all()),
    )


def cleanup_test_entities(
    session: Session,
    created_after: datetime,
    *,
    dry_run: bool = False,
) -> EntityCounts:
    """Delete all entities created after a given timestamp.

    Deletes in dependency order to respect foreign keys:
    1. Tasks (depend on commitments)
    2. Commitments (depend on goals, stakeholders)
    3. Milestones (depend on goals)
    4. Goals (depend on visions)
    5. Stakeholders (standalone)
    6. Visions (standalone)

    Args:
        session: Database session.
        created_after: Delete entities created after this time.
        dry_run: If True, don't actually delete, just count.

    Returns:
        EntityCounts of deleted entities.
    """
    deleted = EntityCounts()

    # 1. Delete Tasks
    tasks = session.exec(select(Task).where(Task.created_at >= created_after)).all()
    deleted.tasks = len(tasks)
    if not dry_run:
        for task in tasks:
            session.delete(task)
        logger.debug(f"Deleted {deleted.tasks} tasks")

    # 2. Delete Commitments
    commitments = session.exec(
        select(Commitment).where(Commitment.created_at >= created_after)
    ).all()
    deleted.commitments = len(commitments)
    if not dry_run:
        for commitment in commitments:
            session.delete(commitment)
        logger.debug(f"Deleted {deleted.commitments} commitments")

    # 3. Delete Milestones
    milestones = session.exec(select(Milestone).where(Milestone.created_at >= created_after)).all()
    deleted.milestones = len(milestones)
    if not dry_run:
        for milestone in milestones:
            session.delete(milestone)
        logger.debug(f"Deleted {deleted.milestones} milestones")

    # 4. Delete Goals
    goals = session.exec(select(Goal).where(Goal.created_at >= created_after)).all()
    deleted.goals = len(goals)
    if not dry_run:
        for goal in goals:
            session.delete(goal)
        logger.debug(f"Deleted {deleted.goals} goals")

    # 5. Delete Stakeholders
    stakeholders = session.exec(
        select(Stakeholder).where(Stakeholder.created_at >= created_after)
    ).all()
    deleted.stakeholders = len(stakeholders)
    if not dry_run:
        for stakeholder in stakeholders:
            session.delete(stakeholder)
        logger.debug(f"Deleted {deleted.stakeholders} stakeholders")

    # 6. Delete Visions
    visions = session.exec(select(Vision).where(Vision.created_at >= created_after)).all()
    deleted.visions = len(visions)
    if not dry_run:
        for vision in visions:
            session.delete(vision)
        logger.debug(f"Deleted {deleted.visions} visions")

    if not dry_run:
        session.commit()
        logger.info(f"UAT cleanup complete: {deleted}")

    return deleted
