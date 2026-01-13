"""Tests for detail panel formatters."""

from __future__ import annotations

from datetime import date, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from jdo.models.goal import Goal, GoalStatus
from jdo.models.milestone import Milestone, MilestoneStatus
from jdo.models.task import ActualHoursCategory, EstimationConfidence, SubTask, Task, TaskStatus


class TestTaskDetailFormatting:
    """Tests for task detail and proposal formatting."""

    def test_format_task_detail_minimal(self) -> None:
        """Test formatting task detail with minimal fields."""
        from jdo.output.task import format_task_detail

        task = Task(
            commitment_id=uuid4(),
            title="Test Task",
            scope="Test scope",
            order=1,
        )
        panel = format_task_detail(task)

        assert panel is not None
        assert "Test Task" in str(panel.renderable)

    def test_format_task_detail_with_all_fields(self) -> None:
        """Test formatting task detail with all fields populated."""
        from jdo.output.task import format_task_detail

        task = Task(
            commitment_id=uuid4(),
            title="Full Task",
            scope="Complete scope description",
            order=1,
            status=TaskStatus.IN_PROGRESS,
            estimated_hours=4.5,
            estimation_confidence=EstimationConfidence.HIGH,
            actual_hours_category=ActualHoursCategory.ON_TARGET,
        )
        panel = format_task_detail(task)

        assert panel is not None
        content = str(panel.renderable)
        assert "Full Task" in content
        assert "Complete scope description" in content

    def test_format_task_detail_with_subtasks(self) -> None:
        """Test formatting task detail with subtasks."""
        from jdo.output.task import format_task_detail

        task = Task(
            commitment_id=uuid4(),
            title="Multi-step Task",
            scope="Has subtasks",
            order=1,
            sub_tasks=[
                {"description": "Step 1", "completed": False},
                {"description": "Step 2", "completed": True},
            ],
        )
        panel = format_task_detail(task)

        assert panel is not None
        content = str(panel.renderable)
        assert "Subtasks" in content
        assert "[ ] Step 1" in content
        assert "[x] Step 2" in content

    def test_format_task_proposal_minimal(self) -> None:
        """Test formatting task proposal with minimal fields."""
        from jdo.output.task import format_task_proposal

        panel = format_task_proposal(
            title="New Task",
            scope="What needs to be done",
        )

        assert panel is not None
        content = str(panel.renderable)
        assert "New Task" in content
        assert "What needs to be done" in content
        assert "Does this look right?" in content

    def test_format_task_proposal_with_hours(self) -> None:
        """Test formatting task proposal with time estimate."""
        from jdo.output.task import format_task_proposal

        panel = format_task_proposal(
            title="Estimated Task",
            scope="Task with time estimate",
            estimated_hours=3.0,
        )

        assert panel is not None
        content = str(panel.renderable)
        assert "3.0h" in content

    def test_format_task_proposal_with_commitment(self) -> None:
        """Test formatting task proposal with parent commitment."""
        from jdo.output.task import format_task_proposal

        panel = format_task_proposal(
            title="Linked Task",
            scope="Task linked to commitment",
            commitment_deliverable="Parent commitment deliverable",
        )

        assert panel is not None
        content = str(panel.renderable)
        assert "Parent commitment deliverable" in content


class TestGoalDetailFormatting:
    """Tests for goal detail and proposal formatting."""

    def test_format_goal_detail_minimal(self) -> None:
        """Test formatting goal detail with minimal fields."""
        from jdo.output.goal import format_goal_detail

        goal = Goal(
            title="Test Goal",
            problem_statement="Problem to solve",
            solution_vision="Envisioned solution",
        )
        panel = format_goal_detail(goal)

        assert panel is not None
        content = str(panel.renderable)
        assert "Test Goal" in content
        assert "Problem to solve" in content

    def test_format_goal_detail_with_motivation(self) -> None:
        """Test formatting goal detail with motivation."""
        from jdo.output.goal import format_goal_detail

        goal = Goal(
            title="Motivated Goal",
            problem_statement="Problem",
            solution_vision="Solution",
            motivation="This matters because...",
        )
        panel = format_goal_detail(goal)

        assert panel is not None
        content = str(panel.renderable)
        assert "This matters because..." in content

    def test_format_goal_detail_with_review_date(self) -> None:
        """Test formatting goal detail with next review date."""
        from jdo.output.goal import format_goal_detail

        goal = Goal(
            title="Review Goal",
            problem_statement="Problem",
            solution_vision="Solution",
            next_review_date=date(2025, 6, 15),
        )
        panel = format_goal_detail(goal)

        assert panel is not None
        content = str(panel.renderable)
        assert "Next Review" in content

    def test_format_goal_proposal_minimal(self) -> None:
        """Test formatting goal proposal with minimal fields."""
        from jdo.output.goal import format_goal_proposal

        panel = format_goal_proposal(
            title="New Goal",
            problem_statement="The problem we're solving",
            solution_vision="What success looks like",
        )

        assert panel is not None
        content = str(panel.renderable)
        assert "New Goal" in content
        assert "problem we're solving" in content
        assert "success looks like" in content

    def test_format_goal_proposal_with_motivation(self) -> None:
        """Test formatting goal proposal with motivation."""
        from jdo.output.goal import format_goal_proposal

        panel = format_goal_proposal(
            title="Motivated Goal",
            problem_statement="Problem",
            solution_vision="Solution",
            motivation="Why this matters",
        )

        assert panel is not None
        content = str(panel.renderable)
        assert "Why this matters" in content

    def test_format_goal_proposal_with_vision(self) -> None:
        """Test formatting goal proposal with linked vision."""
        from jdo.output.goal import format_goal_proposal

        panel = format_goal_proposal(
            title="Linked Goal",
            problem_statement="Problem",
            solution_vision="Solution",
            vision_title="Parent Vision",
        )

        assert panel is not None
        content = str(panel.renderable)
        assert "Parent Vision" in content


class TestMilestoneDetailFormatting:
    """Tests for milestone detail and proposal formatting."""

    def test_format_milestone_detail_minimal(self) -> None:
        """Test formatting milestone detail with minimal fields."""
        from jdo.output.milestone import format_milestone_detail

        milestone = Milestone(
            title="Test Milestone",
            target_date=date(2025, 6, 15),
        )
        panel = format_milestone_detail(milestone)

        assert panel is not None
        content = str(panel.renderable)
        assert "Test Milestone" in content
        assert "2025-06-15" in content

    def test_format_milestone_detail_with_description(self) -> None:
        """Test formatting milestone detail with description."""
        from jdo.output.milestone import format_milestone_detail

        milestone = Milestone(
            title="Described Milestone",
            target_date=date(2025, 6, 15),
            description="This milestone represents...",
        )
        panel = format_milestone_detail(milestone)

        assert panel is not None
        content = str(panel.renderable)
        assert "This milestone represents..." in content

    def test_format_milestone_detail_with_completed_date(self) -> None:
        """Test formatting milestone detail with completed date."""
        from jdo.output.milestone import format_milestone_detail

        milestone = Milestone(
            title="Completed Milestone",
            target_date=date(2025, 1, 1),
            status=MilestoneStatus.COMPLETED,
            completed_at=date(2025, 1, 1),
        )
        panel = format_milestone_detail(milestone)

        assert panel is not None
        content = str(panel.renderable)
        assert "Completed" in content

    def test_format_milestone_proposal_minimal(self) -> None:
        """Test formatting milestone proposal with minimal fields."""
        from jdo.output.milestone import format_milestone_proposal

        panel = format_milestone_proposal(
            title="New Milestone",
            target_date="2025-06-15",
        )

        assert panel is not None
        content = str(panel.renderable)
        assert "New Milestone" in content
        assert "2025-06-15" in content

    def test_format_milestone_proposal_with_description(self) -> None:
        """Test formatting milestone proposal with description."""
        from jdo.output.milestone import format_milestone_proposal

        panel = format_milestone_proposal(
            title="Described Milestone",
            target_date="2025-06-15",
            description="What this milestone means",
        )

        assert panel is not None
        content = str(panel.renderable)
        assert "What this milestone means" in content

    def test_format_milestone_proposal_with_goal(self) -> None:
        """Test formatting milestone proposal with parent goal."""
        from jdo.output.milestone import format_milestone_proposal

        panel = format_milestone_proposal(
            title="Linked Milestone",
            target_date="2025-06-15",
            goal_title="Parent Goal",
        )

        assert panel is not None
        content = str(panel.renderable)
        assert "Parent Goal" in content
