"""TUI test fixtures for JDO."""

from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from jdo.app import JdoApp


@pytest.fixture
def test_db_engine():
    """Create an in-memory SQLite engine for TUI testing.

    Uses StaticPool to ensure the same connection is reused,
    which is required for in-memory SQLite databases.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create a database session for TUI testing."""
    with Session(test_db_engine) as session:
        yield session
        session.rollback()


@pytest.fixture
def mock_db_engine(test_db_engine, monkeypatch):
    """Mock the database engine to use in-memory SQLite.

    This patches get_engine to return our test engine,
    ensuring all database operations use the test database.
    """
    from jdo.db import engine as engine_module

    monkeypatch.setattr(engine_module, "_engine", test_db_engine)
    return test_db_engine


@pytest.fixture
def app(tmp_path: Path, monkeypatch) -> Generator[JdoApp, None, None]:
    """Create a JdoApp instance for testing.

    Sets up test environment with temporary database and paths.
    Ensures engine is reset before and after each test for isolation.
    """
    from jdo.config.settings import reset_settings
    from jdo.db.engine import reset_engine

    # Reset engine before test to ensure fresh database
    reset_engine()

    # Set up test environment
    monkeypatch.setenv("JDO_DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("JDO_AI_PROVIDER", "anthropic")
    monkeypatch.setenv("JDO_AI_MODEL", "claude-sonnet-4-20250514")
    monkeypatch.setenv("JDO_TIMEZONE", "UTC")
    monkeypatch.setenv("JDO_LOG_LEVEL", "DEBUG")
    # Set a test API key to bypass AI-required screen
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-for-testing")

    reset_settings()

    yield JdoApp()

    # Reset engine after test for isolation
    reset_engine()
