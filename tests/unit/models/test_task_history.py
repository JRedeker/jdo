"""Tests for TaskHistoryEntry SQLModel."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlmodel import SQLModel, select

from jdo.models.task import ActualHoursCategory, TaskStatus
from jdo.models.task_history import TaskEventType, TaskHistoryEntry


class TestTaskHistoryEntryModel:
    """Tests for TaskHistoryEntry model structure."""

    def test_inherits_from_sqlmodel_with_table_true(self) -> None:
        """TaskHistoryEntry inherits from SQLModel with table=True."""
        assert issubclass(TaskHistoryEntry, SQLModel)
        assert hasattr(TaskHistoryEntry, "__tablename__")

    def test_has_tablename_task_history(self) -> None:
        """TaskHistoryEntry has tablename 'task_history'."""
        assert TaskHistoryEntry.__tablename__ == "task_history"

    def test_has_required_fields(self) -> None:
        """TaskHistoryEntry has all required fields."""
        fields = TaskHistoryEntry.model_fields
        assert "id" in fields
        assert "task_id" in fields
        assert "commitment_id" in fields
        assert "event_type" in fields
        assert "previous_status" in fields
        assert "new_status" in fields
        assert "estimated_hours" in fields
        assert "actual_hours_category" in fields
        assert "notes" in fields
        assert "created_at" in fields


class TestTaskEventType:
    """Tests for TaskEventType enum."""

    def test_has_all_event_types(self) -> None:
        """TaskEventType has all expected event types."""
        assert TaskEventType.CREATED.value == "created"
        assert TaskEventType.STARTED.value == "started"
        assert TaskEventType.COMPLETED.value == "completed"
        assert TaskEventType.SKIPPED.value == "skipped"
        assert TaskEventType.ABANDONED.value == "abandoned"


class TestTaskHistoryEntryCreation:
    """Tests for creating TaskHistoryEntry instances."""

    def test_create_created_event(self) -> None:
        """Create a CREATED event entry."""
        task_id = uuid4()
        commitment_id = uuid4()
        entry = TaskHistoryEntry(
            task_id=task_id,
            commitment_id=commitment_id,
            event_type=TaskEventType.CREATED,
            new_status=TaskStatus.PENDING,
        )

        assert entry.task_id == task_id
        assert entry.commitment_id == commitment_id
        assert entry.event_type == TaskEventType.CREATED
        assert entry.previous_status is None
        assert entry.new_status == TaskStatus.PENDING
        assert isinstance(entry.id, UUID)

    def test_create_started_event(self) -> None:
        """Create a STARTED event entry with previous status."""
        task_id = uuid4()
        commitment_id = uuid4()
        entry = TaskHistoryEntry(
            task_id=task_id,
            commitment_id=commitment_id,
            event_type=TaskEventType.STARTED,
            previous_status=TaskStatus.PENDING,
            new_status=TaskStatus.IN_PROGRESS,
        )

        assert entry.event_type == TaskEventType.STARTED
        assert entry.previous_status == TaskStatus.PENDING
        assert entry.new_status == TaskStatus.IN_PROGRESS

    def test_create_completed_event_with_actual_hours(self) -> None:
        """Create a COMPLETED event with actual hours category."""
        task_id = uuid4()
        commitment_id = uuid4()
        entry = TaskHistoryEntry(
            task_id=task_id,
            commitment_id=commitment_id,
            event_type=TaskEventType.COMPLETED,
            previous_status=TaskStatus.IN_PROGRESS,
            new_status=TaskStatus.COMPLETED,
            estimated_hours=2.0,
            actual_hours_category=ActualHoursCategory.ON_TARGET,
        )

        assert entry.event_type == TaskEventType.COMPLETED
        assert entry.estimated_hours == 2.0
        assert entry.actual_hours_category == ActualHoursCategory.ON_TARGET

    def test_create_skipped_event_with_notes(self) -> None:
        """Create a SKIPPED event with skip reason notes."""
        task_id = uuid4()
        commitment_id = uuid4()
        entry = TaskHistoryEntry(
            task_id=task_id,
            commitment_id=commitment_id,
            event_type=TaskEventType.SKIPPED,
            previous_status=TaskStatus.PENDING,
            new_status=TaskStatus.SKIPPED,
            notes="No longer needed - requirements changed",
        )

        assert entry.event_type == TaskEventType.SKIPPED
        assert entry.notes == "No longer needed - requirements changed"

    def test_create_abandoned_event(self) -> None:
        """Create an ABANDONED event entry."""
        task_id = uuid4()
        commitment_id = uuid4()
        entry = TaskHistoryEntry(
            task_id=task_id,
            commitment_id=commitment_id,
            event_type=TaskEventType.ABANDONED,
            previous_status=TaskStatus.IN_PROGRESS,
            new_status=TaskStatus.SKIPPED,
            notes="Blocked by external dependency",
        )

        assert entry.event_type == TaskEventType.ABANDONED
        assert entry.previous_status == TaskStatus.IN_PROGRESS
        assert entry.new_status == TaskStatus.SKIPPED

    def test_optional_fields_default_to_none(self) -> None:
        """Optional fields default to None."""
        entry = TaskHistoryEntry(
            task_id=uuid4(),
            commitment_id=uuid4(),
            event_type=TaskEventType.CREATED,
            new_status=TaskStatus.PENDING,
        )

        assert entry.previous_status is None
        assert entry.estimated_hours is None
        assert entry.actual_hours_category is None
        assert entry.notes is None

    def test_created_at_auto_populated(self) -> None:
        """created_at is automatically populated."""
        entry = TaskHistoryEntry(
            task_id=uuid4(),
            commitment_id=uuid4(),
            event_type=TaskEventType.CREATED,
            new_status=TaskStatus.PENDING,
        )

        assert entry.created_at is not None


class TestTaskHistoryEntryPersistence:
    """Tests for TaskHistoryEntry database persistence."""

    def test_save_and_retrieve(self, tmp_path: Path) -> None:
        """Save TaskHistoryEntry and retrieve by id."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType
        from jdo.models.task import Task

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Create stakeholder, commitment, and task
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

            # Create history entry
            entry = TaskHistoryEntry(
                task_id=task_id,
                commitment_id=commitment_id,
                event_type=TaskEventType.CREATED,
                new_status=TaskStatus.PENDING,
            )
            entry_id = entry.id

            with get_session() as session:
                session.add(entry)

            # Retrieve and verify
            with get_session() as session:
                result = session.exec(
                    select(TaskHistoryEntry).where(TaskHistoryEntry.id == entry_id)
                ).first()

                assert result is not None
                assert result.task_id == task_id
                assert result.commitment_id == commitment_id
                assert result.event_type == TaskEventType.CREATED

        reset_engine()

    def test_multiple_entries_for_same_task(self, tmp_path: Path) -> None:
        """Multiple history entries can exist for the same task."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType
        from jdo.models.task import Task

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Create stakeholder, commitment, and task
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

            # Create multiple history entries
            entries = [
                TaskHistoryEntry(
                    task_id=task_id,
                    commitment_id=commitment_id,
                    event_type=TaskEventType.CREATED,
                    new_status=TaskStatus.PENDING,
                ),
                TaskHistoryEntry(
                    task_id=task_id,
                    commitment_id=commitment_id,
                    event_type=TaskEventType.STARTED,
                    previous_status=TaskStatus.PENDING,
                    new_status=TaskStatus.IN_PROGRESS,
                ),
                TaskHistoryEntry(
                    task_id=task_id,
                    commitment_id=commitment_id,
                    event_type=TaskEventType.COMPLETED,
                    previous_status=TaskStatus.IN_PROGRESS,
                    new_status=TaskStatus.COMPLETED,
                    estimated_hours=1.0,
                    actual_hours_category=ActualHoursCategory.SHORTER,
                ),
            ]

            with get_session() as session:
                for entry in entries:
                    session.add(entry)

            # Retrieve all entries for task
            with get_session() as session:
                results = session.exec(
                    select(TaskHistoryEntry).where(TaskHistoryEntry.task_id == task_id)
                ).all()

                assert len(results) == 3
                event_types = [r.event_type for r in results]
                assert TaskEventType.CREATED in event_types
                assert TaskEventType.STARTED in event_types
                assert TaskEventType.COMPLETED in event_types

        reset_engine()

    def test_query_by_commitment_id(self, tmp_path: Path) -> None:
        """Can query history entries by commitment_id (denormalized)."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType
        from jdo.models.task import Task

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Create stakeholder
            stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            # Create two commitments
            commitment1 = Commitment(
                deliverable="Commitment 1",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
            )
            commitment2 = Commitment(
                deliverable="Commitment 2",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
            )
            commitment1_id = commitment1.id
            commitment2_id = commitment2.id

            with get_session() as session:
                session.add(commitment1)
                session.add(commitment2)

            # Create tasks for each commitment
            task1 = Task(
                commitment_id=commitment1_id,
                title="Task 1",
                scope="Scope 1",
                order=1,
            )
            task2 = Task(
                commitment_id=commitment2_id,
                title="Task 2",
                scope="Scope 2",
                order=1,
            )
            task1_id = task1.id
            task2_id = task2.id

            with get_session() as session:
                session.add(task1)
                session.add(task2)

            # Create history entries for both
            entry1 = TaskHistoryEntry(
                task_id=task1_id,
                commitment_id=commitment1_id,
                event_type=TaskEventType.CREATED,
                new_status=TaskStatus.PENDING,
            )
            entry2 = TaskHistoryEntry(
                task_id=task2_id,
                commitment_id=commitment2_id,
                event_type=TaskEventType.CREATED,
                new_status=TaskStatus.PENDING,
            )

            with get_session() as session:
                session.add(entry1)
                session.add(entry2)

            # Query by commitment_id without joining
            with get_session() as session:
                results = session.exec(
                    select(TaskHistoryEntry).where(TaskHistoryEntry.commitment_id == commitment1_id)
                ).all()

                assert len(results) == 1
                assert results[0].task_id == task1_id

        reset_engine()
