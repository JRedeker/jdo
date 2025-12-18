"""Prompt input widget for chat interface.

A multi-line text input that supports Enter for newline and Ctrl+Enter for submit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from textual.binding import Binding
from textual.message import Message
from textual.widgets import TextArea


class PromptInput(TextArea):
    """Multi-line prompt input for chat messages.

    Features:
    - Enter key inserts newline (not submit)
    - Ctrl+Enter or Ctrl+J submits message
    - Detects commands starting with '/'
    - Prevents empty submissions
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("ctrl+enter", "submit", "Send", show=True),
        Binding("ctrl+j", "submit", "Send", show=False),  # Alternative for terminals
    ]

    @dataclass
    class Submitted(Message):
        """Posted when user submits a message.

        Attributes:
            text: The submitted message text.
        """

        text: str

    def __init__(
        self,
        text: str = "",
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Initialize the prompt input.

        Args:
            text: Initial text content.
            name: Widget name.
            id: Widget ID.
            classes: CSS classes.
            disabled: Whether the widget is disabled.
        """
        super().__init__(
            text,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            language=None,  # Plain text, no syntax highlighting
            show_line_numbers=False,
        )

    def action_submit(self) -> None:
        """Submit the current message."""
        text = self.text.strip()
        if not text:
            return  # Prevent empty submissions

        self.post_message(self.Submitted(text=text))
        self.clear()

    def is_command(self) -> bool:
        """Check if the current text is a command.

        Returns:
            True if text starts with '/', False otherwise.
        """
        return self.text.strip().startswith("/")
