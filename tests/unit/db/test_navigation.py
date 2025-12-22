"""Unit tests for NavigationService."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from jdo.db.navigation import NavigationService
from jdo.models import Commitment, Goal, Milestone, Stakeholder, Vision
from jdo.models.commitment import CommitmentStatus
from jdo.models.goal import GoalStatus
from jdo.models.milestone import MilestoneStatus
from jdo.models.stakeholder import StakeholderType
from jdo.models.vision import VisionStatus


class TestNavigationService:
    """Tests for NavigationService methods."""

    def test_get_goals_list(self, db_session) -> None:
        """Test fetching goals list."""
        # Create test goals
        goal1 = Goal(
            title="Test Goal 1",
            problem_statement="Problem 1",
            solution_vision="Solution 1",
            status=GoalStatus.ACTIVE,
        )
        goal2 = Goal(
            title="Test Goal 2",
            problem_statement="Problem 2",
            solution_vision="Solution 2",
            status=GoalStatus.ACHIEVED,
        )
        db_session.add(goal1)
        db_session.add(goal2)
        db_session.flush()

        # Fetch goals list
        goals = NavigationService.get_goals_list(db_session)

        # Verify
        assert len(goals) == 2
        assert goals[0]["title"] == "Test Goal 1"
        assert goals[0]["problem_statement"] == "Problem 1"
        assert goals[0]["status"] == "active"
        assert goals[1]["title"] == "Test Goal 2"
        assert goals[1]["status"] == "achieved"

    def test_get_commitments_list(self, db_session) -> None:
        """Test fetching commitments list."""
        # Create test stakeholder and commitments
        stakeholder = Stakeholder(name="Test Stakeholder", type=StakeholderType.PERSON)
        db_session.add(stakeholder)
        db_session.flush()

        commitment1 = Commitment(
            deliverable="Test Deliverable 1",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 1, 15),
            status=CommitmentStatus.PENDING,
        )
        commitment2 = Commitment(
            deliverable="Test Deliverable 2",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 2, 1),
            status=CommitmentStatus.IN_PROGRESS,
        )
        db_session.add(commitment1)
        db_session.add(commitment2)
        db_session.flush()

        # Fetch commitments list
        commitments = NavigationService.get_commitments_list(db_session)

        # Verify
        assert len(commitments) == 2
        assert commitments[0]["deliverable"] == "Test Deliverable 1"
        assert commitments[0]["stakeholder_name"] == "Test Stakeholder"
        assert commitments[0]["due_date"] == "2025-01-15"
        assert commitments[0]["status"] == "pending"

    def test_get_visions_list(self, db_session) -> None:
        """Test fetching visions list."""
        # Create test visions
        vision1 = Vision(
            title="Test Vision 1",
            narrative="Narrative 1",
            timeframe="1 year",
            status=VisionStatus.ACTIVE,
        )
        vision2 = Vision(
            title="Test Vision 2",
            narrative="Narrative 2",
            timeframe="6 months",
            status=VisionStatus.ACHIEVED,
        )
        db_session.add(vision1)
        db_session.add(vision2)
        db_session.flush()

        # Fetch visions list
        visions = NavigationService.get_visions_list(db_session)

        # Verify
        assert len(visions) == 2
        assert visions[0]["title"] == "Test Vision 1"
        assert visions[0]["timeframe"] == "1 year"
        assert visions[0]["status"] == "active"

    def test_get_milestones_list(self, db_session) -> None:
        """Test fetching milestones list."""
        # Create test goal first (milestone requires goal_id)
        goal = Goal(
            title="Test Goal",
            problem_statement="Problem",
            solution_vision="Solution",
            status=GoalStatus.ACTIVE,
        )
        db_session.add(goal)
        db_session.flush()

        # Create test milestone
        milestone = Milestone(
            title="Test Milestone",
            description="Test Description",
            target_date=date(2025, 3, 1),
            status=MilestoneStatus.PENDING,
            goal_id=goal.id,
        )
        db_session.add(milestone)
        db_session.flush()

        # Fetch milestones list
        milestones = NavigationService.get_milestones_list(db_session)

        # Verify
        assert len(milestones) == 1
        assert milestones[0]["description"] == "Test Description"
        assert milestones[0]["target_date"] == "2025-03-01"
        assert milestones[0]["status"] == "pending"

    def test_get_orphans_list(self, db_session) -> None:
        """Test fetching orphan commitments list."""
        # Create stakeholder
        stakeholder = Stakeholder(name="Test Stakeholder", type=StakeholderType.PERSON)
        db_session.add(stakeholder)
        db_session.flush()

        # Create goal and commitments
        goal = Goal(
            title="Test Goal",
            problem_statement="Problem",
            solution_vision="Solution",
            status=GoalStatus.ACTIVE,
        )
        db_session.add(goal)
        db_session.flush()

        # Orphan commitment (no goal_id)
        orphan = Commitment(
            deliverable="Orphan Deliverable",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 1, 15),
            status=CommitmentStatus.PENDING,
            goal_id=None,
        )
        # Non-orphan commitment (has goal_id)
        non_orphan = Commitment(
            deliverable="Non-Orphan Deliverable",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 2, 1),
            status=CommitmentStatus.PENDING,
            goal_id=goal.id,
        )
        db_session.add(orphan)
        db_session.add(non_orphan)
        db_session.flush()

        # Fetch orphans list
        orphans = NavigationService.get_orphans_list(db_session)

        # Verify - should only get the orphan commitment
        assert len(orphans) == 1
        assert orphans[0]["deliverable"] == "Orphan Deliverable"
        assert orphans[0]["stakeholder_name"] == "Test Stakeholder"

    def test_get_integrity_data(self, db_session) -> None:
        """Test fetching integrity dashboard data."""
        # Fetch integrity data (should work even with no commitments)
        integrity_data = NavigationService.get_integrity_data(db_session)

        # Verify basic structure
        assert "composite_score" in integrity_data
        assert "letter_grade" in integrity_data
        assert "on_time_rate" in integrity_data
        assert "notification_timeliness" in integrity_data
        assert "cleanup_completion_rate" in integrity_data
        assert "current_streak_weeks" in integrity_data

        # New user should have excellent score
        assert integrity_data["letter_grade"] in ("A+", "A")  # May vary based on calculation
        assert integrity_data["composite_score"] >= 95.0

    def test_get_empty_lists(self, db_session) -> None:
        """Test fetching empty lists when no data exists."""
        # Fetch empty lists
        goals = NavigationService.get_goals_list(db_session)
        commitments = NavigationService.get_commitments_list(db_session)
        visions = NavigationService.get_visions_list(db_session)
        milestones = NavigationService.get_milestones_list(db_session)
        orphans = NavigationService.get_orphans_list(db_session)

        # Verify all are empty
        assert goals == []
        assert commitments == []
        assert visions == []
        assert milestones == []
        assert orphans == []
