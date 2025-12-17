"""Database session management."""

from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime
from uuid import UUID

from sqlmodel import Session, func, select

from jdo.db.engine import get_engine
from jdo.models import Commitment, Draft, Goal, Milestone, Vision
from jdo.models.commitment import CommitmentStatus
from jdo.models.goal import GoalProgress, GoalStatus
from jdo.models.milestone import MilestoneStatus
from jdo.models.vision import VisionStatus


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session as a context manager.

    Commits on successful exit, rolls back on exception.

    Yields:
        A SQLModel Session.
    """
    engine = get_engine()
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_visions_due_for_review(session: Session) -> list[Vision]:
    """Get all active visions that are due for review.

    A vision is due for review when:
    - status is ACTIVE
    - next_review_date <= today

    Args:
        session: Database session.

    Returns:
        List of visions due for review.
    """
    today = datetime.now(UTC).date()
    statement = select(Vision).where(
        Vision.status == VisionStatus.ACTIVE,
        Vision.next_review_date <= today,
    )
    return list(session.exec(statement).all())


def get_overdue_milestones(session: Session) -> list[Milestone]:
    """Get all pending or in-progress milestones that are overdue.

    A milestone is overdue when:
    - status is PENDING or IN_PROGRESS
    - target_date < today

    Args:
        session: Database session.

    Returns:
        List of overdue milestones.
    """
    today = datetime.now(UTC).date()
    statement = select(Milestone).where(
        Milestone.status.in_([MilestoneStatus.PENDING, MilestoneStatus.IN_PROGRESS]),
        Milestone.target_date < today,
    )
    return list(session.exec(statement).all())


def update_overdue_milestones(session: Session) -> int:
    """Mark all overdue milestones as missed.

    Args:
        session: Database session.

    Returns:
        Number of milestones marked as missed.
    """
    overdue = get_overdue_milestones(session)
    for milestone in overdue:
        milestone.mark_missed()
        session.add(milestone)
    return len(overdue)


def get_pending_drafts(session: Session) -> list[Draft]:
    """Get all pending drafts.

    Args:
        session: Database session.

    Returns:
        List of pending drafts, ordered by creation date.
    """
    statement = select(Draft).order_by(Draft.created_at.desc())
    return list(session.exec(statement).all())


def delete_draft(session: Session, draft: Draft) -> None:
    """Delete a draft.

    Args:
        session: Database session.
        draft: The draft to delete.
    """
    session.delete(draft)
    session.commit()


def get_goals_due_for_review(session: Session) -> list[Goal]:
    """Get all active goals that are due for review.

    A goal is due for review when:
    - status is ACTIVE
    - next_review_date <= today

    Args:
        session: Database session.

    Returns:
        List of goals due for review.
    """
    today = datetime.now(UTC).date()
    statement = select(Goal).where(
        Goal.status == GoalStatus.ACTIVE,
        Goal.next_review_date <= today,
    )
    return list(session.exec(statement).all())


def get_commitment_progress(session: Session, goal_id: UUID) -> GoalProgress:
    """Get commitment progress summary for a goal.

    Counts commitments by status for the given goal.

    Args:
        session: Database session.
        goal_id: The goal ID to get progress for.

    Returns:
        GoalProgress with counts by status.
    """
    # Query commitment counts by status for this goal
    statement = (
        select(Commitment.status, func.count(Commitment.id))
        .where(Commitment.goal_id == goal_id)
        .group_by(Commitment.status)
    )
    results = session.exec(statement).all()

    # Convert query results to dict, using defaults for missing statuses
    result_counts = dict(results)
    counts = {
        CommitmentStatus.COMPLETED: result_counts.get(CommitmentStatus.COMPLETED, 0),
        CommitmentStatus.IN_PROGRESS: result_counts.get(CommitmentStatus.IN_PROGRESS, 0),
        CommitmentStatus.PENDING: result_counts.get(CommitmentStatus.PENDING, 0),
        CommitmentStatus.ABANDONED: result_counts.get(CommitmentStatus.ABANDONED, 0),
    }

    total = sum(counts.values())

    return GoalProgress(
        total=total,
        completed=counts[CommitmentStatus.COMPLETED],
        in_progress=counts[CommitmentStatus.IN_PROGRESS],
        pending=counts[CommitmentStatus.PENDING],
        abandoned=counts[CommitmentStatus.ABANDONED],
    )
