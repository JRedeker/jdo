"""Chat container widget for scrollable message history.

A VerticalScroll container that holds ChatMessage widgets and auto-scrolls to bottom.
"""

from __future__ import annotations

from textual.containers import VerticalScroll

from jdo.widgets.chat_message import ChatMessage, MessageRole


class ChatContainer(VerticalScroll):
    """Scrollable container for chat messages.

    Features:
    - Auto-scroll to bottom on new messages
    - Keyboard navigation through history
    - Convenience method for adding messages
    """

    DEFAULT_CSS = """
    ChatContainer {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }
    """

    async def add_message(self, role: MessageRole, content: str) -> ChatMessage:
        """Add a new message to the container.

        Args:
            role: The message sender role.
            content: The message content.

        Returns:
            The created ChatMessage widget.
        """
        message = ChatMessage(role=role, content=content)
        await self.mount(message)
        self.scroll_end(animate=False)
        return message

    def on_mount(self) -> None:
        """Initialize container on mount."""
        # Ensure container can receive focus for keyboard nav
        self.can_focus = True
