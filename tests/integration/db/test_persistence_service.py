"""Integration tests for PersistenceService using a real DB."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from sqlmodel import Session, select

from jdo.db.engine import get_engine, reset_engine
from jdo.db.migrations import create_db_and_tables
from jdo.db.persistence import PersistenceService
from jdo.models import Commitment, CommitmentStatus, Stakeholder


@pytest.fixture
def db_session_with_tables(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[Session, None, None]:
    """Create a database with tables for integration testing."""
    from jdo.config.settings import reset_settings

    db_path = tmp_path / "persistence_test.db"
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
class TestPersistenceServiceIntegration:
    """Integration tests for PersistenceService."""

    def test_save_commitment_creates_stakeholder(self, db_session_with_tables: Session) -> None:
        """Saving a commitment creates a missing stakeholder."""
        session = db_session_with_tables
        service = PersistenceService(session)

        commitment = service.save_commitment(
            {
                "deliverable": "Ship the report",
                "stakeholder": "Finance",
                "due_date": date(2026, 1, 15),
            }
        )
        session.commit()

        assert commitment.id is not None

        stakeholders = list(session.exec(select(Stakeholder)).all())
        assert len(stakeholders) == 1
        assert stakeholders[0].name == "Finance"

        commitments = list(session.exec(select(Commitment)).all())
        assert len(commitments) == 1
        assert commitments[0].stakeholder_id == stakeholders[0].id

    def test_save_recurring_commitment_generates_first_instance(
        self, db_session_with_tables: Session
    ) -> None:
        """Saving a recurring commitment generates a first instance."""
        session = db_session_with_tables
        service = PersistenceService(session)

        recurring = service.save_recurring_commitment(
            {
                "deliverable_template": "Daily standup",
                "stakeholder_name": "Team",
                "recurrence_type": "daily",
            }
        )
        session.commit()

        assert recurring.id is not None
        assert recurring.instances_generated == 1
        assert recurring.last_generated_date is not None

        commitments = list(session.exec(select(Commitment)).all())
        assert len(commitments) == 1
        assert commitments[0].recurring_commitment_id == recurring.id

    def test_get_commitment_velocity_empty_db(self, db_session_with_tables: Session) -> None:
        """Velocity returns (0, 0) when database is empty."""
        session = db_session_with_tables
        service = PersistenceService(session)

        created, completed = service.get_commitment_velocity()
        assert created == 0
        assert completed == 0

    def test_get_commitment_velocity_time_window(self, db_session_with_tables: Session) -> None:
        """Velocity correctly filters by time window."""
        session = db_session_with_tables
        service = PersistenceService(session)

        now = datetime.now(UTC)

        # Create commitment from 10 days ago (outside 7-day window)
        old_commitment = service.save_commitment(
            {
                "deliverable": "Old task",
                "stakeholder": "TestUser",
                "due_date": date.today(),
            }
        )
        old_commitment.created_at = now - timedelta(days=10)
        session.add(old_commitment)

        # Create commitment from 3 days ago (inside 7-day window)
        recent_commitment = service.save_commitment(
            {
                "deliverable": "Recent task",
                "stakeholder": "TestUser",
                "due_date": date.today(),
            }
        )
        recent_commitment.created_at = now - timedelta(days=3)
        session.add(recent_commitment)

        # Complete the recent commitment
        recent_commitment.status = CommitmentStatus.COMPLETED
        recent_commitment.completed_at = now - timedelta(days=2)
        session.add(recent_commitment)

        session.commit()

        # Default 7-day window should only see the recent commitment
        created, completed = service.get_commitment_velocity(days=7)
        assert created == 1
        assert completed == 1

        # 14-day window should see both
        created, completed = service.get_commitment_velocity(days=14)
        assert created == 2
        assert completed == 1

    def test_get_commitment_velocity_only_counts_completed_status(
        self, db_session_with_tables: Session
    ) -> None:
        """Velocity only counts commitments with COMPLETED status for completion count."""
        session = db_session_with_tables
        service = PersistenceService(session)

        now = datetime.now(UTC)

        # Create two commitments
        for i in range(2):
            commitment = service.save_commitment(
                {
                    "deliverable": f"Task {i}",
                    "stakeholder": "TestUser",
                    "due_date": date.today(),
                }
            )
            commitment.created_at = now - timedelta(days=3)
            session.add(commitment)

        session.commit()

        # Mark one as completed, one as abandoned
        commitments = list(session.exec(select(Commitment)).all())
        commitments[0].status = CommitmentStatus.COMPLETED
        commitments[0].completed_at = now - timedelta(days=1)
        commitments[1].status = CommitmentStatus.ABANDONED
        commitments[1].completed_at = now - timedelta(days=1)

        session.add(commitments[0])
        session.add(commitments[1])
        session.commit()

        # Should count 2 created, but only 1 completed (abandoned doesn't count)
        created, completed = service.get_commitment_velocity()
        assert created == 2
        assert completed == 1
