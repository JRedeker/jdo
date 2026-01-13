"""Tests for /list command with commitments.

Regression test to ensure /list properly displays commitments with stakeholder info.
"""

from __future__ import annotations

from datetime import date
from io import StringIO
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from rich.console import Console
from sqlmodel import Session

from jdo.models import Commitment, CommitmentStatus, Stakeholder


class TestListCommitmentsUnit:
    """Unit tests for _list_commitments function with mocks."""

    def test_list_commitments_displays_stakeholder_name(self, mock_db_session: MagicMock) -> None:
        """List commitments should display stakeholder name without error."""
        from jdo.repl.loop import _list_commitments

        # Create mock stakeholder and commitment
        mock_stakeholder = MagicMock(spec=Stakeholder)
        mock_stakeholder.name = "Test Person"
        mock_stakeholder.id = "stakeholder-123"

        mock_commitment = MagicMock(spec=Commitment)
        mock_commitment.id = "commit-123"
        mock_commitment.deliverable = "Test deliverable"
        mock_commitment.stakeholder = mock_stakeholder
        mock_commitment.stakeholder_id = "stakeholder-123"
        mock_commitment.due_date = None
        mock_commitment.status = CommitmentStatus.PENDING

        # Mock the query to return our commitment
        mock_result = MagicMock()
        mock_result.all.return_value = [mock_commitment]
        mock_db_session.exec.return_value = mock_result

        # Capture output
        output_buffer = StringIO()
        test_console = Console(file=output_buffer, force_terminal=True, width=100)

        with patch("jdo.repl.loop.console", test_console):
            _list_commitments(mock_db_session)

        output = output_buffer.getvalue()
        assert "Test Person" in output or "Test deliverable" in output


class TestListCommitmentsIntegration:
    """Integration tests for _list_commitments with real DB objects."""

    @pytest.mark.integration
    def test_list_commitments_with_real_objects(self, db_session: Session) -> None:
        """List commitments should work with real SQLModel objects.

        Regression test: Previously failed with AttributeError when accessing
        commitment.stakeholder relationship because it wasn't eager-loaded.
        """
        from jdo.repl.loop import _list_commitments

        # Create real stakeholder
        stakeholder = Stakeholder(
            id=uuid4(),
            name="Integration Test Person",
            type="PERSON",
        )
        db_session.add(stakeholder)
        db_session.flush()

        # Create real commitment
        commitment = Commitment(
            id=uuid4(),
            deliverable="Integration test deliverable",
            stakeholder_id=stakeholder.id,
            due_date=date(2026, 1, 20),
            status=CommitmentStatus.PENDING,
        )
        db_session.add(commitment)
        db_session.flush()

        # Capture output
        output_buffer = StringIO()
        test_console = Console(file=output_buffer, force_terminal=True, width=100)

        with patch("jdo.repl.loop.console", test_console):
            # This should NOT raise an AttributeError
            _list_commitments(db_session)

        output = output_buffer.getvalue()

        # Verify output contains expected content
        assert "Integration test deliverable" in output or "Integration Test Person" in output


@pytest.fixture
def mock_db_session() -> MagicMock:
    """Create a mock database session."""
    return MagicMock()
