"""Tests for instance generation - TDD Red phase."""

from datetime import date, time
from uuid import uuid4

import pytest

from jdo.models.commitment import Commitment
from jdo.models.recurring_commitment import (
    RecurrenceType,
    RecurringCommitment,
    TaskTemplate,
)
from jdo.models.task import Task


class TestGenerateInstance:
    """Tests for generate_instance function."""

    def test_creates_commitment_from_template(self) -> None:
        """generate_instance creates Commitment from template."""
        from jdo.recurrence.generator import generate_instance

        stakeholder_id = uuid4()
        recurring = RecurringCommitment(
            deliverable_template="Weekly report",
            stakeholder_id=stakeholder_id,
            recurrence_type=RecurrenceType.WEEKLY,
            days_of_week=[0],
        )

        commitment, tasks = generate_instance(recurring, due_date=date(2025, 12, 22))

        assert isinstance(commitment, Commitment)
        assert commitment.deliverable == "Weekly report"

    def test_commitment_has_correct_stakeholder(self) -> None:
        """Generated commitment has correct stakeholder_id."""
        from jdo.recurrence.generator import generate_instance

        stakeholder_id = uuid4()
        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=stakeholder_id,
            recurrence_type=RecurrenceType.DAILY,
        )

        commitment, _ = generate_instance(recurring, due_date=date(2025, 12, 22))

        assert commitment.stakeholder_id == stakeholder_id

    def test_commitment_has_correct_due_date(self) -> None:
        """Generated commitment has correct due_date."""
        from jdo.recurrence.generator import generate_instance

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
        )

        commitment, _ = generate_instance(recurring, due_date=date(2025, 12, 22))

        assert commitment.due_date == date(2025, 12, 22)

    def test_commitment_has_recurring_commitment_id_set(self) -> None:
        """Generated commitment has recurring_commitment_id set."""
        from jdo.recurrence.generator import generate_instance

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
        )

        commitment, _ = generate_instance(recurring, due_date=date(2025, 12, 22))

        assert commitment.recurring_commitment_id == recurring.id

    def test_commitment_inherits_optional_goal_id(self) -> None:
        """Generated commitment inherits goal_id from template."""
        from jdo.recurrence.generator import generate_instance

        goal_id = uuid4()
        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            goal_id=goal_id,
            recurrence_type=RecurrenceType.DAILY,
        )

        commitment, _ = generate_instance(recurring, due_date=date(2025, 12, 22))

        assert commitment.goal_id == goal_id

    def test_commitment_inherits_due_time(self) -> None:
        """Generated commitment inherits due_time from template."""
        from jdo.recurrence.generator import generate_instance

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            due_time=time(14, 30),
        )

        commitment, _ = generate_instance(recurring, due_date=date(2025, 12, 22))

        assert commitment.due_time == time(14, 30)

    def test_commitment_inherits_timezone(self) -> None:
        """Generated commitment inherits timezone from template."""
        from jdo.recurrence.generator import generate_instance

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            timezone="America/Los_Angeles",
        )

        commitment, _ = generate_instance(recurring, due_date=date(2025, 12, 22))

        assert commitment.timezone == "America/Los_Angeles"

    def test_commitment_inherits_notes(self) -> None:
        """Generated commitment inherits notes from template."""
        from jdo.recurrence.generator import generate_instance

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            notes="Important notes",
        )

        commitment, _ = generate_instance(recurring, due_date=date(2025, 12, 22))

        assert commitment.notes == "Important notes"


class TestTaskTemplateCopying:
    """Tests for task template copying during generation."""

    def test_tasks_copied_from_templates(self) -> None:
        """Tasks are copied from task_templates."""
        from jdo.recurrence.generator import generate_instance

        templates = [
            TaskTemplate(title="Task 1", scope="Scope 1", order=1),
            TaskTemplate(title="Task 2", scope="Scope 2", order=2),
        ]

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            task_templates=[t.model_dump() for t in templates],
        )

        commitment, tasks = generate_instance(recurring, due_date=date(2025, 12, 22))

        assert len(tasks) == 2
        assert tasks[0].title == "Task 1"
        assert tasks[1].title == "Task 2"

    def test_tasks_have_pending_status(self) -> None:
        """Copied tasks all have status=pending."""
        from jdo.models.task import TaskStatus
        from jdo.recurrence.generator import generate_instance

        templates = [
            TaskTemplate(title="Task 1", scope="Scope 1", order=1),
        ]

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            task_templates=[t.model_dump() for t in templates],
        )

        commitment, tasks = generate_instance(recurring, due_date=date(2025, 12, 22))

        assert tasks[0].status == TaskStatus.PENDING

    def test_tasks_linked_to_commitment(self) -> None:
        """Copied tasks have commitment_id set to new commitment."""
        from jdo.recurrence.generator import generate_instance

        templates = [
            TaskTemplate(title="Task 1", scope="Scope 1", order=1),
        ]

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            task_templates=[t.model_dump() for t in templates],
        )

        commitment, tasks = generate_instance(recurring, due_date=date(2025, 12, 22))

        assert tasks[0].commitment_id == commitment.id

    def test_sub_tasks_copied_as_incomplete(self) -> None:
        """Sub-tasks are copied with completed=false."""
        from jdo.models.recurring_commitment import SubTaskTemplate
        from jdo.recurrence.generator import generate_instance

        templates = [
            TaskTemplate(
                title="Task 1",
                scope="Scope 1",
                order=1,
                sub_tasks=[
                    SubTaskTemplate(description="Step 1"),
                    SubTaskTemplate(description="Step 2"),
                ],
            ),
        ]

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            task_templates=[t.model_dump() for t in templates],
        )

        commitment, tasks = generate_instance(recurring, due_date=date(2025, 12, 22))

        sub_tasks = tasks[0].get_sub_tasks()
        assert len(sub_tasks) == 2
        assert sub_tasks[0].description == "Step 1"
        assert sub_tasks[0].completed is False
        assert sub_tasks[1].description == "Step 2"
        assert sub_tasks[1].completed is False

    def test_task_order_preserved(self) -> None:
        """Task order is preserved from templates."""
        from jdo.recurrence.generator import generate_instance

        templates = [
            TaskTemplate(title="Third", scope="Scope", order=3),
            TaskTemplate(title="First", scope="Scope", order=1),
            TaskTemplate(title="Second", scope="Scope", order=2),
        ]

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            task_templates=[t.model_dump() for t in templates],
        )

        commitment, tasks = generate_instance(recurring, due_date=date(2025, 12, 22))

        assert tasks[0].order == 3
        assert tasks[1].order == 1
        assert tasks[2].order == 2


class TestShouldGenerate:
    """Tests for should_generate_instance function."""

    def test_should_generate_when_within_window(self) -> None:
        """should_generate returns True when next due is within window."""
        from jdo.recurrence.generator import should_generate_instance

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
        )

        # Today is Dec 17, next due is Dec 18 (within default 7-day window)
        result = should_generate_instance(recurring, current_date=date(2025, 12, 17))

        assert result is True

    def test_should_not_generate_when_paused(self) -> None:
        """should_generate returns False when recurrence is paused."""
        from jdo.models.recurring_commitment import RecurringCommitmentStatus
        from jdo.recurrence.generator import should_generate_instance

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            status=RecurringCommitmentStatus.PAUSED,
        )

        result = should_generate_instance(recurring, current_date=date(2025, 12, 17))

        assert result is False

    def test_should_not_generate_when_count_reached(self) -> None:
        """should_generate returns False when end_after_count reached."""
        from jdo.models.recurring_commitment import EndType
        from jdo.recurrence.generator import should_generate_instance

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            end_type=EndType.AFTER_COUNT,
            end_after_count=5,
            instances_generated=5,
        )

        result = should_generate_instance(recurring, current_date=date(2025, 12, 17))

        assert result is False


class TestCatchUpLogic:
    """Tests for catch-up logic when occurrences are missed."""

    def test_missed_occurrences_generate_only_current_instance(self) -> None:
        """When multiple occurrences are missed, only the current/next one is generated.

        If a daily recurring commitment was last generated 5 days ago,
        we should not generate 5 instances - only the next upcoming one.
        """
        from jdo.recurrence.generator import should_generate_instance

        # Last generated 5 days ago
        recurring = RecurringCommitment(
            deliverable_template="Daily standup",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            last_generated_date=date(2025, 12, 12),  # 5 days ago
        )

        # Check if we should generate on Dec 17
        result = should_generate_instance(recurring, current_date=date(2025, 12, 17))

        # Should generate because next due date (Dec 13) is in the past
        # but we generate the "current" instance (Dec 18)
        assert result is True

    def test_multiple_missed_weekly_generates_one_instance(self) -> None:
        """Weekly recurring with missed weeks generates only one current instance."""
        from jdo.recurrence.generator import should_generate_instance

        # Weekly on Monday, last generated 4 weeks ago
        recurring = RecurringCommitment(
            deliverable_template="Weekly report",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.WEEKLY,
            days_of_week=[0],  # Monday
            last_generated_date=date(2025, 11, 17),  # ~4 weeks ago
        )

        # Check if we should generate
        result = should_generate_instance(recurring, current_date=date(2025, 12, 17))

        # Should still only generate one instance
        assert result is True

    def test_catch_up_with_count_limit_respects_limit(self) -> None:
        """Catch-up generation respects end_after_count limit."""
        from jdo.models.recurring_commitment import EndType
        from jdo.recurrence.generator import should_generate_instance

        # Daily with limit of 5, already generated 4
        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            end_type=EndType.AFTER_COUNT,
            end_after_count=5,
            instances_generated=4,
            last_generated_date=date(2025, 12, 10),  # Week ago
        )

        # Should generate one more (4 + 1 = 5, not over limit)
        result = should_generate_instance(recurring, current_date=date(2025, 12, 17))
        assert result is True

    def test_catch_up_at_count_limit_stops(self) -> None:
        """Catch-up generation stops at count limit."""
        from jdo.models.recurring_commitment import EndType
        from jdo.recurrence.generator import should_generate_instance

        # Daily with limit of 5, already generated 5
        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            end_type=EndType.AFTER_COUNT,
            end_after_count=5,
            instances_generated=5,
            last_generated_date=date(2025, 12, 10),  # Week ago
        )

        # Should NOT generate (already at limit)
        result = should_generate_instance(recurring, current_date=date(2025, 12, 17))
        assert result is False

    def test_catch_up_respects_end_by_date(self) -> None:
        """Catch-up generation respects end_by_date limit."""
        from jdo.models.recurring_commitment import EndType
        from jdo.recurrence.generator import should_generate_instance

        # Daily that ended on Dec 10
        # Last generated was Dec 9, so next would be Dec 10 (still valid)
        # But if end_by_date is Dec 9, next (Dec 10) > end_by_date = no generation
        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            end_type=EndType.BY_DATE,
            end_by_date=date(2025, 12, 9),  # Ended Dec 9
            last_generated_date=date(2025, 12, 9),  # Last was Dec 9
        )

        # Next due would be Dec 10, which is after end_by_date (Dec 9)
        # Should NOT generate
        result = should_generate_instance(recurring, current_date=date(2025, 12, 17))
        assert result is False

    def test_catch_up_allows_generation_before_end_date(self) -> None:
        """Generation allowed when next due date is before end_by_date."""
        from jdo.models.recurring_commitment import EndType
        from jdo.recurrence.generator import should_generate_instance

        # Daily that ends on Dec 20
        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            end_type=EndType.BY_DATE,
            end_by_date=date(2025, 12, 20),
            last_generated_date=date(2025, 12, 10),  # Week ago
        )

        # Next due is Dec 11, which is before Dec 20 - should generate
        result = should_generate_instance(recurring, current_date=date(2025, 12, 17))
        assert result is True

    def test_fresh_recurring_generates_first_instance(self) -> None:
        """A new recurring commitment with no history generates its first instance."""
        from jdo.recurrence.generator import should_generate_instance

        # Never generated before
        recurring = RecurringCommitment(
            deliverable_template="Daily standup",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            last_generated_date=None,  # Never generated
        )

        result = should_generate_instance(recurring, current_date=date(2025, 12, 17))

        assert result is True
