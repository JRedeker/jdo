"""Home screen - Main entry point for JDO TUI.

The HomeScreen provides quick access to views and shortcuts,
serving as the main entry point for the application.
"""

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Static

from jdo.db import get_session
from jdo.db.session import get_triage_count


class HomeScreen(Screen[None]):
    """Main entry screen for JDO TUI.

    Provides:
    - Quick access keyboard shortcuts
    - Welcome message and guidance
    - Footer with available actions

    Keyboard shortcuts:
    - n: New chat
    - g: Show goals
    - c: Show commitments
    - v: Show visions
    - m: Show milestones
    - o: Show orphan commitments
    - s: Settings
    - q: Quit
    """

    DEFAULT_CSS = """
    HomeScreen {
        width: 100%;
        height: 100%;
    }

    HomeScreen #welcome-container {
        width: 100%;
        height: 100%;
        align: center middle;
    }

    HomeScreen #welcome-box {
        width: 60;
        height: auto;
        border: solid $primary;
        padding: 2;
    }

    HomeScreen .title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }

    HomeScreen .subtitle {
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }

    HomeScreen .shortcuts {
        margin-top: 1;
    }

    HomeScreen .shortcut-row {
        margin-bottom: 0;
    }

    HomeScreen .shortcut-key {
        color: $accent;
        text-style: bold;
    }

    HomeScreen #triage-indicator {
        text-align: center;
        color: $warning;
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
    }

    HomeScreen #triage-indicator.hidden {
        display: none;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("n", "new_chat", "New chat"),
        Binding("g", "show_goals", "Goals"),
        Binding("c", "show_commitments", "Commitments"),
        Binding("v", "show_visions", "Visions"),
        Binding("m", "show_milestones", "Milestones"),
        Binding("o", "show_orphans", "Orphans"),
        Binding("h", "show_hierarchy", "Hierarchy"),
        Binding("t", "start_triage", "Triage", show=False),
        Binding("s", "settings", "Settings"),
        Binding("q", "quit", "Quit"),
    ]

    triage_count: reactive[int] = reactive(0)

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the home screen.

        Args:
            name: Widget name.
            id: Widget ID.
            classes: CSS classes.
        """
        super().__init__(name=name, id=id, classes=classes)

    def compose(self) -> ComposeResult:
        """Compose the home screen layout."""
        with Container(id="welcome-container"), Vertical(id="welcome-box"):
            yield Static("JDO", classes="title")
            yield Static("Just Do One thing at a time", classes="subtitle")
            yield Static("", id="triage-indicator", classes="hidden")
            yield Static("")
            yield Static("What would you like to do?")
            yield Static("")
            yield Static("[n] New chat    [g] Goals    [c] Commitments", classes="shortcut-row")
            yield Static("[v] Visions     [m] Milestones  [o] Orphans", classes="shortcut-row")
            yield Static("[h] Hierarchy   [s] Settings    [q] Quit", classes="shortcut-row")

    def on_mount(self) -> None:
        """Handle mount event - check for triage items."""
        self._check_triage_count()

    def _check_triage_count(self) -> None:
        """Check database for items needing triage and update count.

        Silently handles database errors (e.g., missing tables during testing).
        """
        try:
            with get_session() as session:
                self.triage_count = get_triage_count(session)
        except Exception:
            # Database may not be initialized (e.g., in tests)
            self.triage_count = 0

    def watch_triage_count(self, count: int) -> None:
        """React to triage_count changes by updating the indicator.

        Args:
            count: The new triage count.
        """
        indicator = self.query_one("#triage-indicator", Static)
        if count > 0:
            indicator.update(f"{count} item(s) need triage [t]")
            indicator.remove_class("hidden")
        else:
            indicator.add_class("hidden")

    def action_new_chat(self) -> None:
        """Start a new chat conversation."""
        # This will be handled by the parent app
        self.post_message(self.NewChat())

    def action_show_goals(self) -> None:
        """Show goals in the data panel."""
        self.post_message(self.ShowGoals())

    def action_show_commitments(self) -> None:
        """Show commitments in the data panel."""
        self.post_message(self.ShowCommitments())

    def action_show_visions(self) -> None:
        """Show visions in the data panel."""
        self.post_message(self.ShowVisions())

    def action_show_milestones(self) -> None:
        """Show milestones in the data panel."""
        self.post_message(self.ShowMilestones())

    def action_show_orphans(self) -> None:
        """Show orphan commitments in the data panel."""
        self.post_message(self.ShowOrphans())

    def action_settings(self) -> None:
        """Open settings screen."""
        self.post_message(self.OpenSettings())

    def action_show_hierarchy(self) -> None:
        """Show the full hierarchy tree view."""
        self.post_message(self.ShowHierarchy())

    def action_start_triage(self) -> None:
        """Start triage workflow for captured items."""
        if self.triage_count > 0:
            self.post_message(self.StartTriage())

    # Custom messages for parent app to handle
    class NewChat(Message):
        """Message to start a new chat."""

    class ShowGoals(Message):
        """Message to show goals."""

    class ShowCommitments(Message):
        """Message to show commitments."""

    class ShowVisions(Message):
        """Message to show visions."""

    class ShowMilestones(Message):
        """Message to show milestones."""

    class ShowOrphans(Message):
        """Message to show orphan commitments."""

    class ShowHierarchy(Message):
        """Message to show the hierarchy tree view."""

    class OpenSettings(Message):
        """Message to open settings."""

    class StartTriage(Message):
        """Message to start triage workflow."""
