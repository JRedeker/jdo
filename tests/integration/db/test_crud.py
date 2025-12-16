"""Integration tests for database CRUD operations."""

from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlmodel import Session, select

from jdo.db.engine import get_engine, reset_engine
from jdo.db.migrations import create_db_and_tables
from jdo.models import Commitment, CommitmentStatus, Stakeholder, StakeholderType


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
