"""Instance generation for recurring commitments."""

from datetime import date, timedelta

from jdo.models.commitment import Commitment, CommitmentStatus, default_due_time
from jdo.models.recurring_commitment import RecurringCommitment, TaskTemplate
from jdo.models.task import Task, TaskStatus
from jdo.recurrence.calculator import get_next_due_date

# Default window in days for upcoming instance generation
DEFAULT_GENERATION_WINDOW_DAYS = 7


def generate_instance(
    recurring: RecurringCommitment,
    due_date: date,
) -> tuple[Commitment, list[Task]]:
    """Generate a Commitment instance from a RecurringCommitment template.

    Args:
        recurring: The recurring commitment template.
        due_date: The due date for the generated commitment.

    Returns:
        A tuple of (Commitment, list[Task]) representing the generated instance.
        Note: The entities are NOT saved to the database - that's the caller's
        responsibility.
    """
    # Create the commitment
    commitment = Commitment(
        deliverable=recurring.deliverable_template,
        stakeholder_id=recurring.stakeholder_id,
        goal_id=recurring.goal_id,
        due_date=due_date,
        due_time=recurring.due_time if recurring.due_time else default_due_time(),
        timezone=recurring.timezone,
        notes=recurring.notes,
        recurring_commitment_id=recurring.id,
        status=CommitmentStatus.PENDING,
    )

    # Copy task templates
    tasks = _create_tasks_from_templates(commitment.id, recurring.get_task_templates())

    return commitment, tasks


def _create_tasks_from_templates(
    commitment_id,  # noqa: ANN001 - UUID type
    templates: list[TaskTemplate],
) -> list[Task]:
    """Create Task instances from TaskTemplates.

    All tasks are created with status=PENDING and sub-tasks with completed=False.
    """
    tasks = []
    for template in templates:
        # Convert SubTaskTemplate list to dicts for JSON storage
        sub_tasks_data = [
            {"description": st.description, "completed": False} for st in template.sub_tasks
        ]

        task = Task(
            commitment_id=commitment_id,
            title=template.title,
            scope=template.scope,
            order=template.order,
            status=TaskStatus.PENDING,
            sub_tasks=sub_tasks_data,
        )
        tasks.append(task)

    return tasks


def should_generate_instance(
    recurring: RecurringCommitment,
    current_date: date,
    window_days: int = DEFAULT_GENERATION_WINDOW_DAYS,
) -> bool:
    """Check if a new instance should be generated.

    Generation should occur if:
    1. The recurrence is active (not paused)
    2. The recurrence hasn't ended (count or date)
    3. The next due date is within the window from current_date

    Args:
        recurring: The recurring commitment to check.
        current_date: The current date to calculate from.
        window_days: Number of days ahead to look for due dates.

    Returns:
        True if an instance should be generated, False otherwise.
    """
    # Get the reference date - either last generated or current
    reference_date = recurring.last_generated_date or (current_date - timedelta(days=1))

    # Calculate next due date
    next_due = get_next_due_date(recurring, after_date=reference_date)

    if next_due is None:
        return False

    # Check if within window
    window_end = current_date + timedelta(days=window_days)
    return next_due <= window_end
