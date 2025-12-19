"""Persistence service for saving entities to the database.

Provides a centralized service for creating and saving entities from draft data.
Handlers return draft_data dicts, and this service converts them to database entities.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from uuid import UUID

from loguru import logger
from sqlmodel import Session, func, select

from jdo.db.task_history_service import TaskHistoryService
from jdo.exceptions import JDOError
from jdo.models import (
    Commitment,
    Goal,
    Milestone,
    RecurringCommitment,
    Stakeholder,
    StakeholderType,
    Task,
    Vision,
)
from jdo.models.recurring_commitment import RecurrenceType
from jdo.models.task import ActualHoursCategory, TaskStatus
from jdo.recurrence.calculator import get_next_due_date
from jdo.recurrence.generator import generate_instance


class PersistenceError(JDOError):
    """Error raised when persistence operations fail."""


class ValidationError(PersistenceError):
    """Error raised when draft data validation fails."""


class PersistenceService:
    """Service for persisting entities to the database.

    Centralizes persistence logic outside command handlers so handlers remain
    pure (they only build draft_data). Each ``save_*`` method takes draft data
    gathered during the conversation, converts it into the appropriate SQLModel
    entity, and writes it to the database using the provided session.

    Example:
        >>> with get_session() as session:
        ...     service = PersistenceService(session)
        ...     commitment = service.save_commitment(draft)

    Args:
        session: Database session used for all persistence operations.
    """

    def __init__(self, session: Session) -> None:
        """Initialize the persistence service.

        Args:
            session: Database session used for all persistence operations.
        """
        self.session = session

    def get_or_create_stakeholder(self, name: str) -> Stakeholder:
        """Get an existing stakeholder by name or create a new one.

        Uses case-insensitive matching to avoid duplicate stakeholders
        from different capitalizations (e.g., "Sarah" vs "sarah").

        Args:
            name: The stakeholder name to find or create.

        Returns:
            Existing or newly created Stakeholder.

        Raises:
            ValidationError: If name is empty.
        """
        if not name or not name.strip():
            msg = "Stakeholder name cannot be empty"
            raise ValidationError(msg)

        name = name.strip()

        # Case-insensitive search using func.lower()
        statement = select(Stakeholder).where(func.lower(Stakeholder.name) == name.lower())
        existing = self.session.exec(statement).first()

        if existing:
            logger.debug(f"Found existing stakeholder: {existing.name}")
            return existing

        # Create new stakeholder - default to PERSON type
        stakeholder = Stakeholder(
            name=name,
            type=StakeholderType.PERSON,
        )
        self.session.add(stakeholder)
        self.session.flush()  # Get ID without committing
        logger.info(f"Created new stakeholder: {stakeholder.name} (id={stakeholder.id})")
        return stakeholder

    def save_commitment(self, draft_data: dict[str, Any]) -> Commitment:
        """Create and save a commitment from draft data.

        Args:
            draft_data: Dict with commitment fields:
                - deliverable (required): What will be delivered
                - stakeholder (required): Name of stakeholder
                - due_date (required): Due date (date or str)
                - due_time (optional): Due time (time or str)
                - goal_id (optional): UUID of linked goal
                - milestone_id (optional): UUID of linked milestone

        Returns:
            The saved Commitment entity.

        Raises:
            ValidationError: If required fields are missing.
        """
        # Validate required fields
        self._require_fields(draft_data, ["deliverable", "stakeholder", "due_date"])

        # Get or create stakeholder
        stakeholder = self.get_or_create_stakeholder(draft_data["stakeholder"])

        # Parse due_date
        due_date = self._parse_date(draft_data["due_date"])

        # Parse optional due_time
        due_time = self._parse_time(draft_data.get("due_time"))

        # Create commitment
        commitment = Commitment(
            deliverable=draft_data["deliverable"],
            stakeholder_id=stakeholder.id,
            due_date=due_date,
            due_time=due_time if due_time else time(9, 0),  # Default 9am
            goal_id=self._parse_uuid(draft_data.get("goal_id")),
            milestone_id=self._parse_uuid(draft_data.get("milestone_id")),
        )

        self.session.add(commitment)
        self.session.flush()
        logger.info(f"Saved commitment: {commitment.deliverable} (id={commitment.id})")
        return commitment

    def save_goal(self, draft_data: dict[str, Any]) -> Goal:
        """Create and save a goal from draft data.

        Args:
            draft_data: Dict with goal fields:
                - title (required): Goal title
                - problem_statement (required): What problem is being solved
                - solution_vision (required): What success looks like
                - motivation (optional): Why this matters
                - vision_id (optional): UUID of linked vision

        Returns:
            The saved Goal entity.

        Raises:
            ValidationError: If required fields are missing.
        """
        self._require_fields(draft_data, ["title", "problem_statement", "solution_vision"])

        goal = Goal(
            title=draft_data["title"],
            problem_statement=draft_data["problem_statement"],
            solution_vision=draft_data["solution_vision"],
            motivation=draft_data.get("motivation"),
            vision_id=self._parse_uuid(draft_data.get("vision_id")),
        )

        self.session.add(goal)
        self.session.flush()
        logger.info(f"Saved goal: {goal.title} (id={goal.id})")
        return goal

    def save_task(self, draft_data: dict[str, Any]) -> Task:
        """Create and save a task from draft data.

        Args:
            draft_data: Dict with task fields:
                - title (required): Task title
                - scope (required): What "done" means for this task
                - commitment_id (required): UUID of parent commitment
                - order (optional): Order within commitment (default 0)
                - sub_tasks (optional): List of subtask dicts
                - estimated_hours (optional): Time estimate in hours

        Returns:
            The saved Task entity.

        Raises:
            ValidationError: If required fields are missing.
        """
        self._require_fields(draft_data, ["title", "commitment_id"])

        # Default scope to title if not provided
        scope = draft_data.get("scope") or draft_data["title"]

        # Get order - count existing tasks for this commitment
        commitment_id = self._parse_uuid(draft_data["commitment_id"])
        if commitment_id is None:
            msg = "commitment_id is required for task"
            raise ValidationError(msg)

        order = draft_data.get("order")
        if order is None:
            # Get next order number
            statement = (
                select(func.count()).select_from(Task).where(Task.commitment_id == commitment_id)
            )
            existing_count = self.session.exec(statement).one()
            order = existing_count

        task = Task(
            title=draft_data["title"],
            scope=scope,
            commitment_id=commitment_id,
            order=order,
            sub_tasks=draft_data.get("sub_tasks", []),
            estimated_hours=draft_data.get("estimated_hours"),
        )

        self.session.add(task)
        self.session.flush()

        # Log task creation to history
        history_service = TaskHistoryService(self.session)
        history_service.log_task_created(task)

        logger.info(f"Saved task: {task.title} (id={task.id})")
        return task

    def update_task_status(
        self,
        task: Task,
        new_status: TaskStatus,
        actual_hours_category: ActualHoursCategory | None = None,
        notes: str | None = None,
    ) -> Task:
        """Update a task's status and log history.

        Args:
            task: The task to update.
            new_status: The new status to set.
            actual_hours_category: Category for completed tasks (optional).
            notes: Optional notes (e.g., skip reason).

        Returns:
            The updated task.
        """
        old_status = task.status
        task.status = new_status

        # Store actual hours category if completing
        if new_status == TaskStatus.COMPLETED and actual_hours_category is not None:
            task.actual_hours_category = actual_hours_category

        self.session.add(task)
        self.session.flush()

        # Log status change to history
        history_service = TaskHistoryService(self.session)
        history_service.log_status_change(
            task=task,
            old_status=old_status,
            new_status=new_status,
            actual_hours_category=actual_hours_category,
            notes=notes,
        )

        logger.info(f"Updated task status: {task.title} {old_status.value} -> {new_status.value}")
        return task

    def save_milestone(self, draft_data: dict[str, Any]) -> Milestone:
        """Create and save a milestone from draft data.

        Args:
            draft_data: Dict with milestone fields:
                - title (required): Milestone title
                - goal_id (required): UUID of parent goal
                - target_date (required): Target completion date
                - description (optional): Additional description

        Returns:
            The saved Milestone entity.

        Raises:
            ValidationError: If required fields are missing.
        """
        self._require_fields(draft_data, ["title", "goal_id", "target_date"])

        goal_id = self._parse_uuid(draft_data["goal_id"])
        if goal_id is None:
            msg = "goal_id is required for milestone"
            raise ValidationError(msg)

        target_date = self._parse_date(draft_data["target_date"])

        milestone = Milestone(
            title=draft_data["title"],
            goal_id=goal_id,
            target_date=target_date,
            description=draft_data.get("description"),
        )

        self.session.add(milestone)
        self.session.flush()
        logger.info(f"Saved milestone: {milestone.title} (id={milestone.id})")
        return milestone

    def save_vision(self, draft_data: dict[str, Any]) -> Vision:
        """Create and save a vision from draft data.

        Args:
            draft_data: Dict with vision fields:
                - title (required): Vision title
                - narrative (required): Vivid description of future state
                - timeframe (optional): e.g., "3-5 years"
                - metrics (optional): List of success metrics
                - why_it_matters (optional): Why this vision matters

        Returns:
            The saved Vision entity.

        Raises:
            ValidationError: If required fields are missing.
        """
        self._require_fields(draft_data, ["title", "narrative"])

        vision = Vision(
            title=draft_data["title"],
            narrative=draft_data["narrative"],
            timeframe=draft_data.get("timeframe"),
            metrics=draft_data.get("metrics", []),
            why_it_matters=draft_data.get("why_it_matters"),
        )

        self.session.add(vision)
        self.session.flush()
        logger.info(f"Saved vision: {vision.title} (id={vision.id})")
        return vision

    def save_recurring_commitment(self, draft_data: dict[str, Any]) -> RecurringCommitment:
        """Create and save a recurring commitment from draft data.

        Args:
            draft_data: Dict with recurring commitment fields:
                - deliverable_template (required): Template for deliverable
                - stakeholder_name (required): Name of stakeholder
                - recurrence_type (required): daily, weekly, monthly, yearly
                - interval (optional): Every N periods (default 1)
                - days_of_week (optional): List of days 0-6 for weekly
                - day_of_month (optional): Day 1-31 for monthly
                - week_of_month (optional): Week 1-5 or -1 for monthly
                - month_of_year (optional): Month 1-12 for yearly
                - due_time (optional): Time of day
                - goal_id (optional): UUID of linked goal

        Returns:
            The saved RecurringCommitment entity.

        Raises:
            ValidationError: If required fields are missing or invalid.
        """
        self._require_fields(
            draft_data, ["deliverable_template", "stakeholder_name", "recurrence_type"]
        )

        # Get or create stakeholder
        stakeholder = self.get_or_create_stakeholder(draft_data["stakeholder_name"])

        # Parse recurrence type
        recurrence_type_str = draft_data["recurrence_type"]
        try:
            recurrence_type = RecurrenceType(recurrence_type_str.lower())
        except ValueError as e:
            msg = f"Invalid recurrence_type: {recurrence_type_str}"
            raise ValidationError(msg) from e

        # Build recurring commitment
        recurring = RecurringCommitment(
            deliverable_template=draft_data["deliverable_template"],
            stakeholder_id=stakeholder.id,
            recurrence_type=recurrence_type,
            interval=draft_data.get("interval", 1),
            days_of_week=draft_data.get("days_of_week"),
            day_of_month=draft_data.get("day_of_month"),
            week_of_month=draft_data.get("week_of_month"),
            month_of_year=draft_data.get("month_of_year"),
            due_time=self._parse_time(draft_data.get("due_time")),
            goal_id=self._parse_uuid(draft_data.get("goal_id")),
        )

        self.session.add(recurring)
        self.session.flush()

        # Generate the first instance immediately so users see a concrete commitment.
        # This also validates the recurrence pattern end-to-end.
        # Use a reference date of "yesterday" so the first instance can be today
        # (matches the logic used by recurring instance generation elsewhere).
        today = datetime.now(UTC).date()
        reference_date = recurring.last_generated_date or (today - timedelta(days=1))
        due_date = get_next_due_date(recurring, after_date=reference_date)
        if due_date is None:
            msg = "Recurring commitment did not yield a next due date"
            raise ValidationError(msg)

        commitment, tasks = generate_instance(recurring, due_date=due_date)
        self.session.add(commitment)
        for task in tasks:
            self.session.add(task)

        recurring.last_generated_date = due_date
        recurring.instances_generated += 1

        self.session.flush()
        logger.info(
            f"Saved recurring commitment: {recurring.deliverable_template} (id={recurring.id})"
        )
        return recurring

    def _require_fields(self, draft_data: dict[str, Any], required: list[str]) -> None:
        """Validate that required fields are present and non-empty.

        Args:
            draft_data: The draft data dict to validate.
            required: List of required field names.

        Raises:
            ValidationError: If any required field is missing or empty.
        """
        missing = []
        for field in required:
            value = draft_data.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(field)

        if missing:
            msg = f"Missing required fields: {', '.join(missing)}"
            raise ValidationError(msg)

    def _parse_date(self, value: Any) -> date:  # noqa: ANN401
        """Parse a value to a date object.

        Args:
            value: Date, string (YYYY-MM-DD), or None.

        Returns:
            Parsed date object.

        Raises:
            ValidationError: If value cannot be parsed.
        """
        if isinstance(value, date):
            return value

        if isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError as e:
                msg = f"Invalid date format: {value}"
                raise ValidationError(msg) from e

        msg = f"Cannot parse date from: {value}"
        raise ValidationError(msg)

    def _parse_time(self, value: Any) -> time | None:  # noqa: ANN401
        """Parse a value to a time object.

        Args:
            value: Time, string (HH:MM or HH:MM:SS), or None.

        Returns:
            Parsed time object or None.

        Raises:
            ValidationError: If a string is provided but cannot be parsed.
        """
        if value is None:
            return None

        if isinstance(value, time):
            return value

        if isinstance(value, str):
            try:
                return time.fromisoformat(value)
            except ValueError as e:
                msg = f"Invalid time format: {value}"
                raise ValidationError(msg) from e

        msg = f"Cannot parse time from: {value}"
        raise ValidationError(msg)

    def _parse_uuid(self, value: Any) -> UUID | None:  # noqa: ANN401
        """Parse a value to a UUID.

        Args:
            value: UUID, string, or None.

        Returns:
            Parsed UUID or None.
        """
        if value is None:
            return None

        if isinstance(value, UUID):
            return value

        if isinstance(value, str):
            try:
                return UUID(value)
            except ValueError:
                return None

        return None
