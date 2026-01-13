"""Tests for Goal review system.

Phase 3: Review System - due-for-review queries and complete_review.
"""

from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlmodel import SQLModel

from jdo.models import Goal
from jdo.models.goal import GoalStatus


class TestGoalIsDueForReview:
    """Tests for Goal.is_due_for_review method."""

    def test_goal_due_when_review_date_in_past(self) -> None:
        """Goal is due for review when next_review_date is in the past."""
        goal = Goal(
            title="Test Goal",
            problem_statement="Problem",
            solution_vision="Vision",
            next_review_date=date(2025, 1, 1),  # In the past
        )

        with patch("jdo.models.goal.today_date") as mock_today:
            mock_today.return_value = date(2025, 12, 16)
            assert goal.is_due_for_review() is True

    def test_goal_due_when_review_date_is_today(self) -> None:
        """Goal is due for review when next_review_date is today."""
        goal = Goal(
            title="Test Goal",
            problem_statement="Problem",
            solution_vision="Vision",
            next_review_date=date(2025, 12, 16),
        )

        with patch("jdo.models.goal.today_date") as mock_today:
            mock_today.return_value = date(2025, 12, 16)
            assert goal.is_due_for_review() is True

    def test_goal_not_due_when_review_date_in_future(self) -> None:
        """Goal is not due for review when next_review_date is in future."""
        goal = Goal(
            title="Test Goal",
            problem_statement="Problem",
            solution_vision="Vision",
            next_review_date=date(2026, 3, 15),
        )

        with patch("jdo.models.goal.today_date") as mock_today:
            mock_today.return_value = date(2025, 12, 16)
            assert goal.is_due_for_review() is False

    def test_goal_not_due_when_no_review_date(self) -> None:
        """Goal with no review date is not due for review."""
        goal = Goal(
            title="Test Goal",
            problem_statement="Problem",
            solution_vision="Vision",
            next_review_date=None,
        )

        assert goal.is_due_for_review() is False

    def test_goal_not_due_when_on_hold(self) -> None:
        """On-hold goal is not due for review even if date is past."""
        goal = Goal(
            title="Test Goal",
            problem_statement="Problem",
            solution_vision="Vision",
            next_review_date=date(2025, 1, 1),
            status=GoalStatus.ON_HOLD,
        )

        with patch("jdo.models.goal.today_date") as mock_today:
            mock_today.return_value = date(2025, 12, 16)
            assert goal.is_due_for_review() is False

    def test_goal_not_due_when_achieved(self) -> None:
        """Achieved goal is not due for review."""
        goal = Goal(
            title="Test Goal",
            problem_statement="Problem",
            solution_vision="Vision",
            next_review_date=date(2025, 1, 1),
            status=GoalStatus.ACHIEVED,
        )

        with patch("jdo.models.goal.today_date") as mock_today:
            mock_today.return_value = date(2025, 12, 16)
            assert goal.is_due_for_review() is False

    def test_goal_not_due_when_abandoned(self) -> None:
        """Abandoned goal is not due for review."""
        goal = Goal(
            title="Test Goal",
            problem_statement="Problem",
            solution_vision="Vision",
            next_review_date=date(2025, 1, 1),
            status=GoalStatus.ABANDONED,
        )

        with patch("jdo.models.goal.today_date") as mock_today:
            mock_today.return_value = date(2025, 12, 16)
            assert goal.is_due_for_review() is False


class TestGoalCompleteReview:
    """Tests for Goal.complete_review method."""

    def test_complete_review_sets_last_reviewed_at(self) -> None:
        """complete_review sets last_reviewed_at to current time."""
        goal = Goal(
            title="Test Goal",
            problem_statement="Problem",
            solution_vision="Vision",
            next_review_date=date(2025, 1, 1),
        )

        with (
            patch("jdo.models.goal.today_date") as mock_today,
            patch("jdo.models.goal.utc_now") as mock_now,
        ):
            mock_today.return_value = date(2025, 12, 16)
            mock_now.return_value = datetime(2025, 12, 16, 10, 0, 0, tzinfo=UTC)

            goal.complete_review()

            assert goal.last_reviewed_at == datetime(2025, 12, 16, 10, 0, 0, tzinfo=UTC)

    def test_complete_review_calculates_next_review_date_from_interval(self) -> None:
        """complete_review calculates next_review_date from interval."""
        goal = Goal(
            title="Test Goal",
            problem_statement="Problem",
            solution_vision="Vision",
            next_review_date=date(2025, 1, 1),
            review_interval_days=30,  # Monthly
        )

        with (
            patch("jdo.models.goal.today_date") as mock_today,
            patch("jdo.models.goal.utc_now") as mock_now,
        ):
            mock_today.return_value = date(2025, 12, 16)
            mock_now.return_value = datetime(2025, 12, 16, 10, 0, 0, tzinfo=UTC)

            goal.complete_review()

            # Next review should be today + 30 days
            assert goal.next_review_date == date(2025, 12, 16) + timedelta(days=30)

    def test_complete_review_with_no_interval_clears_next_review_date(self) -> None:
        """complete_review with no interval clears next_review_date."""
        goal = Goal(
            title="Test Goal",
            problem_statement="Problem",
            solution_vision="Vision",
            next_review_date=date(2025, 1, 1),
            review_interval_days=None,
        )

        with (
            patch("jdo.models.goal.today_date") as mock_today,
            patch("jdo.models.goal.utc_now") as mock_now,
        ):
            mock_today.return_value = date(2025, 12, 16)
            mock_now.return_value = datetime(2025, 12, 16, 10, 0, 0, tzinfo=UTC)

            goal.complete_review()

            assert goal.next_review_date is None

    def test_complete_review_updates_updated_at(self) -> None:
        """complete_review updates the updated_at timestamp."""
        goal = Goal(
            title="Test Goal",
            problem_statement="Problem",
            solution_vision="Vision",
            next_review_date=date(2025, 1, 1),
        )
        original_updated_at = goal.updated_at

        with (
            patch("jdo.models.goal.today_date") as mock_today,
            patch("jdo.models.goal.utc_now") as mock_now,
        ):
            mock_today.return_value = date(2025, 12, 16)
            new_time = datetime(2025, 12, 16, 10, 0, 0, tzinfo=UTC)
            mock_now.return_value = new_time

            goal.complete_review()

            assert goal.updated_at == new_time


class TestGetGoalsDueForReview:
    """Tests for get_goals_due_for_review query."""

    def test_returns_goals_due_for_review(self, tmp_path: Path) -> None:
        """Returns only active goals with past/current review dates."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_goals_due_for_review, get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Create goals with various states
            past_date = date(2025, 1, 1)
            future_date = date(2026, 1, 1)
            today = date(2025, 12, 16)

            goal_due = Goal(
                title="Due Goal",
                problem_statement="Problem",
                solution_vision="Vision",
                next_review_date=past_date,
                status=GoalStatus.ACTIVE,
            )

            goal_today = Goal(
                title="Due Today",
                problem_statement="Problem",
                solution_vision="Vision",
                next_review_date=today,
                status=GoalStatus.ACTIVE,
            )

            goal_future = Goal(
                title="Future Goal",
                problem_statement="Problem",
                solution_vision="Vision",
                next_review_date=future_date,
                status=GoalStatus.ACTIVE,
            )

            goal_on_hold = Goal(
                title="On Hold Goal",
                problem_statement="Problem",
                solution_vision="Vision",
                next_review_date=past_date,
                status=GoalStatus.ON_HOLD,
            )

            goal_no_date = Goal(
                title="No Review Date",
                problem_statement="Problem",
                solution_vision="Vision",
                next_review_date=None,
                status=GoalStatus.ACTIVE,
            )

            with get_session() as session:
                session.add(goal_due)
                session.add(goal_today)
                session.add(goal_future)
                session.add(goal_on_hold)
                session.add(goal_no_date)

            with (
                get_session() as session,
                patch("jdo.db.session.today_date") as mock_today,
            ):
                mock_today.return_value = date(2025, 12, 16)

                due_goals = get_goals_due_for_review(session)

                titles = {g.title for g in due_goals}
                assert "Due Goal" in titles
                assert "Due Today" in titles
                assert "Future Goal" not in titles
                assert "On Hold Goal" not in titles
                assert "No Review Date" not in titles

        reset_engine()

    def test_returns_empty_list_when_no_goals_due(self, tmp_path: Path) -> None:
        """Returns empty list when no goals are due for review."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_goals_due_for_review, get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Create only future goals
            goal = Goal(
                title="Future Goal",
                problem_statement="Problem",
                solution_vision="Vision",
                next_review_date=date(2026, 1, 1),
                status=GoalStatus.ACTIVE,
            )

            with get_session() as session:
                session.add(goal)

            with (
                get_session() as session,
                patch("jdo.db.session.today_date") as mock_today,
            ):
                mock_today.return_value = date(2025, 12, 16)

                due_goals = get_goals_due_for_review(session)

                assert len(due_goals) == 0

        reset_engine()
