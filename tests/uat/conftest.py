"""UAT test fixtures and configuration.

Provides pytest fixtures for AI-driven UAT testing, including
mock and live AI configurations.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any

import pytest
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from jdo.app import JdoApp
from jdo.auth.api import is_authenticated
from jdo.config.settings import get_settings, reset_settings
from jdo.db import create_db_and_tables
from jdo.db.engine import reset_engine
from tests.uat.driver import UAT_SYSTEM_PROMPT, AIUATDriver
from tests.uat.models import UATAction


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "live_ai: marks tests as requiring live AI credentials",
    )


def has_ai_credentials() -> bool:
    """Check if valid AI credentials are available."""
    if os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY"):
        return True
    try:
        settings = get_settings()
        return is_authenticated(settings.ai_provider)
    except (OSError, ValueError, KeyError):
        return False


@pytest.fixture
def scenarios_dir() -> Path:
    """Return the path to the scenarios directory."""
    return Path(__file__).parent / "scenarios"


@pytest.fixture
def uat_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[JdoApp]:
    """Create a JdoApp configured for UAT testing.

    Uses a temporary database and test environment variables.
    """
    reset_engine()

    # Set up test database
    db_path = tmp_path / "uat_test.db"
    monkeypatch.setenv("JDO_DATABASE_PATH", str(db_path))
    monkeypatch.setenv("JDO_AI_PROVIDER", "openai")
    monkeypatch.setenv("JDO_AI_MODEL", "gpt-4o")
    monkeypatch.setenv("JDO_TIMEZONE", "UTC")
    monkeypatch.setenv("JDO_LOG_LEVEL", "INFO")
    # Set a test API key to bypass AI-required screen in mocked tests
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-for-uat")

    reset_settings()
    create_db_and_tables()

    yield JdoApp()

    reset_engine()
    reset_settings()


@pytest.fixture
def live_uat_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[JdoApp]:
    """Create a JdoApp for live AI UAT testing.

    Uses a temporary database but preserves real API credentials.
    Does NOT override ANTHROPIC_API_KEY so stored credentials are used.
    """
    reset_engine()

    # Set up test database
    db_path = tmp_path / "uat_live_test.db"
    monkeypatch.setenv("JDO_DATABASE_PATH", str(db_path))
    monkeypatch.setenv("JDO_AI_PROVIDER", "openai")
    monkeypatch.setenv("JDO_AI_MODEL", "gpt-4o")
    monkeypatch.setenv("JDO_TIMEZONE", "UTC")
    monkeypatch.setenv("JDO_LOG_LEVEL", "INFO")
    # Do NOT set API key - let it use stored credentials

    reset_settings()
    create_db_and_tables()

    yield JdoApp()

    reset_engine()
    reset_settings()


@pytest.fixture
def mock_uat_agent() -> Agent[None, UATAction]:
    """Create a mock UAT agent using TestModel.

    Returns an agent that uses TestModel for deterministic,
    cost-free test execution.
    """
    return Agent(
        TestModel(),
        output_type=UATAction,
        system_prompt=UAT_SYSTEM_PROMPT,
    )


@pytest.fixture
def uat_driver(uat_app: JdoApp, mock_uat_agent: Agent[None, UATAction]) -> AIUATDriver:
    """Create a UAT driver with mock AI agent.

    This driver is suitable for fast, deterministic tests that
    don't require live AI.
    """
    return AIUATDriver(uat_app, mock_uat_agent, debug=True)


@pytest.fixture
def live_uat_agent() -> Agent[None, UATAction]:
    """Create a live UAT agent using real AI.

    Returns an agent configured with the actual AI provider.
    Requires valid credentials.
    """
    settings = get_settings()
    model_id = f"{settings.ai_provider}:{settings.ai_model}"

    return Agent(
        model_id,
        output_type=UATAction,
        system_prompt=UAT_SYSTEM_PROMPT,
    )


@pytest.fixture
def live_uat_driver(uat_app: JdoApp, live_uat_agent: Agent[None, UATAction]) -> AIUATDriver:
    """Create a UAT driver with live AI agent.

    This driver uses real AI for realistic testing.
    Tests using this fixture should be marked with @pytest.mark.live_ai.
    """
    return AIUATDriver(uat_app, live_uat_agent, debug=True)


# Skip marker for tests requiring live AI
skip_without_credentials = pytest.mark.skipif(
    not has_ai_credentials(),
    reason="No AI credentials available - set OPENAI_API_KEY or OPENROUTER_API_KEY",
)
