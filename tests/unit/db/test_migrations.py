"""Tests for database migrations."""

from pathlib import Path
from unittest.mock import patch

from sqlalchemy import inspect


class TestCreateDbAndTables:
    """Tests for create_db_and_tables function."""

    def test_creates_all_tables(self, tmp_path: Path) -> None:
        """create_db_and_tables creates all SQLModel tables."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.migrations import create_db_and_tables

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            create_db_and_tables()
            engine = get_engine()

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # Should have all 4 model tables
        assert "stakeholders" in tables
        assert "goals" in tables
        assert "commitments" in tables
        assert "tasks" in tables
        reset_engine()

    def test_preserves_existing_data(self, tmp_path: Path) -> None:
        """create_db_and_tables preserves existing tables and data."""
        from sqlmodel import Session, select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.migrations import create_db_and_tables
        from jdo.models import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path

            # First create tables and add data
            create_db_and_tables()
            engine = get_engine()

            with Session(engine) as session:
                stakeholder = Stakeholder(
                    name="Test Stakeholder",
                    type=StakeholderType.PERSON,
                )
                session.add(stakeholder)
                session.commit()

            # Call create_db_and_tables again
            create_db_and_tables()

            # Data should still exist
            with Session(engine) as session:
                result = session.exec(select(Stakeholder)).first()
                assert result is not None
                assert result.name == "Test Stakeholder"

        reset_engine()

    def test_creates_foreign_key_constraints(self, tmp_path: Path) -> None:
        """create_db_and_tables creates proper foreign key constraints."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.migrations import create_db_and_tables

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            create_db_and_tables()
            engine = get_engine()

        inspector = inspect(engine)

        # Check commitments table has FKs to stakeholders and goals
        commitment_fks = inspector.get_foreign_keys("commitments")
        fk_tables = {fk["referred_table"] for fk in commitment_fks}
        assert "stakeholders" in fk_tables
        assert "goals" in fk_tables

        # Check tasks table has FK to commitments
        task_fks = inspector.get_foreign_keys("tasks")
        task_fk_tables = {fk["referred_table"] for fk in task_fks}
        assert "commitments" in task_fk_tables

        # Check goals table has self-referential FK
        goal_fks = inspector.get_foreign_keys("goals")
        goal_fk_tables = {fk["referred_table"] for fk in goal_fks}
        assert "goals" in goal_fk_tables

        reset_engine()
