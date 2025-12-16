"""TUI application tests.

Tests for JdoApp - the main application shell that integrates
all screens and manages the application lifecycle.
"""

import pytest
from textual.widgets import Footer, Header

from jdo.app import JdoApp
from jdo.screens.chat import ChatScreen
from jdo.screens.home import HomeScreen
from jdo.screens.settings import SettingsScreen


@pytest.mark.tui
class TestAppStartup:
    """Tests for JdoApp startup behavior."""

    async def test_app_starts_successfully(self, app: JdoApp) -> None:
        """App starts without errors."""
        async with app.run_test() as pilot:
            # App should be running
            assert pilot.app is not None
            assert pilot.app.is_running

    async def test_app_has_header(self, app: JdoApp) -> None:
        """App displays header widget with title."""
        async with app.run_test() as pilot:
            header = pilot.app.query_one(Header)
            assert header is not None

    async def test_app_has_footer(self, app: JdoApp) -> None:
        """App displays footer with key bindings."""
        async with app.run_test() as pilot:
            footer = pilot.app.query_one(Footer)
            assert footer is not None

    async def test_app_shows_home_screen_on_startup(self, app: JdoApp) -> None:
        """App shows HomeScreen after startup."""
        async with app.run_test() as pilot:
            # The screen stack should have HomeScreen as the active screen
            assert isinstance(pilot.app.screen, HomeScreen)

    async def test_app_title_is_jdo(self, app: JdoApp) -> None:
        """App title is 'JDO'."""
        async with app.run_test() as pilot:
            assert pilot.app.TITLE == "JDO"


@pytest.mark.tui
class TestScreenNavigation:
    """Tests for screen navigation."""

    async def test_n_key_navigates_to_chat(self, app: JdoApp) -> None:
        """'n' key on Home navigates to Chat screen."""
        async with app.run_test() as pilot:
            # Start at home
            assert isinstance(pilot.app.screen, HomeScreen)

            # Press 'n' to start new chat
            await pilot.press("n")
            await pilot.pause()

            # Should be on ChatScreen
            assert isinstance(pilot.app.screen, ChatScreen)

    async def test_s_key_navigates_to_settings(self, app: JdoApp) -> None:
        """'s' key on Home navigates to Settings screen."""
        async with app.run_test() as pilot:
            # Start at home
            assert isinstance(pilot.app.screen, HomeScreen)

            # Press 's' to open settings
            await pilot.press("s")
            await pilot.pause()

            # Should be on SettingsScreen
            assert isinstance(pilot.app.screen, SettingsScreen)

    async def test_escape_on_chat_returns_to_home(self, app: JdoApp) -> None:
        """Escape on Chat returns to Home screen."""
        async with app.run_test() as pilot:
            # Navigate to chat first
            await pilot.press("n")
            await pilot.pause()
            assert isinstance(pilot.app.screen, ChatScreen)

            # Press escape to go back
            await pilot.press("escape")
            await pilot.pause()

            # Should be back on HomeScreen
            assert isinstance(pilot.app.screen, HomeScreen)

    async def test_escape_on_settings_returns_to_home(self, app: JdoApp) -> None:
        """Escape on Settings returns to Home screen."""
        async with app.run_test() as pilot:
            # Navigate to settings first
            await pilot.press("s")
            await pilot.pause()
            assert isinstance(pilot.app.screen, SettingsScreen)

            # Press escape to go back
            await pilot.press("escape")
            await pilot.pause()

            # Should be back on HomeScreen
            assert isinstance(pilot.app.screen, HomeScreen)


@pytest.mark.tui
class TestKeyBindings:
    """Tests for keyboard shortcuts."""

    async def test_quit_with_q(self, app: JdoApp) -> None:
        """Pressing q quits the application."""
        async with app.run_test() as pilot:
            await pilot.press("q")
            await pilot.pause()
            # App should have exited or be exiting
            # In test mode, we check that quit was triggered
            assert not pilot.app.is_running or pilot.app._exit

    async def test_toggle_dark_with_d(self, app: JdoApp) -> None:
        """Pressing d toggles dark mode."""
        async with app.run_test() as pilot:
            initial_theme = pilot.app.theme
            await pilot.press("d")
            await pilot.pause()
            # Theme should have changed
            assert pilot.app.theme != initial_theme

    async def test_escape_on_home_does_nothing(self, app: JdoApp) -> None:
        """Escape on Home screen does nothing (no screen to pop)."""
        async with app.run_test() as pilot:
            # Start at home
            assert isinstance(pilot.app.screen, HomeScreen)

            # Press escape - should stay on home
            await pilot.press("escape")
            await pilot.pause()

            # Still on HomeScreen
            assert isinstance(pilot.app.screen, HomeScreen)


@pytest.mark.tui
class TestDatabaseInitialization:
    """Tests for database initialization on startup."""

    async def test_database_initialized_on_startup(self, app: JdoApp, tmp_path) -> None:
        """Database tables are created on app startup."""
        from pathlib import Path

        async with app.run_test() as pilot:
            # App should have initialized the database
            # Check that the database file exists (if not in-memory)
            db_path = Path(pilot.app._db_path) if hasattr(pilot.app, "_db_path") else None
            if db_path and db_path.exists():
                assert db_path.stat().st_size > 0


@pytest.mark.tui
class TestMessageHandlers:
    """Tests for message handlers that route screen navigation."""

    async def test_new_chat_message_navigates_to_chat(self, app: JdoApp) -> None:
        """HomeScreen.NewChat message triggers navigation to Chat."""
        async with app.run_test() as pilot:
            home_screen = pilot.app.screen
            assert isinstance(home_screen, HomeScreen)

            # Post the message directly
            home_screen.post_message(HomeScreen.NewChat())
            await pilot.pause()

            # Should navigate to ChatScreen
            assert isinstance(pilot.app.screen, ChatScreen)

    async def test_open_settings_message_navigates_to_settings(self, app: JdoApp) -> None:
        """HomeScreen.OpenSettings message triggers navigation to Settings."""
        async with app.run_test() as pilot:
            home_screen = pilot.app.screen
            assert isinstance(home_screen, HomeScreen)

            # Post the message directly
            home_screen.post_message(HomeScreen.OpenSettings())
            await pilot.pause()

            # Should navigate to SettingsScreen
            assert isinstance(pilot.app.screen, SettingsScreen)

    async def test_settings_back_message_returns_to_home(self, app: JdoApp) -> None:
        """SettingsScreen.Back message triggers return to Home."""
        async with app.run_test() as pilot:
            # Navigate to settings first
            await pilot.press("s")
            await pilot.pause()

            settings_screen = pilot.app.screen
            assert isinstance(settings_screen, SettingsScreen)

            # Post the Back message
            settings_screen.post_message(SettingsScreen.Back())
            await pilot.pause()

            # Should be back on HomeScreen
            assert isinstance(pilot.app.screen, HomeScreen)


@pytest.mark.tui
class TestDraftRestoration:
    """Tests for draft restoration on startup."""

    async def test_no_prompt_when_no_pending_drafts(self, app: JdoApp) -> None:
        """No restore prompt when there are no pending drafts."""
        async with app.run_test() as pilot:
            # App should show home screen directly, not a modal
            assert isinstance(pilot.app.screen, HomeScreen)
            # No modal dialog should be displayed
            assert not pilot.app.screen.query("ModalScreen")

    async def test_pending_draft_shows_restore_prompt(
        self, app: JdoApp, tmp_path, monkeypatch
    ) -> None:
        """Pending draft triggers restore prompt on startup."""
        from jdo.db import create_db_and_tables, get_session
        from jdo.models.draft import Draft, EntityType

        # Create a draft in the database before starting the app
        create_db_and_tables()
        with get_session() as session:
            draft = Draft(
                entity_type=EntityType.COMMITMENT,
                partial_data={"title": "Test draft"},
            )
            session.add(draft)
            session.commit()

        async with app.run_test() as pilot:
            await pilot.pause()
            # Should show a restore prompt modal
            from jdo.screens.draft_restore import DraftRestoreScreen

            assert isinstance(pilot.app.screen, DraftRestoreScreen)

    async def test_restore_choice_opens_chat_with_draft(
        self, app: JdoApp, tmp_path, monkeypatch
    ) -> None:
        """Choosing restore opens Chat screen with draft loaded."""
        from jdo.db import create_db_and_tables, get_session
        from jdo.models.draft import Draft, EntityType

        # Create a draft in the database
        create_db_and_tables()
        with get_session() as session:
            draft = Draft(
                entity_type=EntityType.COMMITMENT,
                partial_data={"deliverable": "Test deliverable"},
            )
            session.add(draft)
            session.commit()
            draft_id = draft.id

        async with app.run_test() as pilot:
            await pilot.pause()

            # Modal should be showing
            from jdo.screens.draft_restore import DraftRestoreScreen

            assert isinstance(pilot.app.screen, DraftRestoreScreen)

            # Click restore button
            await pilot.press("r")
            await pilot.pause()

            # Should now be on ChatScreen with draft
            assert isinstance(pilot.app.screen, ChatScreen)
            # The draft should be accessible via the screen
            assert pilot.app.screen._draft_id == draft_id

    async def test_discard_choice_deletes_draft(self, app: JdoApp, tmp_path, monkeypatch) -> None:
        """Choosing discard deletes the draft and goes to home."""
        from jdo.db import create_db_and_tables, get_session
        from jdo.models.draft import Draft, EntityType

        # Create a draft in the database
        create_db_and_tables()
        with get_session() as session:
            draft = Draft(
                entity_type=EntityType.COMMITMENT,
                partial_data={"deliverable": "Test deliverable"},
            )
            session.add(draft)
            session.commit()
            draft_id = draft.id

        async with app.run_test() as pilot:
            await pilot.pause()

            # Modal should be showing
            from jdo.screens.draft_restore import DraftRestoreScreen

            assert isinstance(pilot.app.screen, DraftRestoreScreen)

            # Click discard button
            await pilot.press("d")
            await pilot.pause()

            # Should now be on HomeScreen
            assert isinstance(pilot.app.screen, HomeScreen)

            # Draft should be deleted
            from jdo.db import get_session

            with get_session() as session:
                deleted_draft = session.get(Draft, draft_id)
                assert deleted_draft is None


@pytest.mark.tui
class TestVisionReviews:
    """Tests for vision review prompts on startup."""

    async def test_no_notification_when_no_reviews_due(self, app: JdoApp) -> None:
        """No vision review notification when no reviews are due."""
        async with app.run_test() as pilot:
            # App should show home screen directly
            assert isinstance(pilot.app.screen, HomeScreen)
            # No special notification or modal should be displayed
            assert pilot.app.is_running

    async def test_vision_due_for_review_shows_notification(
        self, app: JdoApp, tmp_path, monkeypatch
    ) -> None:
        """Vision due for review shows notification on startup."""
        from datetime import UTC, date, datetime, timedelta

        from jdo.db import create_db_and_tables, get_session
        from jdo.models.vision import Vision, VisionStatus

        # Create a vision that's due for review (review date in the past)
        create_db_and_tables()
        with get_session() as session:
            vision = Vision(
                title="Test Vision",
                narrative="A test vision narrative",
                status=VisionStatus.ACTIVE,
                next_review_date=date.today() - timedelta(days=1),
            )
            session.add(vision)
            session.commit()

        async with app.run_test() as pilot:
            await pilot.pause()

            # Home screen should show, but with a review notification
            assert isinstance(pilot.app.screen, HomeScreen)
            # The app should have tracked the vision for review
            assert len(pilot.app._visions_due_for_review) == 1

    async def test_dismissing_notification_snoozes_for_session(
        self, app: JdoApp, tmp_path, monkeypatch
    ) -> None:
        """Dismissing review notification snoozes it for the session."""
        from datetime import date, timedelta

        from jdo.db import create_db_and_tables, get_session
        from jdo.models.vision import Vision, VisionStatus

        # Create a vision that's due for review
        create_db_and_tables()
        with get_session() as session:
            vision = Vision(
                title="Test Vision",
                narrative="A test vision narrative",
                status=VisionStatus.ACTIVE,
                next_review_date=date.today() - timedelta(days=1),
            )
            session.add(vision)
            session.commit()
            vision_id = vision.id

        async with app.run_test() as pilot:
            await pilot.pause()

            # Snooze the review
            pilot.app.snooze_vision_review(vision_id)

            # Vision should be in snoozed set
            assert vision_id in pilot.app._snoozed_reviews

    async def test_snoozed_review_not_shown_again(self, app: JdoApp, tmp_path, monkeypatch) -> None:
        """Snoozed review doesn't show up in notifications."""
        from datetime import date, timedelta

        from jdo.db import create_db_and_tables, get_session
        from jdo.models.vision import Vision, VisionStatus

        # Create a vision that's due for review
        create_db_and_tables()
        with get_session() as session:
            vision = Vision(
                title="Test Vision",
                narrative="A test vision narrative",
                status=VisionStatus.ACTIVE,
                next_review_date=date.today() - timedelta(days=1),
            )
            session.add(vision)
            session.commit()
            vision_id = vision.id

        async with app.run_test() as pilot:
            await pilot.pause()

            # Snooze the review
            pilot.app.snooze_vision_review(vision_id)

            # Get unsnoozed reviews (should be empty)
            unsnoozed = pilot.app.get_unsnoozed_reviews()
            assert len(unsnoozed) == 0
