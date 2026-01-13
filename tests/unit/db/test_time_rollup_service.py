"""Tests for TimeRollupService."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

from sqlmodel import SQLModel, select

from jdo.models.task import Task, TaskStatus


class TestTimeRollup:
    """Tests for TimeRollup dataclass."""

    def test_has_estimates_true_when_tasks_have_estimates(self) -> None:
        """has_estimates is True when tasks_with_estimates > 0."""
        from jdo.db.time_rollup_service import TimeRollup

        rollup = TimeRollup(
            total_estimated_hours=5.0,
            remaining_estimated_hours=3.0,
            completed_estimated_hours=2.0,
            task_count=3,
            tasks_with_estimates=2,
            completed_task_count=1,
        )
        assert rollup.has_estimates is True

    def test_has_estimates_false_when_no_estimates(self) -> None:
        """has_estimates is False when tasks_with_estimates is 0."""
        from jdo.db.time_rollup_service import TimeRollup

        rollup = TimeRollup(
            total_estimated_hours=0.0,
            remaining_estimated_hours=0.0,
            completed_estimated_hours=0.0,
            task_count=3,
            tasks_with_estimates=0,
            completed_task_count=1,
        )
        assert rollup.has_estimates is False

    def test_estimate_coverage_all_tasks(self) -> None:
        """estimate_coverage is 1.0 when all tasks have estimates."""
        from jdo.db.time_rollup_service import TimeRollup

        rollup = TimeRollup(
            total_estimated_hours=5.0,
            remaining_estimated_hours=3.0,
            completed_estimated_hours=2.0,
            task_count=3,
            tasks_with_estimates=3,
            completed_task_count=1,
        )
        assert rollup.estimate_coverage == 1.0

    def test_estimate_coverage_partial(self) -> None:
        """estimate_coverage reflects partial coverage."""
        from jdo.db.time_rollup_service import TimeRollup

        rollup = TimeRollup(
            total_estimated_hours=2.0,
            remaining_estimated_hours=2.0,
            completed_estimated_hours=0.0,
            task_count=4,
            tasks_with_estimates=2,
            completed_task_count=0,
        )
        assert rollup.estimate_coverage == 0.5

    def test_estimate_coverage_no_tasks(self) -> None:
        """estimate_coverage is 0.0 when no tasks."""
        from jdo.db.time_rollup_service import TimeRollup

        rollup = TimeRollup(
            total_estimated_hours=0.0,
            remaining_estimated_hours=0.0,
            completed_estimated_hours=0.0,
            task_count=0,
            tasks_with_estimates=0,
            completed_task_count=0,
        )
        assert rollup.estimate_coverage == 0.0


class TestTimeRollupServiceGetRollup:
    """Tests for TimeRollupService.get_rollup method."""

    def test_empty_commitment(self, tmp_path: Path) -> None:
        """Get rollup for commitment with no tasks."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.time_rollup_service import TimeRollupService
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

            # Get rollup for empty commitment
            with get_session() as session:
                service = TimeRollupService(session)
                rollup = service.get_rollup(commitment_id)

                assert rollup.total_estimated_hours == 0.0
                assert rollup.remaining_estimated_hours == 0.0
                assert rollup.completed_estimated_hours == 0.0
                assert rollup.task_count == 0
                assert rollup.tasks_with_estimates == 0
                assert rollup.completed_task_count == 0

        reset_engine()

    def test_tasks_without_estimates(self, tmp_path: Path) -> None:
        """Get rollup for tasks without time estimates."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.time_rollup_service import TimeRollupService
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

            # Create tasks without estimates
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

            with get_session() as session:
                session.add(task1)
                session.add(task2)

            with get_session() as session:
                service = TimeRollupService(session)
                rollup = service.get_rollup(commitment_id)

                assert rollup.total_estimated_hours == 0.0
                assert rollup.task_count == 2
                assert rollup.tasks_with_estimates == 0
                assert not rollup.has_estimates

        reset_engine()

    def test_tasks_with_estimates(self, tmp_path: Path) -> None:
        """Get rollup for tasks with time estimates."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.time_rollup_service import TimeRollupService
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

            # Create tasks with estimates
            task1 = Task(
                commitment_id=commitment_id,
                title="Task 1",
                scope="Scope 1",
                order=1,
                estimated_hours=2.0,
            )
            task2 = Task(
                commitment_id=commitment_id,
                title="Task 2",
                scope="Scope 2",
                order=2,
                estimated_hours=3.5,
            )

            with get_session() as session:
                session.add(task1)
                session.add(task2)

            with get_session() as session:
                service = TimeRollupService(session)
                rollup = service.get_rollup(commitment_id)

                assert rollup.total_estimated_hours == 5.5
                assert rollup.remaining_estimated_hours == 5.5  # All pending
                assert rollup.completed_estimated_hours == 0.0
                assert rollup.task_count == 2
                assert rollup.tasks_with_estimates == 2

        reset_engine()

    def test_mixed_task_statuses(self, tmp_path: Path) -> None:
        """Get rollup for tasks with mixed statuses."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.time_rollup_service import TimeRollupService
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

            # Create tasks with different statuses
            task1 = Task(
                commitment_id=commitment_id,
                title="Completed Task",
                scope="Scope 1",
                order=1,
                estimated_hours=2.0,
                status=TaskStatus.COMPLETED,
            )
            task2 = Task(
                commitment_id=commitment_id,
                title="In Progress Task",
                scope="Scope 2",
                order=2,
                estimated_hours=3.0,
                status=TaskStatus.IN_PROGRESS,
            )
            task3 = Task(
                commitment_id=commitment_id,
                title="Pending Task",
                scope="Scope 3",
                order=3,
                estimated_hours=1.5,
                status=TaskStatus.PENDING,
            )
            task4 = Task(
                commitment_id=commitment_id,
                title="Skipped Task",
                scope="Scope 4",
                order=4,
                estimated_hours=1.0,
                status=TaskStatus.SKIPPED,
            )

            with get_session() as session:
                session.add(task1)
                session.add(task2)
                session.add(task3)
                session.add(task4)

            with get_session() as session:
                service = TimeRollupService(session)
                rollup = service.get_rollup(commitment_id)

                assert rollup.total_estimated_hours == 7.5
                assert rollup.completed_estimated_hours == 2.0
                assert rollup.remaining_estimated_hours == 4.5
                assert rollup.task_count == 4
                assert rollup.completed_task_count == 1

        reset_engine()

    def test_mixed_estimates_and_no_estimates(self, tmp_path: Path) -> None:
        """Get rollup for mixed tasks (some with estimates, some without)."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.time_rollup_service import TimeRollupService
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

            # Create tasks - some with estimates, some without
            task1 = Task(
                commitment_id=commitment_id,
                title="Task with estimate",
                scope="Scope 1",
                order=1,
                estimated_hours=2.0,
            )
            task2 = Task(
                commitment_id=commitment_id,
                title="Task without estimate",
                scope="Scope 2",
                order=2,
            )

            with get_session() as session:
                session.add(task1)
                session.add(task2)

            with get_session() as session:
                service = TimeRollupService(session)
                rollup = service.get_rollup(commitment_id)

                assert rollup.total_estimated_hours == 2.0
                assert rollup.task_count == 2
                assert rollup.tasks_with_estimates == 1
                assert rollup.estimate_coverage == 0.5

        reset_engine()


class TestTimeRollupServiceBatch:
    """Tests for TimeRollupService batch methods."""

    def test_get_rollups_batch_empty_list(self, tmp_path: Path) -> None:
        """Get batch rollups for empty list returns empty dict."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.time_rollup_service import TimeRollupService

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            with get_session() as session:
                service = TimeRollupService(session)
                result = service.get_rollups_batch([])

                assert result == {}

        reset_engine()

    def test_get_rollups_batch_multiple_commitments(self, tmp_path: Path) -> None:
        """Get batch rollups for multiple commitments."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.time_rollup_service import TimeRollupService
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

            # Create tasks for commitment 1
            task1 = Task(
                commitment_id=commitment1_id,
                title="Task 1",
                scope="Scope 1",
                order=1,
                estimated_hours=2.0,
            )

            # Create tasks for commitment 2
            task2 = Task(
                commitment_id=commitment2_id,
                title="Task 2",
                scope="Scope 2",
                order=1,
                estimated_hours=3.0,
            )

            with get_session() as session:
                session.add(task1)
                session.add(task2)

            with get_session() as session:
                service = TimeRollupService(session)
                result = service.get_rollups_batch([commitment1_id, commitment2_id])

                assert commitment1_id in result
                assert commitment2_id in result
                assert result[commitment1_id].total_estimated_hours == 2.0
                assert result[commitment2_id].total_estimated_hours == 3.0

        reset_engine()


class TestTimeRollupEdgeCases:
    """Additional edge case tests for TimeRollupService."""

    def test_rollup_with_zero_hours_tasks(self, tmp_path: Path) -> None:
        """Rollup handles tasks with 0.0 estimated hours."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.time_rollup_service import TimeRollupService
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType
        from jdo.models.task import Task, TaskStatus

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

            tasks = [
                Task(
                    commitment_id=commitment_id,
                    title="Zero estimate",
                    scope="Scope",
                    order=1,
                    estimated_hours=0.0,
                ),
                Task(
                    commitment_id=commitment_id,
                    title="Normal estimate",
                    scope="Scope",
                    order=2,
                    estimated_hours=2.0,
                    status=TaskStatus.COMPLETED,
                ),
            ]

            with get_session() as session:
                for task in tasks:
                    session.add(task)

            with get_session() as session:
                service = TimeRollupService(session)
                rollup = service.get_rollup(commitment_id)

                assert rollup.total_estimated_hours == 2.0
                assert rollup.tasks_with_estimates == 2
                assert rollup.estimate_coverage == 1.0

        reset_engine()

    def test_rollup_mixed_status_tasks(self, tmp_path: Path) -> None:
        """Rollup correctly categorizes tasks by status."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.time_rollup_service import TimeRollupService
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType
        from jdo.models.task import Task, TaskStatus

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

            tasks = [
                Task(
                    commitment_id=commitment_id,
                    title="Pending",
                    scope="Scope",
                    order=1,
                    estimated_hours=1.0,
                    status=TaskStatus.PENDING,
                ),
                Task(
                    commitment_id=commitment_id,
                    title="In Progress",
                    scope="Scope",
                    order=2,
                    estimated_hours=2.0,
                    status=TaskStatus.IN_PROGRESS,
                ),
                Task(
                    commitment_id=commitment_id,
                    title="Completed",
                    scope="Scope",
                    order=3,
                    estimated_hours=3.0,
                    status=TaskStatus.COMPLETED,
                ),
                Task(
                    commitment_id=commitment_id,
                    title="Skipped",
                    scope="Scope",
                    order=4,
                    estimated_hours=4.0,
                    status=TaskStatus.SKIPPED,
                ),
            ]

            with get_session() as session:
                for task in tasks:
                    session.add(task)

            with get_session() as session:
                service = TimeRollupService(session)
                rollup = service.get_rollup(commitment_id)

                assert rollup.total_estimated_hours == 10.0
                assert rollup.remaining_estimated_hours == 3.0
                assert rollup.completed_estimated_hours == 3.0
                assert rollup.task_count == 4
                assert rollup.completed_task_count == 1

        reset_engine()

    def test_rollup_all_completed_tasks(self, tmp_path: Path) -> None:
        """Rollup with all completed tasks."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.time_rollup_service import TimeRollupService
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType
        from jdo.models.task import Task, TaskStatus

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

            tasks = [
                Task(
                    commitment_id=commitment_id,
                    title="Done 1",
                    scope="Scope",
                    order=1,
                    estimated_hours=1.0,
                    status=TaskStatus.COMPLETED,
                ),
                Task(
                    commitment_id=commitment_id,
                    title="Done 2",
                    scope="Scope",
                    order=2,
                    estimated_hours=2.0,
                    status=TaskStatus.COMPLETED,
                ),
            ]

            with get_session() as session:
                for task in tasks:
                    session.add(task)

            with get_session() as session:
                service = TimeRollupService(session)
                rollup = service.get_rollup(commitment_id)

                assert rollup.total_estimated_hours == 3.0
                assert rollup.remaining_estimated_hours == 0.0
                assert rollup.completed_estimated_hours == 3.0
                assert rollup.task_count == 2
                assert rollup.completed_task_count == 2

        reset_engine()

    def test_rollup_all_pending_tasks(self, tmp_path: Path) -> None:
        """Rollup with all pending tasks."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.db.time_rollup_service import TimeRollupService
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType
        from jdo.models.task import Task, TaskStatus

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

            tasks = [
                Task(
                    commitment_id=commitment_id,
                    title="Pending 1",
                    scope="Scope",
                    order=1,
                    estimated_hours=1.0,
                    status=TaskStatus.PENDING,
                ),
                Task(
                    commitment_id=commitment_id,
                    title="Pending 2",
                    scope="Scope",
                    order=2,
                    estimated_hours=2.0,
                    status=TaskStatus.PENDING,
                ),
            ]

            with get_session() as session:
                for task in tasks:
                    session.add(task)

            with get_session() as session:
                service = TimeRollupService(session)
                rollup = service.get_rollup(commitment_id)

                assert rollup.total_estimated_hours == 3.0
                assert rollup.remaining_estimated_hours == 3.0
                assert rollup.completed_estimated_hours == 0.0
                assert rollup.task_count == 2
                assert rollup.completed_task_count == 0

        reset_engine()

    def test_calculate_rollup_for_tasks_empty_list(self) -> None:
        """_calculate_rollup_for_tasks handles empty list."""
        from jdo.db.time_rollup_service import TimeRollupService

        service = TimeRollupService(MagicMock())
        rollup = service._calculate_rollup_for_tasks([])

        assert rollup.total_estimated_hours == 0.0
        assert rollup.remaining_estimated_hours == 0.0
        assert rollup.completed_estimated_hours == 0.0
        assert rollup.task_count == 0
        assert rollup.tasks_with_estimates == 0
        assert rollup.completed_task_count == 0
        assert rollup.estimate_coverage == 0.0
