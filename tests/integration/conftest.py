"""Integration test fixtures for JDO.

These fixtures create real database connections with seeded data
for testing database operations and workflows end-to-end.
"""

from collections.abc import Generator
from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlmodel import Session

from jdo.db.engine import get_engine, reset_engine
from jdo.db.migrations import create_db_and_tables
from jdo.models import Commitment, CommitmentStatus, Goal, GoalStatus, Stakeholder, StakeholderType


@pytest.fixture
def populated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[Session, None, None]:
    """Create a database pre-seeded with test data.

    Creates stakeholders, goals, and commitments for integration testing.
    Ensures proper cleanup of database connections to prevent resource warnings.
    """
    from jdo.config.settings import reset_settings

    # Configure test database
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("JDO_DATABASE_PATH", str(db_path))
    reset_settings()
    reset_engine()

    # Create tables and seed data
    create_db_and_tables()
    engine = get_engine()

    session = Session(engine)
    try:
        # Create stakeholders
        self_stakeholder = Stakeholder(name="Self", type=StakeholderType.SELF)
        team_stakeholder = Stakeholder(name="Engineering Team", type=StakeholderType.TEAM)
        session.add(self_stakeholder)
        session.add(team_stakeholder)
        session.commit()
        session.refresh(self_stakeholder)
        session.refresh(team_stakeholder)

        # Create goal
        goal = Goal(
            title="Ship v1.0",
            problem_statement="Need to deliver initial product",
            solution_vision="Complete MVP with core features",
            status=GoalStatus.ACTIVE,
        )
        session.add(goal)
        session.commit()
        session.refresh(goal)

        # Create commitment
        commitment = Commitment(
            deliverable="Complete testing infrastructure",
            stakeholder_id=team_stakeholder.id,
            goal_id=goal.id,
            due_date=date.today() + timedelta(days=14),
            status=CommitmentStatus.IN_PROGRESS,
        )
        session.add(commitment)
        session.commit()

        yield session
    finally:
        session.close()
        reset_engine()
        reset_settings()


@pytest.fixture
def auth_store_path(tmp_path: Path) -> Path:
    """Create a temporary path for auth.json.

    Returns the path where auth credentials would be stored.
    """
    auth_path = tmp_path / "auth.json"
    return auth_path
