"""Main Textual application for JDO.

The JdoApp is the application shell that integrates MainScreen
and manages the application lifecycle.
"""

from __future__ import annotations

from typing import ClassVar
from uuid import UUID

from loguru import logger
from textual.app import App, ComposeResult
from textual.binding import BindingType
from textual.widgets import Footer, Header

from jdo.auth.api import is_authenticated
from jdo.config import get_settings
from jdo.db import create_db_and_tables, get_session
from jdo.db.navigation import NavigationService
from jdo.db.session import get_pending_drafts, get_visions_due_for_review
from jdo.logging import configure_logging
from jdo.models import Commitment, Goal, Milestone, Stakeholder, Vision
from jdo.models.draft import Draft
from jdo.observability import init_sentry
from jdo.screens.ai_required import AiRequiredScreen
from jdo.screens.draft_restore import DraftRestoreScreen
from jdo.screens.main import MainScreen
from jdo.screens.settings import SettingsScreen
from jdo.widgets.hierarchy_view import HierarchyView


class JdoApp(App[None]):
    """The JDO Textual application.

    Uses MainScreen as the primary interface with embedded
    NavSidebar, ChatContainer, PromptInput, and DataPanel.
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
        self._main_screen: MainScreen | None = None

        # Configure logging and observability
        settings = get_settings()
        log_path = settings.log_file_path if settings.log_to_file else None
        configure_logging(level=settings.log_level, log_file_path=log_path)

        # Initialize Sentry (optional - only if DSN configured)
        init_sentry(settings)

        logger.info("JDO application initialized")

    def compose(self) -> ComposeResult:
        """Compose the application layout.

        The app provides header and footer; screens provide content.
        """
        yield Header()
        yield Footer()

    async def on_mount(self) -> None:
        """Handle app mount - initialize database and show main screen."""
        logger.debug("App mounted, initializing database")
        # Initialize database tables
        if not self._db_initialized:
            create_db_and_tables()
            self._db_initialized = True
            logger.info("Database initialized")

        # Start with MainScreen
        main_screen = MainScreen()
        self._main_screen = main_screen
        await self.push_screen(main_screen)

        # If AI is not configured, block usage until configured.
        # Run in a worker to allow push_screen_wait (required by Textual)
        self.run_worker(self._startup_worker(), exclusive=True)

    async def _startup_worker(self) -> None:
        """Startup worker to handle AI configuration and draft checks.

        This runs in a worker context to allow push_screen_wait to work properly.
        """
        await self._ensure_ai_configured()

        # Check for pending drafts after ensuring AI config
        pending_draft = self._check_pending_drafts()
        if pending_draft:
            await self.push_screen(
                DraftRestoreScreen(pending_draft),
                self._on_draft_restore_decision,
            )
            return

        # No drafts; check for vision reviews
        self._check_vision_reviews()

    def _has_ai_credentials(self) -> bool:
        """Check if the configured AI provider has credentials.

        Returns:
            True if the currently selected provider is authenticated.
        """
        settings = get_settings()
        return is_authenticated(settings.ai_provider)

    async def _ensure_ai_configured(self) -> None:
        """Ensure the user has configured AI before using the app.

        Blocks app usage until the user configures a provider or quits.
        """
        settings = get_settings()
        if is_authenticated(settings.ai_provider):
            return

        while True:
            decision = await self.push_screen_wait(AiRequiredScreen())
            if decision == "settings":
                await self.push_screen_wait(SettingsScreen())
                settings = get_settings()
                if is_authenticated(settings.ai_provider):
                    return
                continue

            # Default to quitting
            self.exit()
            return

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

        Note: The DraftRestoreScreen is a ModalScreen that auto-pops on dismiss.
        MainScreen is already on the stack.
        """
        # Get the draft ID from the stored pending draft
        pending = self._check_pending_drafts()
        if not pending:
            # Draft was already deleted or doesn't exist
            self._check_vision_reviews()
            return

        draft_id = pending.id

        if decision == "restore":
            # Update MainScreen with the draft
            if self._main_screen:
                self._main_screen.set_draft_id(draft_id)
        else:
            # Discard (or None/escape) - delete the draft
            self._delete_draft(draft_id)
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

    # Message handlers for MainScreen

    def on_main_screen_quit_requested(self, _message: MainScreen.QuitRequested) -> None:
        """Handle quit request from MainScreen."""
        self.exit()

    def on_main_screen_open_settings(self, _message: MainScreen.OpenSettings) -> None:
        """Handle settings request from MainScreen."""
        logger.debug("Navigating to SettingsScreen")
        self.push_screen(SettingsScreen())

    def on_main_screen_navigation_selected(self, message: MainScreen.NavigationSelected) -> None:
        """Handle navigation selection from MainScreen.

        Updates the MainScreen's data panel based on sidebar selection.
        """
        item_id = message.item_id
        logger.debug(f"Navigation selected: {item_id}")

        if not self._main_screen:
            return

        # Use dispatcher to navigate to the selected view
        self._navigate_to_view(item_id)

    def _navigate_to_view(self, item_id: str) -> None:
        """Navigate to a view based on item ID.

        Dispatcher method that fetches appropriate data and updates the data panel.
        Consolidates all navigation logic previously spread across multiple methods.

        Args:
            item_id: Navigation item ID (e.g., "goals", "commitments", "integrity").
        """
        if not self._main_screen:
            return

        # Special cases that don't follow the list pattern
        if item_id == "chat":
            # Chat view - hide data panel
            self._main_screen.data_panel.show_list("", [])
            return

        if item_id == "hierarchy":
            # Hierarchy view - show empty for now, command can populate
            self._main_screen.data_panel.show_list("", [])
            return

        if item_id == "triage":
            # Triage view - special mode
            self._main_screen.set_triage_mode(True)
            return

        # Standard entity list views - use NavigationService
        with get_session() as session:
            if item_id == "goals":
                items = NavigationService.get_goals_list(session)
                self._main_screen.data_panel.show_list("goal", items)

            elif item_id == "commitments":
                items = NavigationService.get_commitments_list(session)
                self._main_screen.data_panel.show_list("commitment", items)

            elif item_id == "visions":
                items = NavigationService.get_visions_list(session)
                self._main_screen.data_panel.show_list("vision", items)

            elif item_id == "milestones":
                items = NavigationService.get_milestones_list(session)
                self._main_screen.data_panel.show_list("milestone", items)

            elif item_id == "orphans":
                items = NavigationService.get_orphans_list(session)
                self._main_screen.data_panel.show_list("commitment", items)

            elif item_id == "integrity":
                integrity_data = NavigationService.get_integrity_data(session)
                self._main_screen.data_panel.show_integrity_dashboard(integrity_data)

    def on_settings_screen_back(self, _message: SettingsScreen.Back) -> None:
        """Handle back request from SettingsScreen."""
        self.pop_screen()
        # Run in worker since _ensure_ai_configured uses push_screen_wait
        self.run_worker(self._ensure_ai_configured(), exclusive=True)

    def on_settings_screen_auth_status_changed(
        self, _message: SettingsScreen.AuthStatusChanged
    ) -> None:
        """Handle auth status change from SettingsScreen.

        This is informational - the actual AI config check happens when
        returning from settings via on_settings_screen_back.
        """
        logger.info("Authentication status changed")

    def on_hierarchy_view_item_selected(self, message: HierarchyView.ItemSelected) -> None:
        """Handle item selection from HierarchyView widget.

        Shows the selected item's details in the data panel.
        """
        if not self._main_screen:
            return

        item = message.item
        logger.debug(f"Hierarchy item selected: {type(item).__name__}")

        # Determine entity type and build data dict
        if isinstance(item, Vision):
            entity_type = "vision"
            data = {
                "id": str(item.id),
                "title": item.title,
                "timeframe": item.timeframe,
                "status": item.status.value,
            }
        elif isinstance(item, Goal):
            entity_type = "goal"
            data = {
                "id": str(item.id),
                "title": item.title,
                "problem_statement": item.problem_statement,
                "status": item.status.value,
            }
        elif isinstance(item, Milestone):
            entity_type = "milestone"
            data = {
                "id": str(item.id),
                "title": item.title,
                "description": item.description,
                "target_date": item.target_date.isoformat() if item.target_date else None,
                "status": item.status.value,
            }
        elif isinstance(item, Commitment):
            entity_type = "commitment"
            # Get stakeholder name
            stakeholder_name = ""
            with get_session() as session:
                stakeholder = session.get(Stakeholder, item.stakeholder_id)
                if stakeholder:
                    stakeholder_name = stakeholder.name
            data = {
                "id": str(item.id),
                "deliverable": item.deliverable,
                "stakeholder_name": stakeholder_name,
                "due_date": item.due_date.isoformat() if item.due_date else None,
                "status": item.status.value,
            }
        else:
            # Unknown type, ignore
            return

        self._main_screen.data_panel.show_view(entity_type, data)


def main() -> None:
    """Run the application."""
    app = JdoApp()
    app.run()


if __name__ == "__main__":
    main()
