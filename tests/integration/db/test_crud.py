"""Integration tests for database CRUD operations."""

from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlmodel import Session, select

from jdo.db.engine import get_engine, reset_engine
from jdo.db.migrations import create_db_and_tables
from jdo.models import Commitment, CommitmentStatus, Stakeholder, StakeholderType
from jdo.models.recurring_commitment import RecurrenceType, RecurringCommitment


@pytest.fixture
def db_session_with_tables(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Create a database with tables for CRUD testing."""
    from jdo.config.settings import reset_settings

    db_path = tmp_path / "crud_test.db"
    monkeypatch.setenv("JDO_DATABASE_PATH", str(db_path))
    reset_settings()
    reset_engine()

    create_db_and_tables()
    engine = get_engine()

    with Session(engine) as session:
        yield session

    reset_engine()
    reset_settings()


@pytest.mark.integration
class TestStakeholderCRUD:
    """Tests for Stakeholder CRUD operations."""

    def test_create_stakeholder(self, db_session_with_tables: Session) -> None:
        """Can create a stakeholder in the database."""
        session = db_session_with_tables

        stakeholder = Stakeholder(name="Test User", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        assert stakeholder.id is not None
        assert stakeholder.name == "Test User"
        assert stakeholder.type == StakeholderType.PERSON

    def test_read_stakeholder(self, db_session_with_tables: Session) -> None:
        """Can read a stakeholder from the database."""
        session = db_session_with_tables

        # Create
        stakeholder = Stakeholder(name="Read Test", type=StakeholderType.TEAM)
        session.add(stakeholder)
        session.commit()
        stakeholder_id = stakeholder.id

        # Read
        result = session.get(Stakeholder, stakeholder_id)
        assert result is not None
        assert result.name == "Read Test"

    def test_update_stakeholder(self, db_session_with_tables: Session) -> None:
        """Can update a stakeholder in the database."""
        session = db_session_with_tables

        stakeholder = Stakeholder(name="Original", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()

        stakeholder.name = "Updated"
        session.commit()
        session.refresh(stakeholder)

        assert stakeholder.name == "Updated"

    def test_delete_stakeholder(self, db_session_with_tables: Session) -> None:
        """Can delete a stakeholder from the database."""
        session = db_session_with_tables

        stakeholder = Stakeholder(name="To Delete", type=StakeholderType.SELF)
        session.add(stakeholder)
        session.commit()
        stakeholder_id = stakeholder.id

        session.delete(stakeholder)
        session.commit()

        result = session.get(Stakeholder, stakeholder_id)
        assert result is None


@pytest.mark.integration
class TestCommitmentCRUD:
    """Tests for Commitment CRUD operations."""

    def test_create_commitment_with_stakeholder(self, db_session_with_tables: Session) -> None:
        """Can create a commitment linked to a stakeholder."""
        session = db_session_with_tables

        # Create stakeholder first
        stakeholder = Stakeholder(name="Manager", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        # Create commitment
        commitment = Commitment(
            deliverable="Finish report",
            stakeholder_id=stakeholder.id,
            due_date=date.today() + timedelta(days=7),
            status=CommitmentStatus.PENDING,
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)

        assert commitment.id is not None
        assert commitment.stakeholder_id == stakeholder.id

    def test_query_commitments_by_status(self, db_session_with_tables: Session) -> None:
        """Can query commitments by status."""
        session = db_session_with_tables

        stakeholder = Stakeholder(name="Self", type=StakeholderType.SELF)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        # Create multiple commitments
        pending = Commitment(
            deliverable="Pending task",
            stakeholder_id=stakeholder.id,
            due_date=date.today() + timedelta(days=3),
            status=CommitmentStatus.PENDING,
        )
        in_progress = Commitment(
            deliverable="In progress task",
            stakeholder_id=stakeholder.id,
            due_date=date.today() + timedelta(days=5),
            status=CommitmentStatus.IN_PROGRESS,
        )
        session.add_all([pending, in_progress])
        session.commit()

        # Query by status
        results = session.exec(
            select(Commitment).where(Commitment.status == CommitmentStatus.PENDING)
        ).all()

        assert len(results) == 1
        assert results[0].deliverable == "Pending task"


@pytest.mark.integration
class TestRecurringCommitmentCRUD:
    """Tests for RecurringCommitment CRUD operations and FK behavior."""

    def test_create_recurring_commitment(self, db_session_with_tables: Session) -> None:
        """Can create a recurring commitment in the database."""
        session = db_session_with_tables

        # Create stakeholder first
        stakeholder = Stakeholder(name="Manager", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        # Create recurring commitment
        recurring = RecurringCommitment(
            deliverable_template="Weekly status report",
            stakeholder_id=stakeholder.id,
            recurrence_type=RecurrenceType.WEEKLY,
            days_of_week=[0],  # Monday
        )
        session.add(recurring)
        session.commit()
        session.refresh(recurring)

        assert recurring.id is not None
        assert recurring.deliverable_template == "Weekly status report"

    def test_delete_recurring_sets_commitment_link_to_null(
        self, db_session_with_tables: Session
    ) -> None:
        """Deleting RecurringCommitment sets linked Commitment.recurring_commitment_id to NULL."""
        session = db_session_with_tables

        # Create stakeholder
        stakeholder = Stakeholder(name="Self", type=StakeholderType.SELF)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        # Create recurring commitment
        recurring = RecurringCommitment(
            deliverable_template="Daily standup",
            stakeholder_id=stakeholder.id,
            recurrence_type=RecurrenceType.DAILY,
        )
        session.add(recurring)
        session.commit()
        session.refresh(recurring)
        recurring_id = recurring.id

        # Create commitment linked to recurring
        commitment = Commitment(
            deliverable="Daily standup",
            stakeholder_id=stakeholder.id,
            recurring_commitment_id=recurring_id,
            due_date=date.today() + timedelta(days=1),
            status=CommitmentStatus.PENDING,
        )
        session.add(commitment)
        session.commit()
        commitment_id = commitment.id

        # Verify link exists
        session.refresh(commitment)
        assert commitment.recurring_commitment_id == recurring_id

        # Delete the recurring commitment
        session.delete(recurring)
        session.commit()

        # Expire session cache to get fresh data from DB
        session.expire_all()

        # Verify commitment still exists but link is NULL
        result = session.get(Commitment, commitment_id)
        assert result is not None
        assert result.deliverable == "Daily standup"
        assert result.recurring_commitment_id is None  # Should be NULL now

    def test_delete_recurring_preserves_multiple_instances(
        self, db_session_with_tables: Session
    ) -> None:
        """Deleting RecurringCommitment preserves all spawned instances."""
        session = db_session_with_tables

        # Create stakeholder
        stakeholder = Stakeholder(name="Team", type=StakeholderType.TEAM)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        # Create recurring commitment
        recurring = RecurringCommitment(
            deliverable_template="Weekly report",
            stakeholder_id=stakeholder.id,
            recurrence_type=RecurrenceType.WEEKLY,
            days_of_week=[4],  # Friday
        )
        session.add(recurring)
        session.commit()
        session.refresh(recurring)
        recurring_id = recurring.id

        # Create multiple instances
        commitment_ids = []
        for i in range(3):
            commitment = Commitment(
                deliverable="Weekly report",
                stakeholder_id=stakeholder.id,
                recurring_commitment_id=recurring_id,
                due_date=date.today() + timedelta(days=7 * i),
                status=CommitmentStatus.PENDING,
            )
            session.add(commitment)
            session.commit()
            commitment_ids.append(commitment.id)

        # Delete the recurring commitment
        session.delete(recurring)
        session.commit()

        # Expire session cache to get fresh data from DB
        session.expire_all()

        # Verify all instances still exist with NULL links
        for cid in commitment_ids:
            result = session.get(Commitment, cid)
            assert result is not None
            assert result.recurring_commitment_id is None
