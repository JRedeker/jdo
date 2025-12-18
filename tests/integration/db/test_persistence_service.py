"""Integration tests for PersistenceService using a real DB."""

from __future__ import annotations

from collections.abc import Generator
from datetime import date
from pathlib import Path

import pytest
from sqlmodel import Session, select

from jdo.db.engine import get_engine, reset_engine
from jdo.db.migrations import create_db_and_tables
from jdo.db.persistence import PersistenceService
from jdo.models import Commitment, Stakeholder


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
