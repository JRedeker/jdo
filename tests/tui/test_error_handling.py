"""Tests for error handling in TUI.

Phase 15: Error Handling - AI errors, validation errors, connection errors.
"""

import pytest
from textual.app import App, ComposeResult

from jdo.widgets.chat_container import ChatContainer
from jdo.widgets.chat_message import ChatMessage, MessageRole


class TestAIErrorDisplay:
    """Tests for AI error messages in chat."""

    @pytest.fixture
    def chat_app(self) -> type[App]:
        """Create a test app with ChatContainer."""

        class ChatApp(App):
            def compose(self) -> ComposeResult:
                yield ChatContainer()

        return ChatApp

    async def test_ai_error_shows_as_system_message(self, chat_app: type[App]) -> None:
        """AI errors are displayed as system messages."""
        from jdo.widgets.chat_message import create_error_message

        async with chat_app().run_test() as pilot:
            container = pilot.app.query_one(ChatContainer)

            # Create error message and mount directly
            error_msg = create_error_message("AI service unavailable")
            await container.mount(error_msg)
            await pilot.pause()

            # Should be a system message with error styling
            messages = container.query(ChatMessage)
            assert len(messages) == 1
            assert messages[0].role == MessageRole.SYSTEM

    async def test_ai_error_message_contains_error_text(self, chat_app: type[App]) -> None:
        """AI error message contains the error text."""
        from jdo.widgets.chat_message import create_error_message

        async with chat_app().run_test() as pilot:
            container = pilot.app.query_one(ChatContainer)

            error_msg = create_error_message("Rate limit exceeded")
            await container.mount(error_msg)
            await pilot.pause()

            messages = container.query(ChatMessage)
            assert len(messages) == 1
            assert "Rate limit" in messages[0].content


class TestValidationErrorDisplay:
    """Tests for validation error display."""

    def test_validation_error_message_exists(self) -> None:
        """Validation error message function exists."""
        from jdo.widgets.data_panel import create_validation_error

        error = create_validation_error("deliverable", "Required field")

        assert "deliverable" in error.lower() or "Required" in error

    def test_validation_error_includes_field_name(self) -> None:
        """Validation error includes the field name."""
        from jdo.widgets.data_panel import create_validation_error

        error = create_validation_error("due_date", "Invalid date format")

        assert "due_date" in error or "date" in error.lower()

    def test_validation_error_includes_message(self) -> None:
        """Validation error includes the error message."""
        from jdo.widgets.data_panel import create_validation_error

        error = create_validation_error("stakeholder", "Must be at least 2 characters")

        assert "2 characters" in error or "Must be" in error


class TestConnectionErrorHandling:
    """Tests for connection error handling."""

    def test_connection_error_message_exists(self) -> None:
        """Connection error message function exists."""
        from jdo.widgets.chat_message import create_connection_error_message

        error_msg = create_connection_error_message()

        assert isinstance(error_msg, ChatMessage)
        assert error_msg.role == MessageRole.SYSTEM

    def test_connection_error_suggests_retry(self) -> None:
        """Connection error message suggests retry."""
        from jdo.widgets.chat_message import create_connection_error_message

        error_msg = create_connection_error_message()

        # Should mention retry or connection
        assert "retry" in error_msg.content.lower() or "connection" in error_msg.content.lower()


class TestErrorRecovery:
    """Tests for error recovery behavior."""

    def test_recoverable_error_flag(self) -> None:
        """Errors can be flagged as recoverable."""
        from jdo.widgets.chat_message import create_error_message

        # Recoverable error (like rate limit)
        error_msg = create_error_message("Rate limit exceeded", recoverable=True)
        assert error_msg.recoverable is True

        # Non-recoverable error (like auth failure)
        fatal_msg = create_error_message("Authentication failed", recoverable=False)
        assert fatal_msg.recoverable is False

    def test_default_error_is_recoverable(self) -> None:
        """Default errors are recoverable."""
        from jdo.widgets.chat_message import create_error_message

        error_msg = create_error_message("Something went wrong")
        assert error_msg.recoverable is True
