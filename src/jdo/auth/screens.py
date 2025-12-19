"""TUI screens for authentication flows."""

from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

from jdo.auth.api import save_credentials
from jdo.auth.models import ApiKeyCredentials

# Provider info for display
PROVIDER_INFO = {
    "openai": {
        "name": "OpenAI",
        "api_key_url": "https://platform.openai.com/api-keys",
    },
    "openrouter": {
        "name": "OpenRouter",
        "api_key_url": "https://openrouter.ai/keys",
    },
}


class ApiKeyScreen(ModalScreen[bool]):
    """Modal screen for API key entry.

    Returns True on successful save, False on cancel.
    """

    DEFAULT_CSS = """
    ApiKeyScreen {
        align: center middle;
    }

    ApiKeyScreen > Container {
        width: 80;
        height: auto;
        max-height: 18;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    ApiKeyScreen #provider-title {
        text-style: bold;
        margin-bottom: 1;
    }

    ApiKeyScreen #instructions {
        margin-bottom: 1;
    }

    ApiKeyScreen #api-key-input {
        margin-bottom: 1;
    }

    ApiKeyScreen #error-label {
        color: $error;
        margin-bottom: 1;
        display: none;
    }

    ApiKeyScreen #buttons {
        height: auto;
        width: 100%;
        align: right middle;
    }

    ApiKeyScreen Button {
        margin-left: 1;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, provider_id: str) -> None:
        """Initialize the API key screen.

        Args:
            provider_id: The provider identifier (e.g., "openai", "anthropic").
        """
        super().__init__()
        self.provider_id = provider_id
        provider_info = PROVIDER_INFO.get(provider_id, {"name": provider_id, "api_key_url": ""})
        self.provider_name = provider_info["name"]
        self.api_key_url = provider_info["api_key_url"]

    def compose(self) -> ComposeResult:
        """Compose the API key screen."""
        # Create clickable hyperlink for the API key URL (quoted for special chars)
        if self.api_key_url:
            url_markup = (
                f'Get your API key from: [link="{self.api_key_url}"]{self.api_key_url}[/link]'
            )
        else:
            url_markup = "Get your API key from your provider's console."

        with Container():
            yield Static(f"Enter API Key for {self.provider_name}", id="provider-title")
            yield Static(url_markup, id="instructions", markup=True)
            yield Input(
                placeholder="Paste your API key here",
                password=True,
                id="api-key-input",
            )
            yield Label("", id="error-label")
            with Horizontal(id="buttons"):
                yield Button("Save", id="save-btn", variant="primary")
                yield Button("Cancel", id="cancel-btn", variant="default")

    def action_cancel(self) -> None:
        """Handle cancel action."""
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-btn":
            self.dismiss(False)
        elif event.button.id == "save-btn":
            self._save_key()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        if event.input.id == "api-key-input":
            self._save_key()

    def _save_key(self) -> None:
        """Save the API key."""
        key_input = self.query_one("#api-key-input", Input)
        error_label = self.query_one("#error-label", Label)

        api_key = key_input.value.strip()
        if not api_key:
            error_label.update("Please enter your API key")
            error_label.display = True
            return

        # Save credentials
        save_credentials(self.provider_id, ApiKeyCredentials(api_key=api_key))
        self.notify("API key saved!", severity="information")
        self.dismiss(True)
