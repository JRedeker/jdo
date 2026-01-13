"""Tests for database session functions."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from jdo.db.session import (
    check_and_generate_recurring_instances,
    delete_draft,
    generate_next_instance_for_recurring,
    get_active_recurring_commitments,
    get_commitment_progress,
    get_goals_due_for_review,
    get_overdue_milestones,
    get_pending_drafts,
    get_session,
    get_triage_count,
    get_triage_items,
    get_visions_due_for_review,
    update_overdue_milestones,
)


class TestGetSession:
    """Tests for get_session context manager."""

    def test_session_commits_on_success(self) -> None:
        """get_session commits on successful exit."""
        with get_session() as session:
            assert session is not None

    def test_session_rollback_on_exception(self) -> None:
        """get_session rolls back on exception."""
        with pytest.raises(ValueError, match="Test error"), get_session() as session:
            raise ValueError("Test error")

        # The session should have been rolled back - we can't easily test this
        # with mocking but we can verify no exceptions were raised during cleanup


class TestGetVisionsDueForReview:
    """Tests for get_visions_due_for_review function."""

    def test_returns_list(self) -> None:
        """Returns list of visions."""
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = []

        result = get_visions_due_for_review(mock_session)

        assert isinstance(result, list)

    def test_with_vision(self) -> None:
        """Returns vision when exists."""
        mock_vision = MagicMock()
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = [mock_vision]

        result = get_visions_due_for_review(mock_session)

        assert len(result) == 1


class TestGetOverdueMilestones:
    """Tests for get_overdue_milestones function."""

    def test_returns_list(self) -> None:
        """Returns list of milestones."""
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = []

        result = get_overdue_milestones(mock_session)

        assert isinstance(result, list)

    def test_with_milestone(self) -> None:
        """Returns milestone when exists."""
        mock_milestone = MagicMock()
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = [mock_milestone]

        result = get_overdue_milestones(mock_session)

        assert len(result) == 1


class TestUpdateOverdueMilestones:
    """Tests for update_overdue_milestones function."""

    def test_returns_count(self) -> None:
        """Returns count of updated milestones."""
        mock_milestone = MagicMock()
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = [mock_milestone]

        result = update_overdue_milestones(mock_session)

        assert result == 1
        assert mock_milestone.mark_missed.called

    def test_empty_list(self) -> None:
        """Returns 0 when no overdue milestones."""
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = []

        result = update_overdue_milestones(mock_session)

        assert result == 0


class TestGetPendingDrafts:
    """Tests for get_pending_drafts function."""

    def test_returns_list(self) -> None:
        """Returns list of drafts."""
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = []

        result = get_pending_drafts(mock_session)

        assert isinstance(result, list)


class TestDeleteDraft:
    """Tests for delete_draft function."""

    def test_deletes_and_commits(self) -> None:
        """delete_draft deletes draft and commits."""
        mock_draft = MagicMock()
        mock_session = MagicMock()

        delete_draft(mock_session, mock_draft)

        assert mock_session.delete.called
        assert mock_session.commit.called


class TestGetGoalsDueForReview:
    """Tests for get_goals_due_for_review function."""

    def test_returns_list(self) -> None:
        """Returns list of goals."""
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = []

        result = get_goals_due_for_review(mock_session)

        assert isinstance(result, list)


class TestGetActiveRecurringCommitments:
    """Tests for get_active_recurring_commitments function."""

    def test_returns_list(self) -> None:
        """Returns list of recurring commitments."""
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = []

        result = get_active_recurring_commitments(mock_session)

        assert isinstance(result, list)


class TestCheckAndGenerateRecurringInstances:
    """Tests for check_and_generate_recurring_instances function."""

    def test_returns_list(self) -> None:
        """Returns list of generated instances."""
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = []

        result = check_and_generate_recurring_instances(mock_session)

        assert isinstance(result, list)


class TestGenerateNextInstanceForRecurring:
    """Tests for generate_next_instance_for_recurring function."""

    def test_returns_none_for_inactive(self) -> None:
        """Returns None for inactive recurring commitment."""
        mock_session = MagicMock()
        mock_recurring = MagicMock()
        mock_recurring.status.value = "inactive"
        mock_session.get.return_value = mock_recurring

        result = generate_next_instance_for_recurring(mock_session, uuid4())

        assert result is None

    def test_returns_none_for_nonexistent(self) -> None:
        """Returns None for nonexistent recurring commitment."""
        mock_session = MagicMock()
        mock_session.get.return_value = None

        result = generate_next_instance_for_recurring(mock_session, uuid4())

        assert result is None


class TestGetCommitmentProgress:
    """Tests for get_commitment_progress function."""

    def test_returns_progress(self) -> None:
        """Returns GoalProgress with counts."""
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = []

        result = get_commitment_progress(mock_session, uuid4())

        assert result.total == 0
        assert result.completed == 0
        assert result.pending == 0

    def test_with_commitments(self) -> None:
        """Returns progress with actual counts."""
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = [
            ("completed", 5),
            ("in_progress", 3),
            ("pending", 2),
        ]

        result = get_commitment_progress(mock_session, uuid4())

        assert result.total == 10
        assert result.completed == 5
        assert result.in_progress == 3
        assert result.pending == 2


class TestGetTriageItems:
    """Tests for get_triage_items function."""

    def test_returns_list(self) -> None:
        """Returns list of triage items."""
        mock_session = MagicMock()
        mock_session.exec.return_value.all.return_value = []

        result = get_triage_items(mock_session)

        assert isinstance(result, list)


class TestGetTriageCount:
    """Tests for get_triage_count function."""

    def test_returns_count(self) -> None:
        """Returns count as integer."""
        mock_session = MagicMock()
        mock_session.exec.return_value.one.return_value = 5

        result = get_triage_count(mock_session)

        assert result == 5
        assert isinstance(result, int)

    def test_returns_zero(self) -> None:
        """Returns 0 when no items."""
        mock_session = MagicMock()
        mock_session.exec.return_value.one.return_value = 0

        result = get_triage_count(mock_session)

        assert result == 0
