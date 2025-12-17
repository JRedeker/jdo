"""Tests for Goal progress calculation.

Phase 2: Goal Progress - shows commitment counts by status.
"""

from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

from sqlmodel import SQLModel

from jdo.db.session import get_commitment_progress
from jdo.models import Commitment, Goal, Stakeholder
from jdo.models.commitment import CommitmentStatus
from jdo.models.stakeholder import StakeholderType


class TestGoalProgressDataclass:
    """Tests for GoalProgress dataclass structure."""

    def test_goal_progress_exists(self) -> None:
        """GoalProgress dataclass exists in goal module."""
        from jdo.models.goal import GoalProgress

        assert GoalProgress is not None

    def test_goal_progress_has_required_fields(self) -> None:
        """GoalProgress has all count fields."""
        from jdo.models.goal import GoalProgress

        progress = GoalProgress(
            total=10,
            completed=4,
            in_progress=3,
            pending=2,
            abandoned=1,
        )

        assert progress.total == 10
        assert progress.completed == 4
        assert progress.in_progress == 3
        assert progress.pending == 2
        assert progress.abandoned == 1

    def test_goal_progress_zero_counts(self) -> None:
        """GoalProgress handles all zeros."""
        from jdo.models.goal import GoalProgress

        progress = GoalProgress(
            total=0,
            completed=0,
            in_progress=0,
            pending=0,
            abandoned=0,
        )

        assert progress.total == 0

    def test_goal_progress_completion_rate(self) -> None:
        """GoalProgress calculates completion_rate correctly."""
        from jdo.models.goal import GoalProgress

        # 4 completed out of 9 non-abandoned (10 total - 1 abandoned)
        progress = GoalProgress(
            total=10,
            completed=4,
            in_progress=3,
            pending=2,
            abandoned=1,
        )

        # 4 / 9 = 0.444...
        assert abs(progress.completion_rate - (4 / 9)) < 0.001

    def test_goal_progress_completion_rate_all_abandoned(self) -> None:
        """GoalProgress returns 0.0 when all commitments abandoned."""
        from jdo.models.goal import GoalProgress

        progress = GoalProgress(
            total=5,
            completed=0,
            in_progress=0,
            pending=0,
            abandoned=5,
        )

        assert progress.completion_rate == 0.0

    def test_goal_progress_completion_rate_no_commitments(self) -> None:
        """GoalProgress returns 0.0 when no commitments exist."""
        from jdo.models.goal import GoalProgress

        progress = GoalProgress(
            total=0,
            completed=0,
            in_progress=0,
            pending=0,
            abandoned=0,
        )

        assert progress.completion_rate == 0.0


class TestGetCommitmentProgress:
    """Tests for Goal.get_commitment_progress method."""

    def test_goal_with_no_commitments(self, tmp_path: Path) -> None:
        """Goal with no commitments returns all zeros."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            goal = Goal(
                title="Test Goal",
                problem_statement="Problem",
                solution_vision="Vision",
            )
            goal_id = goal.id  # Save ID before session closes

            with get_session() as session:
                session.add(goal)

            with get_session() as session:
                from jdo.db.session import get_commitment_progress

                progress = get_commitment_progress(session, goal_id)

                assert progress.total == 0
                assert progress.completed == 0
                assert progress.in_progress == 0
                assert progress.pending == 0
                assert progress.abandoned == 0

        reset_engine()

    def test_goal_with_mixed_commitment_statuses(self, tmp_path: Path) -> None:
        """Goal with various commitment statuses returns correct counts."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Create stakeholder
            stakeholder = Stakeholder(name="Test Team", type=StakeholderType.TEAM)
            stakeholder_id = stakeholder.id

            # Create goal
            goal = Goal(
                title="Test Goal",
                problem_statement="Problem",
                solution_vision="Vision",
            )
            goal_id = goal.id

            with get_session() as session:
                session.add(stakeholder)
                session.add(goal)

            # Create commitments with various statuses
            tomorrow = date.today() + timedelta(days=1)

            with get_session() as session:
                # 2 completed
                for _ in range(2):
                    c = Commitment(
                        deliverable="Done",
                        stakeholder_id=stakeholder_id,
                        goal_id=goal_id,
                        due_date=tomorrow,
                        status=CommitmentStatus.COMPLETED,
                    )
                    session.add(c)

                # 3 in_progress
                for _ in range(3):
                    c = Commitment(
                        deliverable="Working",
                        stakeholder_id=stakeholder_id,
                        goal_id=goal_id,
                        due_date=tomorrow,
                        status=CommitmentStatus.IN_PROGRESS,
                    )
                    session.add(c)

                # 4 pending
                for _ in range(4):
                    c = Commitment(
                        deliverable="Todo",
                        stakeholder_id=stakeholder_id,
                        goal_id=goal_id,
                        due_date=tomorrow,
                        status=CommitmentStatus.PENDING,
                    )
                    session.add(c)

                # 1 abandoned
                c = Commitment(
                    deliverable="Dropped",
                    stakeholder_id=stakeholder_id,
                    goal_id=goal_id,
                    due_date=tomorrow,
                    status=CommitmentStatus.ABANDONED,
                )
                session.add(c)

            with get_session() as session:
                from jdo.db.session import get_commitment_progress

                progress = get_commitment_progress(session, goal_id)

                assert progress.total == 10
                assert progress.completed == 2
                assert progress.in_progress == 3
                assert progress.pending == 4
                assert progress.abandoned == 1

        reset_engine()
