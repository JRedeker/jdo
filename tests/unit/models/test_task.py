"""Tests for Task SQLModel - TDD Red phase."""

from datetime import date
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlmodel import SQLModel

from jdo.models.task import (
    ActualHoursCategory,
    EstimationConfidence,
    SubTask,
    Task,
    TaskStatus,
)


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

    def test_has_time_estimation_fields(self) -> None:
        """Task has time estimation fields."""
        fields = Task.model_fields
        assert "estimated_hours" in fields
        assert "actual_hours_category" in fields
        assert "estimation_confidence" in fields


class TestActualHoursCategory:
    """Tests for ActualHoursCategory enum."""

    def test_has_all_categories(self) -> None:
        """ActualHoursCategory has all 5 categories."""
        assert ActualHoursCategory.MUCH_SHORTER.value == "much_shorter"
        assert ActualHoursCategory.SHORTER.value == "shorter"
        assert ActualHoursCategory.ON_TARGET.value == "on_target"
        assert ActualHoursCategory.LONGER.value == "longer"
        assert ActualHoursCategory.MUCH_LONGER.value == "much_longer"

    def test_multiplier_much_shorter(self) -> None:
        """MUCH_SHORTER returns 0.25 multiplier."""
        assert ActualHoursCategory.MUCH_SHORTER.multiplier == 0.25

    def test_multiplier_shorter(self) -> None:
        """SHORTER returns 0.675 multiplier."""
        assert ActualHoursCategory.SHORTER.multiplier == 0.675

    def test_multiplier_on_target(self) -> None:
        """ON_TARGET returns 1.0 multiplier."""
        assert ActualHoursCategory.ON_TARGET.multiplier == 1.0

    def test_multiplier_longer(self) -> None:
        """LONGER returns 1.325 multiplier."""
        assert ActualHoursCategory.LONGER.multiplier == 1.325

    def test_multiplier_much_longer(self) -> None:
        """MUCH_LONGER returns 2.0 multiplier."""
        assert ActualHoursCategory.MUCH_LONGER.multiplier == 2.0


class TestEstimationConfidence:
    """Tests for EstimationConfidence enum."""

    def test_has_all_confidence_levels(self) -> None:
        """EstimationConfidence has high, medium, low."""
        assert EstimationConfidence.HIGH.value == "high"
        assert EstimationConfidence.MEDIUM.value == "medium"
        assert EstimationConfidence.LOW.value == "low"


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
        from jdo.models.goal import Goal
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
        from jdo.models.goal import Goal
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


class TestTimeEstimationFields:
    """Tests for Task time estimation fields."""

    def test_time_fields_default_to_none(self) -> None:
        """Time estimation fields default to None."""
        task = Task(
            commitment_id=uuid4(),
            title="Test",
            scope="Test scope",
            order=1,
        )
        assert task.estimated_hours is None
        assert task.actual_hours_category is None
        assert task.estimation_confidence is None

    def test_create_task_with_estimated_hours(self) -> None:
        """Task can be created with estimated_hours."""
        task = Task(
            commitment_id=uuid4(),
            title="Test",
            scope="Test scope",
            order=1,
            estimated_hours=2.5,
        )
        assert task.estimated_hours == 2.5

    def test_create_task_with_estimation_confidence(self) -> None:
        """Task can be created with estimation_confidence."""
        task = Task(
            commitment_id=uuid4(),
            title="Test",
            scope="Test scope",
            order=1,
            estimated_hours=1.0,
            estimation_confidence=EstimationConfidence.HIGH,
        )
        assert task.estimation_confidence == EstimationConfidence.HIGH

    def test_create_task_with_actual_hours_category(self) -> None:
        """Task can be created with actual_hours_category."""
        task = Task(
            commitment_id=uuid4(),
            title="Test",
            scope="Test scope",
            order=1,
            estimated_hours=1.0,
            actual_hours_category=ActualHoursCategory.ON_TARGET,
        )
        assert task.actual_hours_category == ActualHoursCategory.ON_TARGET

    def test_create_task_with_all_time_fields(self) -> None:
        """Task can be created with all time estimation fields."""
        task = Task(
            commitment_id=uuid4(),
            title="Complex task",
            scope="Detailed work",
            order=1,
            estimated_hours=4.0,
            estimation_confidence=EstimationConfidence.MEDIUM,
            actual_hours_category=ActualHoursCategory.LONGER,
        )
        assert task.estimated_hours == 4.0
        assert task.estimation_confidence == EstimationConfidence.MEDIUM
        assert task.actual_hours_category == ActualHoursCategory.LONGER

    def test_time_fields_persist_to_database(self, tmp_path: Path) -> None:
        """Time estimation fields persist to database."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Create stakeholder and commitment
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

            # Create task with time fields
            task = Task(
                commitment_id=commitment_id,
                title="Timed task",
                scope="Task with time estimates",
                order=1,
                estimated_hours=3.5,
                estimation_confidence=EstimationConfidence.LOW,
                actual_hours_category=ActualHoursCategory.MUCH_LONGER,
            )
            task_id = task.id

            with get_session() as session:
                session.add(task)

            # Retrieve and verify
            with get_session() as session:
                result = session.exec(select(Task).where(Task.id == task_id)).first()

                assert result is not None
                assert result.estimated_hours == 3.5
                assert result.estimation_confidence == EstimationConfidence.LOW
                assert result.actual_hours_category == ActualHoursCategory.MUCH_LONGER

        reset_engine()


class TestNotificationTask:
    """Tests for notification task support (integrity protocol)."""

    def test_has_is_notification_task_field(self) -> None:
        """Task has is_notification_task boolean field."""
        fields = Task.model_fields
        assert "is_notification_task" in fields

    def test_is_notification_task_defaults_to_false(self) -> None:
        """is_notification_task defaults to False."""
        task = Task(
            commitment_id=uuid4(),
            title="Regular task",
            scope="Do something",
            order=1,
        )
        assert task.is_notification_task is False

    def test_can_set_is_notification_task_true(self) -> None:
        """is_notification_task can be set to True."""
        task = Task(
            commitment_id=uuid4(),
            title="Notify stakeholder",
            scope="Send notification about at-risk commitment",
            order=0,
            is_notification_task=True,
        )
        assert task.is_notification_task is True

    def test_notification_task_persistence(self, tmp_path: Path) -> None:
        """Notification task flag persists to database."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Create stakeholder and commitment
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

            # Create notification task
            task = Task(
                commitment_id=commitment_id,
                title="Notify stakeholder",
                scope="Notification draft content",
                order=0,
                is_notification_task=True,
            )
            task_id = task.id

            with get_session() as session:
                session.add(task)

            # Retrieve and verify
            with get_session() as session:
                result = session.exec(select(Task).where(Task.id == task_id)).first()

                assert result is not None
                assert result.is_notification_task is True

        reset_engine()


class TestSubTaskSerialization:
    """Tests for SubTask serialization in Task.sub_tasks field."""

    def test_serialize_subtasks_mixed_types(self) -> None:
        """serialize_sub_tasks handles mixed SubTask and dict types."""
        task = Task(
            commitment_id=uuid4(),
            title="Test",
            scope="Test scope",
            order=1,
        )
        mixed_subtasks: list[SubTask | dict[str, object]] = [
            SubTask(description="Step 1"),
            {"description": "Step 2", "completed": True},
        ]
        result = task.serialize_sub_tasks(mixed_subtasks)
        assert len(result) == 2
        assert result[0] == {"description": "Step 1", "completed": False}
        assert result[1] == {"description": "Step 2", "completed": True}

    def test_serialize_subtasks_none_returns_empty_list(self) -> None:
        """serialize_sub_tasks returns empty list for None input."""
        task = Task(
            commitment_id=uuid4(),
            title="Test",
            scope="Test scope",
            order=1,
        )
        result = task.serialize_sub_tasks(None)
        assert result == []

    def test_serialize_subtasks_with_subtask_objects(self) -> None:
        """serialize_sub_tasks converts SubTask objects to dicts."""
        task = Task(
            commitment_id=uuid4(),
            title="Test",
            scope="Test scope",
            order=1,
        )
        subtasks = [
            SubTask(description="First step"),
            SubTask(description="Second step", completed=True),
        ]
        result = task.serialize_sub_tasks(subtasks)
        assert len(result) == 2
        assert result[0] == {"description": "First step", "completed": False}
        assert result[1] == {"description": "Second step", "completed": True}

    def test_serialize_subtasks_with_dicts(self) -> None:
        """serialize_sub_tasks passes through dicts unchanged."""
        task = Task(
            commitment_id=uuid4(),
            title="Test",
            scope="Test scope",
            order=1,
        )
        dict_subtasks = [
            {"description": "Dict step", "completed": False},
        ]
        result = task.serialize_sub_tasks(dict_subtasks)
        assert len(result) == 1
        assert result[0] == {"description": "Dict step", "completed": False}

    def test_serialize_subtasks_with_other_objects(self) -> None:
        """serialize_sub_tasks passes through other objects."""
        task = Task(
            commitment_id=uuid4(),
            title="Test",
            scope="Test scope",
            order=1,
        )
        other_objects: list[object] = ["string", 123, None]
        result = task.serialize_sub_tasks(other_objects)
        assert len(result) == 3
        assert result[0] == "string"
        assert result[1] == 123
        assert result[2] is None
