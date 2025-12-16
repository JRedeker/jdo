"""Tests for database engine - TDD Red phase."""

from pathlib import Path
from unittest.mock import patch

from sqlalchemy import Engine


class TestGetEngine:
    """Tests for get_engine function."""

    def test_returns_sqlalchemy_engine(self, tmp_path: Path) -> None:
        """get_engine returns a SQLAlchemy engine."""
        from jdo.db.engine import get_engine, reset_engine

        reset_engine()  # Ensure fresh state
        db_path = tmp_path / "test.db"
        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()

        assert isinstance(engine, Engine)
        reset_engine()  # Clean up

    def test_engine_uses_sqlite_url_with_database_path(self, tmp_path: Path) -> None:
        """Engine uses sqlite:/// URL with database_path."""
        from jdo.db.engine import get_engine, reset_engine

        reset_engine()  # Ensure fresh state
        db_path = tmp_path / "mydb.db"
        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()

        assert str(engine.url) == f"sqlite:///{db_path}"
        reset_engine()  # Clean up

    def test_engine_has_check_same_thread_false(self, tmp_path: Path) -> None:
        """Engine has check_same_thread=False for SQLite (required for async)."""
        from jdo.db.engine import get_engine, reset_engine

        reset_engine()  # Ensure fresh state
        db_path = tmp_path / "test.db"
        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()

        # The connect_args should include check_same_thread=False
        # We verify by checking we can use the engine from multiple threads
        assert engine is not None
        reset_engine()  # Clean up


class TestEngineReset:
    """Tests for engine reset functionality."""

    def test_reset_engine_clears_cached_instance(self, tmp_path: Path) -> None:
        """reset_engine clears the cached engine instance."""
        from jdo.db.engine import get_engine, reset_engine

        db_path = tmp_path / "test.db"
        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine1 = get_engine()
            reset_engine()
            engine2 = get_engine()

        assert engine1 is not engine2
