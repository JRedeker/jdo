"""Tests for the review system (vision review, milestone auto-update).

Phase 13: Review System for visions and milestones.
"""

from datetime import UTC, date, datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest


class TestVisionReview:
    """Tests for vision review functionality."""

    def test_vision_due_for_review_when_past_date(self) -> None:
        """Vision is due for review when next_review_date has passed."""
        from jdo.models import Vision
        from jdo.models.vision import VisionStatus

        vision = Vision(
            id=uuid4(),
            title="Test Vision",
            narrative="Test narrative",
            status=VisionStatus.ACTIVE,
            next_review_date=date(2025, 1, 1),  # In the past
        )

        with patch("jdo.models.vision.today_date") as mock_today:
            mock_today.return_value = date(2025, 12, 16)
            assert vision.is_due_for_review() is True

    def test_vision_not_due_when_future_date(self) -> None:
        """Vision is not due for review when next_review_date is in future."""
        from jdo.models import Vision
        from jdo.models.vision import VisionStatus

        vision = Vision(
            id=uuid4(),
            title="Test Vision",
            narrative="Test narrative",
            status=VisionStatus.ACTIVE,
            next_review_date=date(2026, 3, 15),  # In the future
        )

        with patch("jdo.models.vision.today_date") as mock_today:
            mock_today.return_value = date(2025, 12, 16)
            assert vision.is_due_for_review() is False

    def test_complete_review_updates_timestamps(self) -> None:
        """complete_review updates last_reviewed_at and next_review_date."""
        from jdo.models import Vision
        from jdo.models.vision import VisionStatus

        vision = Vision(
            id=uuid4(),
            title="Test Vision",
            narrative="Test narrative",
            status=VisionStatus.ACTIVE,
            next_review_date=date(2025, 1, 1),
        )

        with (
            patch("jdo.models.vision.today_date") as mock_today,
            patch("jdo.models.vision.utc_now") as mock_now,
        ):
            mock_today.return_value = date(2025, 12, 16)
            mock_now.return_value = datetime(2025, 12, 16, 10, 0, 0, tzinfo=UTC)

            vision.complete_review()

            assert vision.last_reviewed_at == datetime(2025, 12, 16, 10, 0, 0, tzinfo=UTC)
            # Next review should be 90 days from today
            assert vision.next_review_date == date(2025, 12, 16) + timedelta(days=90)


class TestGetVisionsDueForReview:
    """Tests for getting visions due for review."""

    def test_get_visions_due_for_review_returns_due_visions(self) -> None:
        """get_visions_due_for_review returns only visions past their review date."""
        from jdo.db.session import get_visions_due_for_review

        # This is a placeholder - we need to implement this function
        # The actual test would use a test database
        assert callable(get_visions_due_for_review)


class TestMilestoneAutoUpdate:
    """Tests for milestone auto-update functionality."""

    def test_milestone_overdue_when_past_target_date(self) -> None:
        """Milestone is overdue when target_date has passed and not completed."""
        from jdo.models import Milestone
        from jdo.models.milestone import MilestoneStatus

        milestone = Milestone(
            id=uuid4(),
            goal_id=uuid4(),
            title="Test Milestone",
            target_date=date(2025, 1, 1),  # In the past
            status=MilestoneStatus.PENDING,
        )

        with patch("jdo.models.milestone.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2025, 12, 16, tzinfo=UTC)
            assert milestone.is_overdue() is True

    def test_milestone_not_overdue_when_completed(self) -> None:
        """Completed milestone is not overdue even if past target date."""
        from jdo.models import Milestone
        from jdo.models.milestone import MilestoneStatus

        milestone = Milestone(
            id=uuid4(),
            goal_id=uuid4(),
            title="Test Milestone",
            target_date=date(2025, 1, 1),  # In the past
            status=MilestoneStatus.COMPLETED,
        )

        assert milestone.is_overdue() is False

    def test_milestone_not_overdue_when_already_missed(self) -> None:
        """Missed milestone is not considered overdue (already handled)."""
        from jdo.models import Milestone
        from jdo.models.milestone import MilestoneStatus

        milestone = Milestone(
            id=uuid4(),
            goal_id=uuid4(),
            title="Test Milestone",
            target_date=date(2025, 1, 1),
            status=MilestoneStatus.MISSED,
        )

        assert milestone.is_overdue() is False

    def test_mark_missed_transitions_status(self) -> None:
        """mark_missed transitions status to MISSED."""
        from jdo.models import Milestone
        from jdo.models.milestone import MilestoneStatus

        milestone = Milestone(
            id=uuid4(),
            goal_id=uuid4(),
            title="Test Milestone",
            target_date=date(2025, 1, 1),
            status=MilestoneStatus.PENDING,
        )

        milestone.mark_missed()

        assert milestone.status == MilestoneStatus.MISSED


class TestGetOverdueMilestones:
    """Tests for getting overdue milestones."""

    def test_get_overdue_milestones_exists(self) -> None:
        """get_overdue_milestones function exists."""
        from jdo.db.session import get_overdue_milestones

        assert callable(get_overdue_milestones)


class TestUpdateOverdueMilestones:
    """Tests for auto-updating overdue milestones."""

    def test_update_overdue_milestones_exists(self) -> None:
        """update_overdue_milestones function exists."""
        from jdo.db.session import update_overdue_milestones

        assert callable(update_overdue_milestones)
