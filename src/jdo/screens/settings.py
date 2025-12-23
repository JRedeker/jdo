"""Settings screen - Provider authentication and AI settings.

The SettingsScreen integrates with the jdo.auth module to show
authentication status and launch auth flows for AI providers.
"""

from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.css.query import NoMatches
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, RadioButton, RadioSet, Static

from jdo.auth.api import is_authenticated
from jdo.auth.registry import AuthMethod, get_auth_methods, get_provider_info, list_providers
from jdo.auth.screens import ApiKeyScreen
from jdo.config import set_ai_provider
from jdo.config.settings import get_settings


class SettingsScreen(Screen[None]):
    """Settings screen for AI provider configuration.

    Provides:
    - View authentication status per provider
    - Launch API key authentication flows
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
        width: 100%;
        margin-bottom: 1;
    }

    SettingsScreen .provider-name {
        width: 20;
        height: auto;
    }

    SettingsScreen .auth-status {
        width: 18;
        height: auto;
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

    SettingsScreen #provider-selector {
        margin-top: 1;
        margin-bottom: 1;
        height: auto;
        width: 100%;
    }

    SettingsScreen #provider-selector-section {
        display: block;
    }

    SettingsScreen #provider-selector-section.hidden {
        display: none;
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
        current_provider = settings.ai_provider

        # Get authenticated providers for the selector
        authenticated_providers = [p for p in list_providers() if is_authenticated(p)]

        with Container(id="settings-container"), Vertical(id="settings-box"):
            yield Static("Settings", classes="title")

            # Current AI Settings section
            yield Static("Current AI Configuration", classes="section-title")
            yield Static(
                f"Provider: {settings.ai_provider}",
                classes="current-setting",
                id="current-provider-display",
            )
            yield Static(
                f"Model: {settings.ai_model}",
                classes="current-setting",
            )

            # Provider selector section - only show if multiple authenticated providers
            hide_selector = len(authenticated_providers) <= 1
            with Container(
                id="provider-selector-section",
                classes="hidden" if hide_selector else "",
            ):
                yield Static("Switch Provider", classes="section-title")
                with RadioSet(id="provider-selector"):
                    for provider_id in list_providers():
                        provider_info = get_provider_info(provider_id)
                        provider_name = provider_info.name if provider_info else provider_id
                        is_current = provider_id == current_provider
                        is_auth = is_authenticated(provider_id)
                        # Only show authenticated providers in selector
                        if is_auth:
                            yield RadioButton(
                                provider_name,
                                value=is_current,
                                id=f"provider-radio-{provider_id}",
                            )

            # Provider Authentication section
            yield Static("Provider Authentication", classes="section-title")

            for provider_id in list_providers():
                provider_info = get_provider_info(provider_id)
                provider_name = provider_info.name if provider_info else provider_id

                authenticated = is_authenticated(provider_id)
                status_text = "Authenticated" if authenticated else "Not authenticated"
                status_class = "authenticated" if authenticated else "not-authenticated"

                with Horizontal(classes="provider-row"):
                    yield Static(provider_name, classes="provider-name")
                    yield Static(
                        status_text,
                        id=f"auth-status-{provider_id}",
                        classes=f"auth-status {status_class}",
                    )
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

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle provider selection change.

        Args:
            event: The RadioSet.Changed event.
        """
        if event.radio_set.id != "provider-selector":
            return

        # Get the selected radio button
        pressed = event.pressed
        if not pressed or not pressed.id:
            return

        # Extract provider_id from radio button id (format: provider-radio-{provider_id})
        provider_id = pressed.id.replace("provider-radio-", "")

        # Update provider setting
        set_ai_provider(provider_id)

        # Update the display
        self._update_provider_display(provider_id)

    def _update_provider_display(self, provider_id: str) -> None:
        """Update the current provider display.

        Args:
            provider_id: The new provider ID.
        """
        try:
            display_widget = self.query_one("#current-provider-display", Static)
            display_widget.update(f"Provider: {provider_id}")
        except NoMatches:
            pass

    def _configure_provider(self, provider_id: str) -> None:
        """Configure authentication for a provider.

        Args:
            provider_id: The provider to configure.
        """
        auth_methods = get_auth_methods(provider_id)

        if AuthMethod.API_KEY in auth_methods:
            self.launch_api_key_flow(provider_id)

    def launch_api_key_flow(self, provider_id: str) -> None:
        """Launch API key authentication flow."""
        self.app.push_screen(ApiKeyScreen(provider_id), self._on_auth_complete)

    def _on_auth_complete(self, success: bool | None) -> None:
        """Handle auth flow completion.

        Args:
            success: Whether authentication succeeded, or None if dismissed.
        """
        # Always refresh auth statuses and restore focus after modal dismiss
        self._refresh_auth_statuses()
        self.focus()  # Fix: Restore focus after modal dismiss to fix Back binding

        if success:
            self.post_message(self.AuthStatusChanged())

    def _refresh_auth_statuses(self) -> None:
        """Refresh auth status widgets to reflect current state.

        Queries each provider's authentication status and updates the
        corresponding status widget text and classes. Also updates
        the provider selector visibility.
        """
        authenticated_providers = []

        for provider_id in list_providers():
            try:
                status_widget = self.query_one(f"#auth-status-{provider_id}", Static)
            except NoMatches:
                # Widget not found, skip
                continue

            authenticated = is_authenticated(provider_id)
            if authenticated:
                authenticated_providers.append(provider_id)
            status_text = "Authenticated" if authenticated else "Not authenticated"

            # Update widget text
            status_widget.update(status_text)

            # Update widget classes
            status_widget.remove_class("authenticated", "not-authenticated")
            status_widget.add_class("authenticated" if authenticated else "not-authenticated")

        # Update provider selector section visibility
        try:
            selector_section = self.query_one("#provider-selector-section", Container)
            if len(authenticated_providers) <= 1:
                selector_section.add_class("hidden")
            else:
                selector_section.remove_class("hidden")
        except NoMatches:
            pass

    def action_back(self) -> None:
        """Go back to the previous screen."""
        self.post_message(self.Back())

    # Custom messages for parent app to handle
    class Back(Message):
        """Message to go back to previous screen."""

    class AuthStatusChanged(Message):
        """Message when auth status changes (e.g., successful authentication)."""
