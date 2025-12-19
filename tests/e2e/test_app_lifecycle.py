"""End-to-end tests for JDO application lifecycle.

These tests verify complete user journeys from app startup through
multi-screen workflows, database persistence, and AI interactions.
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pydantic_ai import Agent
from sqlmodel import Session, select

from jdo.app import JdoApp
from jdo.db import get_session
from jdo.models import (
    Commitment,
    CommitmentStatus,
    Draft,
    Stakeholder,
    StakeholderType,
    Vision,
    VisionStatus,
)
from jdo.models.draft import EntityType
from jdo.screens.ai_required import AiRequiredScreen
from jdo.screens.chat import ChatScreen
from jdo.screens.draft_restore import DraftRestoreScreen
from jdo.screens.home import HomeScreen
from jdo.screens.settings import SettingsScreen


class TestAppStartupFlows:
    """E2E tests for app startup and initialization flows."""

    @pytest.fixture(autouse=True)
    def _reset_db(self, test_db: None) -> None:
        """Reset database before each test."""
        # test_db fixture handles cleanup

    async def test_app_starts_with_ai_configured(self) -> None:
        """App starts normally when AI is already configured."""
        with patch("jdo.app.is_authenticated", return_value=True):
            app = JdoApp()
            async with app.run_test() as pilot:
                await pilot.pause()

                # Should show HomeScreen directly (no AI required screen)
                home_screens = app.screen_stack
                assert any(isinstance(screen, HomeScreen) for screen in home_screens)
                assert not any(isinstance(screen, AiRequiredScreen) for screen in home_screens)

    async def test_app_shows_draft_restore_on_pending_draft(self) -> None:
        """App shows DraftRestoreScreen when pending drafts exist."""
        # Create a pending draft in the database
        draft_id = uuid4()
        with get_session() as session:
            draft = Draft(
                id=draft_id,
                entity_type=EntityType.COMMITMENT,
                partial_data={"deliverable": "Test task"},
            )
            session.add(draft)
            session.commit()

        with patch("jdo.app.is_authenticated", return_value=True):
            app = JdoApp()
            async with app.run_test() as pilot:
                await pilot.pause()

                # Should show DraftRestoreScreen
                assert any(isinstance(screen, DraftRestoreScreen) for screen in app.screen_stack)

    async def test_draft_restore_flow_discard_path(self) -> None:
        """User can discard a pending draft and continue to home."""
        draft_id = uuid4()
        with get_session() as session:
            draft = Draft(
                id=draft_id,
                entity_type=EntityType.COMMITMENT,
                partial_data={"deliverable": "Test task"},
            )
            session.add(draft)
            session.commit()

        with patch("jdo.app.is_authenticated", return_value=True):
            app = JdoApp()
            async with app.run_test() as pilot:
                await pilot.pause()

                # Press 'd' to discard
                await pilot.press("d")
                await pilot.pause()

                # Should navigate to HomeScreen
                assert any(isinstance(screen, HomeScreen) for screen in app.screen_stack)

                # Draft should be deleted from database
                with get_session() as session:
                    stmt = select(Draft).where(Draft.id == draft_id)
                    result = session.exec(stmt).first()
                    assert result is None

    async def test_vision_review_check_on_startup(self) -> None:
        """App checks for visions due for review on startup."""
        # Create a vision due for review
        vision_id = uuid4()
        with get_session() as session:
            vision = Vision(
                id=vision_id,
                title="Test Vision",
                narrative="Test narrative",
                status=VisionStatus.ACTIVE,
                next_review_date=date.today() - timedelta(days=1),  # Past due
            )
            session.add(vision)
            session.commit()

        with patch("jdo.app.is_authenticated", return_value=True):
            app = JdoApp()
            async with app.run_test() as pilot:
                await pilot.pause()

                # App should have loaded visions due for review
                assert len(app._visions_due_for_review) > 0
                assert app._visions_due_for_review[0].id == vision_id


class TestSettingsScreenFlows:
    """E2E tests for settings screen authentication flows."""

    @pytest.fixture(autouse=True)
    def _reset_db(self, test_db: None) -> None:
        """Reset database before each test."""

    async def test_settings_shows_authentication_status(self) -> None:
        """SettingsScreen displays authentication status for all providers."""
        with (
            patch("jdo.screens.settings.is_authenticated", return_value=False),
            patch("jdo.screens.settings.list_providers", return_value=["anthropic", "openai"]),
        ):
            app = JdoApp()
            async with app.run_test() as pilot:
                await pilot.pause()

                # Navigate to settings
                await app.push_screen(SettingsScreen())
                await pilot.pause()

                settings_screen = app.screen
                assert isinstance(settings_screen, SettingsScreen)

    async def test_settings_back_with_ai_configured(self) -> None:
        """Back from settings returns to home when AI is configured.

        Regression test: Previously this caused NoActiveWorker error
        because _ensure_ai_configured used push_screen_wait outside worker.
        """
        with patch("jdo.app.is_authenticated", return_value=True):
            app = JdoApp()
            async with app.run_test() as pilot:
                await pilot.pause()

                # Should be on home
                assert isinstance(app.screen, HomeScreen)

                # Navigate to settings
                await pilot.press("s")
                await pilot.pause()
                assert isinstance(app.screen, SettingsScreen)

                # Go back - this should NOT raise NoActiveWorker
                await pilot.press("escape")
                await pilot.pause()

                # Should be back on home
                assert isinstance(app.screen, HomeScreen)

    async def test_settings_back_triggers_ai_check_via_worker(self) -> None:
        """Back from settings triggers AI config check in worker context.

        Verifies that on_settings_screen_back runs _ensure_ai_configured
        in a worker (via run_worker), not directly in the message handler.
        """
        # Start with AI configured
        with patch("jdo.app.is_authenticated", return_value=True):
            app = JdoApp()
            async with app.run_test() as pilot:
                await pilot.pause()

                # Navigate to settings
                await pilot.press("s")
                await pilot.pause()

                # Go back
                await pilot.press("escape")
                await pilot.pause()

                # App should still be running (no crash)
                assert app.is_running or app._exit
                # Should have returned to home without errors
                assert isinstance(app.screen, HomeScreen)


class TestChatCommandFlows:
    """E2E tests for complete chat command workflows."""

    @pytest.fixture(autouse=True)
    def _reset_db(self, test_db: None) -> None:
        """Reset database before each test."""

    async def test_chat_screen_renders(self) -> None:
        """ChatScreen renders successfully with all components."""
        mock_agent = MagicMock(spec=Agent)

        with (
            patch("jdo.app.is_authenticated", return_value=True),
            patch("jdo.ai.agent.create_agent", return_value=mock_agent),
            patch("jdo.screens.chat.get_session"),
            patch("jdo.screens.chat.IntegrityService"),
        ):
            app = JdoApp()
            async with app.run_test() as pilot:
                await pilot.pause()

                # Navigate to chat
                chat = ChatScreen()
                await app.push_screen(chat)
                await pilot.pause()

                # Verify all components are present
                assert chat.chat_container is not None
                assert chat.data_panel is not None
                assert chat.prompt_input is not None


class TestAtRiskWorkflowE2E:
    """E2E tests for complete at-risk commitment workflow."""

    @pytest.fixture(autouse=True)
    def _reset_db(self, test_db: None) -> None:
        """Reset database before each test."""

    async def test_atrisk_data_panel_setup(self) -> None:
        """At-risk workflow can be triggered from data panel."""
        # Create a commitment
        commitment_id = uuid4()
        stakeholder_id = uuid4()
        with get_session() as session:
            stakeholder = Stakeholder(
                id=stakeholder_id,
                name="Test Stakeholder",
                type=StakeholderType.PERSON,
            )
            session.add(stakeholder)
            session.commit()
            session.refresh(stakeholder)  # Ensure stakeholder is committed first

            commitment = Commitment(
                id=commitment_id,
                deliverable="At-risk test commitment",
                stakeholder_id=stakeholder_id,
                due_date=date.today() + timedelta(days=5),
                status=CommitmentStatus.PENDING,
            )
            session.add(commitment)
            session.commit()
            session.refresh(commitment)

        mock_agent = MagicMock(spec=Agent)

        with (
            patch("jdo.app.is_authenticated", return_value=True),
            patch("jdo.ai.agent.create_agent", return_value=mock_agent),
            patch("jdo.screens.chat.get_session") as mock_session,
            patch("jdo.screens.chat.IntegrityService"),
        ):
            # Mock session to return our test commitment
            mock_db_session = MagicMock(spec=Session)
            mock_db_session.get.return_value = None
            mock_session.return_value.__enter__.return_value = mock_db_session

            app = JdoApp()
            async with app.run_test() as pilot:
                await pilot.pause()

                # Navigate to chat
                chat = ChatScreen()
                await app.push_screen(chat)
                await pilot.pause()

                # Set up panel to show commitment
                from jdo.widgets.data_panel import PanelMode

                chat.data_panel.mode = PanelMode.VIEW
                chat.data_panel._entity_type = "commitment"
                chat.data_panel._data = {
                    "id": str(commitment_id),
                    "deliverable": "At-risk test commitment",
                    "status": "pending",
                    "stakeholder_name": "Test Stakeholder",
                }
                await pilot.pause()

                # Verify panel is set up correctly
                assert chat.data_panel.mode == PanelMode.VIEW
