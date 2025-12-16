"""Main Textual application."""

from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import BindingType
from textual.widgets import Footer, Header, Static


class JdoApp(App[None]):
    """A Textual application."""

    TITLE = "JDO"
    SUB_TITLE = "Terminal Application"

    BINDINGS: ClassVar[list[BindingType]] = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()
        yield Static("Welcome to JDO!", id="main")
        yield Footer()

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.theme = "textual-light" if self.theme == "textual-dark" else "textual-dark"


def main() -> None:
    """Run the application."""
    app = JdoApp()
    app.run()


if __name__ == "__main__":
    main()
