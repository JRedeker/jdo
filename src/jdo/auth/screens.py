"""TUI screens for authentication flows."""

import webbrowser

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

from jdo.auth.api import save_credentials
from jdo.auth.models import ApiKeyCredentials
from jdo.auth.oauth import (
    AuthenticationError,
    build_authorization_url,
    exchange_code,
)

# Provider info for display
PROVIDER_INFO = {
    "anthropic": {
        "name": "Anthropic (Claude)",
        "api_key_url": "https://console.anthropic.com/settings/keys",
    },
    "openai": {
        "name": "OpenAI",
        "api_key_url": "https://platform.openai.com/api-keys",
    },
    "openrouter": {
        "name": "OpenRouter",
        "api_key_url": "https://openrouter.ai/keys",
    },
}


class OAuthScreen(ModalScreen[bool]):
    """Modal screen for OAuth authentication flow.

    Returns True on successful authentication, False on cancel.
    """

    DEFAULT_CSS = """
    OAuthScreen {
        align: center middle;
    }

    OAuthScreen > Container {
        width: 80;
        height: auto;
        max-height: 24;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    OAuthScreen #title {
        text-style: bold;
        margin-bottom: 1;
    }

    OAuthScreen #instructions {
        margin-bottom: 1;
    }

    OAuthScreen #auth-url {
        margin-bottom: 1;
        color: $secondary;
    }

    OAuthScreen #code-input {
        margin-bottom: 1;
    }

    OAuthScreen #error-label {
        color: $error;
        margin-bottom: 1;
        display: none;
    }

    OAuthScreen #buttons {
        height: auto;
        align: right middle;
    }

    OAuthScreen Button {
        margin-left: 1;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self) -> None:
        """Initialize the OAuth screen."""
        super().__init__()
        self.auth_url, self.verifier = build_authorization_url()

    def compose(self) -> ComposeResult:
        """Compose the OAuth screen."""
        with Container():
            yield Static("Claude OAuth Authentication", id="title")
            yield Static(
                "1. Click 'Open Browser' or copy the URL below\n"
                "2. Sign in to your Claude account\n"
                "3. Copy the authorization code and paste it below",
                id="instructions",
            )
            yield Static(self.auth_url, id="auth-url")
            yield Input(
                placeholder="Paste authorization code here",
                id="code-input",
            )
            yield Label("", id="error-label")
            with Container(id="buttons"):
                yield Button("Open Browser", id="browser-btn", variant="default")
                yield Button("Submit", id="submit-btn", variant="primary")
                yield Button("Cancel", id="cancel-btn", variant="default")

    def action_cancel(self) -> None:
        """Handle cancel action."""
        self.dismiss(False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-btn":
            self.dismiss(False)
        elif event.button.id == "browser-btn":
            webbrowser.open(self.auth_url)
        elif event.button.id == "submit-btn":
            await self._submit_code()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)."""
        if event.input.id == "code-input":
            await self._submit_code()

    async def _submit_code(self) -> None:
        """Submit the authorization code for token exchange."""
        code_input = self.query_one("#code-input", Input)
        error_label = self.query_one("#error-label", Label)

        code = code_input.value.strip()
        if not code:
            error_label.update("Please enter the authorization code")
            error_label.display = True
            return

        try:
            # Exchange code for tokens
            credentials = await exchange_code(code, self.verifier)
            # Save credentials
            save_credentials("anthropic", credentials)
            self.notify("Authentication successful!", severity="information")
            self.dismiss(True)
        except AuthenticationError as e:
            error_label.update(f"Authentication failed: {e}")
            error_label.display = True


class ApiKeyScreen(ModalScreen[bool]):
    """Modal screen for API key entry.

    Returns True on successful save, False on cancel.
    """

    DEFAULT_CSS = """
    ApiKeyScreen {
        align: center middle;
    }

    ApiKeyScreen > Container {
        width: 70;
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
        align: right middle;
    }

    ApiKeyScreen Button {
        margin-left: 1;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
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
        with Container():
            yield Static(f"Enter API Key for {self.provider_name}", id="provider-title")
            yield Static(
                f"Get your API key from:\n{self.api_key_url}",
                id="instructions",
            )
            yield Input(
                placeholder="Paste your API key here",
                password=True,
                id="api-key-input",
            )
            yield Label("", id="error-label")
            with Container(id="buttons"):
                yield Button("Open URL", id="url-btn", variant="default")
                yield Button("Save", id="save-btn", variant="primary")
                yield Button("Cancel", id="cancel-btn", variant="default")

    def action_cancel(self) -> None:
        """Handle cancel action."""
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-btn":
            self.dismiss(False)
        elif event.button.id == "url-btn":
            if self.api_key_url:
                webbrowser.open(self.api_key_url)
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
