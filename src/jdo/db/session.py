"""Database session management."""

from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime

from sqlmodel import Session, select

from jdo.db.engine import get_engine
from jdo.models import Draft, Milestone, Vision
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
