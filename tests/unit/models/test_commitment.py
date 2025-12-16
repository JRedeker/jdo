"""Tests for Commitment SQLModel - TDD Red phase."""

from datetime import date, time
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlmodel import SQLModel

from jdo.models.commitment import Commitment, CommitmentStatus


class TestCommitmentModel:
    """Tests for Commitment model structure."""

    def test_inherits_from_sqlmodel_with_table_true(self) -> None:
        """Commitment inherits from SQLModel with table=True."""
        assert issubclass(Commitment, SQLModel)
        assert hasattr(Commitment, "__tablename__")

    def test_has_tablename_commitments(self) -> None:
        """Commitment has tablename 'commitments'."""
        assert Commitment.__tablename__ == "commitments"

    def test_has_required_fields(self) -> None:
        """Commitment has all required fields."""
        fields = Commitment.model_fields
        assert "id" in fields
        assert "deliverable" in fields
        assert "stakeholder_id" in fields
        assert "goal_id" in fields
        assert "due_date" in fields
        assert "due_time" in fields
        assert "timezone" in fields
        assert "status" in fields
        assert "completed_at" in fields
        assert "notes" in fields
        assert "created_at" in fields
        assert "updated_at" in fields


class TestCommitmentValidation:
    """Tests for Commitment field validation."""

    def test_creates_with_required_fields(self) -> None:
        """Create commitment with required fields."""
        stakeholder_id = uuid4()
        commitment = Commitment(
            deliverable="Send report",
            stakeholder_id=stakeholder_id,
            due_date=date(2025, 12, 31),
        )

        assert commitment.deliverable == "Send report"
        assert commitment.stakeholder_id == stakeholder_id
        assert commitment.due_date == date(2025, 12, 31)
        assert commitment.status == CommitmentStatus.PENDING
        assert isinstance(commitment.id, UUID)

    def test_validates_deliverable_non_empty(self) -> None:
        """Reject empty deliverable via model_validate."""
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            Commitment.model_validate(
                {
                    "deliverable": "",
                    "stakeholder_id": str(uuid4()),
                    "due_date": "2025-12-31",
                }
            )

    def test_due_time_defaults_to_nine_am(self) -> None:
        """due_time defaults to 09:00 if not specified."""
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=uuid4(),
            due_date=date(2025, 12, 31),
        )

        assert commitment.due_time == time(9, 0)

    def test_accepts_specific_due_time(self) -> None:
        """Accept specific due_time."""
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=uuid4(),
            due_date=date(2025, 12, 31),
            due_time=time(15, 0),
        )

        assert commitment.due_time == time(15, 0)

    def test_timezone_defaults_to_est(self) -> None:
        """timezone defaults to America/New_York."""
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=uuid4(),
            due_date=date(2025, 12, 31),
        )

        assert commitment.timezone == "America/New_York"

    def test_optional_fields_default_properly(self) -> None:
        """Optional fields have correct defaults."""
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=uuid4(),
            due_date=date(2025, 12, 31),
        )

        assert commitment.goal_id is None
        assert commitment.completed_at is None
        assert commitment.notes is None


class TestCommitmentStatus:
    """Tests for CommitmentStatus enum."""

    def test_has_required_values(self) -> None:
        """CommitmentStatus has pending, in_progress, completed, abandoned."""
        assert CommitmentStatus.PENDING.value == "pending"
        assert CommitmentStatus.IN_PROGRESS.value == "in_progress"
        assert CommitmentStatus.COMPLETED.value == "completed"
        assert CommitmentStatus.ABANDONED.value == "abandoned"


class TestCommitmentForeignKeys:
    """Tests for Commitment foreign key relationships."""

    def test_accepts_stakeholder_id(self) -> None:
        """Commitment requires stakeholder_id."""
        stakeholder_id = uuid4()
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=stakeholder_id,
            due_date=date(2025, 12, 31),
        )

        assert commitment.stakeholder_id == stakeholder_id

    def test_accepts_optional_goal_id(self) -> None:
        """Commitment accepts optional goal_id."""
        goal_id = uuid4()
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=uuid4(),
            goal_id=goal_id,
            due_date=date(2025, 12, 31),
        )

        assert commitment.goal_id == goal_id


class TestCommitmentPersistence:
    """Tests for Commitment database persistence."""

    def test_save_and_retrieve(self, tmp_path: Path) -> None:
        """Save commitment via session and retrieve by id."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.models.goal import Goal  # noqa: F401 - needed for FK resolution
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Create stakeholder first
            stakeholder = Stakeholder(name="Test Person", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            # Create commitment
            commitment = Commitment(
                deliverable="Send report",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
            )
            commitment_id = commitment.id

            with get_session() as session:
                session.add(commitment)

            # Retrieve
            with get_session() as session:
                result = session.exec(
                    select(Commitment).where(Commitment.id == commitment_id)
                ).first()

                assert result is not None
                assert result.deliverable == "Send report"
                assert result.stakeholder_id == stakeholder_id

        reset_engine()

    def test_foreign_key_to_stakeholder(self, tmp_path: Path) -> None:
        """Commitment has FK to stakeholders table."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.models.goal import Goal  # noqa: F401 - needed for FK resolution
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Alice", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            commitment = Commitment(
                deliverable="Task for Alice",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
            )

            with get_session() as session:
                session.add(commitment)

            # Query commitments by stakeholder
            with get_session() as session:
                result = session.exec(
                    select(Commitment).where(Commitment.stakeholder_id == stakeholder_id)
                ).first()

                assert result is not None
                assert result.deliverable == "Task for Alice"

        reset_engine()

    def test_foreign_key_to_goal(self, tmp_path: Path) -> None:
        """Commitment has optional FK to goals table."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.models.goal import Goal
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Bob", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            goal = Goal(
                title="Test Goal",
                problem_statement="Problem",
                solution_vision="Vision",
            )
            goal_id = goal.id

            with get_session() as session:
                session.add(stakeholder)
                session.add(goal)

            commitment = Commitment(
                deliverable="Work toward goal",
                stakeholder_id=stakeholder_id,
                goal_id=goal_id,
                due_date=date(2025, 12, 31),
            )

            with get_session() as session:
                session.add(commitment)

            # Query commitments by goal
            with get_session() as session:
                result = session.exec(
                    select(Commitment).where(Commitment.goal_id == goal_id)
                ).first()

                assert result is not None
                assert result.deliverable == "Work toward goal"

        reset_engine()
