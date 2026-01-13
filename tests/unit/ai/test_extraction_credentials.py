"""Tests for extraction agent credential handling.

Regression tests to ensure extraction agents work with real AI providers.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.openrouter import OpenRouterModel

from jdo.ai.extraction import (
    COMMITMENT_EXTRACTION_PROMPT,
    GOAL_EXTRACTION_PROMPT,
    ExtractedCommitment,
    ExtractedGoal,
    create_extraction_agent,
)


class TestExtractionAgentCredentials:
    """Tests for extraction agent credential handling."""

    def test_create_extraction_agent_with_model_object(self) -> None:
        """Extraction agent works when passed a Model object."""
        # Create a mock model object
        mock_model = MagicMock(spec=OpenRouterModel)

        agent = create_extraction_agent(
            mock_model, ExtractedCommitment, COMMITMENT_EXTRACTION_PROMPT
        )

        assert agent is not None
        # Agent should use the model we passed
        assert agent.model is mock_model

    def test_create_extraction_agent_with_string_uses_credentials(self) -> None:
        """Extraction agent with string model identifier uses credentials from settings.

        When a string model identifier is passed (not "test"), the function should
        automatically load credentials and create a proper model.
        """
        # Mock credentials and settings
        mock_creds = MagicMock()
        mock_creds.api_key = "test-api-key-12345"

        mock_settings = MagicMock()
        mock_settings.ai_provider = "openrouter"
        mock_settings.ai_model = "anthropic/claude-3.5-sonnet"

        with (
            patch("jdo.ai.extraction.get_credentials", return_value=mock_creds) as mock_get_creds,
            patch("jdo.ai.extraction.get_settings", return_value=mock_settings),
        ):
            agent = create_extraction_agent(
                "openrouter:anthropic/claude-3.5-sonnet",
                ExtractedCommitment,
                COMMITMENT_EXTRACTION_PROMPT,
            )

            # Verify credentials were loaded
            mock_get_creds.assert_called_once_with("openrouter")

            # Agent should be created successfully
            assert agent is not None
            # Model should be OpenRouterModel (not the original string)
            assert isinstance(agent.model, OpenRouterModel)

    def test_create_extraction_agent_with_test_model_works(self) -> None:
        """Extraction agent works with 'test' model (no credentials needed)."""
        agent = create_extraction_agent("test", ExtractedCommitment, COMMITMENT_EXTRACTION_PROMPT)

        assert agent is not None

    def test_create_goal_extraction_agent_with_model_object(self) -> None:
        """Goal extraction agent works when passed a Model object."""
        mock_model = MagicMock(spec=OpenAIChatModel)

        agent = create_extraction_agent(mock_model, ExtractedGoal, GOAL_EXTRACTION_PROMPT)

        assert agent is not None
        assert agent.model is mock_model
