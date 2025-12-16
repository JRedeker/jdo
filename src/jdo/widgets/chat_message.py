"""Chat message widget for displaying conversation messages.

Displays messages with role labels (USER, ASSISTANT, SYSTEM) and timestamps.
"""

from datetime import UTC, datetime
from enum import Enum

from rich.text import Text
from textual.widgets import Static


class MessageRole(str, Enum):
    """Role of the message sender."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# Role label styles
_ROLE_STYLES = {
    MessageRole.USER: "bold cyan",
    MessageRole.ASSISTANT: "bold green",
    MessageRole.SYSTEM: "bold yellow on red",
}


class ChatMessage(Static):
    """A single chat message with role label and timestamp.

    Displays messages in the format:
    ```
    USER                           12:34 PM
    Message content here...
    ```
    """

    DEFAULT_CSS = """
    ChatMessage {
        padding: 1 2;
        margin-bottom: 1;
    }

    ChatMessage.-user {
        background: $surface;
    }

    ChatMessage.-assistant {
        background: $surface-darken-1;
    }

    ChatMessage.-system {
        background: $error 20%;
        border: solid $error;
    }
    """

    def __init__(
        self,
        role: MessageRole,
        content: str,
        *,
        timestamp: datetime | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize a chat message.

        Args:
            role: The role of the message sender.
            content: The message content.
            timestamp: Message timestamp (defaults to now).
            name: Widget name.
            id: Widget ID.
            classes: CSS classes.
        """
        super().__init__(name=name, id=id, classes=classes)
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now(UTC)
        # Add role-based CSS class
        self.add_class(f"-{role.value}")

    def render(self) -> Text:
        """Render the message with role label and timestamp.

        Returns:
            Rich Text object with formatted message.
        """
        text = Text()

        # Role label
        role_label = self.role.value.upper()
        role_style = _ROLE_STYLES.get(self.role, "bold")
        text.append(role_label, style=role_style)

        # Timestamp (right-aligned via padding)
        time_str = self.timestamp.strftime("%I:%M %p")
        # Calculate padding for right alignment (assuming 60 char width)
        padding = " " * max(1, 60 - len(role_label) - len(time_str))
        text.append(padding)
        text.append(time_str, style="dim")
        text.append("\n")

        # Message content
        text.append(self.content)

        return text

    def update_content(self, content: str) -> None:
        """Update the message content (for streaming responses).

        Args:
            content: New content to display.
        """
        self.content = content
        self.refresh()

    @property
    def recoverable(self) -> bool:
        """Check if this is a recoverable error message.

        Returns:
            True if recoverable, False otherwise.
        """
        return getattr(self, "_recoverable", True)

    @recoverable.setter
    def recoverable(self, value: bool) -> None:
        """Set whether this error is recoverable."""
        self._recoverable = value


def create_error_message(
    error_text: str,
    *,
    recoverable: bool = True,
) -> ChatMessage:
    """Create an error message for display in chat.

    Args:
        error_text: The error description.
        recoverable: Whether the error is recoverable (default True).

    Returns:
        ChatMessage configured as a system error message.
    """
    msg = ChatMessage(
        role=MessageRole.SYSTEM,
        content=f"Error: {error_text}",
    )
    msg.recoverable = recoverable
    return msg


def create_connection_error_message() -> ChatMessage:
    """Create a connection error message.

    Returns:
        ChatMessage configured as a connection error.
    """
    return ChatMessage(
        role=MessageRole.SYSTEM,
        content=(
            "Connection error: Unable to reach the AI service. "
            "Please check your connection and retry."
        ),
    )
