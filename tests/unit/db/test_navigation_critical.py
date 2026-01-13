"""Tests for database navigation service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from jdo.db.navigation import NavigationService


class TestNavigationService:
    """Tests for NavigationService."""

    def test_get_goals_list_empty(self) -> None:
        """get_goals_list returns empty list on error."""
        session = MagicMock()
        session.exec.side_effect = Exception("DB error")

        result = NavigationService.get_goals_list(session)

        assert result == []

    def test_get_goals_list_with_data(self) -> None:
        """get_goals_list returns goal dicts."""
        session = MagicMock()
        mock_goal = MagicMock()
        mock_goal.id = "test-id"
        mock_goal.title = "Test Goal"
        mock_goal.problem_statement = "Test problem"
        mock_goal.status.value = "active"
        session.exec.return_value.all.return_value = [mock_goal]

        result = NavigationService.get_goals_list(session)

        assert len(result) == 1
        assert result[0]["id"] == "test-id"
        assert result[0]["title"] == "Test Goal"

    def test_get_commitments_list_empty(self) -> None:
        """get_commitments_list returns empty list on error."""
        session = MagicMock()
        session.exec.side_effect = Exception("DB error")

        result = NavigationService.get_commitments_list(session)

        assert result == []

    def test_get_commitments_list_with_data(self) -> None:
        """get_commitments_list returns commitment dicts."""
        session = MagicMock()
        mock_commitment = MagicMock()
        mock_stakeholder = MagicMock()
        mock_commitment.id = "commit-id"
        mock_commitment.deliverable = "Test deliverable"
        mock_commitment.due_date.isoformat.return_value = "2024-01-15"
        mock_commitment.status.value = "pending"
        mock_stakeholder.name = "Alice"
        session.exec.return_value.all.return_value = [(mock_commitment, mock_stakeholder)]

        result = NavigationService.get_commitments_list(session)

        assert len(result) == 1
        assert result[0]["deliverable"] == "Test deliverable"
        assert result[0]["stakeholder_name"] == "Alice"

    def test_get_visions_list_empty(self) -> None:
        """get_visions_list returns empty list on error."""
        session = MagicMock()
        session.exec.side_effect = Exception("DB error")

        result = NavigationService.get_visions_list(session)

        assert result == []

    def test_get_visions_list_with_data(self) -> None:
        """get_visions_list returns vision dicts."""
        session = MagicMock()
        mock_vision = MagicMock()
        mock_vision.id = "vision-id"
        mock_vision.title = "Test Vision"
        mock_vision.timeframe = "5 years"
        mock_vision.status.value = "active"
        session.exec.return_value.all.return_value = [mock_vision]

        result = NavigationService.get_visions_list(session)

        assert len(result) == 1
        assert result[0]["title"] == "Test Vision"

    def test_get_milestones_list_empty(self) -> None:
        """get_milestones_list returns empty list on error."""
        session = MagicMock()
        session.exec.side_effect = Exception("DB error")

        result = NavigationService.get_milestones_list(session)

        assert result == []

    def test_get_milestones_list_with_data(self) -> None:
        """get_milestones_list returns milestone dicts."""
        session = MagicMock()
        mock_milestone = MagicMock()
        mock_milestone.id = "milestone-id"
        mock_milestone.description = "Test milestone"
        mock_milestone.target_date.isoformat.return_value = "2024-02-01"
        mock_milestone.status.value = "pending"
        session.exec.return_value.all.return_value = [mock_milestone]

        result = NavigationService.get_milestones_list(session)

        assert len(result) == 1
        assert result[0]["description"] == "Test milestone"

    def test_get_orphans_list_empty(self) -> None:
        """get_orphans_list returns empty list on error."""
        session = MagicMock()
        session.exec.side_effect = Exception("DB error")

        result = NavigationService.get_orphans_list(session)

        assert result == []

    def test_get_orphans_list_with_data(self) -> None:
        """get_orphans_list returns orphan commitment dicts."""
        session = MagicMock()
        mock_commitment = MagicMock()
        mock_stakeholder = MagicMock()
        mock_commitment.id = "orphan-id"
        mock_commitment.deliverable = "Orphan deliverable"
        mock_commitment.due_date.isoformat.return_value = "2024-01-20"
        mock_commitment.status.value = "pending"
        mock_stakeholder.name = "Bob"
        session.exec.return_value.all.return_value = [(mock_commitment, mock_stakeholder)]

        result = NavigationService.get_orphans_list(session)

        assert len(result) == 1
        assert result[0]["deliverable"] == "Orphan deliverable"

    def test_get_integrity_data_default(self) -> None:
        """get_integrity_data returns defaults on error."""
        session = MagicMock()
        with patch("jdo.db.navigation.IntegrityService") as mock_service:
            mock_service.return_value.calculate_integrity_metrics.side_effect = Exception("Error")

            result = NavigationService.get_integrity_data(session)

            assert result["composite_score"] == 100.0
            assert result["letter_grade"] == "A+"

    def test_get_integrity_data_with_metrics(self) -> None:
        """get_integrity_data returns metrics when successful."""
        session = MagicMock()
        mock_metrics = MagicMock()
        mock_metrics.composite_score = 85.5
        mock_metrics.letter_grade = "B"
        mock_metrics.on_time_rate = 0.8
        mock_metrics.notification_timeliness = 0.9
        mock_metrics.cleanup_completion_rate = 0.85
        mock_metrics.current_streak_weeks = 3
        mock_metrics.total_completed = 10
        mock_metrics.total_on_time = 8
        mock_metrics.total_at_risk = 2
        mock_metrics.total_abandoned = 0

        with patch("jdo.db.navigation.IntegrityService") as mock_service:
            mock_service.return_value.calculate_integrity_metrics.return_value = mock_metrics

            result = NavigationService.get_integrity_data(session)

            assert result["composite_score"] == 85.5
            assert result["letter_grade"] == "B"
            assert result["total_completed"] == 10
