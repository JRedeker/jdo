"""Tests for Goal SQLModel - TDD Red phase."""

from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlmodel import SQLModel

from jdo.models.goal import Goal, GoalStatus


class TestGoalModel:
    """Tests for Goal model structure."""

    def test_inherits_from_sqlmodel_with_table_true(self) -> None:
        """Goal inherits from SQLModel with table=True."""
        assert issubclass(Goal, SQLModel)
        assert hasattr(Goal, "__tablename__")

    def test_has_tablename_goals(self) -> None:
        """Goal has tablename 'goals'."""
        assert Goal.__tablename__ == "goals"

    def test_has_required_fields(self) -> None:
        """Goal has all required fields."""
        fields = Goal.model_fields
        assert "id" in fields
        assert "title" in fields
        assert "problem_statement" in fields
        assert "solution_vision" in fields
        assert "motivation" in fields
        assert "parent_goal_id" in fields
        assert "vision_id" in fields  # NEW: Vision hierarchy link
        assert "status" in fields
        assert "next_review_date" in fields
        assert "review_interval_days" in fields
        assert "last_reviewed_at" in fields
        assert "created_at" in fields
        assert "updated_at" in fields


class TestGoalValidation:
    """Tests for Goal field validation."""

    def test_creates_with_required_fields(self) -> None:
        """Create goal with required fields."""
        goal = Goal(
            title="Learn Python",
            problem_statement="Need to improve coding skills",
            solution_vision="Become proficient in Python",
        )

        assert goal.title == "Learn Python"
        assert goal.problem_statement == "Need to improve coding skills"
        assert goal.solution_vision == "Become proficient in Python"
        assert goal.status == GoalStatus.ACTIVE
        assert isinstance(goal.id, UUID)

    def test_validates_title_non_empty(self) -> None:
        """Reject empty title via model_validate."""
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            Goal.model_validate(
                {
                    "title": "",
                    "problem_statement": "Problem",
                    "solution_vision": "Vision",
                }
            )

    def test_validates_problem_statement_non_empty(self) -> None:
        """Reject empty problem_statement via model_validate."""
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            Goal.model_validate(
                {
                    "title": "Title",
                    "problem_statement": "",
                    "solution_vision": "Vision",
                }
            )

    def test_validates_solution_vision_non_empty(self) -> None:
        """Reject empty solution_vision via model_validate."""
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            Goal.model_validate(
                {
                    "title": "Title",
                    "problem_statement": "Problem",
                    "solution_vision": "",
                }
            )

    def test_optional_fields_default_to_none(self) -> None:
        """Optional fields default to None."""
        goal = Goal(
            title="Test Goal",
            problem_statement="Test problem",
            solution_vision="Test vision",
        )

        assert goal.motivation is None
        assert goal.parent_goal_id is None
        assert goal.vision_id is None  # NEW: Vision hierarchy link
        assert goal.next_review_date is None
        assert goal.review_interval_days is None
        assert goal.last_reviewed_at is None

    def test_validates_review_interval_days(self) -> None:
        """Only 7, 30, or 90 allowed for review_interval_days."""
        # Valid values
        for days in [7, 30, 90]:
            goal = Goal(
                title="Test",
                problem_statement="Problem",
                solution_vision="Vision",
                review_interval_days=days,
            )
            assert goal.review_interval_days == days

        # Invalid value
        with pytest.raises(ValueError, match="Review interval must be 7, 30, or 90"):
            Goal.model_validate(
                {
                    "title": "Test",
                    "problem_statement": "Problem",
                    "solution_vision": "Vision",
                    "review_interval_days": 15,
                }
            )


class TestGoalStatus:
    """Tests for GoalStatus enum."""

    def test_has_required_values(self) -> None:
        """GoalStatus has active, on_hold, achieved, abandoned."""
        assert GoalStatus.ACTIVE.value == "active"
        assert GoalStatus.ON_HOLD.value == "on_hold"
        assert GoalStatus.ACHIEVED.value == "achieved"
        assert GoalStatus.ABANDONED.value == "abandoned"


class TestGoalSelfReferential:
    """Tests for Goal self-referential parent_goal_id."""

    def test_accepts_parent_goal_id(self) -> None:
        """Goal accepts parent_goal_id for nesting."""
        parent_id = uuid4()
        goal = Goal(
            title="Child Goal",
            problem_statement="Problem",
            solution_vision="Vision",
            parent_goal_id=parent_id,
        )

        assert goal.parent_goal_id == parent_id


class TestGoalPersistence:
    """Tests for Goal database persistence."""

    def test_save_and_retrieve(self, tmp_path: Path) -> None:
        """Save goal via session and retrieve by id."""
        from sqlmodel import select

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
                problem_statement="Test problem",
                solution_vision="Test vision",
            )
            original_id = goal.id

            with get_session() as session:
                session.add(goal)

            with get_session() as session:
                result = session.exec(select(Goal).where(Goal.id == original_id)).first()

                assert result is not None
                assert result.title == "Test Goal"
                assert result.status == GoalStatus.ACTIVE

        reset_engine()

    def test_nested_goals_via_parent_goal_id(self, tmp_path: Path) -> None:
        """Save nested goals with parent-child relationship."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            parent = Goal(
                title="Parent Goal",
                problem_statement="Parent problem",
                solution_vision="Parent vision",
            )
            parent_id = parent.id  # Save ID before session

            with get_session() as session:
                session.add(parent)

            child = Goal(
                title="Child Goal",
                problem_statement="Child problem",
                solution_vision="Child vision",
                parent_goal_id=parent_id,
            )

            with get_session() as session:
                session.add(child)

            with get_session() as session:
                result = session.exec(select(Goal).where(Goal.parent_goal_id == parent_id)).first()

                assert result is not None
                assert result.title == "Child Goal"

        reset_engine()


class TestGoalVisionLink:
    """Tests for Goal-Vision linkage."""

    def test_accepts_vision_id(self) -> None:
        """Goal accepts optional vision_id."""
        vision_id = uuid4()
        goal = Goal(
            title="Goal with Vision",
            problem_statement="Problem",
            solution_vision="Vision",
            vision_id=vision_id,
        )

        assert goal.vision_id == vision_id

    def test_goal_without_vision_id(self) -> None:
        """Goal can be created without vision_id."""
        goal = Goal(
            title="Standalone Goal",
            problem_statement="Problem",
            solution_vision="Vision",
        )

        assert goal.vision_id is None

    def test_goal_links_to_vision_in_database(self, tmp_path: Path) -> None:
        """Goal with vision_id links to Vision in database."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.models.vision import Vision

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Create a vision first
            vision = Vision(
                title="Test Vision",
                narrative="Test narrative",
            )
            vision_id = vision.id

            with get_session() as session:
                session.add(vision)

            # Create a goal linked to the vision
            goal = Goal(
                title="Goal Linked to Vision",
                problem_statement="Problem",
                solution_vision="Vision",
                vision_id=vision_id,
            )
            goal_id = goal.id

            with get_session() as session:
                session.add(goal)

            with get_session() as session:
                result = session.exec(select(Goal).where(Goal.id == goal_id)).first()

                assert result is not None
                assert result.vision_id == vision_id

        reset_engine()

    def test_query_goals_by_vision_id(self, tmp_path: Path) -> None:
        """Query goals linked to a specific vision."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.models.vision import Vision

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Create two visions
            vision1 = Vision(title="Vision 1", narrative="Narrative 1")
            vision2 = Vision(title="Vision 2", narrative="Narrative 2")
            vision1_id = vision1.id
            vision2_id = vision2.id

            with get_session() as session:
                session.add(vision1)
                session.add(vision2)

            # Create goals linked to different visions
            goal1 = Goal(
                title="Goal 1 for Vision 1",
                problem_statement="Problem",
                solution_vision="Vision",
                vision_id=vision1_id,
            )
            goal2 = Goal(
                title="Goal 2 for Vision 1",
                problem_statement="Problem",
                solution_vision="Vision",
                vision_id=vision1_id,
            )
            goal3 = Goal(
                title="Goal for Vision 2",
                problem_statement="Problem",
                solution_vision="Vision",
                vision_id=vision2_id,
            )

            with get_session() as session:
                session.add(goal1)
                session.add(goal2)
                session.add(goal3)

            with get_session() as session:
                result = session.exec(select(Goal).where(Goal.vision_id == vision1_id)).all()

                assert len(result) == 2
                titles = {g.title for g in result}
                assert titles == {"Goal 1 for Vision 1", "Goal 2 for Vision 1"}

        reset_engine()
