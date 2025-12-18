"""Tests for Commitment SQLModel - TDD Red phase."""

from datetime import UTC, date, time
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
        assert "milestone_id" in fields  # NEW: Milestone hierarchy link
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
        assert commitment.milestone_id is None  # NEW: Milestone hierarchy link
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

    def test_has_at_risk_status(self) -> None:
        """CommitmentStatus includes at_risk value for integrity protocol."""
        assert CommitmentStatus.AT_RISK.value == "at_risk"


class TestCommitmentAtRiskFields:
    """Tests for Commitment at-risk and integrity fields."""

    def test_has_marked_at_risk_at_field(self) -> None:
        """Commitment has marked_at_risk_at datetime field."""
        fields = Commitment.model_fields
        assert "marked_at_risk_at" in fields

    def test_marked_at_risk_at_defaults_to_none(self) -> None:
        """marked_at_risk_at defaults to None."""
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=uuid4(),
            due_date=date(2025, 12, 31),
        )
        assert commitment.marked_at_risk_at is None

    def test_has_completed_on_time_field(self) -> None:
        """Commitment has completed_on_time boolean field."""
        fields = Commitment.model_fields
        assert "completed_on_time" in fields

    def test_completed_on_time_defaults_to_none(self) -> None:
        """completed_on_time defaults to None (set on completion)."""
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=uuid4(),
            due_date=date(2025, 12, 31),
        )
        assert commitment.completed_on_time is None

    def test_can_set_at_risk_status(self) -> None:
        """Commitment can be set to at_risk status."""
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=uuid4(),
            due_date=date(2025, 12, 31),
            status=CommitmentStatus.AT_RISK,
        )
        assert commitment.status == CommitmentStatus.AT_RISK

    def test_can_set_marked_at_risk_at_timestamp(self) -> None:
        """Commitment can store marked_at_risk_at timestamp."""
        from datetime import datetime, timezone

        now = datetime.now(UTC)
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=uuid4(),
            due_date=date(2025, 12, 31),
            status=CommitmentStatus.AT_RISK,
            marked_at_risk_at=now,
        )
        assert commitment.marked_at_risk_at == now

    def test_can_set_completed_on_time_true(self) -> None:
        """completed_on_time can be set to True."""
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=uuid4(),
            due_date=date(2025, 12, 31),
            status=CommitmentStatus.COMPLETED,
            completed_on_time=True,
        )
        assert commitment.completed_on_time is True

    def test_can_set_completed_on_time_false(self) -> None:
        """completed_on_time can be set to False."""
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=uuid4(),
            due_date=date(2025, 12, 31),
            status=CommitmentStatus.COMPLETED,
            completed_on_time=False,
        )
        assert commitment.completed_on_time is False


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

    def test_accepts_optional_milestone_id(self) -> None:
        """Commitment accepts optional milestone_id."""
        milestone_id = uuid4()
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=uuid4(),
            milestone_id=milestone_id,
            due_date=date(2025, 12, 31),
        )

        assert commitment.milestone_id == milestone_id


class TestCommitmentPersistence:
    """Tests for Commitment database persistence."""

    def test_save_and_retrieve(self, tmp_path: Path) -> None:
        """Save commitment via session and retrieve by id."""
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
        from jdo.models.goal import Goal
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

    def test_foreign_key_to_milestone(self, tmp_path: Path) -> None:
        """Commitment has optional FK to milestones table."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.models.goal import Goal
        from jdo.models.milestone import Milestone
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Carol", type=StakeholderType.PERSON)
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

            milestone = Milestone(
                goal_id=goal_id,
                title="First Milestone",
                target_date=date(2025, 6, 1),
            )
            milestone_id = milestone.id

            with get_session() as session:
                session.add(milestone)

            commitment = Commitment(
                deliverable="Work toward milestone",
                stakeholder_id=stakeholder_id,
                milestone_id=milestone_id,
                due_date=date(2025, 5, 1),
            )

            with get_session() as session:
                session.add(commitment)

            # Query commitments by milestone
            with get_session() as session:
                result = session.exec(
                    select(Commitment).where(Commitment.milestone_id == milestone_id)
                ).first()

                assert result is not None
                assert result.deliverable == "Work toward milestone"

        reset_engine()


class TestCommitmentRecurringLink:
    """Tests for Commitment link to RecurringCommitment."""

    def test_has_recurring_commitment_id_field(self) -> None:
        """Commitment has optional recurring_commitment_id field."""
        fields = Commitment.model_fields
        assert "recurring_commitment_id" in fields

    def test_accepts_optional_recurring_commitment_id(self) -> None:
        """Commitment accepts optional recurring_commitment_id."""
        recurring_id = uuid4()
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=uuid4(),
            due_date=date(2025, 12, 31),
            recurring_commitment_id=recurring_id,
        )

        assert commitment.recurring_commitment_id == recurring_id

    def test_recurring_commitment_id_defaults_to_none(self) -> None:
        """recurring_commitment_id defaults to None."""
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=uuid4(),
            due_date=date(2025, 12, 31),
        )

        assert commitment.recurring_commitment_id is None

    def test_is_recurring_property(self) -> None:
        """Commitment.is_recurring returns True when linked to recurring."""
        # Not recurring
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=uuid4(),
            due_date=date(2025, 12, 31),
        )
        assert not commitment.is_recurring

        # Recurring
        recurring_commitment = Commitment(
            deliverable="Test",
            stakeholder_id=uuid4(),
            due_date=date(2025, 12, 31),
            recurring_commitment_id=uuid4(),
        )
        assert recurring_commitment.is_recurring


class TestCommitmentOrphanTracking:
    """Tests for Commitment orphan tracking (no goal AND no milestone)."""

    def test_is_orphan_with_neither_goal_nor_milestone(self) -> None:
        """Commitment without goal_id AND milestone_id is orphan."""
        commitment = Commitment(
            deliverable="Unlinked task",
            stakeholder_id=uuid4(),
            due_date=date(2025, 12, 31),
        )

        assert commitment.is_orphan()

    def test_is_not_orphan_with_goal_id(self) -> None:
        """Commitment with goal_id is NOT orphan."""
        commitment = Commitment(
            deliverable="Task with goal",
            stakeholder_id=uuid4(),
            goal_id=uuid4(),
            due_date=date(2025, 12, 31),
        )

        assert not commitment.is_orphan()

    def test_is_not_orphan_with_milestone_id(self) -> None:
        """Commitment with milestone_id is NOT orphan (even without goal_id)."""
        commitment = Commitment(
            deliverable="Task with milestone",
            stakeholder_id=uuid4(),
            milestone_id=uuid4(),
            due_date=date(2025, 12, 31),
        )

        assert not commitment.is_orphan()

    def test_is_not_orphan_with_both(self) -> None:
        """Commitment with both goal_id and milestone_id is NOT orphan."""
        commitment = Commitment(
            deliverable="Task with both",
            stakeholder_id=uuid4(),
            goal_id=uuid4(),
            milestone_id=uuid4(),
            due_date=date(2025, 12, 31),
        )

        assert not commitment.is_orphan()

    def test_query_orphan_commitments(self, tmp_path: Path) -> None:
        """Query commitments without goal AND without milestone."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.models.goal import Goal
        from jdo.models.milestone import Milestone
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
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

            milestone = Milestone(
                goal_id=goal_id,
                title="Test Milestone",
                target_date=date(2025, 6, 1),
            )
            milestone_id = milestone.id

            with get_session() as session:
                session.add(milestone)

            # Create various commitments
            orphan = Commitment(
                deliverable="Orphan task",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
            )
            with_goal = Commitment(
                deliverable="Task with goal",
                stakeholder_id=stakeholder_id,
                goal_id=goal_id,
                due_date=date(2025, 12, 31),
            )
            with_milestone = Commitment(
                deliverable="Task with milestone",
                stakeholder_id=stakeholder_id,
                milestone_id=milestone_id,
                due_date=date(2025, 12, 31),
            )

            with get_session() as session:
                session.add(orphan)
                session.add(with_goal)
                session.add(with_milestone)

            # Query orphans
            with get_session() as session:
                result = session.exec(
                    select(Commitment).where(
                        Commitment.goal_id.is_(None),  # type: ignore[union-attr]
                        Commitment.milestone_id.is_(None),  # type: ignore[union-attr]
                    )
                ).all()

                assert len(result) == 1
                assert result[0].deliverable == "Orphan task"

        reset_engine()
