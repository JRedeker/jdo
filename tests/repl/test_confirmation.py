"""Tests for REPL confirmation flows and draft execution."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from jdo.repl.loop import _confirm_draft, _handle_confirmation
from jdo.repl.session import PendingDraft, Session


class TestConfirmDraft:
    """Tests for _confirm_draft function."""

    @pytest.fixture
    def mock_db_session(self) -> MagicMock:
        """Create a mock database session."""
        session = MagicMock()
        return session

    @pytest.fixture
    def mock_persistence(self) -> MagicMock:
        """Create a mock PersistenceService."""
        persistence = MagicMock()
        return persistence

    def test_confirm_draft_with_commitment_success(
        self, mock_db_session: MagicMock, mock_persistence: MagicMock
    ) -> None:
        """Test successful commitment creation from draft."""
        commitment_id = uuid4()
        mock_commitment = MagicMock()
        mock_commitment.id = commitment_id
        mock_commitment.deliverable = "Test commitment"
        mock_persistence.save_commitment.return_value = mock_commitment

        draft = PendingDraft(
            action="create", entity_type="commitment", data={"deliverable": "Test commitment"}
        )
        session = Session()

        with (
            patch("jdo.repl.loop.PersistenceService", return_value=mock_persistence),
            patch("jdo.repl.loop._get_active_commitment_count", return_value=5),
        ):
            result = _confirm_draft(draft, session, mock_db_session)

        assert result is True
        mock_persistence.save_commitment.assert_called_once_with({"deliverable": "Test commitment"})
        mock_db_session.commit.assert_called_once()
        assert session.pending_draft is None

    def test_confirm_draft_with_commitment_error(
        self, mock_db_session: MagicMock, mock_persistence: MagicMock
    ) -> None:
        """Test error handling when commitment creation fails."""
        mock_persistence.save_commitment.side_effect = Exception("Database error")

        draft = PendingDraft(
            action="create", entity_type="commitment", data={"deliverable": "Test"}
        )
        session = Session()

        with patch("jdo.repl.loop.PersistenceService", return_value=mock_persistence):
            result = _confirm_draft(draft, session, mock_db_session)

        assert result is True
        mock_db_session.commit.assert_not_called()

    def test_confirm_draft_unknown_entity_type(self, mock_db_session: MagicMock) -> None:
        """Test handling of unknown entity type in draft."""
        draft = PendingDraft(action="create", entity_type="unknown", data={"some": "data"})
        session = Session()

        result = _confirm_draft(draft, session, mock_db_session)

        assert result is True
        assert session.pending_draft is None


class TestHandleConfirmation:
    """Tests for _handle_confirmation function."""

    def test_yes_confirmation_accepts(self) -> None:
        """Test that 'yes' confirms the draft."""
        session = Session()
        session.set_pending_draft("create", "commitment", {"deliverable": "Test"})

        with patch("jdo.repl.loop._confirm_draft", return_value=True) as mock_confirm:
            result = _handle_confirmation("yes", session, MagicMock())

        assert result is True
        mock_confirm.assert_called_once()

    def test_no_confirmation_rejects(self) -> None:
        """Test that 'no' rejects and clears the draft."""
        session = Session()
        session.set_pending_draft("create", "commitment", {"deliverable": "Test"})

        result = _handle_confirmation("no", session, MagicMock())

        assert result is True
        assert session.pending_draft is None

    def test_refine_confirmation_returns_false(self) -> None:
        """Test that 'refine' returns False to let AI handle it."""
        session = Session()
        session.set_pending_draft("create", "commitment", {"deliverable": "Test"})

        result = _handle_confirmation("refine", session, MagicMock())

        assert result is False
        assert session.pending_draft is not None

    def test_invalid_input_returns_false(self) -> None:
        """Test that invalid input returns False (not confirmed)."""
        session = Session()
        session.set_pending_draft("create", "commitment", {"deliverable": "Test"})

        result = _handle_confirmation("maybe", session, MagicMock())

        assert result is False

    def test_empty_input_returns_false(self) -> None:
        """Test that empty input returns False (not confirmed)."""
        session = Session()
        session.set_pending_draft("create", "commitment", {"deliverable": "Test"})

        result = _handle_confirmation("", session, MagicMock())

        assert result is False

    def test_case_insensitive_yes(self) -> None:
        """Test that 'YES' (uppercase) is accepted."""
        session = Session()
        session.set_pending_draft("create", "commitment", {"deliverable": "Test"})

        with patch("jdo.repl.loop._confirm_draft", return_value=True) as mock_confirm:
            result = _handle_confirmation("YES", session, MagicMock())

        assert result is True
        mock_confirm.assert_called_once()

    def test_case_insensitive_no(self) -> None:
        """Test that 'NO' (uppercase) is rejected."""
        session = Session()
        session.set_pending_draft("create", "commitment", {"deliverable": "Test"})

        result = _handle_confirmation("NO", session, MagicMock())

        assert result is True
        assert session.pending_draft is None
