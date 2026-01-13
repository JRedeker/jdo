"""Shared pytest fixtures for JDO tests.

This module provides core fixtures used across all test types.
See docs/TESTING.md for best practices and usage guidelines.
"""

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

    The engine is properly disposed after the test to prevent
    resource warnings about unclosed database connections.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    try:
        yield engine
    finally:
        # Ensure all connections are closed before disposal
        engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a database session for testing.

    Yields a session from the test engine and rolls back
    any changes after the test completes. The session is
    explicitly closed to prevent resource warnings.
    """
    session = Session(db_engine)
    try:
        yield session
        session.rollback()
    finally:
        session.close()


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
    monkeypatch.setenv("JDO_AI_PROVIDER", "openai")
    monkeypatch.setenv("JDO_AI_MODEL", "gpt-4o")
    monkeypatch.setenv("JDO_TIMEZONE", "UTC")
    monkeypatch.setenv("JDO_LOG_LEVEL", "DEBUG")

    reset_settings()

    from jdo.config.settings import get_settings

    try:
        yield get_settings()
    finally:
        reset_settings()
