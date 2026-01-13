"""Tests for AI agent core functionality."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from jdo.ai.agent import (
    JDODependencies,
    create_agent,
    create_agent_with_model,
    get_model_identifier,
)
from jdo.exceptions import InvalidCredentialsError


class TestJDODependencies:
    """Tests for JDODependencies."""

    def test_jdo_dependencies_defaults(self) -> None:
        """JDODependencies has expected defaults."""
        session = MagicMock()
        deps = JDODependencies(session=session)

        assert deps.session is session
        assert deps.timezone == "America/New_York"
        assert deps.available_hours_remaining is None

    def test_jdo_dependencies_with_values(self) -> None:
        """JDODependencies accepts custom values."""
        session = MagicMock()
        deps = JDODependencies(
            session=session,
            timezone="America/New_York",
            available_hours_remaining=4.0,
        )

        assert deps.session is session
        assert deps.timezone == "America/New_York"
        assert deps.available_hours_remaining == 4.0

    def test_set_available_hours(self) -> None:
        """set_available_hours sets the value."""
        deps = JDODependencies(session=MagicMock())
        deps.set_available_hours(5.0)

        assert deps.available_hours_remaining == 5.0

    def test_set_available_hours_negative_raises(self) -> None:
        """set_available_hours raises for negative values."""
        deps = JDODependencies(session=MagicMock())

        with pytest.raises(ValueError, match="Available hours cannot be negative"):
            deps.set_available_hours(-1.0)

    def test_deduct_hours(self) -> None:
        """deduct_hours reduces available hours."""
        deps = JDODependencies(session=MagicMock(), available_hours_remaining=4.0)
        deps.deduct_hours(1.5)

        assert deps.available_hours_remaining == 2.5

    def test_deduct_hours_clips_to_zero(self) -> None:
        """deduct_hours doesn't go below zero."""
        deps = JDODependencies(session=MagicMock(), available_hours_remaining=2.0)
        deps.deduct_hours(5.0)

        assert deps.available_hours_remaining == 0.0

    def test_deduct_hours_with_none(self) -> None:
        """deduct_hours handles None available_hours_remaining."""
        deps = JDODependencies(session=MagicMock(), available_hours_remaining=None)
        deps.deduct_hours(1.0)

        assert deps.available_hours_remaining is None


class TestCreateAgent:
    """Tests for create_agent function."""

    def test_create_agent_returns_agent(self) -> None:
        """create_agent returns an Agent instance."""
        agent = create_agent()

        assert agent is not None
        assert isinstance(agent, Agent)

    def test_create_agent_with_model(self) -> None:
        """create_agent_with_model creates agent with specified model."""
        model = TestModel()
        agent = create_agent_with_model(model)

        assert agent is not None
        assert isinstance(agent, Agent)

    @dataclass
    class MockCredentials:
        """Mock credentials for testing."""

        api_key: str

    def test_create_agent_with_empty_api_key_raises(self) -> None:
        """create_agent raises InvalidCredentialsError for empty api_key."""
        mock_creds = self.MockCredentials(api_key="")
        with (
            patch("jdo.ai.agent.get_settings") as mock_settings,
            patch("jdo.ai.agent.get_credentials") as mock_get_creds,
        ):
            mock_settings.return_value.ai_provider = "openai"
            mock_settings.return_value.ai_model = "gpt-4"
            mock_get_creds.return_value = mock_creds

            with pytest.raises(InvalidCredentialsError, match="Invalid credentials format"):
                create_agent()

    def test_create_agent_with_short_api_key_raises(self) -> None:
        """create_agent raises InvalidCredentialsError for api_key < 10 chars."""
        mock_creds = self.MockCredentials(api_key="short123")
        with (
            patch("jdo.ai.agent.get_settings") as mock_settings,
            patch("jdo.ai.agent.get_credentials") as mock_get_creds,
        ):
            mock_settings.return_value.ai_provider = "openrouter"
            mock_settings.return_value.ai_model = "anthropic/claude-3"
            mock_get_creds.return_value = mock_creds

            with pytest.raises(InvalidCredentialsError, match="Invalid credentials format"):
                create_agent()

    def test_create_agent_with_valid_api_key(self) -> None:
        """create_agent works with valid api_key (>= 10 chars)."""
        mock_creds = self.MockCredentials(api_key="sk-12345678901234567890")
        with (
            patch("jdo.ai.agent.get_settings") as mock_settings,
            patch("jdo.ai.agent.get_credentials") as mock_get_creds,
            patch("jdo.ai.agent.create_agent_with_model") as mock_create_with_model,
        ):
            mock_settings.return_value.ai_provider = "openai"
            mock_settings.return_value.ai_model = "gpt-4"
            mock_get_creds.return_value = mock_creds
            mock_create_with_model.return_value = MagicMock(spec=Agent)

            agent = create_agent()
            assert agent is not None


class TestGetModelIdentifier:
    """Tests for get_model_identifier function."""

    def test_returns_identifier_string(self) -> None:
        """get_model_identifier returns a string identifier."""
        with patch("jdo.ai.agent.get_settings") as mock_settings:
            mock_settings.return_value.ai_model = "gpt-4"
            result = get_model_identifier()

            assert isinstance(result, str)
            assert "gpt-4" in result

    def test_handles_different_models(self) -> None:
        """get_model_identifier handles different model settings."""
        with patch("jdo.ai.agent.get_settings") as mock_settings:
            mock_settings.return_value.ai_model = "claude-3"
            result = get_model_identifier()

            assert "claude-3" in result


class TestAgentToolRegistration:
    """Tests for agent tool registration."""

    def test_agent_deps_type_is_jdodependencies(self) -> None:
        """Agent has correct deps_type."""
        agent = create_agent()

        assert agent.deps_type == JDODependencies

    def test_agent_system_prompt_callable(self) -> None:
        """Agent system_prompt is callable."""
        agent = create_agent()

        assert callable(agent.system_prompt)
