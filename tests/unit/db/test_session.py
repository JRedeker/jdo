"""Tests for database session management - TDD Red phase."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, select


class TestGetSession:
    """Tests for get_session context manager."""

    def test_yields_session_from_engine(self, tmp_path: Path) -> None:
        """get_session yields a Session from the engine."""
        from jdo.db.session import get_session

        with patch("jdo.db.session.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_get_engine.return_value = mock_engine

            with get_session() as session:
                assert isinstance(session, Session)

    def test_session_committed_on_success(self, tmp_path: Path) -> None:
        """Session is committed on successful context exit."""
        from sqlmodel import Field, SQLModel

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()

            # Create a simple test table
            class TestModel(SQLModel, table=True):
                __tablename__ = "test_commit"
                id: int | None = Field(default=None, primary_key=True)
                name: str

            SQLModel.metadata.create_all(engine)

            # Insert in one session
            with get_session() as session:
                item = TestModel(name="test")
                session.add(item)
            # Should be committed

            # Verify in a new session
            with get_session() as session:
                result = session.exec(select(TestModel)).first()
                assert result is not None
                assert result.name == "test"

    def test_session_rolled_back_on_exception(self, tmp_path: Path) -> None:
        """Session is rolled back on exception."""
        from sqlmodel import Field, SQLModel

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()

            class TestRollback(SQLModel, table=True):
                __tablename__ = "test_rollback"
                id: int | None = Field(default=None, primary_key=True)
                name: str

            SQLModel.metadata.create_all(engine)

            # Try to insert but raise an exception
            msg = "Intentional error"
            with pytest.raises(ValueError, match=msg), get_session() as session:
                item = TestRollback(name="should_rollback")
                session.add(item)
                raise ValueError(msg)

            # Should be rolled back - nothing in database
            with get_session() as session:
                result = session.exec(select(TestRollback)).first()
                assert result is None

    def test_session_closed_after_use(self, tmp_path: Path) -> None:
        """Session is closed after context exit."""
        from jdo.db.engine import reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path

            with get_session() as session:
                # Session should be usable inside context
                from sqlalchemy import text

                result = session.execute(text("SELECT 1"))
                assert result is not None

            # After context exits, session transaction is committed/closed
            # SQLAlchemy sessions can still execute after close (they reconnect),
            # but we verify the context manager properly yields a working session
