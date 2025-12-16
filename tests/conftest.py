"""Shared pytest fixtures for JDO tests."""

from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture
def db_engine():
    """Create an in-memory SQLite engine for testing.

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
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a database session for testing.

    Yields a session from the test engine and rolls back
    any changes after the test completes.
    """
    with Session(db_engine) as session:
        yield session
        session.rollback()


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory for testing.

    Returns a Path to a temporary directory that will be
    cleaned up after the test.
    """
    data_dir = tmp_path / "jdo_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def test_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Create test settings with environment variable overrides.

    Configures JDO settings to use temporary paths and test values.
    Resets the settings singleton after the test.
    """
    from jdo.config.settings import reset_settings

    # Set up test environment
    monkeypatch.setenv("JDO_DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("JDO_AI_PROVIDER", "anthropic")
    monkeypatch.setenv("JDO_AI_MODEL", "claude-sonnet-4-20250514")
    monkeypatch.setenv("JDO_TIMEZONE", "UTC")
    monkeypatch.setenv("JDO_LOG_LEVEL", "DEBUG")

    reset_settings()

    from jdo.config.settings import get_settings

    yield get_settings()

    reset_settings()
