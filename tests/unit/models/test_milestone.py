"""Tests for Milestone SQLModel - TDD Red phase."""

from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlmodel import SQLModel

from jdo.models.milestone import Milestone, MilestoneStatus


class TestMilestoneModel:
    """Tests for Milestone model structure."""

    def test_inherits_from_sqlmodel_with_table_true(self) -> None:
        """Milestone inherits from SQLModel with table=True."""
        assert issubclass(Milestone, SQLModel)
        assert hasattr(Milestone, "__tablename__")

    def test_has_tablename_milestones(self) -> None:
        """Milestone has tablename 'milestones'."""
        assert Milestone.__tablename__ == "milestones"

    def test_has_required_fields(self) -> None:
        """Milestone has all required fields."""
        fields = Milestone.model_fields
        assert "id" in fields
        assert "goal_id" in fields
        assert "title" in fields
        assert "description" in fields
        assert "target_date" in fields
        assert "status" in fields
        assert "completed_at" in fields
        assert "created_at" in fields
        assert "updated_at" in fields


class TestMilestoneValidation:
    """Tests for Milestone field validation."""

    def test_creates_with_required_fields(self) -> None:
        """Create milestone with required fields."""
        goal_id = uuid4()
        milestone = Milestone(
            goal_id=goal_id,
            title="Complete first draft",
            target_date=date(2025, 6, 1),
        )

        assert milestone.goal_id == goal_id
        assert milestone.title == "Complete first draft"
        assert milestone.target_date == date(2025, 6, 1)
        assert milestone.status == MilestoneStatus.PENDING
        assert isinstance(milestone.id, UUID)

    def test_validates_goal_id_required(self) -> None:
        """Reject missing goal_id via model_validate."""
        with pytest.raises(ValueError, match="Field required"):
            Milestone.model_validate(
                {
                    "title": "Some title",
                    "target_date": date(2025, 6, 1),
                }
            )

    def test_validates_title_non_empty(self) -> None:
        """Reject empty title via model_validate."""
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            Milestone.model_validate(
                {
                    "goal_id": uuid4(),
                    "title": "",
                    "target_date": date(2025, 6, 1),
                }
            )

    def test_validates_target_date_required(self) -> None:
        """Reject missing target_date via model_validate."""
        with pytest.raises(ValueError, match="Field required"):
            Milestone.model_validate(
                {
                    "goal_id": uuid4(),
                    "title": "Some title",
                }
            )

    def test_status_defaults_to_pending(self) -> None:
        """Status defaults to pending."""
        milestone = Milestone(
            goal_id=uuid4(),
            title="Test Milestone",
            target_date=date(2025, 6, 1),
        )

        assert milestone.status == MilestoneStatus.PENDING

    def test_optional_fields_default_to_none(self) -> None:
        """Optional fields default to None."""
        milestone = Milestone(
            goal_id=uuid4(),
            title="Test Milestone",
            target_date=date(2025, 6, 1),
        )

        assert milestone.description is None
        assert milestone.completed_at is None

    def test_auto_generates_id_and_timestamps(self) -> None:
        """Auto-generates id, created_at, updated_at."""
        milestone = Milestone(
            goal_id=uuid4(),
            title="Test Milestone",
            target_date=date(2025, 6, 1),
        )

        assert isinstance(milestone.id, UUID)
        assert isinstance(milestone.created_at, datetime)
        assert isinstance(milestone.updated_at, datetime)


class TestMilestoneStatus:
    """Tests for MilestoneStatus enum."""

    def test_has_required_values(self) -> None:
        """MilestoneStatus has pending, in_progress, completed, missed."""
        assert MilestoneStatus.PENDING.value == "pending"
        assert MilestoneStatus.IN_PROGRESS.value == "in_progress"
        assert MilestoneStatus.COMPLETED.value == "completed"
        assert MilestoneStatus.MISSED.value == "missed"


class TestMilestoneStatusTransitions:
    """Tests for Milestone status transitions."""

    def test_transition_pending_to_in_progress(self) -> None:
        """Transition pending -> in_progress."""
        milestone = Milestone(
            goal_id=uuid4(),
            title="Test Milestone",
            target_date=date(2025, 6, 1),
            status=MilestoneStatus.PENDING,
        )

        milestone.start()

        assert milestone.status == MilestoneStatus.IN_PROGRESS

    def test_transition_to_completed_sets_completed_at(self) -> None:
        """Transition to completed sets completed_at."""
        milestone = Milestone(
            goal_id=uuid4(),
            title="Test Milestone",
            target_date=date(2025, 6, 1),
            status=MilestoneStatus.IN_PROGRESS,
        )

        milestone.complete()

        assert milestone.status == MilestoneStatus.COMPLETED
        assert milestone.completed_at is not None
        assert isinstance(milestone.completed_at, datetime)

    def test_is_overdue_when_pending_and_past_target(self) -> None:
        """Milestone is overdue when pending and target_date passed."""
        milestone = Milestone(
            goal_id=uuid4(),
            title="Test Milestone",
            target_date=date.today() - timedelta(days=7),
            status=MilestoneStatus.PENDING,
        )

        assert milestone.is_overdue()

    def test_not_overdue_when_in_progress(self) -> None:
        """Milestone is not considered overdue if in_progress (active work)."""
        milestone = Milestone(
            goal_id=uuid4(),
            title="Test Milestone",
            target_date=date.today() - timedelta(days=7),
            status=MilestoneStatus.IN_PROGRESS,
        )

        # in_progress means actively working - still overdue for reporting
        assert milestone.is_overdue()

    def test_not_overdue_when_completed(self) -> None:
        """Milestone is not overdue when completed."""
        milestone = Milestone(
            goal_id=uuid4(),
            title="Test Milestone",
            target_date=date.today() - timedelta(days=7),
            status=MilestoneStatus.COMPLETED,
        )

        assert not milestone.is_overdue()

    def test_not_overdue_when_missed(self) -> None:
        """Milestone is not considered overdue if already missed."""
        milestone = Milestone(
            goal_id=uuid4(),
            title="Test Milestone",
            target_date=date.today() - timedelta(days=7),
            status=MilestoneStatus.MISSED,
        )

        assert not milestone.is_overdue()

    def test_mark_missed_transitions_status(self) -> None:
        """mark_missed transitions status to missed."""
        milestone = Milestone(
            goal_id=uuid4(),
            title="Test Milestone",
            target_date=date.today() - timedelta(days=7),
            status=MilestoneStatus.PENDING,
        )

        milestone.mark_missed()

        assert milestone.status == MilestoneStatus.MISSED

    def test_missed_milestone_can_be_completed(self) -> None:
        """Missed milestone can still be completed (late completion)."""
        milestone = Milestone(
            goal_id=uuid4(),
            title="Test Milestone",
            target_date=date.today() - timedelta(days=7),
            status=MilestoneStatus.MISSED,
        )

        milestone.complete()

        assert milestone.status == MilestoneStatus.COMPLETED
        assert milestone.completed_at is not None


class TestMilestonePersistence:
    """Tests for Milestone database persistence."""

    def test_save_and_retrieve(self, tmp_path: Path) -> None:
        """Save milestone via session and retrieve by id."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.models.goal import Goal

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Create a goal first
            goal = Goal(
                title="Test Goal",
                problem_statement="Test problem",
                solution_vision="Test vision",
            )
            goal_id = goal.id  # Save ID before session

            with get_session() as session:
                session.add(goal)

            milestone = Milestone(
                goal_id=goal_id,
                title="Test Milestone",
                target_date=date(2025, 6, 1),
            )
            original_id = milestone.id

            with get_session() as session:
                session.add(milestone)

            with get_session() as session:
                result = session.exec(select(Milestone).where(Milestone.id == original_id)).first()

                assert result is not None
                assert result.title == "Test Milestone"
                assert result.status == MilestoneStatus.PENDING

        reset_engine()

    def test_list_milestones_by_goal_sorted_by_date(self, tmp_path: Path) -> None:
        """List milestones by goal_id sorted by target_date."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.models.goal import Goal

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            goal = Goal(
                title="Test Goal",
                problem_statement="Test problem",
                solution_vision="Test vision",
            )
            goal_id = goal.id  # Save ID before session

            with get_session() as session:
                session.add(goal)

            milestone1 = Milestone(
                goal_id=goal_id,
                title="Milestone 3 (later)",
                target_date=date(2025, 9, 1),
            )
            milestone2 = Milestone(
                goal_id=goal_id,
                title="Milestone 1 (earliest)",
                target_date=date(2025, 3, 1),
            )
            milestone3 = Milestone(
                goal_id=goal_id,
                title="Milestone 2 (middle)",
                target_date=date(2025, 6, 1),
            )

            with get_session() as session:
                session.add(milestone1)
                session.add(milestone2)
                session.add(milestone3)

            with get_session() as session:
                result = session.exec(
                    select(Milestone).where(Milestone.goal_id == goal_id).order_by("target_date")
                ).all()

                assert len(result) == 3
                assert result[0].title == "Milestone 1 (earliest)"
                assert result[1].title == "Milestone 2 (middle)"
                assert result[2].title == "Milestone 3 (later)"

        reset_engine()

    def test_query_milestones_at_risk(self, tmp_path: Path) -> None:
        """Query milestones at risk (target_date within 7 days, status=pending)."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.models.goal import Goal

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            goal = Goal(
                title="Test Goal",
                problem_statement="Test problem",
                solution_vision="Test vision",
            )
            goal_id = goal.id  # Save ID before session

            with get_session() as session:
                session.add(goal)

            # At risk (pending, due in 5 days)
            at_risk = Milestone(
                goal_id=goal_id,
                title="At Risk",
                target_date=date.today() + timedelta(days=5),
                status=MilestoneStatus.PENDING,
            )
            # Not at risk (in progress)
            not_at_risk_status = Milestone(
                goal_id=goal_id,
                title="In Progress",
                target_date=date.today() + timedelta(days=5),
                status=MilestoneStatus.IN_PROGRESS,
            )
            # Not at risk (too far out)
            not_at_risk_date = Milestone(
                goal_id=goal_id,
                title="Future",
                target_date=date.today() + timedelta(days=30),
                status=MilestoneStatus.PENDING,
            )

            with get_session() as session:
                session.add(at_risk)
                session.add(not_at_risk_status)
                session.add(not_at_risk_date)

            with get_session() as session:
                seven_days = date.today() + timedelta(days=7)
                result = session.exec(
                    select(Milestone).where(
                        Milestone.status == MilestoneStatus.PENDING,
                        Milestone.target_date <= seven_days,
                    )
                ).all()

                assert len(result) == 1
                assert result[0].title == "At Risk"

        reset_engine()
