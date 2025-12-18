"""Tests for AI context management - message formatting and streaming.

Phase 10.1/10.2: AI Context for the conversational TUI.
"""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestMessageFormatting:
    """Tests for conversation message formatting for AI API."""

    def test_format_user_message(self) -> None:
        """User message formats with 'user' role."""
        from jdo.ai.context import format_message

        msg = {"role": "user", "content": "Hello, AI!"}
        result = format_message(msg)

        assert result["role"] == "user"
        assert result["content"] == "Hello, AI!"

    def test_format_assistant_message(self) -> None:
        """Assistant message formats with 'assistant' role."""
        from jdo.ai.context import format_message

        msg = {"role": "assistant", "content": "Hello, human!"}
        result = format_message(msg)

        assert result["role"] == "assistant"
        assert result["content"] == "Hello, human!"

    def test_format_system_message(self) -> None:
        """System message formats with 'system' role."""
        from jdo.ai.context import format_message

        msg = {"role": "system", "content": "You are a helpful assistant."}
        result = format_message(msg)

        assert result["role"] == "system"
        assert result["content"] == "You are a helpful assistant."

    def test_format_conversation_history(self) -> None:
        """Conversation history formats as list of messages."""
        from jdo.ai.context import format_conversation

        messages = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "How are you?"},
        ]

        result = format_conversation(messages)

        assert len(result) == 3
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"
        assert result[2]["role"] == "user"


class TestSystemPrompt:
    """Tests for JDO system prompt."""

    def test_system_prompt_includes_jdo_context(self) -> None:
        """System prompt includes JDO-specific instructions."""
        from jdo.ai.context import get_system_prompt

        prompt = get_system_prompt()

        assert "commitment" in prompt.lower()
        assert "JDO" in prompt or "jdo" in prompt.lower()

    def test_system_prompt_includes_command_instructions(self) -> None:
        """System prompt explains slash commands."""
        from jdo.ai.context import get_system_prompt

        prompt = get_system_prompt()

        assert "/commit" in prompt or "commit" in prompt.lower()

    def test_system_prompt_includes_extraction_guidance(self) -> None:
        """System prompt guides AI on field extraction."""
        from jdo.ai.context import get_system_prompt

        prompt = get_system_prompt()

        # Should mention deliverable, stakeholder, due date
        assert "deliverable" in prompt.lower() or "what" in prompt.lower()


class TestStreamingSupport:
    """Tests for streaming response support."""

    async def test_stream_response_yields_chunks(self) -> None:
        """stream_response yields text chunks as they arrive."""
        from jdo.ai.context import stream_response

        # Mock the agent's run_stream - stream_text returns an async iterator directly
        mock_result = MagicMock()
        mock_result.stream_text = MagicMock(return_value=async_iter(["Hello", " ", "world", "!"]))

        mock_agent = MagicMock()
        mock_agent.run_stream = MagicMock(return_value=async_context_manager(mock_result))

        chunks = []
        async for chunk in stream_response(mock_agent, "Test prompt", MagicMock()):
            chunks.append(chunk)

        assert len(chunks) == 4
        assert "".join(chunks) == "Hello world!"

    async def test_stream_response_passes_message_history(self) -> None:
        """stream_response converts and passes message history to agent."""
        from pydantic_ai.messages import ModelRequest, ModelResponse

        from jdo.ai.context import stream_response

        mock_result = MagicMock()
        mock_result.stream_text = MagicMock(return_value=async_iter(["Response"]))

        mock_agent = MagicMock()
        mock_agent.run_stream = MagicMock(return_value=async_context_manager(mock_result))

        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"},
        ]

        # Consume the stream
        chunks = []
        async for chunk in stream_response(mock_agent, "New prompt", MagicMock(), history):
            chunks.append(chunk)

        # Verify run_stream was called with converted history
        mock_agent.run_stream.assert_called_once()
        call_kwargs = mock_agent.run_stream.call_args.kwargs
        assert "message_history" in call_kwargs
        model_history = call_kwargs["message_history"]
        assert len(model_history) == 2
        assert isinstance(model_history[0], ModelRequest)
        assert isinstance(model_history[1], ModelResponse)

    async def test_stream_response_handles_empty_response(self) -> None:
        """stream_response handles empty AI response gracefully."""
        from jdo.ai.context import stream_response

        mock_result = MagicMock()
        mock_result.stream_text = MagicMock(return_value=async_iter([]))

        mock_agent = MagicMock()
        mock_agent.run_stream = MagicMock(return_value=async_context_manager(mock_result))

        chunks = []
        async for chunk in stream_response(mock_agent, "Test prompt", MagicMock()):
            chunks.append(chunk)

        assert len(chunks) == 0


class TestConversationContext:
    """Tests for building conversation context for AI."""

    def test_build_context_includes_recent_messages(self) -> None:
        """build_context includes recent conversation messages."""
        from jdo.ai.context import build_context

        messages = [
            {"role": "user", "content": "I need to send a report"},
            {"role": "assistant", "content": "I can help with that"},
        ]

        context = build_context(messages)

        assert len(context) >= 2
        # Should include the messages
        user_msgs = [m for m in context if m["role"] == "user"]
        assert any("report" in m["content"] for m in user_msgs)

    def test_build_context_truncates_long_history(self) -> None:
        """build_context truncates very long conversation history."""
        from jdo.ai.context import MAX_CONTEXT_MESSAGES, build_context

        # Create more messages than the limit
        messages = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
            for i in range(MAX_CONTEXT_MESSAGES + 10)
        ]

        context = build_context(messages)

        # Should not exceed max (excluding system prompt)
        non_system = [m for m in context if m["role"] != "system"]
        assert len(non_system) <= MAX_CONTEXT_MESSAGES


class TestMessageHistoryConversion:
    """Tests for converting message history to PydanticAI format."""

    def test_convert_user_message(self) -> None:
        """User message converts to ModelRequest."""
        from pydantic_ai.messages import ModelRequest, UserPromptPart

        from jdo.ai.context import _convert_to_model_messages

        messages = [{"role": "user", "content": "Hello AI"}]
        result = _convert_to_model_messages(messages)

        assert len(result) == 1
        assert isinstance(result[0], ModelRequest)
        assert len(result[0].parts) == 1
        assert isinstance(result[0].parts[0], UserPromptPart)
        assert result[0].parts[0].content == "Hello AI"

    def test_convert_assistant_message(self) -> None:
        """Assistant message converts to ModelResponse."""
        from pydantic_ai.messages import ModelResponse, TextPart

        from jdo.ai.context import _convert_to_model_messages

        messages = [{"role": "assistant", "content": "Hi there!"}]
        result = _convert_to_model_messages(messages)

        assert len(result) == 1
        assert isinstance(result[0], ModelResponse)
        assert len(result[0].parts) == 1
        assert isinstance(result[0].parts[0], TextPart)
        assert result[0].parts[0].content == "Hi there!"

    def test_convert_conversation_preserves_order(self) -> None:
        """Conversation history maintains message order."""
        from pydantic_ai.messages import ModelRequest, ModelResponse

        from jdo.ai.context import _convert_to_model_messages

        messages = [
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Second"},
            {"role": "user", "content": "Third"},
        ]
        result = _convert_to_model_messages(messages)

        assert len(result) == 3
        assert isinstance(result[0], ModelRequest)
        assert isinstance(result[1], ModelResponse)
        assert isinstance(result[2], ModelRequest)

    def test_system_messages_are_skipped(self) -> None:
        """System messages are skipped (handled via system_prompt)."""
        from jdo.ai.context import _convert_to_model_messages

        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]
        result = _convert_to_model_messages(messages)

        # Only the user message should be converted
        assert len(result) == 1

    def test_empty_history_returns_empty_list(self) -> None:
        """Empty message list returns empty result."""
        from jdo.ai.context import _convert_to_model_messages

        result = _convert_to_model_messages([])
        assert result == []


# Helper functions for async testing
async def async_iter(items: list[Any]):
    """Create an async iterator from a list."""
    for item in items:
        yield item


def async_context_manager(result: Any):
    """Create an async context manager that returns result."""

    class AsyncCM:
        async def __aenter__(self):
            return result

        async def __aexit__(self, *args):
            pass

    return AsyncCM()
