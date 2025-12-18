"""Modal screen shown when AI is not configured."""

from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class AiRequiredScreen(ModalScreen[str]):
    """Blocking modal requiring AI configuration.

    This screen is shown when the user has not configured any AI provider.
    It blocks app usage until the user opens Settings to configure a provider,
    or quits the app.

    Dismiss values:
    - "settings": User chose to open settings
    - "quit": User chose to quit
    """

    DEFAULT_CSS = """
    AiRequiredScreen {
        align: center middle;
        background: $primary 30%;
    }

    AiRequiredScreen #dialog {
        width: 72;
        height: auto;
        border: solid $error;
        background: $surface;
        padding: 2;
    }

    AiRequiredScreen .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    AiRequiredScreen .body {
        margin-bottom: 1;
    }

    AiRequiredScreen #buttons {
        height: auto;
        margin-top: 1;
        align: center middle;
    }

    AiRequiredScreen Button {
        margin: 0 1;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("escape", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the modal layout."""
        with Container(id="dialog"):
            yield Static("AI Not Configured", classes="title")

            with Vertical(classes="body"):
                yield Static(
                    "JDO requires an AI provider to be configured before use.",
                )
                yield Static(
                    "Open Settings to configure at least one provider and model.",
                )

            with Horizontal(id="buttons"):
                yield Button("Open Settings", id="settings", variant="primary")
                yield Button("Quit", id="quit", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "settings":
            self.dismiss("settings")
        elif event.button.id == "quit":
            self.dismiss("quit")

    def action_quit(self) -> None:
        """Quit the application."""
        self.dismiss("quit")
