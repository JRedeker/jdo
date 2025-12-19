"""Live AI-driven E2E tests for JDO TUI.

These tests use real AI interactions to verify the complete user experience.
They require valid API credentials and are skipped if credentials are not available.

Run with: uv run pytest tests/e2e/test_live_ai.py -v -s
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import date, timedelta
from pathlib import Path

import pytest

from jdo.app import JdoApp
from jdo.auth.api import is_authenticated
from jdo.config.settings import get_settings, reset_settings
from jdo.db import create_db_and_tables, get_session
from jdo.db.engine import reset_engine
from jdo.models import Commitment, CommitmentStatus, Goal, GoalStatus, Stakeholder, StakeholderType
from jdo.models.draft import Draft, EntityType
from jdo.screens.chat import ChatScreen
from jdo.screens.home import HomeScreen
from jdo.screens.settings import SettingsScreen
from jdo.widgets.chat_message import ChatMessage


def has_ai_credentials() -> bool:
    """Check if valid AI credentials are available."""
    # Check environment variable first
    if os.environ.get("ANTHROPIC_API_KEY"):
        return True
    # Check auth store
    try:
        settings = get_settings()
        return is_authenticated(settings.ai_provider)
    except (OSError, ValueError, KeyError):
        return False


# Skip all tests in this module if no credentials
pytestmark = pytest.mark.skipif(
    not has_ai_credentials(),
    reason="No AI credentials available - set ANTHROPIC_API_KEY or configure API key in settings",
)


@pytest.fixture
def live_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[JdoApp]:
    """Create a JdoApp with real AI for live testing."""
    reset_engine()

    # Set up test database
    db_path = tmp_path / "live_test.db"
    monkeypatch.setenv("JDO_DATABASE_PATH", str(db_path))
    monkeypatch.setenv("JDO_AI_PROVIDER", "anthropic")
    monkeypatch.setenv("JDO_AI_MODEL", "claude-sonnet-4-20250514")
    monkeypatch.setenv("JDO_TIMEZONE", "America/New_York")
    monkeypatch.setenv("JDO_LOG_LEVEL", "INFO")

    reset_settings()
    create_db_and_tables()

    yield JdoApp()

    reset_engine()
    reset_settings()


@pytest.fixture
def seeded_live_app(
    live_app: JdoApp,
) -> JdoApp:
    """Create a live app with pre-seeded test data."""
    with get_session() as session:
        # Create stakeholders
        self_stakeholder = Stakeholder(name="Self", type=StakeholderType.SELF)
        boss = Stakeholder(name="Boss", type=StakeholderType.PERSON)
        session.add(self_stakeholder)
        session.add(boss)
        session.commit()
        session.refresh(self_stakeholder)
        session.refresh(boss)

        # Create a goal
        goal = Goal(
            title="Ship JDO v1.0",
            problem_statement="Need to deliver the initial version of JDO",
            solution_vision="A complete TUI app for commitment management",
            status=GoalStatus.ACTIVE,
        )
        session.add(goal)
        session.commit()
        session.refresh(goal)

        # Create an existing commitment
        commitment = Commitment(
            deliverable="Complete E2E testing",
            stakeholder_id=self_stakeholder.id,
            goal_id=goal.id,
            due_date=date.today() + timedelta(days=7),
            status=CommitmentStatus.IN_PROGRESS,
        )
        session.add(commitment)
        session.commit()

        # Create triage items (drafts with UNKNOWN type)
        triage_item = Draft(
            entity_type=EntityType.UNKNOWN,
            partial_data={"text": "Remember to review the API design"},
        )
        session.add(triage_item)
        session.commit()

    return live_app


def count_chat_messages(chat_screen: ChatScreen) -> int:
    """Count the number of chat messages in the screen."""
    return len(chat_screen.chat_container.query(ChatMessage))


class TestLiveAppStartup:
    """Test app startup with real AI."""

    async def test_app_starts_with_credentials(self, live_app: JdoApp) -> None:
        """App starts successfully when AI credentials are valid."""
        async with live_app.run_test() as pilot:
            await pilot.pause()

            # Should land on home screen (not AI required screen)
            assert isinstance(pilot.app.screen, HomeScreen)
            assert pilot.app.is_running

    async def test_navigate_to_chat(self, live_app: JdoApp) -> None:
        """Can navigate to chat screen."""
        async with live_app.run_test() as pilot:
            await pilot.pause()

            # Navigate to chat
            await pilot.press("n")
            await pilot.pause()

            assert isinstance(pilot.app.screen, ChatScreen)


class TestLiveAIConversation:
    """Test real AI conversations in the TUI."""

    async def test_simple_greeting(self, live_app: JdoApp) -> None:
        """AI responds to a simple greeting."""
        async with live_app.run_test() as pilot:
            await pilot.pause()

            # Navigate to chat
            await pilot.press("n")
            await pilot.pause()

            chat_screen = pilot.app.screen
            assert isinstance(chat_screen, ChatScreen)

            # Type a simple message using the TextArea's text property
            prompt = chat_screen.prompt_input
            prompt.load_text("Hello! What can you help me with?")
            await pilot.press("ctrl+enter")  # Submit with ctrl+enter

            # Wait for AI response (with pauses to allow processing)
            for _ in range(30):  # Max 30 seconds
                await pilot.pause(delay=1.0)
                # Check if there are messages in the chat
                msg_count = count_chat_messages(chat_screen)
                if msg_count >= 2:  # User message + AI response
                    break

            # Verify we got a response
            msg_count = count_chat_messages(chat_screen)
            assert msg_count >= 2, "Should have user message and AI response"

    async def test_help_command(self, live_app: JdoApp) -> None:
        """Help command shows available commands."""
        async with live_app.run_test() as pilot:
            await pilot.pause()

            # Navigate to chat
            await pilot.press("n")
            await pilot.pause()

            chat_screen = pilot.app.screen
            assert isinstance(chat_screen, ChatScreen)

            # Type /help command
            prompt = chat_screen.prompt_input
            prompt.load_text("/help")
            await pilot.press("ctrl+enter")
            await pilot.pause()

            # Check for help output in messages
            msg_count = count_chat_messages(chat_screen)
            assert msg_count >= 2, "Should have command and response"


class TestLiveCommitmentCreation:
    """Test creating commitments with real AI assistance."""

    async def test_create_commitment_flow(self, seeded_live_app: JdoApp) -> None:
        """Create a commitment through conversation with AI."""
        async with seeded_live_app.run_test() as pilot:
            await pilot.pause()

            # Navigate to chat
            await pilot.press("n")
            await pilot.pause()

            chat_screen = pilot.app.screen
            assert isinstance(chat_screen, ChatScreen)

            # Request to create a commitment
            prompt = chat_screen.prompt_input
            prompt.load_text("I need to finish the documentation by next Friday for my boss")
            await pilot.press("ctrl+enter")

            # Wait for AI processing
            for _ in range(45):  # Max 45 seconds
                await pilot.pause(delay=1.0)
                msg_count = count_chat_messages(chat_screen)
                if msg_count >= 2:
                    break

            # Should have a response
            msg_count = count_chat_messages(chat_screen)
            assert msg_count >= 2

    async def test_list_commitments(self, seeded_live_app: JdoApp) -> None:
        """List commitments shows existing data."""
        async with seeded_live_app.run_test() as pilot:
            await pilot.pause()

            # Navigate to chat
            await pilot.press("n")
            await pilot.pause()

            chat_screen = pilot.app.screen
            assert isinstance(chat_screen, ChatScreen)

            # Use /list command
            prompt = chat_screen.prompt_input
            prompt.load_text("/list commitments")
            await pilot.press("ctrl+enter")
            await pilot.pause()

            # Check response
            msg_count = count_chat_messages(chat_screen)
            assert msg_count >= 2


class TestLiveSettingsFlow:
    """Test settings and authentication flows."""

    async def test_settings_back_navigation(self, live_app: JdoApp) -> None:
        """Navigate to settings and back without errors.

        This is a regression test for the NoActiveWorker bug.
        """
        async with live_app.run_test() as pilot:
            await pilot.pause()

            # Should be on home
            assert isinstance(pilot.app.screen, HomeScreen)

            # Go to settings
            await pilot.press("s")
            await pilot.pause()

            assert isinstance(pilot.app.screen, SettingsScreen)

            # Go back - this previously crashed with NoActiveWorker
            await pilot.press("escape")
            await pilot.pause()

            # Should be back on home without errors
            assert isinstance(pilot.app.screen, HomeScreen)
            assert pilot.app.is_running


class TestLiveTriageFlow:
    """Test triage mode with real AI."""

    async def test_triage_mode_startup(self, seeded_live_app: JdoApp) -> None:
        """Triage mode starts and shows current status."""
        async with seeded_live_app.run_test() as pilot:
            await pilot.pause()

            # Start triage mode
            await pilot.press("t")
            await pilot.pause()

            chat_screen = pilot.app.screen
            assert isinstance(chat_screen, ChatScreen)

            # App should be in triage mode
            assert chat_screen._triage_mode


class TestLiveIntegrityDashboard:
    """Test integrity dashboard with real data."""

    async def test_integrity_view(self, seeded_live_app: JdoApp) -> None:
        """Integrity dashboard shows metrics."""
        async with seeded_live_app.run_test() as pilot:
            await pilot.pause()

            # Press 'i' for integrity
            await pilot.press("i")
            await pilot.pause()

            chat_screen = pilot.app.screen
            assert isinstance(chat_screen, ChatScreen)


class TestLiveErrorRecovery:
    """Test error handling and recovery with real AI."""

    async def test_invalid_command_recovery(self, live_app: JdoApp) -> None:
        """App recovers gracefully from invalid commands."""
        async with live_app.run_test() as pilot:
            await pilot.pause()

            await pilot.press("n")
            await pilot.pause()

            chat_screen = pilot.app.screen
            assert isinstance(chat_screen, ChatScreen)

            # Try an invalid command
            prompt = chat_screen.prompt_input
            prompt.load_text("/nonexistent_command")
            await pilot.press("ctrl+enter")
            await pilot.pause()

            # App should still be running and responsive
            assert pilot.app.is_running

            # Should have an error message
            msg_count = count_chat_messages(chat_screen)
            assert msg_count >= 2

    async def test_escape_from_any_screen(self, live_app: JdoApp) -> None:
        """Escape key works from any screen to go back."""
        async with live_app.run_test() as pilot:
            await pilot.pause()

            # Home -> Chat
            await pilot.press("n")
            await pilot.pause()
            assert isinstance(pilot.app.screen, ChatScreen)

            # Chat -> Home
            await pilot.press("escape")
            await pilot.pause()
            assert isinstance(pilot.app.screen, HomeScreen)

            # Home -> Settings
            await pilot.press("s")
            await pilot.pause()

            assert isinstance(pilot.app.screen, SettingsScreen)

            # Settings -> Home
            await pilot.press("escape")
            await pilot.pause()
            assert isinstance(pilot.app.screen, HomeScreen)
