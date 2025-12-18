"""Draft restore modal screen.

A modal dialog that appears on startup when pending drafts exist,
allowing the user to restore or discard them.
"""

from __future__ import annotations

from typing import ClassVar
from uuid import UUID

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Static

from jdo.models.draft import Draft

# Maximum length for preview text in draft restoration dialog
_PREVIEW_MAX_LENGTH = 50


class DraftRestoreScreen(ModalScreen[str]):
    """Modal screen for draft restoration on startup.

    Displays information about the pending draft and offers
    options to restore it (continue editing) or discard it.

    The screen dismisses with either "restore" or "discard"
    depending on user choice.
    """

    DEFAULT_CSS = """
    DraftRestoreScreen {
        align: center middle;
        background: $primary 30%;
    }

    DraftRestoreScreen #dialog {
        width: 60;
        height: auto;
        border: solid $primary;
        background: $surface;
        padding: 2;
    }

    DraftRestoreScreen .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    DraftRestoreScreen .draft-info {
        margin-bottom: 1;
    }

    DraftRestoreScreen .field-label {
        color: $text-muted;
    }

    DraftRestoreScreen .field-value {
        margin-left: 2;
    }

    DraftRestoreScreen #buttons {
        height: auto;
        margin-top: 2;
        align: center middle;
    }

    DraftRestoreScreen Button {
        margin: 0 1;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("r", "restore", "Restore"),
        Binding("d", "discard_draft", "Discard"),
        Binding("escape", "discard_draft", "Discard"),
    ]

    def __init__(
        self,
        draft: Draft,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the draft restore screen.

        Args:
            draft: The draft to potentially restore.
            name: Widget name.
            id: Widget ID.
            classes: CSS classes.
        """
        super().__init__(name=name, id=id, classes=classes)
        self._draft = draft

    @property
    def draft_id(self) -> UUID:
        """Get the draft's ID."""
        return self._draft.id

    def compose(self) -> ComposeResult:
        """Compose the dialog layout."""
        entity_name = self._draft.entity_type.value.title()

        with Container(id="dialog"):
            yield Static(f"Restore {entity_name} Draft?", classes="title")

            with Vertical(classes="draft-info"):
                yield Static(f"Type: {entity_name}", classes="field-label")

                # Show preview of draft data
                partial_data = self._draft.partial_data
                if partial_data:
                    # Show first available field
                    for key in ["deliverable", "title", "narrative"]:
                        if partial_data.get(key):
                            value = str(partial_data[key])[:_PREVIEW_MAX_LENGTH]
                            if len(str(partial_data[key])) > _PREVIEW_MAX_LENGTH:
                                value += "..."
                            yield Static(f"{key.title()}: {value}", classes="field-value")
                            break

                # Show age
                age = self._draft.created_at.strftime("%Y-%m-%d %H:%M")
                yield Static(f"Created: {age}", classes="field-label")

            with Horizontal(id="buttons"):
                yield Button("Restore (r)", id="restore", variant="primary")
                yield Button("Discard (d)", id="discard", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "restore":
            self.dismiss("restore")
        elif event.button.id == "discard":
            self.dismiss("discard")

    def action_restore(self) -> None:
        """Restore the draft."""
        self.dismiss("restore")

    def action_discard_draft(self) -> None:
        """Discard the draft."""
        self.dismiss("discard")

    # Messages for external handling
    class Restore(Message):
        """Message to restore the draft."""

        def __init__(self, draft_id: UUID) -> None:
            """Initialize the message.

            Args:
                draft_id: ID of the draft to restore.
            """
            super().__init__()
            self.draft_id = draft_id

    class Discard(Message):
        """Message to discard the draft."""

        def __init__(self, draft_id: UUID) -> None:
            """Initialize the message.

            Args:
                draft_id: ID of the draft to discard.
            """
            super().__init__()
            self.draft_id = draft_id
