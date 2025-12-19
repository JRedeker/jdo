"""Time rollup service for calculating commitment time totals.

Provides efficient queries for time-based aggregations across tasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlmodel import Session, select

from jdo.models.task import Task, TaskStatus


@dataclass
class TimeRollup:
    """Time rollup data for a commitment.

    Attributes:
        total_estimated_hours: Sum of estimated hours for all tasks.
        remaining_estimated_hours: Sum of estimated hours for incomplete tasks.
        completed_estimated_hours: Sum of estimated hours for completed tasks.
        task_count: Total number of tasks.
        tasks_with_estimates: Number of tasks that have estimates.
        completed_task_count: Number of completed tasks.
    """

    total_estimated_hours: float
    remaining_estimated_hours: float
    completed_estimated_hours: float
    task_count: int
    tasks_with_estimates: int
    completed_task_count: int

    @property
    def has_estimates(self) -> bool:
        """Check if any tasks have time estimates."""
        return self.tasks_with_estimates > 0

    @property
    def estimate_coverage(self) -> float:
        """Percentage of tasks that have time estimates (0-1)."""
        if self.task_count == 0:
            return 0.0
        return self.tasks_with_estimates / self.task_count


class TimeRollupService:
    """Service for calculating time rollups for commitments.

    Provides efficient aggregation queries to avoid N+1 problems.

    Example:
        >>> with get_session() as session:
        ...     service = TimeRollupService(session)
        ...     rollup = service.get_rollup(commitment_id)
        ...     print(f"Total: {rollup.total_estimated_hours}h")

    Args:
        session: Database session used for queries.
    """

    def __init__(self, session: Session) -> None:
        """Initialize the time rollup service.

        Args:
            session: Database session used for queries.
        """
        self.session = session

    def get_rollup(self, commitment_id: UUID) -> TimeRollup:
        """Get time rollup for a commitment.

        Calculates all time totals in a single efficient query.

        Args:
            commitment_id: UUID of the commitment.

        Returns:
            TimeRollup with all calculated values.
        """
        # Get all tasks for this commitment
        statement = select(Task).where(Task.commitment_id == commitment_id)
        tasks = list(self.session.exec(statement).all())

        # Calculate totals
        total_estimated = 0.0
        remaining_estimated = 0.0
        completed_estimated = 0.0
        tasks_with_estimates = 0
        completed_count = 0

        for task in tasks:
            if task.estimated_hours is not None:
                tasks_with_estimates += 1
                total_estimated += task.estimated_hours

                if task.status == TaskStatus.COMPLETED:
                    completed_estimated += task.estimated_hours
                elif task.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS):
                    remaining_estimated += task.estimated_hours

            if task.status == TaskStatus.COMPLETED:
                completed_count += 1

        return TimeRollup(
            total_estimated_hours=total_estimated,
            remaining_estimated_hours=remaining_estimated,
            completed_estimated_hours=completed_estimated,
            task_count=len(tasks),
            tasks_with_estimates=tasks_with_estimates,
            completed_task_count=completed_count,
        )

    def get_rollups_batch(self, commitment_ids: list[UUID]) -> dict[UUID, TimeRollup]:
        """Get time rollups for multiple commitments efficiently.

        Uses individual queries per commitment but avoids N+1 by
        pre-calculating all in one method call.

        Args:
            commitment_ids: List of commitment UUIDs.

        Returns:
            Dict mapping commitment_id to TimeRollup.
        """
        if not commitment_ids:
            return {}

        # Get rollup for each commitment
        # Note: For very large lists, could optimize with raw SQL IN clause
        result: dict[UUID, TimeRollup] = {}
        for commitment_id in commitment_ids:
            result[commitment_id] = self.get_rollup(commitment_id)

        return result

    def get_rollups_batch_optimized(self, commitment_ids: list[UUID]) -> dict[UUID, TimeRollup]:
        """Get time rollups for multiple commitments in a single query.

        More efficient for large batches - fetches all tasks at once.

        Args:
            commitment_ids: List of commitment UUIDs.

        Returns:
            Dict mapping commitment_id to TimeRollup.
        """
        if not commitment_ids:
            return {}

        # Get all tasks - we'll filter in Python
        # This avoids pyrefly issues with .in_() method
        statement = select(Task)
        tasks = list(self.session.exec(statement).all())

        # Group tasks by commitment
        tasks_by_commitment = self._group_tasks_by_commitment(tasks, commitment_ids)

        # Calculate rollups for each commitment
        return {
            cid: self._calculate_rollup_for_tasks(commitment_tasks)
            for cid, commitment_tasks in tasks_by_commitment.items()
        }

    def _group_tasks_by_commitment(
        self, tasks: list[Task], commitment_ids: list[UUID]
    ) -> dict[UUID, list[Task]]:
        """Group tasks by their commitment ID.

        Args:
            tasks: List of all tasks.
            commitment_ids: List of commitment IDs to group by.

        Returns:
            Dict mapping commitment_id to list of tasks.
        """
        tasks_by_commitment: dict[UUID, list[Task]] = {cid: [] for cid in commitment_ids}
        for task in tasks:
            if task.commitment_id in tasks_by_commitment:
                tasks_by_commitment[task.commitment_id].append(task)
        return tasks_by_commitment

    def _calculate_rollup_for_tasks(self, tasks: list[Task]) -> TimeRollup:
        """Calculate time rollup from a list of tasks.

        Args:
            tasks: List of tasks for a single commitment.

        Returns:
            TimeRollup with aggregated estimates and counts.
        """
        total_estimated = 0.0
        remaining_estimated = 0.0
        completed_estimated = 0.0
        tasks_with_estimates = 0
        completed_count = 0

        for task in tasks:
            if task.estimated_hours is not None:
                tasks_with_estimates += 1
                total_estimated += task.estimated_hours

                if task.status == TaskStatus.COMPLETED:
                    completed_estimated += task.estimated_hours
                elif task.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS):
                    remaining_estimated += task.estimated_hours

            if task.status == TaskStatus.COMPLETED:
                completed_count += 1

        return TimeRollup(
            total_estimated_hours=total_estimated,
            remaining_estimated_hours=remaining_estimated,
            completed_estimated_hours=completed_estimated,
            task_count=len(tasks),
            tasks_with_estimates=tasks_with_estimates,
            completed_task_count=completed_count,
        )
