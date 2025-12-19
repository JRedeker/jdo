"""Time context utilities for AI coaching.

Provides calculations for user time allocation and capacity.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlmodel import Session, select

from jdo.models.commitment import Commitment, CommitmentStatus
from jdo.models.task import Task, TaskStatus


@dataclass
class TimeContext:
    """User's current time context for AI coaching.

    Attributes:
        available_hours: User-reported available hours (None if not set).
        allocated_hours: Sum of estimated hours for active tasks.
        over_allocated: True if allocated > available.
        remaining_capacity: available - allocated (can be negative).
        active_task_count: Number of pending/in-progress tasks with estimates.
        tasks_without_estimates: Number of active tasks missing estimates.
    """

    available_hours: float | None
    allocated_hours: float
    active_task_count: int
    tasks_without_estimates: int

    @property
    def over_allocated(self) -> bool:
        """Check if user is over-allocated."""
        if self.available_hours is None:
            return False
        return self.allocated_hours > self.available_hours

    @property
    def remaining_capacity(self) -> float | None:
        """Calculate remaining capacity (available - allocated).

        Returns:
            Remaining hours, or None if available_hours not set.
        """
        if self.available_hours is None:
            return None
        return self.available_hours - self.allocated_hours

    @property
    def utilization_percent(self) -> float | None:
        """Calculate utilization percentage.

        Returns:
            Percentage of available hours allocated (can exceed 100%), or None.
        """
        if self.available_hours is None or self.available_hours == 0:
            return None
        return (self.allocated_hours / self.available_hours) * 100


def calculate_allocated_hours(session: Session) -> tuple[float, int, int]:
    """Calculate total allocated hours from active tasks.

    Active tasks are those in PENDING or IN_PROGRESS status belonging to
    active commitments (PENDING, IN_PROGRESS, or AT_RISK).

    Args:
        session: Database session.

    Returns:
        Tuple of (total_hours, task_count, tasks_without_estimates).
    """
    # Get active commitment IDs
    active_statuses = [
        CommitmentStatus.PENDING,
        CommitmentStatus.IN_PROGRESS,
        CommitmentStatus.AT_RISK,
    ]
    active_commitments = session.exec(
        select(Commitment.id).where(Commitment.status.in_(active_statuses))  # type: ignore[union-attr]
    ).all()
    active_commitment_ids = set(active_commitments)

    if not active_commitment_ids:
        return 0.0, 0, 0

    # Get tasks for active commitments
    task_statuses = [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]
    tasks = session.exec(
        select(Task).where(
            Task.status.in_(task_statuses),  # type: ignore[union-attr]
        )
    ).all()

    # Filter to active commitments and calculate
    total_hours = 0.0
    task_count = 0
    without_estimates = 0

    for task in tasks:
        if task.commitment_id not in active_commitment_ids:
            continue
        task_count += 1
        if task.estimated_hours is not None:
            total_hours += task.estimated_hours
        else:
            without_estimates += 1

    return total_hours, task_count, without_estimates


def get_time_context(session: Session, available_hours: float | None = None) -> TimeContext:
    """Get the user's current time context.

    Args:
        session: Database session.
        available_hours: User's available hours (from JDODependencies).

    Returns:
        TimeContext with all calculated values.
    """
    allocated, task_count, without_estimates = calculate_allocated_hours(session)

    return TimeContext(
        available_hours=available_hours,
        allocated_hours=allocated,
        active_task_count=task_count,
        tasks_without_estimates=without_estimates,
    )


def format_time_context_for_ai(context: TimeContext) -> str:
    """Format time context as a string for AI consumption.

    Args:
        context: The time context to format.

    Returns:
        Human-readable summary string.
    """
    lines = []

    if context.available_hours is not None:
        lines.append(f"Available hours: {context.available_hours:.1f}")
    else:
        lines.append("Available hours: Not set (ask user)")

    lines.append(f"Allocated hours: {context.allocated_hours:.1f}")
    tasks_with_estimates = context.active_task_count - context.tasks_without_estimates
    lines.append(f"Active tasks with estimates: {tasks_with_estimates}")

    if context.tasks_without_estimates > 0:
        lines.append(f"Active tasks missing estimates: {context.tasks_without_estimates}")

    if context.remaining_capacity is not None:
        if context.remaining_capacity >= 0:
            lines.append(f"Remaining capacity: {context.remaining_capacity:.1f} hours")
        else:
            lines.append(f"OVER-ALLOCATED by {abs(context.remaining_capacity):.1f} hours")

    if context.utilization_percent is not None:
        lines.append(f"Utilization: {context.utilization_percent:.0f}%")

    return "\n".join(lines)
