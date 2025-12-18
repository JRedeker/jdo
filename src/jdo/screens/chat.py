"""Chat screen with split-panel layout.

The main chat interface with:
- Chat panel on left (60%) - messages and prompt
- Data panel on right (40%) - structured data display
- Responsive collapse on narrow terminals
"""

from typing import ClassVar
from uuid import UUID

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import Screen

from jdo.widgets.chat_container import ChatContainer
from jdo.widgets.data_panel import DataPanel
from jdo.widgets.prompt_input import PromptInput


class ChatScreen(Screen[None]):
    """Main chat interface with split-panel layout.

    Layout:
    - Left panel (60%): Chat messages and prompt input
    - Right panel (40%): Data panel for drafts/views/lists

    Keyboard shortcuts:
    - Tab: Toggle focus between chat and data panel
    - Escape: Return to home (or focus prompt first if not focused)
    - p: Toggle data panel visibility
    """

    DEFAULT_CSS = """
    ChatScreen {
        width: 100%;
        height: 100%;
    }

    ChatScreen Horizontal {
        width: 100%;
        height: 100%;
    }

    ChatScreen #chat-panel {
        width: 60%;
        height: 100%;
    }

    ChatScreen #chat-panel.expanded {
        width: 100%;
    }

    ChatScreen ChatContainer {
        height: 1fr;
        border: solid $primary;
    }

    ChatScreen PromptInput {
        height: auto;
        max-height: 10;
        border: solid $accent;
        margin-top: 1;
    }

    ChatScreen DataPanel {
        width: 40%;
    }

    ChatScreen DataPanel.hidden {
        display: none;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("tab", "toggle_focus", "Switch panel", show=False),
        Binding("escape", "back", "Back", show=False),
        Binding("p", "toggle_panel", "Toggle panel"),
    ]

    def __init__(
        self,
        *,
        draft_id: UUID | None = None,
        triage_mode: bool = False,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the chat screen.

        Args:
            draft_id: Optional draft ID to restore on mount.
            triage_mode: If True, start in triage mode for captured items.
            name: Widget name.
            id: Widget ID.
            classes: CSS classes.
        """
        super().__init__(name=name, id=id, classes=classes)
        self._panel_visible = True
        self._draft_id = draft_id
        self._triage_mode = triage_mode

    def compose(self) -> ComposeResult:
        """Compose the chat screen layout."""
        with Horizontal():
            with Vertical(id="chat-panel"):
                yield ChatContainer(id="chat-container")
                yield PromptInput(id="prompt-input")
            yield DataPanel(id="data-panel")

    def on_mount(self) -> None:
        """Handle mount event."""
        # Focus the prompt input on mount
        prompt = self.query_one("#prompt-input", PromptInput)
        prompt.focus()

    def action_toggle_focus(self) -> None:
        """Toggle focus between chat panel and data panel."""
        data_panel = self.query_one("#data-panel", DataPanel)
        prompt = self.query_one("#prompt-input", PromptInput)

        if prompt.has_focus:
            data_panel.focus()
        else:
            prompt.focus()

    def action_focus_prompt(self) -> None:
        """Return focus to the prompt input."""
        prompt = self.query_one("#prompt-input", PromptInput)
        prompt.focus()

    def action_back(self) -> None:
        """Go back to home screen.

        If prompt doesn't have focus, focus it first.
        If prompt has focus and is empty, go back to home.
        """
        prompt = self.query_one("#prompt-input", PromptInput)
        if not prompt.has_focus:
            prompt.focus()
        elif not prompt.text.strip():
            # Prompt is focused and empty, go back
            self.post_message(ChatScreen.Back())
        else:
            # Prompt has content, just focus it (no-op since already focused)
            pass

    def action_toggle_panel(self) -> None:
        """Toggle data panel visibility."""
        data_panel = self.query_one("#data-panel", DataPanel)
        chat_panel = self.query_one("#chat-panel", Vertical)

        self._panel_visible = not self._panel_visible

        if self._panel_visible:
            data_panel.display = True
            data_panel.remove_class("hidden")
            chat_panel.remove_class("expanded")
        else:
            data_panel.display = False
            data_panel.add_class("hidden")
            chat_panel.add_class("expanded")

    # Custom messages for parent app to handle
    class Back(Message):
        """Message to go back to home screen."""
