"""E2E test fixtures for JDO application."""

from collections.abc import Generator
from pathlib import Path

import pytest

from jdo.config.settings import reset_settings
from jdo.db.engine import get_engine, reset_engine
from jdo.db.migrations import create_db_and_tables


@pytest.fixture
def test_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Create a clean test database for e2e tests.

    Configures a temporary database, creates tables, and ensures cleanup.
    """
    # Configure test database
    db_path = tmp_path / "test_e2e.db"
    monkeypatch.setenv("JDO_DATABASE_PATH", str(db_path))
    monkeypatch.setenv("JDO_AI_PROVIDER", "anthropic")
    monkeypatch.setenv("JDO_AI_MODEL", "claude-sonnet-4-20250514")
    monkeypatch.setenv("JDO_TIMEZONE", "UTC")
    monkeypatch.setenv("JDO_LOG_LEVEL", "ERROR")  # Reduce noise in e2e tests
    reset_settings()
    reset_engine()

    # Create tables
    create_db_and_tables()

    yield

    # Cleanup
    reset_engine()
    reset_settings()
