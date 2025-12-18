"""Database session management."""

from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlmodel import Session, func, select

from jdo.db.engine import get_engine
from jdo.models import Commitment, Draft, Goal, Milestone, RecurringCommitment, Vision
from jdo.models.commitment import CommitmentStatus
from jdo.models.draft import EntityType
from jdo.models.goal import GoalProgress, GoalStatus
from jdo.models.milestone import MilestoneStatus
from jdo.models.recurring_commitment import RecurringCommitmentStatus
from jdo.models.task import Task
from jdo.models.vision import VisionStatus
from jdo.recurrence.calculator import get_next_due_date
from jdo.recurrence.generator import generate_instance, should_generate_instance


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


def get_active_recurring_commitments(session: Session) -> list[RecurringCommitment]:
    """Get all active recurring commitments.

    Args:
        session: Database session.

    Returns:
        List of active recurring commitments.
    """
    statement = select(RecurringCommitment).where(
        RecurringCommitment.status == RecurringCommitmentStatus.ACTIVE,
    )
    return list(session.exec(statement).all())


def check_and_generate_recurring_instances(
    session: Session,
    current_date: datetime | None = None,
) -> list[tuple[Commitment, list[Task]]]:
    """Check all active recurring commitments and generate instances if due.

    This is the main trigger function called when viewing upcoming commitments.
    It checks all active recurring commitments and generates new instances
    for those that are due within the generation window.

    Args:
        session: Database session.
        current_date: Current date for calculation. If None, uses today.

    Returns:
        List of (Commitment, list[Task]) tuples for generated instances.
    """
    if current_date is None:
        current_date = datetime.now(UTC)

    today = current_date.date()
    generated: list[tuple[Commitment, list[Task]]] = []

    # Get all active recurring commitments
    recurring_list = get_active_recurring_commitments(session)

    for recurring in recurring_list:
        # Check if we should generate
        if not should_generate_instance(recurring, today):
            continue

        # Calculate the next due date
        reference_date = recurring.last_generated_date or (today - timedelta(days=1))
        next_due = get_next_due_date(recurring, after_date=reference_date)

        if next_due is None:
            continue

        # Generate the instance
        commitment, tasks = generate_instance(recurring, due_date=next_due)

        # Update the recurring commitment tracking
        recurring.last_generated_date = next_due
        recurring.instances_generated += 1
        recurring.updated_at = current_date

        # Save all entities
        session.add(recurring)
        session.add(commitment)
        for task in tasks:
            session.add(task)

        generated.append((commitment, tasks))

    return generated


def generate_next_instance_for_recurring(
    session: Session,
    recurring_commitment_id: UUID,
    current_date: datetime | None = None,
) -> tuple[Commitment, list[Task]] | None:
    """Generate the next instance for a specific recurring commitment.

    This is called when a recurring commitment instance is completed
    to trigger generation of the next instance.

    Args:
        session: Database session.
        recurring_commitment_id: The ID of the recurring commitment.
        current_date: Current date for calculation. If None, uses today.

    Returns:
        Tuple of (Commitment, list[Task]) if generated, None otherwise.
    """
    if current_date is None:
        current_date = datetime.now(UTC)

    today = current_date.date()

    # Get the recurring commitment
    recurring = session.get(RecurringCommitment, recurring_commitment_id)
    if recurring is None:
        return None

    if recurring.status != RecurringCommitmentStatus.ACTIVE:
        return None

    # Calculate next due date from the last generated date
    reference_date = recurring.last_generated_date or today
    next_due = get_next_due_date(recurring, after_date=reference_date)

    if next_due is None:
        return None

    # Generate the instance
    commitment, tasks = generate_instance(recurring, due_date=next_due)

    # Update tracking
    recurring.last_generated_date = next_due
    recurring.instances_generated += 1
    recurring.updated_at = current_date

    # Save
    session.add(recurring)
    session.add(commitment)
    for task in tasks:
        session.add(task)

    return (commitment, tasks)


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


def get_triage_items(session: Session) -> list[Draft]:
    """Get all drafts with UNKNOWN entity type for triage.

    Returns items in FIFO order (oldest first) for processing.

    Args:
        session: Database session.

    Returns:
        List of drafts needing triage, ordered by creation date (oldest first).
    """
    statement = (
        select(Draft)
        .where(
            Draft.entity_type == EntityType.UNKNOWN,
        )
        .order_by(Draft.created_at.asc())
    )
    return list(session.exec(statement).all())


def get_triage_count(session: Session) -> int:
    """Get count of items needing triage.

    Args:
        session: Database session.

    Returns:
        Number of drafts with UNKNOWN entity type.
    """
    statement = select(func.count(Draft.id)).where(
        Draft.entity_type == EntityType.UNKNOWN,
    )
    result = session.exec(statement).one()
    return int(result)
