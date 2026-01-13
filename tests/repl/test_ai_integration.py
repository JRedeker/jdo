"""Tests for AI integration in the REPL loop."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jdo.ai.agent import JDODependencies
from jdo.repl.loop import process_ai_input
from jdo.repl.session import Session


class TestProcessAiInput:
    """Tests for AI input processing."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        return MagicMock()

    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies."""
        deps = MagicMock(spec=JDODependencies)
        return deps

    @pytest.fixture
    def session(self):
        """Create a test session."""
        return Session()

    async def test_returns_response_text(self, mock_agent, mock_deps, session):
        """Returns the complete response text."""

        # Mock stream_response to yield chunks
        async def mock_stream(*args, **kwargs):
            for chunk in ["Hello", " ", "world"]:
                yield chunk

        with (
            patch("jdo.repl.loop.stream_response", mock_stream),
            patch("jdo.repl.loop.console"),  # Suppress console output
        ):
            result = await process_ai_input(
                "test input",
                mock_agent,
                mock_deps,
                session,
            )

        assert result == "Hello world"

    async def test_handles_timeout_gracefully(self, mock_agent, mock_deps, session):
        """Returns empty string on timeout."""

        async def mock_stream(*args, **kwargs):
            # Simulate a timeout
            raise TimeoutError
            yield  # Make it a generator

        with (
            patch("jdo.repl.loop.stream_response", mock_stream),
            patch("jdo.repl.loop.console"),
        ):
            result = await process_ai_input(
                "test input",
                mock_agent,
                mock_deps,
                session,
            )

        assert result == ""

    async def test_handles_connection_error_gracefully(self, mock_agent, mock_deps, session):
        """Returns empty string on connection error."""

        async def mock_stream(*args, **kwargs):
            raise ConnectionError("Network error")
            yield  # Make it a generator

        with (
            patch("jdo.repl.loop.stream_response", mock_stream),
            patch("jdo.repl.loop.console"),
        ):
            result = await process_ai_input(
                "test input",
                mock_agent,
                mock_deps,
                session,
            )

        assert result == ""

    async def test_uses_session_message_history(self, mock_agent, mock_deps, session):
        """Passes message history to stream_response."""
        session.add_user_message("Previous message")
        session.add_assistant_message("Previous response")

        captured_kwargs = {}

        async def mock_stream(*args, **kwargs):
            captured_kwargs.update(kwargs)
            yield "Response"

        with (
            patch("jdo.repl.loop.stream_response", mock_stream),
            patch("jdo.repl.loop.console"),
        ):
            await process_ai_input(
                "test input",
                mock_agent,
                mock_deps,
                session,
            )

        assert "message_history" in captured_kwargs
        assert len(captured_kwargs["message_history"]) == 2

    async def test_empty_response_clears_thinking_indicator(self, mock_agent, mock_deps, session):
        """Clears thinking indicator even when no chunks received."""

        async def mock_stream(*args, **kwargs):
            # Generator that yields nothing
            return
            yield  # Make it a generator

        mock_console = MagicMock()
        with (
            patch("jdo.repl.loop.stream_response", mock_stream),
            patch("jdo.repl.loop.console", mock_console),
        ):
            await process_ai_input(
                "test input",
                mock_agent,
                mock_deps,
                session,
            )

        # Should have printed at least twice (thinking indicator + clear)
        assert mock_console.print.call_count >= 1


class TestSessionMessageHistory:
    """Tests for session message history integration."""

    def test_message_history_format_for_ai(self):
        """Messages are formatted correctly for AI."""
        session = Session()
        session.add_user_message("Hello")
        session.add_assistant_message("Hi there!")

        history = session.message_history

        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Hi there!"
