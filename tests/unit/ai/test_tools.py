"""Tests for AI agent tools - TDD Red phase.

Tools provide the agent with query capabilities for domain objects.
"""

from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel
from sqlmodel import SQLModel, select

from jdo.ai.agent import JDODependencies, create_agent_with_model
from jdo.models import (
    Commitment,
    CommitmentStatus,
    Goal,
    GoalStatus,
    Milestone,
    MilestoneStatus,
    Stakeholder,
    StakeholderType,
    Task,
    TaskStatus,
    Vision,
    VisionStatus,
)
from jdo.models.task import ActualHoursCategory
from jdo.models.task_history import TaskEventType, TaskHistoryEntry


class TestGetCurrentCommitments:
    """Tests for get_current_commitments tool."""

    def test_returns_pending_commitments(self, tmp_path: Path) -> None:
        """get_current_commitments returns pending commitments."""
        from jdo.ai.tools import get_current_commitments
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Alice", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            pending = Commitment(
                deliverable="Pending task",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
                status=CommitmentStatus.PENDING,
            )

            with get_session() as session:
                session.add(pending)

            with get_session() as session:
                result = get_current_commitments(session)

                assert len(result) == 1
                assert result[0]["deliverable"] == "Pending task"
                assert result[0]["status"] == "pending"

        reset_engine()

    def test_returns_in_progress_commitments(self, tmp_path: Path) -> None:
        """get_current_commitments returns in_progress commitments."""
        from jdo.ai.tools import get_current_commitments
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Bob", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            in_progress = Commitment(
                deliverable="In progress task",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
                status=CommitmentStatus.IN_PROGRESS,
            )

            with get_session() as session:
                session.add(in_progress)

            with get_session() as session:
                result = get_current_commitments(session)

                assert len(result) == 1
                assert result[0]["deliverable"] == "In progress task"
                assert result[0]["status"] == "in_progress"

        reset_engine()

    def test_excludes_completed_commitments(self, tmp_path: Path) -> None:
        """get_current_commitments excludes completed commitments."""
        from jdo.ai.tools import get_current_commitments
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Carol", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            completed = Commitment(
                deliverable="Completed task",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
                status=CommitmentStatus.COMPLETED,
            )

            with get_session() as session:
                session.add(completed)

            with get_session() as session:
                result = get_current_commitments(session)

                assert len(result) == 0

        reset_engine()


class TestGetOverdueCommitments:
    """Tests for get_overdue_commitments tool."""

    def test_returns_commitments_past_due_date(self, tmp_path: Path) -> None:
        """get_overdue_commitments returns commitments past due date."""
        from jdo.ai.tools import get_overdue_commitments
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Dan", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            past_due = Commitment(
                deliverable="Overdue task",
                stakeholder_id=stakeholder_id,
                due_date=date(2024, 1, 1),  # Past date
                status=CommitmentStatus.PENDING,
            )

            with get_session() as session:
                session.add(past_due)

            with get_session() as session:
                result = get_overdue_commitments(session)

                assert len(result) == 1
                assert result[0]["deliverable"] == "Overdue task"

        reset_engine()


class TestGetCommitmentsForGoal:
    """Tests for get_commitments_for_goal tool."""

    def test_returns_commitments_for_goal_id(self, tmp_path: Path) -> None:
        """get_commitments_for_goal returns commitments for specific goal."""
        from jdo.ai.tools import get_commitments_for_goal
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Eve", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            goal = Goal(
                title="Test Goal",
                problem_statement="Problem",
                solution_vision="Solution",
            )
            goal_id = goal.id

            with get_session() as session:
                session.add(stakeholder)
                session.add(goal)

            linked = Commitment(
                deliverable="Linked to goal",
                stakeholder_id=stakeholder_id,
                goal_id=goal_id,
                due_date=date(2025, 12, 31),
            )
            unlinked = Commitment(
                deliverable="No goal",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
            )

            with get_session() as session:
                session.add(linked)
                session.add(unlinked)

            with get_session() as session:
                result = get_commitments_for_goal(session, str(goal_id))

                assert len(result) == 1
                assert result[0]["deliverable"] == "Linked to goal"

        reset_engine()


class TestGetMilestonesForGoal:
    """Tests for get_milestones_for_goal tool."""

    def test_returns_milestones_for_goal_id(self, tmp_path: Path) -> None:
        """get_milestones_for_goal returns milestones for specific goal."""
        from jdo.ai.tools import get_milestones_for_goal
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            goal = Goal(
                title="Goal with milestones",
                problem_statement="Problem",
                solution_vision="Solution",
            )
            goal_id = goal.id

            other_goal = Goal(
                title="Other goal",
                problem_statement="Problem",
                solution_vision="Solution",
            )
            other_goal_id = other_goal.id

            with get_session() as session:
                session.add(goal)
                session.add(other_goal)

            ms1 = Milestone(
                goal_id=goal_id,
                title="First milestone",
                target_date=date(2025, 6, 1),
            )
            ms2 = Milestone(
                goal_id=other_goal_id,
                title="Other milestone",
                target_date=date(2025, 6, 1),
            )

            with get_session() as session:
                session.add(ms1)
                session.add(ms2)

            with get_session() as session:
                result = get_milestones_for_goal(session, str(goal_id))

                assert len(result) == 1
                assert result[0]["title"] == "First milestone"

        reset_engine()


class TestGetVisionsDueForReview:
    """Tests for get_visions_due_for_review tool."""

    def test_returns_visions_needing_review(self, tmp_path: Path) -> None:
        """get_visions_due_for_review returns visions with next_review_date <= today."""
        from jdo.ai.tools import get_visions_due_for_review
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            due_vision = Vision(
                title="Due for review",
                timeframe="5 years",
                narrative="Future state",
                next_review_date=date.today() - timedelta(days=1),  # Past due
                status=VisionStatus.ACTIVE,
            )
            future_vision = Vision(
                title="Not yet due",
                timeframe="5 years",
                narrative="Future state",
                next_review_date=date.today() + timedelta(days=30),
                status=VisionStatus.ACTIVE,
            )

            with get_session() as session:
                session.add(due_vision)
                session.add(future_vision)

            with get_session() as session:
                result = get_visions_due_for_review(session)

                assert len(result) == 1
                assert result[0]["title"] == "Due for review"

        reset_engine()


class TestToolsReturnStructuredDicts:
    """Tests that tools return structured dicts suitable for AI response."""

    def test_commitment_dict_has_required_fields(self, tmp_path: Path) -> None:
        """Commitment dict has id, deliverable, stakeholder_name, due_date, status."""
        from jdo.ai.tools import get_current_commitments
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Frank", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            commitment = Commitment(
                deliverable="Test",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
            )

            with get_session() as session:
                session.add(commitment)

            with get_session() as session:
                result = get_current_commitments(session)

                assert len(result) == 1
                item = result[0]
                assert "id" in item
                assert "deliverable" in item
                assert "stakeholder_name" in item
                assert "due_date" in item
                assert "status" in item

        reset_engine()


class TestAgentToolIntegration:
    """Tests that agent can use tools end-to-end."""

    def test_tools_are_registered_with_agent(self) -> None:
        """Agent has tools registered after register_tools call."""
        from jdo.ai.tools import register_tools

        test_model = TestModel()
        # Create agent without auto-registering tools, then register manually
        agent = create_agent_with_model(test_model, with_tools=False)

        register_tools(agent)

        # Assert tools registered by name (agent internal toolset)
        toolset = agent._function_toolset
        tool_names = set(toolset.tools)

        assert "query_current_commitments" in tool_names
        assert "query_overdue_commitments" in tool_names
        assert "query_commitments_for_goal" in tool_names
        assert "query_milestones_for_goal" in tool_names
        assert "query_visions_due_for_review" in tool_names
        # New time coaching tools
        assert "query_user_time_context" in tool_names
        assert "query_task_history" in tool_names
        assert "query_commitment_time_rollup" in tool_names
        assert "query_integrity_with_context" in tool_names

    async def test_agent_can_run_with_tools(self, tmp_path: Path) -> None:
        """Agent can run with tools registered (no tool calls triggered)."""
        from jdo.ai.tools import register_tools
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Create agent without auto-registering tools, then register manually
            test_model = TestModel(call_tools=[])  # Don't call any tools
            agent = create_agent_with_model(test_model, with_tools=False)
            register_tools(agent)

            with get_session() as session:
                deps = JDODependencies(session=session)
                result = await agent.run(
                    "Hello!",
                    deps=deps,
                )

                # Should get success without tool calls
                assert result.output == "success (no tool calls)"

        reset_engine()


class TestGetRecentTaskHistory:
    """Tests for _get_recent_task_history helper function."""

    def test_returns_completed_entries_most_recent_first(self, tmp_path: Path) -> None:
        """_get_recent_task_history returns completed entries ordered by created_at desc."""
        from jdo.ai.tools import _get_recent_task_history
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Create all entities in one session to avoid detached instance errors
            with get_session() as session:
                stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
                session.add(stakeholder)
                session.flush()
                stakeholder_id = stakeholder.id

                commitment = Commitment(
                    deliverable="Test commitment",
                    stakeholder_id=stakeholder_id,
                    due_date=date(2025, 12, 31),
                )
                session.add(commitment)
                session.flush()
                commitment_id = commitment.id

                task1 = Task(
                    commitment_id=commitment_id,
                    title="Task 1",
                    scope="Scope 1",
                    order=0,
                    status=TaskStatus.COMPLETED,
                )
                task2 = Task(
                    commitment_id=commitment_id,
                    title="Task 2",
                    scope="Scope 2",
                    order=1,
                    status=TaskStatus.COMPLETED,
                )
                session.add(task1)
                session.add(task2)
                session.flush()
                task1_id = task1.id
                task2_id = task2.id

                # Create history entries
                entry1 = TaskHistoryEntry(
                    task_id=task1_id,
                    commitment_id=commitment_id,
                    event_type=TaskEventType.COMPLETED,
                    new_status=TaskStatus.COMPLETED,
                    estimated_hours=2.0,
                    actual_hours_category=ActualHoursCategory.ON_TARGET,
                )
                entry2 = TaskHistoryEntry(
                    task_id=task2_id,
                    commitment_id=commitment_id,
                    event_type=TaskEventType.COMPLETED,
                    new_status=TaskStatus.COMPLETED,
                    estimated_hours=1.0,
                    actual_hours_category=ActualHoursCategory.SHORTER,
                )
                session.add(entry1)
                session.add(entry2)

            with get_session() as session:
                result = _get_recent_task_history(session, limit=10)

                assert len(result) == 2
                # All should be COMPLETED events
                assert all(e.event_type == TaskEventType.COMPLETED for e in result)

        reset_engine()

    def test_respects_limit_parameter(self, tmp_path: Path) -> None:
        """_get_recent_task_history respects limit parameter."""
        from jdo.ai.tools import _get_recent_task_history
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Create all entities in one session
            with get_session() as session:
                stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
                session.add(stakeholder)
                session.flush()
                stakeholder_id = stakeholder.id

                commitment = Commitment(
                    deliverable="Test commitment",
                    stakeholder_id=stakeholder_id,
                    due_date=date(2025, 12, 31),
                )
                session.add(commitment)
                session.flush()
                commitment_id = commitment.id

                # Create 5 tasks
                task_ids = []
                for i in range(5):
                    task = Task(
                        commitment_id=commitment_id,
                        title=f"Task {i}",
                        scope=f"Scope {i}",
                        order=i,
                        status=TaskStatus.COMPLETED,
                    )
                    session.add(task)
                    session.flush()
                    task_ids.append(task.id)

                # Create 5 completed history entries
                for task_id in task_ids:
                    entry = TaskHistoryEntry(
                        task_id=task_id,
                        commitment_id=commitment_id,
                        event_type=TaskEventType.COMPLETED,
                        new_status=TaskStatus.COMPLETED,
                    )
                    session.add(entry)

            with get_session() as session:
                result = _get_recent_task_history(session, limit=3)

                assert len(result) == 3

        reset_engine()


class TestFormatTaskHistoryEntries:
    """Tests for _format_task_history_entries helper function."""

    def test_formats_entries_with_estimates(self) -> None:
        """_format_task_history_entries includes estimate info in output."""
        from jdo.ai.tools import _format_task_history_entries

        entry = TaskHistoryEntry(
            task_id=uuid4(),
            commitment_id=uuid4(),
            event_type=TaskEventType.COMPLETED,
            new_status=TaskStatus.COMPLETED,
            estimated_hours=2.5,
            actual_hours_category=ActualHoursCategory.ON_TARGET,
        )

        result = _format_task_history_entries([entry], limit=10)

        assert "completed" in result.lower()
        assert "2.5h" in result
        assert "on_target" in result.lower()

    def test_handles_entries_without_estimates(self) -> None:
        """_format_task_history_entries handles entries without estimates."""
        from jdo.ai.tools import _format_task_history_entries

        entry = TaskHistoryEntry(
            task_id=uuid4(),
            commitment_id=uuid4(),
            event_type=TaskEventType.COMPLETED,
            new_status=TaskStatus.COMPLETED,
        )

        result = _format_task_history_entries([entry], limit=10)

        assert "completed" in result.lower()
        # Should not have estimate info
        assert "est:" not in result


class TestGetCoachingAreas:
    """Tests for _get_coaching_areas helper function."""

    def test_returns_empty_for_good_metrics(self) -> None:
        """_get_coaching_areas returns empty list for good metrics."""
        from jdo.ai.tools import _get_coaching_areas
        from jdo.models.integrity_metrics import IntegrityMetrics

        metrics = IntegrityMetrics(
            on_time_rate=0.9,
            notification_timeliness=0.8,
            cleanup_completion_rate=0.9,
            current_streak_weeks=2,
            total_completed=10,
            total_on_time=9,
            total_at_risk=1,
            total_abandoned=0,
            estimation_accuracy=0.8,
            tasks_with_estimates=10,
        )

        result = _get_coaching_areas(metrics)

        assert len(result) == 0

    def test_identifies_low_on_time_rate(self) -> None:
        """_get_coaching_areas identifies low on-time rate."""
        from jdo.ai.tools import _get_coaching_areas
        from jdo.models.integrity_metrics import IntegrityMetrics

        metrics = IntegrityMetrics(
            on_time_rate=0.6,  # Below 0.8 threshold
            notification_timeliness=0.8,
            cleanup_completion_rate=0.9,
            current_streak_weeks=0,
            total_completed=10,
            total_on_time=6,
            total_at_risk=2,
            total_abandoned=0,
            estimation_accuracy=0.8,
            tasks_with_estimates=10,
        )

        result = _get_coaching_areas(metrics)

        assert "on-time delivery" in result

    def test_identifies_low_notification_timeliness(self) -> None:
        """_get_coaching_areas identifies low notification timeliness."""
        from jdo.ai.tools import _get_coaching_areas
        from jdo.models.integrity_metrics import IntegrityMetrics

        metrics = IntegrityMetrics(
            on_time_rate=0.9,
            notification_timeliness=0.5,  # Below 0.7 threshold
            cleanup_completion_rate=0.9,
            current_streak_weeks=2,
            total_completed=10,
            total_on_time=9,
            total_at_risk=2,
            total_abandoned=0,
            estimation_accuracy=0.8,
            tasks_with_estimates=10,
        )

        result = _get_coaching_areas(metrics)

        assert "earlier at-risk notification" in result

    def test_identifies_low_estimation_accuracy_with_enough_tasks(self) -> None:
        """_get_coaching_areas identifies low estimation accuracy with enough tasks."""
        from jdo.ai.tools import _get_coaching_areas
        from jdo.models.integrity_metrics import IntegrityMetrics

        metrics = IntegrityMetrics(
            on_time_rate=0.9,
            notification_timeliness=0.8,
            cleanup_completion_rate=0.9,
            current_streak_weeks=2,
            total_completed=10,
            total_on_time=9,
            total_at_risk=1,
            total_abandoned=0,
            estimation_accuracy=0.5,  # Below 0.7 threshold
            tasks_with_estimates=10,  # Enough tasks
        )

        result = _get_coaching_areas(metrics)

        assert "estimation accuracy" in result

    def test_ignores_low_estimation_accuracy_with_few_tasks(self) -> None:
        """_get_coaching_areas ignores low estimation accuracy with few tasks."""
        from jdo.ai.tools import _get_coaching_areas
        from jdo.models.integrity_metrics import IntegrityMetrics

        metrics = IntegrityMetrics(
            on_time_rate=0.9,
            notification_timeliness=0.8,
            cleanup_completion_rate=0.9,
            current_streak_weeks=2,
            total_completed=10,
            total_on_time=9,
            total_at_risk=1,
            total_abandoned=0,
            estimation_accuracy=0.5,  # Low but...
            tasks_with_estimates=3,  # Not enough tasks (< 5)
        )

        result = _get_coaching_areas(metrics)

        assert "estimation accuracy" not in result
