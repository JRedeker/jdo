"""Tests for critical REPL loop functions."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from jdo.repl.loop import (
    _get_at_risk_commitments,
    _get_vision_review_message,
    _handle_list,
    _is_first_run,
    _show_startup_guidance,
    check_credentials,
)
from jdo.repl.session import Session


class TestGetAtRiskCommitments:
    """Tests for _get_at_risk_commitments function."""

    def test_returns_empty_when_no_commitments(self) -> None:
        """Returns empty list when no at-risk commitments exist."""
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = []

        result = _get_at_risk_commitments(mock_session)

        assert result == []

    def test_returns_at_risk_commitments(self) -> None:
        """Returns commitments with AT_RISK status."""
        mock_session = MagicMock()
        mock_commitment = MagicMock()
        mock_commitment.status.value = "at_risk"
        mock_commitment.due_date = date.today()
        mock_session.exec.return_value.all.return_value = [mock_commitment]

        result = _get_at_risk_commitments(mock_session)

        assert len(result) == 1

    def test_returns_overdue_pending_commitments(self) -> None:
        """Returns pending commitments past their due date."""
        mock_session = MagicMock()
        mock_commitment = MagicMock()
        mock_commitment.status.value = "pending"
        mock_commitment.due_date = date(2020, 1, 1)  # Past date
        mock_session.exec.return_value.all.return_value = [mock_commitment]

        result = _get_at_risk_commitments(mock_session)

        assert len(result) == 1


class TestGetVisionReviewMessage:
    """Tests for _get_vision_review_message function."""

    def test_returns_none_when_no_visions_due(self) -> None:
        """Returns None when no visions are due for review."""
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = []

        session = Session()
        message, visions = _get_vision_review_message(mock_db, session)

        assert message is None
        assert visions == []

    def test_returns_message_for_single_vision(self) -> None:
        """Returns formatted message for single vision due."""
        from jdo.models.vision import Vision, VisionStatus

        mock_vision = MagicMock()
        mock_vision.id = uuid4()
        mock_vision.title = "Test Vision"
        mock_vision.status = VisionStatus.ACTIVE
        mock_vision.next_review_date = date.today()

        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [mock_vision]

        session = Session()
        message, visions = _get_vision_review_message(mock_db, session)

        assert message is not None
        assert "Test Vision" in message
        assert len(visions) == 1

    def test_returns_message_for_multiple_visions(self) -> None:
        """Returns message for multiple visions due."""
        mock_vision1 = MagicMock()
        mock_vision1.id = uuid4()
        mock_vision1.title = "Vision 1"
        mock_vision1.status.value = "active"
        mock_vision1.next_review_date = date.today()

        mock_vision2 = MagicMock()
        mock_vision2.id = uuid4()
        mock_vision2.title = "Vision 2"
        mock_vision2.status.value = "active"
        mock_vision2.next_review_date = date.today()

        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [mock_vision1, mock_vision2]

        session = Session()
        message, visions = _get_vision_review_message(mock_db, session)

        assert message is not None
        assert "2 visions" in message
        assert len(visions) == 2

    def test_filters_snoozed_visions(self) -> None:
        """Filters out visions that have been snoozed."""
        from jdo.models.vision import Vision, VisionStatus

        vision_id = uuid4()
        mock_vision = MagicMock()
        mock_vision.id = vision_id
        mock_vision.title = "Snoozed Vision"
        mock_vision.status = VisionStatus.ACTIVE
        mock_vision.next_review_date = date.today()

        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = [mock_vision]

        session = Session()
        session.snoozed_vision_ids.add(vision_id)
        message, visions = _get_vision_review_message(mock_db, session)

        assert message is None
        assert visions == []

    def test_handles_database_error(self) -> None:
        """Returns None on database error."""
        mock_db = MagicMock()
        mock_db.exec.side_effect = OSError("Database error")

        session = Session()
        message, visions = _get_vision_review_message(mock_db, session)

        assert message is None
        assert visions == []


class TestShowStartupGuidance:
    """Tests for _show_startup_guidance function."""

    def test_calls_vision_review_when_visions_due(self) -> None:
        """Shows vision review message when visions are due."""
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = []

        session = Session()

        with patch("jdo.repl.loop._get_vision_review_message") as mock_review:
            mock_review.return_value = ("Vision message", [])
            _show_startup_guidance(mock_db, session)

            mock_review.assert_called_once()

    def test_first_run_with_no_data(self) -> None:
        """Handles first run scenario."""
        mock_db = MagicMock()
        mock_db.exec.return_value.first.return_value = None

        session = Session()

        with (
            patch("jdo.repl.loop._is_first_run", return_value=True),
            patch("jdo.repl.loop._get_vision_review_message") as mock_review,
        ):
            mock_review.return_value = (None, [])
            _show_startup_guidance(mock_db, session)


class TestHandleList:
    """Tests for _handle_list function."""

    def test_list_default_shows_commitments(self) -> None:
        """Default /list shows commitments."""
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = []

        with patch("jdo.repl.loop.console.print"):
            _handle_list("", mock_db)

    def test_list_with_empty_args(self) -> None:
        """Empty args shows commitments."""
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = []

        with patch("jdo.repl.loop.console.print"):
            _handle_list("", mock_db)

    def test_list_goals(self) -> None:
        """List goals shows goal list."""
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = []

        with patch("jdo.repl.loop.console.print"):
            _handle_list("goals", mock_db)

    def test_list_visions(self) -> None:
        """List visions shows vision list."""
        mock_db = MagicMock()
        mock_db.exec.return_value.all.return_value = []

        with patch("jdo.repl.loop.console.print"):
            _handle_list("visions", mock_db)


class TestCheckCredentials:
    """Tests for check_credentials function."""

    def test_returns_true_when_authenticated(self) -> None:
        """Returns True when AI provider is authenticated."""
        with (
            patch("jdo.repl.loop.is_authenticated", return_value=True),
            patch("jdo.repl.loop.get_settings") as mock_settings,
        ):
            mock_settings.return_value.ai_provider = "openai"

            assert check_credentials() is True

    def test_returns_false_when_not_authenticated(self) -> None:
        """Returns False when AI provider is not authenticated."""
        with (
            patch("jdo.repl.loop.is_authenticated", return_value=False),
            patch("jdo.repl.loop.get_settings") as mock_settings,
        ):
            mock_settings.return_value.ai_provider = "openai"

            assert check_credentials() is False

    def test_checks_correct_provider(self) -> None:
        """Uses the configured AI provider for authentication check."""
        with (
            patch("jdo.repl.loop.is_authenticated") as mock_auth,
            patch("jdo.repl.loop.get_settings") as mock_settings,
        ):
            mock_settings.return_value.ai_provider = "anthropic"
            mock_auth.return_value = True

            check_credentials()

            mock_auth.assert_called_once_with("anthropic")


class TestIsFirstRun:
    """Tests for _is_first_run function."""

    def test_returns_true_when_empty_database(self) -> None:
        """Returns True when no commitments, goals, or visions exist."""
        mock_db = MagicMock()
        mock_db.exec.return_value.first.return_value = None

        result = _is_first_run(mock_db)

        assert result is True

    def test_returns_false_when_commitments_exist(self) -> None:
        """Returns False when commitments exist."""
        mock_db = MagicMock()
        mock_db.exec.return_value.first.side_effect = [
            MagicMock(),  # commitment exists
            None,
            None,
        ]

        result = _is_first_run(mock_db)

        assert result is False

    def test_returns_false_when_goals_exist(self) -> None:
        """Returns False when goals exist."""
        mock_db = MagicMock()
        mock_db.exec.return_value.first.side_effect = [
            None,  # no commitments
            MagicMock(),  # goal exists
            None,
        ]

        result = _is_first_run(mock_db)

        assert result is False

    def test_returns_false_when_visions_exist(self) -> None:
        """Returns False when visions exist."""
        mock_db = MagicMock()
        mock_db.exec.return_value.first.side_effect = [
            None,
            None,
            MagicMock(),  # vision exists
        ]

        result = _is_first_run(mock_db)

        assert result is False
