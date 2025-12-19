"""Tests for AI time context utilities."""

from __future__ import annotations

from datetime import date

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from jdo.ai.time_context import (
    TimeContext,
    calculate_allocated_hours,
    format_time_context_for_ai,
    get_time_context,
)
from jdo.models.commitment import Commitment, CommitmentStatus
from jdo.models.stakeholder import Stakeholder, StakeholderType
from jdo.models.task import Task, TaskStatus


@pytest.fixture(name="session")
def session_fixture():
    """Create in-memory SQLite session for testing."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


class TestTimeContext:
    """Tests for TimeContext dataclass."""

    def test_over_allocated_when_exceeds_available(self) -> None:
        """over_allocated is True when allocated > available."""
        context = TimeContext(
            available_hours=4.0,
            allocated_hours=6.0,
            active_task_count=3,
            tasks_without_estimates=0,
        )
        assert context.over_allocated is True

    def test_not_over_allocated_when_within_available(self) -> None:
        """over_allocated is False when allocated <= available."""
        context = TimeContext(
            available_hours=8.0,
            allocated_hours=6.0,
            active_task_count=3,
            tasks_without_estimates=0,
        )
        assert context.over_allocated is False

    def test_not_over_allocated_when_no_available_set(self) -> None:
        """over_allocated is False when available_hours is None."""
        context = TimeContext(
            available_hours=None,
            allocated_hours=6.0,
            active_task_count=3,
            tasks_without_estimates=0,
        )
        assert context.over_allocated is False

    def test_remaining_capacity_positive(self) -> None:
        """remaining_capacity is positive when under-allocated."""
        context = TimeContext(
            available_hours=8.0,
            allocated_hours=5.0,
            active_task_count=2,
            tasks_without_estimates=0,
        )
        assert context.remaining_capacity == 3.0

    def test_remaining_capacity_negative(self) -> None:
        """remaining_capacity is negative when over-allocated."""
        context = TimeContext(
            available_hours=4.0,
            allocated_hours=6.0,
            active_task_count=2,
            tasks_without_estimates=0,
        )
        assert context.remaining_capacity == -2.0

    def test_remaining_capacity_none_when_no_available(self) -> None:
        """remaining_capacity is None when available_hours not set."""
        context = TimeContext(
            available_hours=None,
            allocated_hours=6.0,
            active_task_count=2,
            tasks_without_estimates=0,
        )
        assert context.remaining_capacity is None

    def test_utilization_percent(self) -> None:
        """utilization_percent calculates correctly."""
        context = TimeContext(
            available_hours=8.0,
            allocated_hours=4.0,
            active_task_count=2,
            tasks_without_estimates=0,
        )
        assert context.utilization_percent == 50.0

    def test_utilization_percent_over_100(self) -> None:
        """utilization_percent can exceed 100%."""
        context = TimeContext(
            available_hours=4.0,
            allocated_hours=8.0,
            active_task_count=2,
            tasks_without_estimates=0,
        )
        assert context.utilization_percent == 200.0

    def test_utilization_percent_none_when_no_available(self) -> None:
        """utilization_percent is None when available_hours not set."""
        context = TimeContext(
            available_hours=None,
            allocated_hours=4.0,
            active_task_count=2,
            tasks_without_estimates=0,
        )
        assert context.utilization_percent is None


class TestCalculateAllocatedHours:
    """Tests for calculate_allocated_hours function."""

    def test_returns_zero_with_no_tasks(self, session: Session) -> None:
        """Returns zero when no tasks exist."""
        total, count, without = calculate_allocated_hours(session)
        assert total == 0.0
        assert count == 0
        assert without == 0

    def test_sums_estimated_hours_for_active_tasks(self, session: Session) -> None:
        """Sums estimated hours for tasks in active commitments."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=stakeholder.id,
            due_date=date.today(),
            status=CommitmentStatus.PENDING,
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)

        task1 = Task(
            commitment_id=commitment.id,
            title="Task 1",
            scope="Scope 1",
            order=1,
            estimated_hours=2.0,
            status=TaskStatus.PENDING,
        )
        task2 = Task(
            commitment_id=commitment.id,
            title="Task 2",
            scope="Scope 2",
            order=2,
            estimated_hours=1.5,
            status=TaskStatus.IN_PROGRESS,
        )
        session.add(task1)
        session.add(task2)
        session.commit()

        total, count, without = calculate_allocated_hours(session)
        assert total == 3.5
        assert count == 2
        assert without == 0

    def test_excludes_completed_tasks(self, session: Session) -> None:
        """Excludes tasks that are completed or skipped."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=stakeholder.id,
            due_date=date.today(),
            status=CommitmentStatus.IN_PROGRESS,
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)

        pending_task = Task(
            commitment_id=commitment.id,
            title="Pending",
            scope="Scope",
            order=1,
            estimated_hours=2.0,
            status=TaskStatus.PENDING,
        )
        completed_task = Task(
            commitment_id=commitment.id,
            title="Completed",
            scope="Scope",
            order=2,
            estimated_hours=3.0,
            status=TaskStatus.COMPLETED,
        )
        session.add(pending_task)
        session.add(completed_task)
        session.commit()

        total, count, without = calculate_allocated_hours(session)
        assert total == 2.0
        assert count == 1

    def test_excludes_tasks_in_completed_commitments(self, session: Session) -> None:
        """Excludes tasks from completed/abandoned commitments."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        active_commitment = Commitment(
            deliverable="Active",
            stakeholder_id=stakeholder.id,
            due_date=date.today(),
            status=CommitmentStatus.PENDING,
        )
        completed_commitment = Commitment(
            deliverable="Completed",
            stakeholder_id=stakeholder.id,
            due_date=date.today(),
            status=CommitmentStatus.COMPLETED,
        )
        session.add(active_commitment)
        session.add(completed_commitment)
        session.commit()
        session.refresh(active_commitment)
        session.refresh(completed_commitment)

        active_task = Task(
            commitment_id=active_commitment.id,
            title="Active Task",
            scope="Scope",
            order=1,
            estimated_hours=2.0,
            status=TaskStatus.PENDING,
        )
        inactive_task = Task(
            commitment_id=completed_commitment.id,
            title="Inactive Task",
            scope="Scope",
            order=1,
            estimated_hours=5.0,
            status=TaskStatus.PENDING,
        )
        session.add(active_task)
        session.add(inactive_task)
        session.commit()

        total, count, without = calculate_allocated_hours(session)
        assert total == 2.0
        assert count == 1

    def test_counts_tasks_without_estimates(self, session: Session) -> None:
        """Counts tasks that don't have time estimates."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=stakeholder.id,
            due_date=date.today(),
            status=CommitmentStatus.PENDING,
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)

        with_estimate = Task(
            commitment_id=commitment.id,
            title="With Estimate",
            scope="Scope",
            order=1,
            estimated_hours=2.0,
            status=TaskStatus.PENDING,
        )
        without_estimate = Task(
            commitment_id=commitment.id,
            title="Without Estimate",
            scope="Scope",
            order=2,
            status=TaskStatus.PENDING,
        )
        session.add(with_estimate)
        session.add(without_estimate)
        session.commit()

        total, count, without = calculate_allocated_hours(session)
        assert total == 2.0
        assert count == 2
        assert without == 1


class TestGetTimeContext:
    """Tests for get_time_context function."""

    def test_combines_available_and_allocated(self, session: Session) -> None:
        """Combines user-provided available hours with calculated allocated."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=stakeholder.id,
            due_date=date.today(),
            status=CommitmentStatus.PENDING,
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)

        task = Task(
            commitment_id=commitment.id,
            title="Task",
            scope="Scope",
            order=1,
            estimated_hours=3.0,
            status=TaskStatus.PENDING,
        )
        session.add(task)
        session.commit()

        context = get_time_context(session, available_hours=8.0)
        assert context.available_hours == 8.0
        assert context.allocated_hours == 3.0
        assert context.remaining_capacity == 5.0
        assert context.over_allocated is False


class TestFormatTimeContextForAI:
    """Tests for format_time_context_for_ai function."""

    def test_formats_full_context(self) -> None:
        """Formats a complete time context."""
        context = TimeContext(
            available_hours=8.0,
            allocated_hours=5.0,
            active_task_count=3,
            tasks_without_estimates=1,
        )
        result = format_time_context_for_ai(context)

        assert "Available hours: 8.0" in result
        assert "Allocated hours: 5.0" in result
        assert "Remaining capacity: 3.0 hours" in result
        assert "missing estimates: 1" in result

    def test_formats_over_allocated(self) -> None:
        """Shows OVER-ALLOCATED warning when applicable."""
        context = TimeContext(
            available_hours=4.0,
            allocated_hours=6.0,
            active_task_count=3,
            tasks_without_estimates=0,
        )
        result = format_time_context_for_ai(context)

        assert "OVER-ALLOCATED by 2.0 hours" in result

    def test_formats_no_available_hours(self) -> None:
        """Prompts to ask user when available_hours not set."""
        context = TimeContext(
            available_hours=None,
            allocated_hours=3.0,
            active_task_count=2,
            tasks_without_estimates=0,
        )
        result = format_time_context_for_ai(context)

        assert "Not set (ask user)" in result
