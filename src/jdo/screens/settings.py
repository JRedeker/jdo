"""Settings screen - Provider authentication and AI settings.

The SettingsScreen integrates with the jdo.auth module to show
authentication status and launch auth flows for AI providers.
"""

from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, Static

from jdo.auth.api import is_authenticated
from jdo.auth.registry import AuthMethod, get_auth_methods, get_provider_info, list_providers
from jdo.auth.screens import ApiKeyScreen, OAuthScreen
from jdo.config.settings import get_settings


class SettingsScreen(Screen[None]):
    """Settings screen for AI provider configuration.

    Provides:
    - View authentication status per provider
    - Launch OAuth/API key authentication flows
    - View current AI provider and model settings

    Keyboard shortcuts:
    - escape: Go back to previous screen
    """

    DEFAULT_CSS = """
    SettingsScreen {
        width: 100%;
        height: 100%;
    }

    SettingsScreen #settings-container {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    SettingsScreen #settings-box {
        width: 70;
        height: auto;
        border: solid $primary;
        padding: 2;
    }

    SettingsScreen .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    SettingsScreen .section-title {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
    }

    SettingsScreen .provider-row {
        height: auto;
        margin-bottom: 1;
    }

    SettingsScreen .provider-name {
        width: 20;
    }

    SettingsScreen .auth-status {
        width: 15;
    }

    SettingsScreen .auth-status.authenticated {
        color: $success;
    }

    SettingsScreen .auth-status.not-authenticated {
        color: $warning;
    }

    SettingsScreen .current-setting {
        margin-bottom: 0;
    }

    SettingsScreen .setting-label {
        color: $text-muted;
    }

    SettingsScreen .setting-value {
        text-style: bold;
    }

    SettingsScreen #back-hint {
        margin-top: 2;
        text-align: center;
        color: $text-muted;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("escape", "back", "Back"),
    ]

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the settings screen.

        Args:
            name: Widget name.
            id: Widget ID.
            classes: CSS classes.
        """
        super().__init__(name=name, id=id, classes=classes)

    def compose(self) -> ComposeResult:
        """Compose the settings screen layout."""
        settings = get_settings()

        with Container(id="settings-container"), Vertical(id="settings-box"):
            yield Static("Settings", classes="title")

            # Current AI Settings section
            yield Static("Current AI Configuration", classes="section-title")
            yield Static(
                f"Provider: {settings.ai_provider}",
                classes="current-setting",
            )
            yield Static(
                f"Model: {settings.ai_model}",
                classes="current-setting",
            )

            # Provider Authentication section
            yield Static("Provider Authentication", classes="section-title")

            for provider_id in list_providers():
                provider_info = get_provider_info(provider_id)
                provider_name = provider_info.name if provider_info else provider_id

                authenticated = is_authenticated(provider_id)
                status_text = "Authenticated" if authenticated else "Not authenticated"
                status_class = "authenticated" if authenticated else "not-authenticated"

                with Container(classes="provider-row"):
                    yield Static(provider_name, classes="provider-name")
                    yield Static(status_text, classes=f"auth-status {status_class}")
                    yield Button(
                        "Configure",
                        id=f"configure-{provider_id}",
                        variant="default",
                    )

            yield Static("[Escape] Back", id="back-hint")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        if button_id and button_id.startswith("configure-"):
            provider_id = button_id.replace("configure-", "")
            self._configure_provider(provider_id)

    def _configure_provider(self, provider_id: str) -> None:
        """Configure authentication for a provider.

        Args:
            provider_id: The provider to configure.
        """
        auth_methods = get_auth_methods(provider_id)

        # Prefer OAuth if available (currently only Anthropic)
        if AuthMethod.OAUTH in auth_methods:
            self.launch_oauth_flow(provider_id)
        elif AuthMethod.API_KEY in auth_methods:
            self.launch_api_key_flow(provider_id)

    def launch_oauth_flow(self, provider_id: str) -> None:
        """Launch OAuth authentication flow.

        Args:
            provider_id: The provider to authenticate with (currently only anthropic).
        """
        # Store provider_id for potential multi-provider OAuth support
        _ = provider_id  # Currently only Anthropic supports OAuth
        # Push the OAuthScreen modal
        self.app.push_screen(OAuthScreen(), self._on_auth_complete)

    def launch_api_key_flow(self, provider_id: str) -> None:
        """Launch API key authentication flow.

        Args:
            provider_id: The provider to authenticate with.
        """
        # Push the ApiKeyScreen modal
        self.app.push_screen(ApiKeyScreen(provider_id), self._on_auth_complete)

    def _on_auth_complete(self, success: bool | None) -> None:
        """Handle auth flow completion.

        Args:
            success: Whether authentication succeeded, or None if dismissed.
        """
        if success:
            # Refresh the screen to show updated auth status
            self.refresh()
            self.post_message(self.AuthStatusChanged())

    def action_back(self) -> None:
        """Go back to the previous screen."""
        self.post_message(self.Back())

    # Custom messages for parent app to handle
    class Back(Message):
        """Message to go back to previous screen."""

    class ProviderChanged(Message):
        """Message when AI provider is changed."""

        def __init__(self, provider_id: str) -> None:
            """Initialize the message.

            Args:
                provider_id: The new provider ID.
            """
            super().__init__()
            self.provider_id = provider_id

    class AuthStatusChanged(Message):
        """Message when auth status changes."""
