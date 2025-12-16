"""Tests for Task SQLModel - TDD Red phase."""

from datetime import date
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlmodel import SQLModel

from jdo.models.task import SubTask, Task, TaskStatus


class TestTaskModel:
    """Tests for Task model structure."""

    def test_inherits_from_sqlmodel_with_table_true(self) -> None:
        """Task inherits from SQLModel with table=True."""
        assert issubclass(Task, SQLModel)
        assert hasattr(Task, "__tablename__")

    def test_has_tablename_tasks(self) -> None:
        """Task has tablename 'tasks'."""
        assert Task.__tablename__ == "tasks"

    def test_has_required_fields(self) -> None:
        """Task has all required fields."""
        fields = Task.model_fields
        assert "id" in fields
        assert "commitment_id" in fields
        assert "title" in fields
        assert "scope" in fields
        assert "status" in fields
        assert "sub_tasks" in fields
        assert "order" in fields
        assert "created_at" in fields
        assert "updated_at" in fields


class TestTaskValidation:
    """Tests for Task field validation."""

    def test_creates_with_required_fields(self) -> None:
        """Create task with required fields."""
        commitment_id = uuid4()
        task = Task(
            commitment_id=commitment_id,
            title="Draft email",
            scope="Write email body with 3 key points",
            order=1,
        )

        assert task.title == "Draft email"
        assert task.scope == "Write email body with 3 key points"
        assert task.order == 1
        assert task.status == TaskStatus.PENDING
        assert isinstance(task.id, UUID)

    def test_validates_title_non_empty(self) -> None:
        """Reject empty title via model_validate."""
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            Task.model_validate(
                {
                    "commitment_id": str(uuid4()),
                    "title": "",
                    "scope": "Valid scope",
                    "order": 1,
                }
            )

    def test_validates_scope_non_empty(self) -> None:
        """Reject empty scope via model_validate."""
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            Task.model_validate(
                {
                    "commitment_id": str(uuid4()),
                    "title": "Valid title",
                    "scope": "",
                    "order": 1,
                }
            )

    def test_sub_tasks_default_to_empty_list(self) -> None:
        """sub_tasks defaults to empty list."""
        task = Task(
            commitment_id=uuid4(),
            title="Test",
            scope="Test scope",
            order=1,
        )

        assert task.sub_tasks == []
        assert task.get_sub_tasks() == []


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_has_required_values(self) -> None:
        """TaskStatus has pending, in_progress, completed, skipped."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.SKIPPED.value == "skipped"


class TestSubTask:
    """Tests for SubTask embedded model."""

    def test_creates_subtask(self) -> None:
        """Create SubTask with required fields."""
        subtask = SubTask(description="Check email")

        assert subtask.description == "Check email"
        assert subtask.completed is False

    def test_subtask_completed_default_false(self) -> None:
        """SubTask completed defaults to False."""
        subtask = SubTask(description="Test")
        assert subtask.completed is False

    def test_subtask_can_be_marked_completed(self) -> None:
        """SubTask can be marked as completed."""
        subtask = SubTask(description="Test", completed=True)
        assert subtask.completed is True

    def test_task_with_subtasks_as_dicts(self) -> None:
        """Task can contain SubTasks stored as dicts."""
        # SubTasks must be passed as dicts for JSON storage
        subtasks = [
            {"description": "Step 1", "completed": False},
            {"description": "Step 2", "completed": True},
        ]
        task = Task(
            commitment_id=uuid4(),
            title="Multi-step task",
            scope="Complete all steps",
            order=1,
            sub_tasks=subtasks,
        )

        # Raw sub_tasks is stored as dicts
        assert len(task.sub_tasks) == 2
        # Use get_sub_tasks() to get SubTask objects
        parsed = task.get_sub_tasks()
        assert parsed[0].description == "Step 1"
        assert parsed[0].completed is False
        assert parsed[1].completed is True

    def test_task_set_sub_tasks_helper(self) -> None:
        """Task.set_sub_tasks converts SubTask objects to dicts."""
        task = Task(
            commitment_id=uuid4(),
            title="Test",
            scope="Test scope",
            order=1,
        )

        subtasks = [
            SubTask(description="Step 1"),
            SubTask(description="Step 2", completed=True),
        ]
        task.set_sub_tasks(subtasks)

        assert len(task.sub_tasks) == 2
        assert task.sub_tasks[0] == {"description": "Step 1", "completed": False}
        assert task.sub_tasks[1] == {"description": "Step 2", "completed": True}


class TestTaskPersistence:
    """Tests for Task database persistence."""

    def test_save_and_retrieve(self, tmp_path: Path) -> None:
        """Save task via session and retrieve by id."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.models.commitment import Commitment
        from jdo.models.goal import Goal  # noqa: F401 - needed for FK
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Create stakeholder and commitment first
            stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            commitment = Commitment(
                deliverable="Test deliverable",
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
            )
            task_id = task.id

            with get_session() as session:
                session.add(task)

            # Retrieve
            with get_session() as session:
                result = session.exec(select(Task).where(Task.id == task_id)).first()

                assert result is not None
                assert result.title == "Test Task"
                assert result.commitment_id == commitment_id

        reset_engine()

    def test_stores_subtasks_as_json(self, tmp_path: Path) -> None:
        """Task stores sub_tasks as JSON column."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.models.commitment import Commitment
        from jdo.models.goal import Goal  # noqa: F401 - needed for FK
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

            # Create task with subtasks (as dicts for JSON storage)
            subtasks = [
                {"description": "Step 1", "completed": False},
                {"description": "Step 2", "completed": True},
            ]
            task = Task(
                commitment_id=commitment_id,
                title="Task with subtasks",
                scope="Complete steps",
                order=1,
                sub_tasks=subtasks,
            )
            task_id = task.id

            with get_session() as session:
                session.add(task)

            # Retrieve and verify subtasks
            with get_session() as session:
                result = session.exec(select(Task).where(Task.id == task_id)).first()

                assert result is not None
                assert len(result.sub_tasks) == 2
                # Use helper method to get SubTask objects
                parsed = result.get_sub_tasks()
                assert parsed[0].description == "Step 1"
                assert parsed[0].completed is False
                assert parsed[1].description == "Step 2"
                assert parsed[1].completed is True

        reset_engine()
