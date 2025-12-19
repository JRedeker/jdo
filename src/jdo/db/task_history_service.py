"""Task history service for logging task lifecycle events.

Provides centralized logging of task events to the task_history table.
Events are immutable and form an audit log that survives task deletion.
"""

from __future__ import annotations

from uuid import UUID

from loguru import logger
from sqlmodel import Session, select

from jdo.models.task import ActualHoursCategory, Task, TaskStatus
from jdo.models.task_history import TaskEventType, TaskHistoryEntry


class TaskHistoryService:
    """Service for logging task lifecycle events.

    Creates immutable audit log entries for task status transitions.
    These entries are used by the AI for pattern analysis and coaching.

    Example:
        >>> with get_session() as session:
        ...     service = TaskHistoryService(session)
        ...     service.log_task_created(task)

    Args:
        session: Database session used for all operations.
    """

    def __init__(self, session: Session) -> None:
        """Initialize the task history service.

        Args:
            session: Database session used for all operations.
        """
        self.session = session

    def log_event(
        self,
        task_id: UUID,
        commitment_id: UUID,
        event_type: TaskEventType,
        new_status: TaskStatus,
        previous_status: TaskStatus | None = None,
        estimated_hours: float | None = None,
        actual_hours_category: ActualHoursCategory | None = None,
        notes: str | None = None,
    ) -> TaskHistoryEntry:
        """Log a task lifecycle event.

        Creates an immutable history entry for the event. This is the
        low-level method - prefer using convenience methods like
        log_task_created() or log_status_change() when possible.

        Args:
            task_id: UUID of the task.
            commitment_id: UUID of the parent commitment (denormalized).
            event_type: Type of event (CREATED, STARTED, COMPLETED, etc.).
            new_status: The task's new status after this event.
            previous_status: The task's status before this event (None for CREATED).
            estimated_hours: Snapshot of estimated hours at event time.
            actual_hours_category: Category for completed events (None otherwise).
            notes: Optional notes (e.g., skip reason).

        Returns:
            The created TaskHistoryEntry.
        """
        entry = TaskHistoryEntry(
            task_id=task_id,
            commitment_id=commitment_id,
            event_type=event_type,
            previous_status=previous_status,
            new_status=new_status,
            estimated_hours=estimated_hours,
            actual_hours_category=actual_hours_category,
            notes=notes,
        )
        self.session.add(entry)
        self.session.flush()

        logger.debug(
            f"Logged task history: {event_type.value} for task {task_id} "
            f"(commitment={commitment_id})"
        )
        return entry

    def log_task_created(self, task: Task) -> TaskHistoryEntry:
        """Log a CREATED event for a new task.

        Convenience method that extracts all relevant fields from the task.

        Args:
            task: The newly created task.

        Returns:
            The created TaskHistoryEntry.
        """
        return self.log_event(
            task_id=task.id,
            commitment_id=task.commitment_id,
            event_type=TaskEventType.CREATED,
            new_status=task.status,
            estimated_hours=task.estimated_hours,
        )

    def log_status_change(
        self,
        task: Task,
        old_status: TaskStatus,
        new_status: TaskStatus,
        actual_hours_category: ActualHoursCategory | None = None,
        notes: str | None = None,
    ) -> TaskHistoryEntry:
        """Log a status change event for a task.

        Determines the appropriate event type based on the new status:
        - IN_PROGRESS -> STARTED
        - COMPLETED -> COMPLETED
        - SKIPPED -> SKIPPED (or ABANDONED if from IN_PROGRESS)

        Args:
            task: The task being updated.
            old_status: The task's previous status.
            new_status: The task's new status.
            actual_hours_category: Category for completed tasks (optional).
            notes: Optional notes (e.g., skip reason).

        Returns:
            The created TaskHistoryEntry.
        """
        # Determine event type from status transition
        event_type = self._get_event_type_for_transition(old_status, new_status)

        return self.log_event(
            task_id=task.id,
            commitment_id=task.commitment_id,
            event_type=event_type,
            previous_status=old_status,
            new_status=new_status,
            estimated_hours=task.estimated_hours,
            actual_hours_category=actual_hours_category,
            notes=notes,
        )

    def get_history_for_task(self, task_id: UUID) -> list[TaskHistoryEntry]:
        """Get all history entries for a specific task.

        Args:
            task_id: UUID of the task.

        Returns:
            List of history entries ordered by created_at.
        """
        statement = (
            select(TaskHistoryEntry)
            .where(TaskHistoryEntry.task_id == task_id)
            .order_by(TaskHistoryEntry.created_at)  # type: ignore[arg-type]
        )
        return list(self.session.exec(statement).all())

    def get_history_for_commitment(self, commitment_id: UUID) -> list[TaskHistoryEntry]:
        """Get all history entries for a commitment (all its tasks).

        Uses the denormalized commitment_id for efficient querying.

        Args:
            commitment_id: UUID of the commitment.

        Returns:
            List of history entries ordered by created_at.
        """
        statement = (
            select(TaskHistoryEntry)
            .where(TaskHistoryEntry.commitment_id == commitment_id)
            .order_by(TaskHistoryEntry.created_at)  # type: ignore[arg-type]
        )
        return list(self.session.exec(statement).all())

    def _get_event_type_for_transition(
        self, old_status: TaskStatus, new_status: TaskStatus
    ) -> TaskEventType:
        """Determine the event type for a status transition.

        Args:
            old_status: The task's previous status.
            new_status: The task's new status.

        Returns:
            The appropriate TaskEventType.
        """
        if new_status == TaskStatus.IN_PROGRESS:
            return TaskEventType.STARTED
        if new_status == TaskStatus.COMPLETED:
            return TaskEventType.COMPLETED
        if new_status == TaskStatus.SKIPPED:
            # ABANDONED if coming from IN_PROGRESS, otherwise SKIPPED
            if old_status == TaskStatus.IN_PROGRESS:
                return TaskEventType.ABANDONED
            return TaskEventType.SKIPPED

        # Fallback - shouldn't happen with current statuses
        return TaskEventType.STARTED
