"""Tests for the REPL loop module."""

from unittest.mock import MagicMock, patch

import pytest

from jdo.repl.loop import (
    FIRST_RUN_MESSAGE,
    GOODBYE_MESSAGE,
    NO_CREDENTIALS_MESSAGE,
    WELCOME_MESSAGE,
    _get_at_risk_commitments,
    _handle_confirmation,
    _is_first_run,
    _show_startup_guidance,
    check_credentials,
    handle_slash_command,
)
from jdo.repl.session import Session


class TestSessionBasics:
    """Basic tests for Session (detailed tests in test_session.py)."""

    def test_initial_state(self):
        """Session starts with empty state."""
        session = Session()

        assert session.message_history == []
        assert session.entity_context.is_set is False
        assert session.pending_draft is None

    def test_add_user_message(self):
        """Add user message to history."""
        session = Session()
        session.add_user_message("Hello")

        assert len(session.message_history) == 1
        assert session.message_history[0] == {"role": "user", "content": "Hello"}

    def test_add_assistant_message(self):
        """Add assistant message to history."""
        session = Session()
        session.add_assistant_message("Hi there!")

        assert len(session.message_history) == 1
        assert session.message_history[0] == {"role": "assistant", "content": "Hi there!"}

    def test_message_history_ordering(self):
        """Messages maintain order."""
        session = Session()
        session.add_user_message("First")
        session.add_assistant_message("Second")
        session.add_user_message("Third")

        assert len(session.message_history) == 3
        assert session.message_history[0]["content"] == "First"
        assert session.message_history[1]["content"] == "Second"
        assert session.message_history[2]["content"] == "Third"

    def test_clear_pending_draft(self):
        """Clear pending draft."""
        session = Session()
        session.set_pending_draft("create", "commitment", {"data": {}})

        session.clear_pending_draft()

        assert session.pending_draft is None


class TestCheckCredentials:
    """Tests for credential checking."""

    def test_returns_true_when_authenticated(self):
        """Returns True when provider is authenticated."""
        with (
            patch("jdo.repl.loop.is_authenticated", return_value=True),
            patch("jdo.repl.loop.get_settings") as mock_settings,
        ):
            mock_settings.return_value.ai_provider = "openai"
            assert check_credentials() is True

    def test_returns_false_when_not_authenticated(self):
        """Returns False when provider is not authenticated."""
        with (
            patch("jdo.repl.loop.is_authenticated", return_value=False),
            patch("jdo.repl.loop.get_settings") as mock_settings,
        ):
            mock_settings.return_value.ai_provider = "openai"
            assert check_credentials() is False


class TestSlashCommands:
    """Tests for slash command handling."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        from unittest.mock import MagicMock

        return MagicMock()

    async def test_help_command(self, mock_db_session, capsys):
        """Help command prints available commands."""
        session = Session()
        result = await handle_slash_command("/help", session, mock_db_session)

        assert result is True

    async def test_list_command_returns_true(self, mock_db_session):
        """List command returns True (handled)."""
        session = Session()
        # Mock the database query to return empty list
        mock_db_session.exec.return_value.all.return_value = []
        result = await handle_slash_command("/list", session, mock_db_session)

        assert result is True

    async def test_commit_command_shows_usage(self, mock_db_session):
        """Commit command without args shows usage."""
        session = Session()
        result = await handle_slash_command("/commit", session, mock_db_session)

        assert result is True

    async def test_complete_command_not_implemented(self, mock_db_session):
        """Complete command shows not implemented message."""
        session = Session()
        result = await handle_slash_command("/complete", session, mock_db_session)

        assert result is True

    async def test_unknown_command(self, mock_db_session):
        """Unknown command shows error message."""
        session = Session()
        result = await handle_slash_command("/unknown", session, mock_db_session)

        assert result is True  # Still returns True to indicate command was handled

    async def test_command_case_insensitive(self, mock_db_session):
        """Commands are case insensitive."""
        session = Session()
        mock_db_session.exec.return_value.all.return_value = []

        # All should work without error
        assert await handle_slash_command("/HELP", session, mock_db_session) is True
        assert await handle_slash_command("/Help", session, mock_db_session) is True
        assert await handle_slash_command("/LIST", session, mock_db_session) is True

    @patch("jdo.repl.loop.get_visions_due_for_review")
    async def test_review_command_no_visions(self, mock_visions, mock_db_session):
        """Review command with no visions due shows message."""
        mock_visions.return_value = []
        session = Session()

        result = await handle_slash_command("/review", session, mock_db_session)

        assert result is True

    @patch("jdo.repl.loop.get_visions_due_for_review")
    async def test_review_command_with_vision(self, mock_visions, mock_db_session):
        """Review command with vision due displays and marks reviewed."""
        from uuid import uuid4

        mock_vision = MagicMock()
        mock_vision.id = uuid4()
        mock_vision.title = "Test Vision"
        mock_vision.narrative = "A test narrative"
        mock_vision.timeframe = "2025"
        mock_vision.why_it_matters = "Testing"
        mock_vision.metrics = ["Metric 1"]
        mock_vision.next_review_date = "2025-04-12"
        mock_visions.return_value = [mock_vision]

        session = Session()

        result = await handle_slash_command("/review", session, mock_db_session)

        assert result is True
        mock_vision.complete_review.assert_called_once()
        mock_db_session.add.assert_called_with(mock_vision)
        mock_db_session.commit.assert_called_once()


class TestMessages:
    """Tests for REPL messages."""

    def test_welcome_message_content(self):
        """Welcome message contains expected text."""
        assert "JDO" in WELCOME_MESSAGE
        assert "exit" in WELCOME_MESSAGE or "quit" in WELCOME_MESSAGE

    def test_goodbye_message_content(self):
        """Goodbye message exists."""
        assert len(GOODBYE_MESSAGE) > 0

    def test_no_credentials_message_content(self):
        """No credentials message contains guidance."""
        assert "OPENAI_API_KEY" in NO_CREDENTIALS_MESSAGE or "API" in NO_CREDENTIALS_MESSAGE


class TestConfirmationFlow:
    """Tests for the confirmation flow."""

    @pytest.fixture
    def session_with_draft(self):
        """Create a session with a pending commitment draft."""
        session = Session()
        session.set_pending_draft(
            action="create",
            entity_type="commitment",
            data={
                "deliverable": "Send report",
                "stakeholder": "Sarah",
                "due_date": "2025-01-17",
            },
        )
        return session

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        mock_session = MagicMock()
        mock_session.commit = MagicMock()
        return mock_session

    def test_no_pending_draft_returns_false(self, mock_db_session):
        """Returns False when no pending draft exists."""
        session = Session()
        result = _handle_confirmation("yes", session, mock_db_session)
        assert result is False

    def test_affirmative_yes(self, session_with_draft, mock_db_session):
        """'yes' confirms the draft."""
        # Mock the persistence service
        with patch("jdo.repl.loop.PersistenceService") as mock_persistence_class:
            mock_persistence = MagicMock()
            mock_commitment = MagicMock()
            mock_commitment.id = "test-id-1234"
            mock_commitment.deliverable = "Send report"
            mock_persistence.save_commitment.return_value = mock_commitment
            mock_persistence_class.return_value = mock_persistence

            result = _handle_confirmation("yes", session_with_draft, mock_db_session)

            assert result is True
            assert session_with_draft.pending_draft is None  # Cleared after confirmation
            mock_persistence.save_commitment.assert_called_once()

    def test_affirmative_y(self, session_with_draft, mock_db_session):
        """'y' confirms the draft."""
        with patch("jdo.repl.loop.PersistenceService") as mock_persistence_class:
            mock_persistence = MagicMock()
            mock_commitment = MagicMock()
            mock_commitment.id = "test-id"
            mock_commitment.deliverable = "Send report"
            mock_persistence.save_commitment.return_value = mock_commitment
            mock_persistence_class.return_value = mock_persistence

            result = _handle_confirmation("y", session_with_draft, mock_db_session)
            assert result is True

    def test_affirmative_looks_good(self, session_with_draft, mock_db_session):
        """'looks good' confirms the draft."""
        with patch("jdo.repl.loop.PersistenceService") as mock_persistence_class:
            mock_persistence = MagicMock()
            mock_commitment = MagicMock()
            mock_commitment.id = "test-id"
            mock_commitment.deliverable = "Send report"
            mock_persistence.save_commitment.return_value = mock_commitment
            mock_persistence_class.return_value = mock_persistence

            result = _handle_confirmation("looks good", session_with_draft, mock_db_session)
            assert result is True

    def test_negative_no(self, session_with_draft, mock_db_session):
        """'no' cancels the draft."""
        result = _handle_confirmation("no", session_with_draft, mock_db_session)

        assert result is True
        assert session_with_draft.pending_draft is None  # Cleared after cancellation

    def test_negative_cancel(self, session_with_draft, mock_db_session):
        """'cancel' cancels the draft."""
        result = _handle_confirmation("cancel", session_with_draft, mock_db_session)

        assert result is True
        assert session_with_draft.pending_draft is None

    def test_negative_never_mind(self, session_with_draft, mock_db_session):
        """'never mind' cancels the draft."""
        result = _handle_confirmation("never mind", session_with_draft, mock_db_session)

        assert result is True
        assert session_with_draft.pending_draft is None

    def test_refinement_returns_false(self, session_with_draft, mock_db_session):
        """Refinement text returns False (handled by AI)."""
        result = _handle_confirmation(
            "change the date to Monday", session_with_draft, mock_db_session
        )

        assert result is False
        assert session_with_draft.pending_draft is not None  # Still pending

    def test_case_insensitive(self, session_with_draft, mock_db_session):
        """Confirmation is case insensitive."""
        result = _handle_confirmation("NO", session_with_draft, mock_db_session)

        assert result is True
        assert session_with_draft.pending_draft is None


class TestProactiveGuidance:
    """Tests for proactive guidance features."""

    def test_is_first_run_with_no_data(self):
        """First run detected when no entities exist."""
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None

        result = _is_first_run(mock_session)

        assert result is True

    def test_is_first_run_with_commitments(self):
        """Not first run when commitments exist."""
        mock_session = MagicMock()
        mock_commitment = MagicMock()
        mock_session.exec.return_value.first.return_value = mock_commitment

        result = _is_first_run(mock_session)

        assert result is False

    def test_get_at_risk_commitments_returns_list(self):
        """At-risk commitments returns a list."""
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = []

        result = _get_at_risk_commitments(mock_session)

        assert isinstance(result, list)

    @patch("jdo.repl.loop.console")
    @patch("jdo.repl.loop._is_first_run")
    def test_show_startup_guidance_first_run(self, mock_first_run, mock_console):
        """First run shows special welcome message."""
        mock_first_run.return_value = True
        mock_db_session = MagicMock()
        session = Session()

        _show_startup_guidance(mock_db_session, session)

        mock_console.print.assert_called()
        # Should print the first run message
        call_args = mock_console.print.call_args_list[0][0][0]
        assert "Welcome to JDO" in call_args

    @patch("jdo.repl.loop.console")
    @patch("jdo.repl.loop.get_visions_due_for_review")
    @patch("jdo.repl.loop.get_triage_count")
    @patch("jdo.repl.loop._get_at_risk_commitments")
    @patch("jdo.repl.loop._is_first_run")
    def test_show_startup_guidance_with_at_risk(
        self, mock_first_run, mock_at_risk, mock_triage, mock_visions, mock_console
    ):
        """At-risk commitments shown at startup."""
        mock_first_run.return_value = False
        mock_commitment = MagicMock()
        mock_commitment.deliverable = "Test commitment"
        mock_at_risk.return_value = [mock_commitment]
        mock_triage.return_value = 0
        mock_visions.return_value = []
        mock_db_session = MagicMock()
        session = Session()

        _show_startup_guidance(mock_db_session, session)

        # Should print welcome + at-risk warning
        assert mock_console.print.call_count >= 2

    @patch("jdo.repl.loop.console")
    @patch("jdo.repl.loop.get_visions_due_for_review")
    @patch("jdo.repl.loop.get_triage_count")
    @patch("jdo.repl.loop._get_at_risk_commitments")
    @patch("jdo.repl.loop._is_first_run")
    def test_show_startup_guidance_with_triage(
        self, mock_first_run, mock_at_risk, mock_triage, mock_visions, mock_console
    ):
        """Triage items shown at startup."""
        mock_first_run.return_value = False
        mock_at_risk.return_value = []
        mock_triage.return_value = 3
        mock_visions.return_value = []
        mock_db_session = MagicMock()
        session = Session()

        _show_startup_guidance(mock_db_session, session)

        # Should print welcome + triage reminder
        assert mock_console.print.call_count >= 2

    @patch("jdo.repl.loop.console")
    @patch("jdo.repl.loop.get_visions_due_for_review")
    @patch("jdo.repl.loop.get_triage_count")
    @patch("jdo.repl.loop._get_at_risk_commitments")
    @patch("jdo.repl.loop._is_first_run")
    def test_show_startup_guidance_clean_state(
        self, mock_first_run, mock_at_risk, mock_triage, mock_visions, mock_console
    ):
        """Clean state shows only welcome message."""
        mock_first_run.return_value = False
        mock_at_risk.return_value = []
        mock_triage.return_value = 0
        mock_visions.return_value = []
        mock_db_session = MagicMock()
        session = Session()

        _show_startup_guidance(mock_db_session, session)

        # Should print just welcome message (no extra warnings)
        mock_console.print.assert_called_once()

    @patch("jdo.repl.loop.console")
    @patch("jdo.repl.loop.get_visions_due_for_review")
    @patch("jdo.repl.loop.get_triage_count")
    @patch("jdo.repl.loop._get_at_risk_commitments")
    @patch("jdo.repl.loop._is_first_run")
    def test_show_startup_guidance_single_vision_due(
        self, mock_first_run, mock_at_risk, mock_triage, mock_visions, mock_console
    ):
        """Single vision due shows specific message."""
        from uuid import uuid4

        mock_first_run.return_value = False
        mock_at_risk.return_value = []
        mock_triage.return_value = 0

        mock_vision = MagicMock()
        mock_vision.id = uuid4()
        mock_vision.title = "Become a public speaker"
        mock_visions.return_value = [mock_vision]

        mock_db_session = MagicMock()
        session = Session()

        _show_startup_guidance(mock_db_session, session)

        # Should print welcome + vision notice
        assert mock_console.print.call_count >= 2
        # Vision should be snoozed
        assert mock_vision.id in session.snoozed_vision_ids

    @patch("jdo.repl.loop.console")
    @patch("jdo.repl.loop.get_visions_due_for_review")
    @patch("jdo.repl.loop.get_triage_count")
    @patch("jdo.repl.loop._get_at_risk_commitments")
    @patch("jdo.repl.loop._is_first_run")
    def test_show_startup_guidance_multiple_visions_due(
        self, mock_first_run, mock_at_risk, mock_triage, mock_visions, mock_console
    ):
        """Multiple visions due shows consolidated message."""
        from uuid import uuid4

        mock_first_run.return_value = False
        mock_at_risk.return_value = []
        mock_triage.return_value = 0

        mock_vision1 = MagicMock()
        mock_vision1.id = uuid4()
        mock_vision1.title = "Vision 1"
        mock_vision2 = MagicMock()
        mock_vision2.id = uuid4()
        mock_vision2.title = "Vision 2"
        mock_visions.return_value = [mock_vision1, mock_vision2]

        mock_db_session = MagicMock()
        session = Session()

        _show_startup_guidance(mock_db_session, session)

        # Both visions should be snoozed
        assert mock_vision1.id in session.snoozed_vision_ids
        assert mock_vision2.id in session.snoozed_vision_ids

    @patch("jdo.repl.loop.console")
    @patch("jdo.repl.loop.get_visions_due_for_review")
    @patch("jdo.repl.loop.get_triage_count")
    @patch("jdo.repl.loop._get_at_risk_commitments")
    @patch("jdo.repl.loop._is_first_run")
    def test_show_startup_guidance_already_snoozed_vision(
        self, mock_first_run, mock_at_risk, mock_triage, mock_visions, mock_console
    ):
        """Already-snoozed visions are filtered out."""
        from uuid import uuid4

        mock_first_run.return_value = False
        mock_at_risk.return_value = []
        mock_triage.return_value = 0

        vision_id = uuid4()
        mock_vision = MagicMock()
        mock_vision.id = vision_id
        mock_vision.title = "Already snoozed vision"
        mock_visions.return_value = [mock_vision]

        mock_db_session = MagicMock()
        session = Session()
        session.snoozed_vision_ids.add(vision_id)  # Pre-snooze the vision

        _show_startup_guidance(mock_db_session, session)

        # Should print just welcome message (vision was already snoozed)
        mock_console.print.assert_called_once()

    @patch("jdo.repl.loop.console")
    @patch("jdo.repl.loop.logger")
    @patch("jdo.repl.loop.get_visions_due_for_review")
    @patch("jdo.repl.loop.get_triage_count")
    @patch("jdo.repl.loop._get_at_risk_commitments")
    @patch("jdo.repl.loop._is_first_run")
    def test_show_startup_guidance_vision_query_error(
        self, mock_first_run, mock_at_risk, mock_triage, mock_visions, mock_logger, mock_console
    ):
        """Vision query error is logged but doesn't block startup."""
        mock_first_run.return_value = False
        mock_at_risk.return_value = []
        mock_triage.return_value = 0
        from sqlalchemy.exc import SQLAlchemyError

        mock_visions.side_effect = SQLAlchemyError("Database error")

        mock_db_session = MagicMock()
        session = Session()

        # Should not raise
        _show_startup_guidance(mock_db_session, session)

        # Error should be logged
        mock_logger.warning.assert_called_once()
        # Welcome message should still be printed
        mock_console.print.assert_called()
