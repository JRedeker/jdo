"""Tests for TaskHistoryService."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlmodel import SQLModel, select

from jdo.models.task import ActualHoursCategory, Task, TaskStatus
from jdo.models.task_history import TaskEventType, TaskHistoryEntry


class TestTaskHistoryServiceLogEvent:
    """Tests for TaskHistoryService.log_event method."""

    def test_log_created_event(self, tmp_path: Path) -> None:
        """Log a CREATED event when task is created."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.task_history_service import TaskHistoryService
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Setup: Create stakeholder and commitment
            stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            commitment = Commitment(
                deliverable="Test",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
            )
            commitment_id = commitment.id

            with get_session() as session:
                session.add(commitment)

            # Create task
            task = Task(
                commitment_id=commitment_id,
                title="Test Task",
                scope="Test scope",
                order=1,
                estimated_hours=2.0,
            )
            task_id = task.id

            with get_session() as session:
                session.add(task)

            # Log created event
            with get_session() as session:
                service = TaskHistoryService(session)
                entry = service.log_event(
                    task_id=task_id,
                    commitment_id=commitment_id,
                    event_type=TaskEventType.CREATED,
                    new_status=TaskStatus.PENDING,
                    estimated_hours=2.0,
                )
                entry_id = entry.id

            # Verify entry was saved
            with get_session() as session:
                result = session.exec(
                    select(TaskHistoryEntry).where(TaskHistoryEntry.id == entry_id)
                ).first()

                assert result is not None
                assert result.task_id == task_id
                assert result.commitment_id == commitment_id
                assert result.event_type == TaskEventType.CREATED
                assert result.new_status == TaskStatus.PENDING
                assert result.previous_status is None
                assert result.estimated_hours == 2.0

        reset_engine()

    def test_log_started_event(self, tmp_path: Path) -> None:
        """Log a STARTED event with previous status."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.task_history_service import TaskHistoryService
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            commitment = Commitment(
                deliverable="Test",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
            )
            commitment_id = commitment.id

            with get_session() as session:
                session.add(commitment)

            task = Task(
                commitment_id=commitment_id,
                title="Test Task",
                scope="Test scope",
                order=1,
            )
            task_id = task.id

            with get_session() as session:
                session.add(task)

            # Log started event
            with get_session() as session:
                service = TaskHistoryService(session)
                entry = service.log_event(
                    task_id=task_id,
                    commitment_id=commitment_id,
                    event_type=TaskEventType.STARTED,
                    previous_status=TaskStatus.PENDING,
                    new_status=TaskStatus.IN_PROGRESS,
                )
                entry_id = entry.id

            with get_session() as session:
                result = session.exec(
                    select(TaskHistoryEntry).where(TaskHistoryEntry.id == entry_id)
                ).first()

                assert result is not None
                assert result.event_type == TaskEventType.STARTED
                assert result.previous_status == TaskStatus.PENDING
                assert result.new_status == TaskStatus.IN_PROGRESS

        reset_engine()

    def test_log_completed_event_with_actual_hours(self, tmp_path: Path) -> None:
        """Log a COMPLETED event with actual hours category."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.task_history_service import TaskHistoryService
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            commitment = Commitment(
                deliverable="Test",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
            )
            commitment_id = commitment.id

            with get_session() as session:
                session.add(commitment)

            task = Task(
                commitment_id=commitment_id,
                title="Test Task",
                scope="Test scope",
                order=1,
                estimated_hours=2.0,
            )
            task_id = task.id

            with get_session() as session:
                session.add(task)

            # Log completed event
            with get_session() as session:
                service = TaskHistoryService(session)
                entry = service.log_event(
                    task_id=task_id,
                    commitment_id=commitment_id,
                    event_type=TaskEventType.COMPLETED,
                    previous_status=TaskStatus.IN_PROGRESS,
                    new_status=TaskStatus.COMPLETED,
                    estimated_hours=2.0,
                    actual_hours_category=ActualHoursCategory.ON_TARGET,
                )
                entry_id = entry.id

            with get_session() as session:
                result = session.exec(
                    select(TaskHistoryEntry).where(TaskHistoryEntry.id == entry_id)
                ).first()

                assert result is not None
                assert result.event_type == TaskEventType.COMPLETED
                assert result.estimated_hours == 2.0
                assert result.actual_hours_category == ActualHoursCategory.ON_TARGET

        reset_engine()

    def test_log_skipped_event_with_notes(self, tmp_path: Path) -> None:
        """Log a SKIPPED event with reason notes."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.task_history_service import TaskHistoryService
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            commitment = Commitment(
                deliverable="Test",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
            )
            commitment_id = commitment.id

            with get_session() as session:
                session.add(commitment)

            task = Task(
                commitment_id=commitment_id,
                title="Test Task",
                scope="Test scope",
                order=1,
            )
            task_id = task.id

            with get_session() as session:
                session.add(task)

            # Log skipped event
            with get_session() as session:
                service = TaskHistoryService(session)
                entry = service.log_event(
                    task_id=task_id,
                    commitment_id=commitment_id,
                    event_type=TaskEventType.SKIPPED,
                    previous_status=TaskStatus.PENDING,
                    new_status=TaskStatus.SKIPPED,
                    notes="No longer needed - requirements changed",
                )
                entry_id = entry.id

            with get_session() as session:
                result = session.exec(
                    select(TaskHistoryEntry).where(TaskHistoryEntry.id == entry_id)
                ).first()

                assert result is not None
                assert result.event_type == TaskEventType.SKIPPED
                assert result.notes == "No longer needed - requirements changed"

        reset_engine()


class TestTaskHistoryServiceLogTaskCreated:
    """Tests for TaskHistoryService.log_task_created convenience method."""

    def test_log_task_created(self, tmp_path: Path) -> None:
        """Log task creation event with all task details."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.task_history_service import TaskHistoryService
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            commitment = Commitment(
                deliverable="Test",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
            )
            commitment_id = commitment.id

            with get_session() as session:
                session.add(commitment)

            task = Task(
                commitment_id=commitment_id,
                title="Test Task",
                scope="Test scope",
                order=1,
                estimated_hours=3.0,
            )
            task_id = task.id

            with get_session() as session:
                session.add(task)
                # Reload task to get it attached to session
                task = session.exec(select(Task).where(Task.id == task_id)).first()
                assert task is not None

                service = TaskHistoryService(session)
                entry = service.log_task_created(task)
                entry_id = entry.id

            with get_session() as session:
                result = session.exec(
                    select(TaskHistoryEntry).where(TaskHistoryEntry.id == entry_id)
                ).first()

                assert result is not None
                assert result.event_type == TaskEventType.CREATED
                assert result.new_status == TaskStatus.PENDING
                assert result.estimated_hours == 3.0

        reset_engine()


class TestTaskHistoryServiceLogStatusChange:
    """Tests for TaskHistoryService.log_status_change convenience method."""

    def test_log_status_change_to_in_progress(self, tmp_path: Path) -> None:
        """Log status change from pending to in_progress."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.task_history_service import TaskHistoryService
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            commitment = Commitment(
                deliverable="Test",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
            )
            commitment_id = commitment.id

            with get_session() as session:
                session.add(commitment)

            task = Task(
                commitment_id=commitment_id,
                title="Test Task",
                scope="Test scope",
                order=1,
            )
            task_id = task.id

            with get_session() as session:
                session.add(task)

            with get_session() as session:
                task = session.exec(select(Task).where(Task.id == task_id)).first()
                assert task is not None

                service = TaskHistoryService(session)
                entry = service.log_status_change(
                    task=task,
                    old_status=TaskStatus.PENDING,
                    new_status=TaskStatus.IN_PROGRESS,
                )
                entry_id = entry.id

            with get_session() as session:
                result = session.exec(
                    select(TaskHistoryEntry).where(TaskHistoryEntry.id == entry_id)
                ).first()

                assert result is not None
                assert result.event_type == TaskEventType.STARTED
                assert result.previous_status == TaskStatus.PENDING
                assert result.new_status == TaskStatus.IN_PROGRESS

        reset_engine()

    def test_log_status_change_to_completed(self, tmp_path: Path) -> None:
        """Log status change to completed with actual hours."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.task_history_service import TaskHistoryService
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            commitment = Commitment(
                deliverable="Test",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
            )
            commitment_id = commitment.id

            with get_session() as session:
                session.add(commitment)

            task = Task(
                commitment_id=commitment_id,
                title="Test Task",
                scope="Test scope",
                order=1,
                estimated_hours=2.0,
            )
            task_id = task.id

            with get_session() as session:
                session.add(task)

            with get_session() as session:
                task = session.exec(select(Task).where(Task.id == task_id)).first()
                assert task is not None

                service = TaskHistoryService(session)
                entry = service.log_status_change(
                    task=task,
                    old_status=TaskStatus.IN_PROGRESS,
                    new_status=TaskStatus.COMPLETED,
                    actual_hours_category=ActualHoursCategory.SHORTER,
                )
                entry_id = entry.id

            with get_session() as session:
                result = session.exec(
                    select(TaskHistoryEntry).where(TaskHistoryEntry.id == entry_id)
                ).first()

                assert result is not None
                assert result.event_type == TaskEventType.COMPLETED
                assert result.estimated_hours == 2.0
                assert result.actual_hours_category == ActualHoursCategory.SHORTER

        reset_engine()

    def test_log_status_change_to_skipped(self, tmp_path: Path) -> None:
        """Log status change to skipped with notes."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.task_history_service import TaskHistoryService
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            commitment = Commitment(
                deliverable="Test",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
            )
            commitment_id = commitment.id

            with get_session() as session:
                session.add(commitment)

            task = Task(
                commitment_id=commitment_id,
                title="Test Task",
                scope="Test scope",
                order=1,
            )
            task_id = task.id

            with get_session() as session:
                session.add(task)

            with get_session() as session:
                task = session.exec(select(Task).where(Task.id == task_id)).first()
                assert task is not None

                service = TaskHistoryService(session)
                entry = service.log_status_change(
                    task=task,
                    old_status=TaskStatus.PENDING,
                    new_status=TaskStatus.SKIPPED,
                    notes="Blocked by external dependency",
                )
                entry_id = entry.id

            with get_session() as session:
                result = session.exec(
                    select(TaskHistoryEntry).where(TaskHistoryEntry.id == entry_id)
                ).first()

                assert result is not None
                assert result.event_type == TaskEventType.SKIPPED
                assert result.notes == "Blocked by external dependency"

        reset_engine()


class TestTaskHistoryServiceGetHistory:
    """Tests for TaskHistoryService.get_history method."""

    def test_get_history_for_task(self, tmp_path: Path) -> None:
        """Get all history entries for a task."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.task_history_service import TaskHistoryService
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            commitment = Commitment(
                deliverable="Test",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
            )
            commitment_id = commitment.id

            with get_session() as session:
                session.add(commitment)

            task = Task(
                commitment_id=commitment_id,
                title="Test Task",
                scope="Test scope",
                order=1,
            )
            task_id = task.id

            with get_session() as session:
                session.add(task)

            # Log multiple events
            with get_session() as session:
                service = TaskHistoryService(session)
                service.log_event(
                    task_id=task_id,
                    commitment_id=commitment_id,
                    event_type=TaskEventType.CREATED,
                    new_status=TaskStatus.PENDING,
                )
                service.log_event(
                    task_id=task_id,
                    commitment_id=commitment_id,
                    event_type=TaskEventType.STARTED,
                    previous_status=TaskStatus.PENDING,
                    new_status=TaskStatus.IN_PROGRESS,
                )
                service.log_event(
                    task_id=task_id,
                    commitment_id=commitment_id,
                    event_type=TaskEventType.COMPLETED,
                    previous_status=TaskStatus.IN_PROGRESS,
                    new_status=TaskStatus.COMPLETED,
                )

            # Get history
            with get_session() as session:
                service = TaskHistoryService(session)
                history = service.get_history_for_task(task_id)

                assert len(history) == 3
                # Should be ordered by created_at
                assert history[0].event_type == TaskEventType.CREATED
                assert history[1].event_type == TaskEventType.STARTED
                assert history[2].event_type == TaskEventType.COMPLETED

        reset_engine()

    def test_get_history_for_commitment(self, tmp_path: Path) -> None:
        """Get all history entries for a commitment (across all tasks)."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.task_history_service import TaskHistoryService
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            commitment = Commitment(
                deliverable="Test",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
            )
            commitment_id = commitment.id

            with get_session() as session:
                session.add(commitment)

            # Create two tasks
            task1 = Task(
                commitment_id=commitment_id,
                title="Task 1",
                scope="Scope 1",
                order=1,
            )
            task2 = Task(
                commitment_id=commitment_id,
                title="Task 2",
                scope="Scope 2",
                order=2,
            )
            task1_id = task1.id
            task2_id = task2.id

            with get_session() as session:
                session.add(task1)
                session.add(task2)

            # Log events for both tasks
            with get_session() as session:
                service = TaskHistoryService(session)
                service.log_event(
                    task_id=task1_id,
                    commitment_id=commitment_id,
                    event_type=TaskEventType.CREATED,
                    new_status=TaskStatus.PENDING,
                )
                service.log_event(
                    task_id=task2_id,
                    commitment_id=commitment_id,
                    event_type=TaskEventType.CREATED,
                    new_status=TaskStatus.PENDING,
                )

            # Get history for commitment
            with get_session() as session:
                service = TaskHistoryService(session)
                history = service.get_history_for_commitment(commitment_id)

                assert len(history) == 2

        reset_engine()
