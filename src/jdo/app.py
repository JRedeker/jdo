"""Main Textual application for JDO.

The JdoApp is the application shell that integrates all screens
and manages the application lifecycle.
"""

from typing import ClassVar
from uuid import UUID

from loguru import logger
from textual.app import App, ComposeResult
from textual.binding import BindingType
from textual.widgets import Footer, Header

from jdo.config import get_settings
from jdo.db import create_db_and_tables, get_session
from jdo.db.session import get_pending_drafts, get_visions_due_for_review
from jdo.logging import configure_logging
from jdo.models.draft import Draft
from jdo.models.vision import Vision
from jdo.screens.chat import ChatScreen
from jdo.screens.draft_restore import DraftRestoreScreen
from jdo.screens.home import HomeScreen
from jdo.screens.settings import SettingsScreen


class JdoApp(App[None]):
    """The JDO Textual application.

    Integrates HomeScreen, ChatScreen, and SettingsScreen with
    message-based navigation and startup initialization.
    """

    TITLE = "JDO"
    SUB_TITLE = "Just Do One thing at a time"

    CSS = """
    Screen {
        background: $surface;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
    ]

    def __init__(self) -> None:
        """Initialize the JDO application."""
        super().__init__()
        self._db_initialized = False
        self._snoozed_reviews: set[UUID] = set()
        self._visions_due_for_review: list[Vision] = []

        # Configure logging
        settings = get_settings()
        log_path = settings.log_file_path if settings.log_to_file else None
        configure_logging(level=settings.log_level, log_file_path=log_path)
        logger.info("JDO application initialized")

    def compose(self) -> ComposeResult:
        """Compose the application layout.

        The app provides header and footer; screens provide content.
        """
        yield Header()
        yield Footer()

    async def on_mount(self) -> None:
        """Handle app mount - initialize database and show home screen."""
        logger.debug("App mounted, initializing database")
        # Initialize database tables
        if not self._db_initialized:
            create_db_and_tables()
            self._db_initialized = True
            logger.info("Database initialized")

        # Check for pending drafts
        pending_draft = self._check_pending_drafts()
        if pending_draft:
            # Show draft restore modal
            await self.push_screen(
                DraftRestoreScreen(pending_draft),
                self._on_draft_restore_decision,
            )
        else:
            # No drafts, go to home screen
            await self.push_screen(HomeScreen())
            # Check for vision reviews after showing home
            self._check_vision_reviews()

    def _check_pending_drafts(self) -> Draft | None:
        """Check for pending drafts in the database.

        Returns:
            The most recent pending draft if any, None otherwise.
        """
        with get_session() as session:
            drafts = get_pending_drafts(session)
            if drafts:
                # Detach the draft from session before returning
                draft = drafts[0]
                # Make a copy of the needed attributes before session closes
                session.expunge(draft)
                return draft
        return None

    def _on_draft_restore_decision(self, decision: str | None) -> None:
        """Handle the user's draft restore decision.

        Args:
            decision: "restore" or "discard", or None if dismissed.
        """
        # Get the draft ID from the stored pending draft
        pending = self._check_pending_drafts()
        if not pending:
            # Draft was already deleted or doesn't exist
            self.push_screen(HomeScreen())
            self._check_vision_reviews()
            return

        draft_id = pending.id

        if decision == "restore":
            # Navigate to chat with the draft
            self.push_screen(ChatScreen(draft_id=draft_id))
        else:
            # Discard (or None/escape) - delete the draft
            self._delete_draft(draft_id)
            self.push_screen(HomeScreen())
            self._check_vision_reviews()

    def _delete_draft(self, draft_id: UUID) -> None:
        """Delete a draft by ID.

        Args:
            draft_id: ID of the draft to delete.
        """
        with get_session() as session:
            draft = session.get(Draft, draft_id)
            if draft:
                session.delete(draft)

    def _check_vision_reviews(self) -> None:
        """Check for visions due for review and store them."""
        with get_session() as session:
            visions = get_visions_due_for_review(session)
            # Detach visions from session
            for vision in visions:
                session.expunge(vision)
            self._visions_due_for_review = visions

    def snooze_vision_review(self, vision_id: UUID) -> None:
        """Snooze a vision review for this session.

        Args:
            vision_id: ID of the vision to snooze.
        """
        self._snoozed_reviews.add(vision_id)

    def get_unsnoozed_reviews(self) -> list[Vision]:
        """Get visions due for review that haven't been snoozed.

        Returns:
            List of visions that are due and not snoozed.
        """
        return [v for v in self._visions_due_for_review if v.id not in self._snoozed_reviews]

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.theme = "textual-light" if self.theme == "textual-dark" else "textual-dark"

    # Message handlers for screen navigation

    def on_home_screen_new_chat(self, _message: HomeScreen.NewChat) -> None:
        """Handle new chat request from HomeScreen."""
        logger.debug("Navigating to ChatScreen")
        self.push_screen(ChatScreen())

    def on_home_screen_open_settings(self, _message: HomeScreen.OpenSettings) -> None:
        """Handle settings request from HomeScreen."""
        logger.debug("Navigating to SettingsScreen")
        self.push_screen(SettingsScreen())

    def on_settings_screen_back(self, _message: SettingsScreen.Back) -> None:
        """Handle back request from SettingsScreen."""
        self.pop_screen()

    def on_chat_screen_back(self, _message: ChatScreen.Back) -> None:
        """Handle back request from ChatScreen."""
        self.pop_screen()

    def on_home_screen_start_triage(self, _message: HomeScreen.StartTriage) -> None:
        """Handle triage request from HomeScreen."""
        logger.debug("Navigating to ChatScreen in triage mode")
        # Navigate to chat with triage mode
        self.push_screen(ChatScreen(triage_mode=True))


def main() -> None:
    """Run the application."""
    app = JdoApp()
    app.run()


if __name__ == "__main__":
    main()
