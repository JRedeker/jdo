"""Integration tests for database migration operations."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from jdo.db.engine import get_engine, reset_engine
from jdo.db.migrations import (
    create_db_and_tables,
    create_revision,
    downgrade_database,
    get_alembic_config,
    get_migration_status,
    upgrade_database,
)


@pytest.fixture
def db_session_for_migrations(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Create a database for migration testing."""
    from jdo.config.settings import reset_settings

    db_path = tmp_path / "migration_test.db"
    monkeypatch.setenv("JDO_DATABASE_PATH", str(db_path))
    reset_settings()
    reset_engine()

    # Create initial tables
    create_db_and_tables()
    engine = get_engine()

    with Session(engine) as session:
        yield session

    reset_engine()
    reset_settings()


class TestGetAlembicConfig:
    """Tests for get_alembic_config function."""

    def test_returns_config_object(self):
        """get_alembic_config returns an Alembic Config object."""
        cfg = get_alembic_config()

        assert cfg is not None
        assert cfg.get_main_option("script_location") is not None

    def test_config_points_to_migrations_dir(self):
        """Config points to the migrations directory."""
        cfg = get_alembic_config()
        script_location = cfg.get_main_option("script_location")

        assert "migrations" in script_location


class TestCreateDbAndTables:
    """Tests for create_db_and_tables function."""

    def test_creates_tables(self, db_session_for_migrations):
        """create_db_and_tables creates all model tables."""
        # Tables should already exist from fixture
        # Verify by querying - this would fail if tables don't exist
        from jdo.models import Stakeholder

        result = db_session_for_migrations.exec(__import__("sqlmodel").select(Stakeholder)).all()
        # Should be empty but not error
        assert result == []


class TestMigrationCommands:
    """Tests for migration command functions."""

    @patch("jdo.db.migrations.command")
    def test_get_migration_status_calls_current(self, mock_command):
        """get_migration_status calls alembic current command."""
        get_migration_status()

        mock_command.current.assert_called_once()

    @patch("jdo.db.migrations.command")
    def test_upgrade_database_calls_upgrade(self, mock_command):
        """upgrade_database calls alembic upgrade command."""
        upgrade_database("head")

        mock_command.upgrade.assert_called_once()
        call_args = mock_command.upgrade.call_args
        assert call_args[0][1] == "head"  # Second arg is revision

    @patch("jdo.db.migrations.command")
    def test_downgrade_database_calls_downgrade(self, mock_command):
        """downgrade_database calls alembic downgrade command."""
        downgrade_database("-1")

        mock_command.downgrade.assert_called_once()
        call_args = mock_command.downgrade.call_args
        assert call_args[0][1] == "-1"

    @patch("jdo.db.migrations.command")
    def test_create_revision_calls_revision(self, mock_command):
        """create_revision calls alembic revision command."""
        create_revision("test migration", autogenerate=True)

        mock_command.revision.assert_called_once()
        call_kwargs = mock_command.revision.call_args.kwargs
        assert call_kwargs["message"] == "test migration"
        assert call_kwargs["autogenerate"] is True


class TestMigrationsDirectory:
    """Tests for migrations directory structure."""

    def test_migrations_directory_exists(self):
        """Migrations directory exists."""
        cfg = get_alembic_config()
        script_location = Path(cfg.get_main_option("script_location"))

        assert script_location.exists()
        assert script_location.is_dir()

    def test_alembic_ini_exists(self):
        """alembic.ini configuration file exists."""
        cfg = get_alembic_config()
        script_location = Path(cfg.get_main_option("script_location"))
        alembic_ini = script_location / "alembic.ini"

        assert alembic_ini.exists()

    def test_env_py_exists(self):
        """env.py environment file exists."""
        cfg = get_alembic_config()
        script_location = Path(cfg.get_main_option("script_location"))
        env_py = script_location / "env.py"

        assert env_py.exists()

    def test_script_template_exists(self):
        """script.py.mako template file exists."""
        cfg = get_alembic_config()
        script_location = Path(cfg.get_main_option("script_location"))
        template = script_location / "script.py.mako"

        assert template.exists()

    def test_versions_directory_exists(self):
        """versions directory for migration scripts exists."""
        cfg = get_alembic_config()
        script_location = Path(cfg.get_main_option("script_location"))
        versions_dir = script_location / "versions"

        assert versions_dir.exists()
        assert versions_dir.is_dir()
