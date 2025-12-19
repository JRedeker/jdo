"""Main Textual application for JDO.

The JdoApp is the application shell that integrates all screens
and manages the application lifecycle.
"""

from __future__ import annotations

from typing import ClassVar
from uuid import UUID

from loguru import logger
from sqlmodel import select
from textual.app import App, ComposeResult
from textual.binding import BindingType
from textual.widgets import Footer, Header

from jdo.auth.api import is_authenticated
from jdo.config import get_settings
from jdo.db import create_db_and_tables, get_session
from jdo.db.session import get_pending_drafts, get_visions_due_for_review
from jdo.integrity.service import IntegrityService
from jdo.logging import configure_logging
from jdo.models import Commitment, Goal, Milestone, Stakeholder, Vision
from jdo.models.draft import Draft
from jdo.observability import init_sentry
from jdo.screens.ai_required import AiRequiredScreen
from jdo.screens.chat import ChatScreen, ChatScreenConfig
from jdo.screens.draft_restore import DraftRestoreScreen
from jdo.screens.home import HomeScreen
from jdo.screens.settings import SettingsScreen
from jdo.widgets.hierarchy_view import HierarchyView
from jdo.widgets.nav_sidebar import NavSidebar


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
        """Handle app mount - initialize database and show home screen."""
        logger.debug("App mounted, initializing database")
        # Initialize database tables
        if not self._db_initialized:
            create_db_and_tables()
            self._db_initialized = True
            logger.info("Database initialized")

        # Always start at home screen
        await self.push_screen(HomeScreen())

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
        HomeScreen is already on the stack, so we only push if navigating to ChatScreen.
        """
        # Get the draft ID from the stored pending draft
        pending = self._check_pending_drafts()
        if not pending:
            # Draft was already deleted or doesn't exist
            # HomeScreen is already showing, just check vision reviews
            self._check_vision_reviews()
            return

        draft_id = pending.id

        if decision == "restore":
            # Navigate to chat with the draft
            self.push_screen(ChatScreen(ChatScreenConfig(draft_id=draft_id)))
        else:
            # Discard (or None/escape) - delete the draft
            self._delete_draft(draft_id)
            # HomeScreen is already showing, just check vision reviews
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
        # Run in worker since _ensure_ai_configured uses push_screen_wait
        self.run_worker(self._ensure_ai_configured(), exclusive=True)

    def on_chat_screen_back(self, _message: ChatScreen.Back) -> None:
        """Handle back request from ChatScreen."""
        self.pop_screen()

    def on_home_screen_start_triage(self, _message: HomeScreen.StartTriage) -> None:
        """Handle triage request from HomeScreen."""
        logger.debug("Navigating to ChatScreen in triage mode")
        # Navigate to chat with triage mode
        self.push_screen(ChatScreen(ChatScreenConfig(triage_mode=True)))

    def on_home_screen_show_goals(self, _message: HomeScreen.ShowGoals) -> None:
        """Handle show goals request from HomeScreen."""
        logger.debug("Navigating to ChatScreen with goals view")
        with get_session() as session:
            goals = list(session.exec(select(Goal)).all())
            goal_items = [
                {
                    "id": str(g.id),
                    "title": g.title,
                    "problem_statement": g.problem_statement,
                    "status": g.status.value,
                }
                for g in goals
            ]
        self.push_screen(
            ChatScreen(
                ChatScreenConfig(
                    initial_mode="list", initial_entity_type="goal", initial_data=goal_items
                )
            )
        )

    def on_home_screen_show_commitments(self, _message: HomeScreen.ShowCommitments) -> None:
        """Handle show commitments request from HomeScreen."""
        logger.debug("Navigating to ChatScreen with commitments view")
        with get_session() as session:
            results = list(session.exec(select(Commitment, Stakeholder).join(Stakeholder)).all())
            commitment_items = [
                {
                    "id": str(c.id),
                    "deliverable": c.deliverable,
                    "stakeholder_name": s.name,
                    "due_date": c.due_date.isoformat(),
                    "status": c.status.value,
                }
                for c, s in results
            ]
        self.push_screen(
            ChatScreen(
                ChatScreenConfig(
                    initial_mode="list",
                    initial_entity_type="commitment",
                    initial_data=commitment_items,
                )
            )
        )

    def on_home_screen_show_visions(self, _message: HomeScreen.ShowVisions) -> None:
        """Handle show visions request from HomeScreen."""
        logger.debug("Navigating to ChatScreen with visions view")
        with get_session() as session:
            visions = list(session.exec(select(Vision)).all())
            vision_items = [
                {
                    "id": str(v.id),
                    "title": v.title,
                    "timeframe": v.timeframe,
                    "status": v.status.value,
                }
                for v in visions
            ]
        self.push_screen(
            ChatScreen(
                ChatScreenConfig(
                    initial_mode="list", initial_entity_type="vision", initial_data=vision_items
                )
            )
        )

    def on_home_screen_show_milestones(self, _message: HomeScreen.ShowMilestones) -> None:
        """Handle show milestones request from HomeScreen."""
        logger.debug("Navigating to ChatScreen with milestones view")
        with get_session() as session:
            milestones = list(session.exec(select(Milestone)).all())
            milestone_items = [
                {
                    "id": str(m.id),
                    "description": m.description,
                    "target_date": m.target_date.isoformat(),
                    "status": m.status.value,
                }
                for m in milestones
            ]
        self.push_screen(
            ChatScreen(
                ChatScreenConfig(
                    initial_mode="list",
                    initial_entity_type="milestone",
                    initial_data=milestone_items,
                )
            )
        )

    def on_home_screen_show_orphans(self, _message: HomeScreen.ShowOrphans) -> None:
        """Handle show orphan commitments request from HomeScreen."""
        logger.debug("Navigating to ChatScreen with orphan commitments view")
        with get_session() as session:
            # Orphan commitments have no goal_id
            results = list(
                session.exec(
                    select(Commitment, Stakeholder)
                    .join(Stakeholder)
                    .where(Commitment.goal_id == None)  # noqa: E711
                ).all()
            )
            orphan_items = [
                {
                    "id": str(c.id),
                    "deliverable": c.deliverable,
                    "stakeholder_name": s.name,
                    "due_date": c.due_date.isoformat(),
                    "status": c.status.value,
                }
                for c, s in results
            ]
        self.push_screen(
            ChatScreen(
                ChatScreenConfig(
                    initial_mode="list",
                    initial_entity_type="commitment",
                    initial_data=orphan_items,
                )
            )
        )

    def on_home_screen_show_hierarchy(self, _message: HomeScreen.ShowHierarchy) -> None:
        """Handle show hierarchy request from HomeScreen."""
        logger.debug("Navigating to ChatScreen with hierarchy view")
        # For now, just navigate to chat - hierarchy view can be built with /hierarchy command
        self.push_screen(ChatScreen())

    def on_home_screen_show_integrity(self, _message: HomeScreen.ShowIntegrity) -> None:
        """Handle show integrity dashboard request from HomeScreen."""
        logger.debug("Navigating to ChatScreen with integrity dashboard")
        with get_session() as session:
            service = IntegrityService()
            metrics = service.calculate_integrity_metrics(session)
            integrity_data = {
                "composite_score": metrics.composite_score,
                "letter_grade": metrics.letter_grade,
                "on_time_rate": metrics.on_time_rate,
                "notification_timeliness": metrics.notification_timeliness,
                "cleanup_completion_rate": metrics.cleanup_completion_rate,
                "current_streak_weeks": metrics.current_streak_weeks,
                "total_completed": metrics.total_completed,
                "total_on_time": metrics.total_on_time,
                "total_at_risk": metrics.total_at_risk,
                "total_abandoned": metrics.total_abandoned,
            }
        self.push_screen(
            ChatScreen(
                ChatScreenConfig(
                    initial_mode="integrity", initial_entity_type="", initial_data=integrity_data
                )
            )
        )

    def on_settings_screen_auth_status_changed(
        self, _message: SettingsScreen.AuthStatusChanged
    ) -> None:
        """Handle auth status change from SettingsScreen.

        This is informational - the actual AI config check happens when
        returning from settings via on_settings_screen_back.
        """
        logger.info("Authentication status changed")

    def on_nav_sidebar_selected(self, message: NavSidebar.Selected) -> None:
        """Handle navigation selection from NavSidebar.

        Routes sidebar selections to the appropriate view/screen.
        """
        item_id = message.item_id
        logger.debug(f"NavSidebar selection: {item_id}")

        # Map item IDs to handler methods
        handlers = {
            "chat": self._nav_to_chat,
            "goals": self._nav_to_goals,
            "commitments": self._nav_to_commitments,
            "visions": self._nav_to_visions,
            "milestones": self._nav_to_milestones,
            "hierarchy": self._nav_to_hierarchy,
            "integrity": self._nav_to_integrity,
            "orphans": self._nav_to_orphans,
            "triage": self._nav_to_triage,
            "settings": self._nav_to_settings,
        }

        handler = handlers.get(item_id)
        if handler:
            handler()

    def _nav_to_chat(self) -> None:
        """Navigate to chat screen."""
        self.push_screen(ChatScreen())

    def _nav_to_goals(self) -> None:
        """Navigate to goals list view."""
        with get_session() as session:
            goals = list(session.exec(select(Goal)).all())
            goal_items = [
                {
                    "id": str(g.id),
                    "title": g.title,
                    "problem_statement": g.problem_statement,
                    "status": g.status.value,
                }
                for g in goals
            ]
        self.push_screen(
            ChatScreen(
                ChatScreenConfig(
                    initial_mode="list", initial_entity_type="goal", initial_data=goal_items
                )
            )
        )

    def _nav_to_commitments(self) -> None:
        """Navigate to commitments list view."""
        with get_session() as session:
            results = list(session.exec(select(Commitment, Stakeholder).join(Stakeholder)).all())
            commitment_items = [
                {
                    "id": str(c.id),
                    "deliverable": c.deliverable,
                    "stakeholder_name": s.name,
                    "due_date": c.due_date.isoformat(),
                    "status": c.status.value,
                }
                for c, s in results
            ]
        self.push_screen(
            ChatScreen(
                ChatScreenConfig(
                    initial_mode="list",
                    initial_entity_type="commitment",
                    initial_data=commitment_items,
                )
            )
        )

    def _nav_to_visions(self) -> None:
        """Navigate to visions list view."""
        with get_session() as session:
            visions = list(session.exec(select(Vision)).all())
            vision_items = [
                {
                    "id": str(v.id),
                    "title": v.title,
                    "timeframe": v.timeframe,
                    "status": v.status.value,
                }
                for v in visions
            ]
        self.push_screen(
            ChatScreen(
                ChatScreenConfig(
                    initial_mode="list", initial_entity_type="vision", initial_data=vision_items
                )
            )
        )

    def _nav_to_milestones(self) -> None:
        """Navigate to milestones list view."""
        with get_session() as session:
            milestones = list(session.exec(select(Milestone)).all())
            milestone_items = [
                {
                    "id": str(m.id),
                    "description": m.description,
                    "target_date": m.target_date.isoformat(),
                    "status": m.status.value,
                }
                for m in milestones
            ]
        self.push_screen(
            ChatScreen(
                ChatScreenConfig(
                    initial_mode="list",
                    initial_entity_type="milestone",
                    initial_data=milestone_items,
                )
            )
        )

    def _nav_to_hierarchy(self) -> None:
        """Navigate to hierarchy view."""
        self.push_screen(ChatScreen())

    def _nav_to_integrity(self) -> None:
        """Navigate to integrity dashboard."""
        with get_session() as session:
            service = IntegrityService()
            metrics = service.calculate_integrity_metrics(session)
            integrity_data = {
                "composite_score": metrics.composite_score,
                "letter_grade": metrics.letter_grade,
                "on_time_rate": metrics.on_time_rate,
                "notification_timeliness": metrics.notification_timeliness,
                "cleanup_completion_rate": metrics.cleanup_completion_rate,
                "current_streak_weeks": metrics.current_streak_weeks,
                "total_completed": metrics.total_completed,
                "total_on_time": metrics.total_on_time,
                "total_at_risk": metrics.total_at_risk,
                "total_abandoned": metrics.total_abandoned,
            }
        self.push_screen(
            ChatScreen(
                ChatScreenConfig(
                    initial_mode="integrity", initial_entity_type="", initial_data=integrity_data
                )
            )
        )

    def _nav_to_orphans(self) -> None:
        """Navigate to orphan commitments view."""
        with get_session() as session:
            results = list(
                session.exec(
                    select(Commitment, Stakeholder)
                    .join(Stakeholder)
                    .where(Commitment.goal_id == None)  # noqa: E711
                ).all()
            )
            orphan_items = [
                {
                    "id": str(c.id),
                    "deliverable": c.deliverable,
                    "stakeholder_name": s.name,
                    "due_date": c.due_date.isoformat(),
                    "status": c.status.value,
                }
                for c, s in results
            ]
        self.push_screen(
            ChatScreen(
                ChatScreenConfig(
                    initial_mode="list",
                    initial_entity_type="commitment",
                    initial_data=orphan_items,
                )
            )
        )

    def _nav_to_triage(self) -> None:
        """Navigate to triage mode."""
        self.push_screen(ChatScreen(ChatScreenConfig(triage_mode=True)))

    def _nav_to_settings(self) -> None:
        """Navigate to settings screen."""
        self.push_screen(SettingsScreen())

    def on_hierarchy_view_item_selected(self, message: HierarchyView.ItemSelected) -> None:
        """Handle item selection from HierarchyView widget.

        Shows the selected item's details in a ChatScreen view.
        """
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

        self.push_screen(
            ChatScreen(
                ChatScreenConfig(
                    initial_mode="view",
                    initial_entity_type=entity_type,
                    initial_data=data,
                )
            )
        )


def main() -> None:
    """Run the application."""
    app = JdoApp()
    app.run()


if __name__ == "__main__":
    main()
