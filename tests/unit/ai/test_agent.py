"""Tests for AI agent configuration."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel


class TestGetModelIdentifier:
    """Tests for get_model_identifier function."""

    def test_returns_anthropic_identifier(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_model_identifier returns anthropic:model format."""
        from jdo.ai.agent import get_model_identifier
        from jdo.config.settings import reset_settings

        reset_settings()
        monkeypatch.setenv("JDO_AI_PROVIDER", "anthropic")
        monkeypatch.setenv("JDO_AI_MODEL", "claude-sonnet-4-20250514")

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            result = get_model_identifier()

        assert result == "anthropic:claude-sonnet-4-20250514"
        reset_settings()

    def test_returns_openai_identifier(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """get_model_identifier returns openai:model format."""
        from jdo.ai.agent import get_model_identifier
        from jdo.config.settings import reset_settings

        reset_settings()
        monkeypatch.setenv("JDO_AI_PROVIDER", "openai")
        monkeypatch.setenv("JDO_AI_MODEL", "gpt-4o")

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            result = get_model_identifier()

        assert result == "openai:gpt-4o"
        reset_settings()


class TestCreateAgent:
    """Tests for create_agent and create_agent_with_model functions."""

    def test_creates_agent_returns_agent_instance(self) -> None:
        """create_agent_with_model returns an Agent instance."""
        from jdo.ai.agent import create_agent_with_model

        agent = create_agent_with_model(TestModel())

        assert isinstance(agent, Agent)

    def test_agent_has_system_prompt(self) -> None:
        """Agent has system prompt for commitment tracking."""
        from jdo.ai.agent import SYSTEM_PROMPT, create_agent_with_model

        agent = create_agent_with_model(TestModel())

        # Verify system prompt is set (accessing internal _system_prompts)
        assert agent._system_prompts is not None
        assert len(agent._system_prompts) > 0
        # The first system prompt should be our SYSTEM_PROMPT
        assert SYSTEM_PROMPT in agent._system_prompts

    async def test_agent_can_run_with_test_model(self) -> None:
        """Agent can be run with TestModel for testing."""
        from jdo.ai.agent import JDODependencies, create_agent_with_model

        mock_session = MagicMock()
        deps = JDODependencies(session=mock_session)
        # Disable tools to avoid tool calls against mock session
        agent = create_agent_with_model(TestModel(), with_tools=False)

        result = await agent.run("Test prompt", deps=deps)

        assert result.output == "success (no tool calls)"

    def test_agent_has_tools_registered_by_default(self) -> None:
        """create_agent_with_model registers tools by default."""
        from jdo.ai.agent import create_agent_with_model

        agent = create_agent_with_model(TestModel())

        # Check that tools are registered via the function toolset
        toolset = agent._function_toolset
        tool_names = list(toolset.tools)
        assert "query_current_commitments" in tool_names
        assert "query_overdue_commitments" in tool_names
        assert "query_visions_due_for_review" in tool_names

    def test_agent_without_tools_option(self) -> None:
        """create_agent_with_model can skip tool registration."""
        from jdo.ai.agent import create_agent_with_model

        agent = create_agent_with_model(TestModel(), with_tools=False)

        # Check that no tools are registered
        toolset = agent._function_toolset
        assert len(list(toolset.tools)) == 0


class TestJDODependencies:
    """Tests for JDODependencies dataclass."""

    def test_dependencies_include_session(self) -> None:
        """JDODependencies includes session."""
        from jdo.ai.agent import JDODependencies

        mock_session = MagicMock()
        deps = JDODependencies(session=mock_session)

        assert deps.session is mock_session

    def test_dependencies_include_timezone(self) -> None:
        """JDODependencies includes timezone."""
        from jdo.ai.agent import JDODependencies

        mock_session = MagicMock()
        deps = JDODependencies(session=mock_session, timezone="Europe/London")

        assert deps.timezone == "Europe/London"

    def test_timezone_default_value(self) -> None:
        """JDODependencies timezone defaults to America/New_York."""
        from jdo.ai.agent import JDODependencies

        mock_session = MagicMock()
        deps = JDODependencies(session=mock_session)

        assert deps.timezone == "America/New_York"

    def test_available_hours_remaining_defaults_to_none(self) -> None:
        """JDODependencies available_hours_remaining defaults to None."""
        from jdo.ai.agent import JDODependencies

        mock_session = MagicMock()
        deps = JDODependencies(session=mock_session)

        assert deps.available_hours_remaining is None

    def test_set_available_hours(self) -> None:
        """set_available_hours sets available_hours_remaining."""
        from jdo.ai.agent import JDODependencies

        mock_session = MagicMock()
        deps = JDODependencies(session=mock_session)

        deps.set_available_hours(4.5)

        assert deps.available_hours_remaining == 4.5

    def test_set_available_hours_zero(self) -> None:
        """set_available_hours accepts zero."""
        from jdo.ai.agent import JDODependencies

        mock_session = MagicMock()
        deps = JDODependencies(session=mock_session, available_hours_remaining=3.0)

        deps.set_available_hours(0.0)

        assert deps.available_hours_remaining == 0.0

    def test_set_available_hours_negative_raises(self) -> None:
        """set_available_hours raises ValueError for negative hours."""
        from jdo.ai.agent import JDODependencies

        mock_session = MagicMock()
        deps = JDODependencies(session=mock_session)

        with pytest.raises(ValueError, match="cannot be negative"):
            deps.set_available_hours(-1.0)

    def test_deduct_hours_subtracts_from_available(self) -> None:
        """deduct_hours subtracts from available_hours_remaining."""
        from jdo.ai.agent import JDODependencies

        mock_session = MagicMock()
        deps = JDODependencies(session=mock_session, available_hours_remaining=5.0)

        deps.deduct_hours(1.5)

        assert deps.available_hours_remaining == 3.5

    def test_deduct_hours_does_nothing_when_none(self) -> None:
        """deduct_hours does nothing when available_hours_remaining is None."""
        from jdo.ai.agent import JDODependencies

        mock_session = MagicMock()
        deps = JDODependencies(session=mock_session)

        deps.deduct_hours(1.0)

        assert deps.available_hours_remaining is None

    def test_deduct_hours_floors_at_zero(self) -> None:
        """deduct_hours floors at zero, does not go negative."""
        from jdo.ai.agent import JDODependencies

        mock_session = MagicMock()
        deps = JDODependencies(session=mock_session, available_hours_remaining=1.0)

        deps.deduct_hours(2.5)

        assert deps.available_hours_remaining == 0.0

    def test_deduct_hours_ignores_negative_deduction(self) -> None:
        """deduct_hours ignores negative or zero deduction values."""
        from jdo.ai.agent import JDODependencies

        mock_session = MagicMock()
        deps = JDODependencies(session=mock_session, available_hours_remaining=5.0)

        deps.deduct_hours(0.0)
        assert deps.available_hours_remaining == 5.0

        deps.deduct_hours(-1.0)
        assert deps.available_hours_remaining == 5.0
