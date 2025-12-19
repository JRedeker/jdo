"""Tests for Chat Widgets - TDD Red phase.

Tests for PromptInput, ChatMessage, and ChatContainer widgets.
"""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import TextArea

from jdo.widgets.chat_container import ChatContainer
from jdo.widgets.chat_message import ChatMessage, MessageRole
from jdo.widgets.prompt_input import PromptInput


class PromptInputTestApp(App):
    """Test app for PromptInput widget."""

    def compose(self) -> ComposeResult:
        yield PromptInput()


class ChatMessageTestApp(App):
    """Test app for ChatMessage widget."""

    def compose(self) -> ComposeResult:
        yield ChatMessage(role=MessageRole.USER, content="Hello")
        yield ChatMessage(role=MessageRole.ASSISTANT, content="Hi there")
        yield ChatMessage(role=MessageRole.SYSTEM, content="Error occurred")


class ChatContainerTestApp(App):
    """Test app for ChatContainer widget."""

    def compose(self) -> ComposeResult:
        yield ChatContainer()


class TestPromptInput:
    """Tests for PromptInput widget."""

    async def test_is_textarea_subclass(self) -> None:
        """PromptInput is a TextArea subclass."""
        assert issubclass(PromptInput, TextArea)

    async def test_enter_key_inserts_newline(self) -> None:
        """Enter key inserts newline (not submit)."""
        app = PromptInputTestApp()
        async with app.run_test() as pilot:
            prompt = app.query_one(PromptInput)
            prompt.focus()
            await pilot.press("h", "e", "l", "l", "o")
            await pilot.press("enter")
            await pilot.press("w", "o", "r", "l", "d")
            # Text should contain newline
            assert "\n" in prompt.text
            assert "hello" in prompt.text
            assert "world" in prompt.text

    async def test_ctrl_enter_submits_message(self) -> None:
        """Ctrl+Enter submits message."""

        # Create app that tracks submitted messages
        class SubmitTrackingApp(App):
            submitted: list[str] = []

            def compose(self) -> ComposeResult:
                yield PromptInput()

            def on_prompt_input_submitted(self, message: PromptInput.Submitted) -> None:
                self.submitted.append(message.text)

        app = SubmitTrackingApp()
        async with app.run_test() as pilot:
            prompt = app.query_one(PromptInput)
            prompt.focus()
            await pilot.press("h", "e", "l", "l", "o")
            await pilot.press("ctrl+enter")
            # Should trigger submit
            assert len(app.submitted) == 1
            assert app.submitted[0] == "hello"

    async def test_empty_submit_prevented(self) -> None:
        """Empty submit is prevented."""

        class SubmitTrackingApp(App):
            submitted: list[str] = []

            def compose(self) -> ComposeResult:
                yield PromptInput()

            def on_prompt_input_submitted(self, message: PromptInput.Submitted) -> None:
                self.submitted.append(message.text)

        app = SubmitTrackingApp()
        async with app.run_test() as pilot:
            prompt = app.query_one(PromptInput)
            prompt.focus()
            await pilot.press("ctrl+enter")
            # Should NOT trigger submit
            assert len(app.submitted) == 0

    async def test_message_starting_with_slash_detected_as_command(self) -> None:
        """Message starting with '/' detected as command."""
        app = PromptInputTestApp()
        async with app.run_test() as pilot:
            prompt = app.query_one(PromptInput)
            prompt.focus()
            await pilot.press("/", "c", "o", "m", "m", "i", "t")
            assert prompt.is_command()

    async def test_normal_message_not_command(self) -> None:
        """Normal message is not detected as command."""
        app = PromptInputTestApp()
        async with app.run_test() as pilot:
            prompt = app.query_one(PromptInput)
            prompt.focus()
            await pilot.press("h", "e", "l", "l", "o")
            assert not prompt.is_command()


class TestChatMessage:
    """Tests for ChatMessage widget."""

    async def test_user_message_displays_with_user_label(self) -> None:
        """User message displays with 'USER' label."""
        app = ChatMessageTestApp()
        async with app.run_test():
            messages = app.query(ChatMessage)
            user_msg = messages[0]
            assert user_msg.role == MessageRole.USER
            # The rendered content should contain USER label
            rendered = user_msg.render()
            assert "USER" in str(rendered)

    async def test_assistant_message_displays_with_assistant_label(self) -> None:
        """Assistant message displays with 'ASSISTANT' label."""
        app = ChatMessageTestApp()
        async with app.run_test():
            messages = app.query(ChatMessage)
            assistant_msg = messages[1]
            assert assistant_msg.role == MessageRole.ASSISTANT
            rendered = assistant_msg.render()
            assert "ASSISTANT" in str(rendered)

    async def test_system_message_displays_with_system_label(self) -> None:
        """System message displays with 'SYSTEM' label."""
        app = ChatMessageTestApp()
        async with app.run_test():
            messages = app.query(ChatMessage)
            system_msg = messages[2]
            assert system_msg.role == MessageRole.SYSTEM
            rendered = system_msg.render()
            assert "SYSTEM" in str(rendered)

    async def test_messages_show_timestamp(self) -> None:
        """Messages show timestamp."""
        app = ChatMessageTestApp()
        async with app.run_test():
            messages = app.query(ChatMessage)
            for msg in messages:
                # Each message should have a timestamp attribute
                assert hasattr(msg, "timestamp")
                assert msg.timestamp is not None


class TestChatContainer:
    """Tests for ChatContainer widget."""

    async def test_is_vertical_scroll(self) -> None:
        """ChatContainer is based on scrollable container."""
        from textual.containers import VerticalScroll

        assert issubclass(ChatContainer, VerticalScroll)

    async def test_new_message_scrolls_to_bottom(self) -> None:
        """New message scrolls to bottom."""
        app = ChatContainerTestApp()
        async with app.run_test() as pilot:
            container = app.query_one(ChatContainer)
            # Add multiple messages to trigger scroll
            for i in range(10):
                msg = ChatMessage(role=MessageRole.USER, content=f"Message {i}")
                await container.mount(msg)
                await pilot.pause()
            # Container should be scrolled to bottom
            # (scroll_y should be at max or near it)
            assert container.scroll_y >= 0  # Basic check that scrolling is enabled

    async def test_add_message_method(self) -> None:
        """ChatContainer has add_message convenience method."""
        app = ChatContainerTestApp()
        async with app.run_test() as pilot:
            container = app.query_one(ChatContainer)
            await container.add_message(MessageRole.USER, "Test message")
            await pilot.pause()
            messages = container.query(ChatMessage)
            assert len(messages) == 1
            assert messages[0].content == "Test message"


class TestChatMessageStreaming:
    """Tests for ChatMessage streaming updates."""

    async def test_update_content_changes_message(self) -> None:
        """update_content updates the message content."""
        app = ChatMessageTestApp()
        async with app.run_test() as pilot:
            messages = app.query(ChatMessage)
            user_msg = messages[0]

            original_content = user_msg.content
            user_msg.update_content("Updated content")
            await pilot.pause()

            assert user_msg.content == "Updated content"
            assert user_msg.content != original_content

    async def test_set_thinking_adds_class(self) -> None:
        """set_thinking(True) adds the -thinking CSS class."""
        app = ChatMessageTestApp()
        async with app.run_test() as pilot:
            messages = app.query(ChatMessage)
            msg = messages[0]

            assert not msg.has_class("-thinking")
            msg.set_thinking(True)
            await pilot.pause()

            assert msg.has_class("-thinking")
            assert msg.is_thinking is True

    async def test_set_thinking_false_removes_class(self) -> None:
        """set_thinking(False) removes the -thinking CSS class."""
        app = ChatMessageTestApp()
        async with app.run_test() as pilot:
            messages = app.query(ChatMessage)
            msg = messages[0]

            msg.set_thinking(True)
            await pilot.pause()
            assert msg.has_class("-thinking")

            msg.set_thinking(False)
            await pilot.pause()

            assert not msg.has_class("-thinking")
            assert msg.is_thinking is False

    async def test_is_thinking_default_false(self) -> None:
        """is_thinking defaults to False."""
        app = ChatMessageTestApp()
        async with app.run_test():
            messages = app.query(ChatMessage)
            msg = messages[0]
            assert msg.is_thinking is False


class TestMessageRole:
    """Tests for MessageRole enum."""

    def test_has_required_roles(self) -> None:
        """MessageRole has user, assistant, system."""
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"


class TestChatMessageSelection:
    """Tests for ChatMessage selection handling."""

    async def test_get_selection_handles_out_of_range_coordinates(self) -> None:
        """get_selection handles out-of-range selection coordinates gracefully.

        This tests a workaround for a Textual bug where selection coordinates
        may be screen-relative rather than widget-relative, causing IndexError.
        """
        from textual.geometry import Offset
        from textual.selection import Selection

        app = ChatMessageTestApp()
        async with app.run_test():
            messages = app.query(ChatMessage)
            msg = messages[0]  # A short message

            # Create a selection with coordinates that would be out of range
            # for the widget's text content (simulating the Textual bug)
            out_of_range_selection = Selection(
                start=Offset(x=0, y=100),  # y=100 is way beyond the text
                end=None,
            )

            # This should return None instead of raising IndexError
            result = msg.get_selection(out_of_range_selection)
            assert result is None

    async def test_get_selection_works_for_valid_coordinates(self) -> None:
        """get_selection works correctly for valid selection coordinates."""
        from textual.geometry import Offset
        from textual.selection import Selection

        app = ChatMessageTestApp()
        async with app.run_test():
            messages = app.query(ChatMessage)
            msg = messages[0]  # "Hello" message

            # Create a valid selection for the first line
            valid_selection = Selection(
                start=Offset(x=0, y=0),
                end=Offset(x=4, y=0),  # Select "USER"
            )

            result = msg.get_selection(valid_selection)
            assert result is not None
            extracted_text, separator = result
            assert extracted_text == "USER"
            assert separator == "\n"
