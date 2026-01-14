"""AI agent tools for querying domain objects.

These tools provide the AI agent with database query capabilities
to help users manage their commitments, goals, milestones, and visions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from jdo.utils.datetime import today_date

if TYPE_CHECKING:
    pass
from uuid import UUID

from loguru import logger
from pydantic_ai import Agent, RunContext
from sqlmodel import Session, select

from jdo.ai.agent import JDODependencies
from jdo.ai.time_context import format_time_context_for_ai, get_time_context
from jdo.db.persistence import PersistenceService, ValidationError
from jdo.db.session import get_session
from jdo.db.task_history_service import TaskHistoryService
from jdo.db.time_rollup_service import TimeRollupService
from jdo.integrity.service import IntegrityService
from jdo.models import (
    Commitment,
    CommitmentStatus,
    Milestone,
    Stakeholder,
    Vision,
    VisionStatus,
)
from jdo.models.integrity_metrics import IntegrityMetrics
from jdo.models.task_history import TaskEventType, TaskHistoryEntry
from jdo.output.formatters import (
    format_commitment_list_plain,
    format_milestones_plain,
    format_overdue_commitments_plain,
    format_visions_plain,
)

# Coaching threshold constants
COACHING_ON_TIME_THRESHOLD = 0.8
COACHING_NOTIFICATION_THRESHOLD = 0.7
COACHING_CLEANUP_THRESHOLD = 0.8
COACHING_ESTIMATION_THRESHOLD = 0.7
MIN_TASKS_FOR_ESTIMATION_COACHING = 5


def get_current_commitments(session: Session) -> list[dict[str, Any]]:
    """Get pending and in-progress commitments.

    Args:
        session: Database session.

    Returns:
        List of commitment dicts with id, deliverable, stakeholder_name, due_date, status.
    """
    logger.debug("Querying current commitments")
    # Query commitments with stakeholder join
    commitments = session.exec(
        select(Commitment, Stakeholder)
        .join(Stakeholder, Commitment.stakeholder_id == Stakeholder.id)
        .where(Commitment.status.in_([CommitmentStatus.PENDING, CommitmentStatus.IN_PROGRESS]))
        .order_by(Commitment.due_date)
    ).all()

    return [
        {
            "id": str(c.id),
            "deliverable": c.deliverable,
            "stakeholder_name": s.name,
            "due_date": c.due_date.isoformat(),
            "due_time": c.due_time.isoformat() if c.due_time else None,
            "status": c.status.value,
            "goal_id": str(c.goal_id) if c.goal_id else None,
            "milestone_id": str(c.milestone_id) if c.milestone_id else None,
        }
        for c, s in commitments
    ]


def get_overdue_commitments(session: Session) -> list[dict[str, Any]]:
    """Get commitments past their due date.

    Args:
        session: Database session.

    Returns:
        List of overdue commitment dicts.
    """
    today = today_date()
    commitments = session.exec(
        select(Commitment, Stakeholder)
        .join(Stakeholder, Commitment.stakeholder_id == Stakeholder.id)
        .where(
            Commitment.due_date < today,
            Commitment.status.in_([CommitmentStatus.PENDING, CommitmentStatus.IN_PROGRESS]),
        )
        .order_by(Commitment.due_date)
    ).all()

    return [
        {
            "id": str(c.id),
            "deliverable": c.deliverable,
            "stakeholder_name": s.name,
            "due_date": c.due_date.isoformat(),
            "status": c.status.value,
            "days_overdue": (today - c.due_date).days,
        }
        for c, s in commitments
    ]


def get_commitments_for_goal(session: Session, goal_id: str) -> list[dict[str, Any]]:
    """Get commitments for a specific goal.

    Args:
        session: Database session.
        goal_id: UUID of the goal.

    Returns:
        List of commitment dicts for the goal.
    """
    goal_uuid = UUID(goal_id)
    commitments = session.exec(
        select(Commitment, Stakeholder)
        .join(Stakeholder, Commitment.stakeholder_id == Stakeholder.id)
        .where(Commitment.goal_id == goal_uuid)
        .order_by(Commitment.due_date)
    ).all()

    return [
        {
            "id": str(c.id),
            "deliverable": c.deliverable,
            "stakeholder_name": s.name,
            "due_date": c.due_date.isoformat(),
            "status": c.status.value,
        }
        for c, s in commitments
    ]


def get_milestones_for_goal(session: Session, goal_id: str) -> list[dict[str, Any]]:
    """Get milestones for a specific goal.

    Args:
        session: Database session.
        goal_id: UUID of the goal.

    Returns:
        List of milestone dicts for the goal.
    """
    goal_uuid = UUID(goal_id)
    milestones = session.exec(
        select(Milestone).where(Milestone.goal_id == goal_uuid).order_by(Milestone.target_date)
    ).all()

    return [
        {
            "id": str(m.id),
            "title": m.title,
            "description": m.description,
            "target_date": m.target_date.isoformat(),
            "status": m.status.value,
        }
        for m in milestones
    ]


def get_visions_due_for_review(session: Session) -> list[dict[str, Any]]:
    """Get visions that need review (next_review_date <= today).

    Args:
        session: Database session.

    Returns:
        List of vision dicts due for review.
    """
    today = today_date()
    visions = session.exec(
        select(Vision)
        .where(
            Vision.next_review_date <= today,
            Vision.status == VisionStatus.ACTIVE,
        )
        .order_by(Vision.next_review_date)
    ).all()

    return [
        {
            "id": str(v.id),
            "title": v.title,
            "timeframe": v.timeframe,
            "narrative": v.narrative,
            "next_review_date": v.next_review_date.isoformat() if v.next_review_date else None,
            "days_overdue": (today - v.next_review_date).days if v.next_review_date else 0,
        }
        for v in visions
    ]


def _register_commitment_tools(agent: Agent[JDODependencies, str]) -> None:
    """Register commitment-related query tools."""

    @agent.tool_plain
    def query_current_commitments() -> str:
        """Get all pending and in-progress commitments.

        Returns a list of current commitments with deliverable, stakeholder, due date, and status.
        """
        # Use a dedicated session to avoid concurrency issues with parallel tool calls
        with get_session() as session:
            result = get_current_commitments(session)
            return format_commitment_list_plain(result)

    @agent.tool_plain
    def query_overdue_commitments() -> str:
        """Get all commitments that are past their due date.

        Returns a list of overdue commitments with days overdue.
        """
        # Use a dedicated session to avoid concurrency issues with parallel tool calls
        with get_session() as session:
            result = get_overdue_commitments(session)
            return format_overdue_commitments_plain(result)

    @agent.tool_plain
    def query_commitments_for_goal(goal_id: str) -> str:
        """Get all commitments linked to a specific goal.

        Args:
            goal_id: The UUID of the goal to query commitments for.

        Returns:
            Commitments for the specified goal as a string.
        """
        # Use a dedicated session to avoid concurrency issues with parallel tool calls
        with get_session() as session:
            result = get_commitments_for_goal(session, goal_id)
            if not result:
                return f"No commitments found for goal {goal_id}."
            return format_commitment_list_plain(result)


def _register_milestone_vision_tools(agent: Agent[JDODependencies, str]) -> None:
    """Register milestone and vision-related query tools."""

    @agent.tool_plain
    def query_milestones_for_goal(goal_id: str) -> str:
        """Get all milestones for a specific goal.

        Args:
            goal_id: The UUID of the goal to query milestones for.

        Returns:
            Milestones for the specified goal sorted by target date.
        """
        # Use a dedicated session to avoid concurrency issues with parallel tool calls
        with get_session() as session:
            result = get_milestones_for_goal(session, goal_id)
            if not result:
                return f"No milestones found for goal {goal_id}."
            return format_milestones_plain(result)

    @agent.tool_plain
    def query_visions_due_for_review() -> str:
        """Get all visions that are due for review.

        Returns visions where next_review_date is today or in the past.
        """
        # Use a dedicated session to avoid concurrency issues with parallel tool calls
        with get_session() as session:
            result = get_visions_due_for_review(session)
            return format_visions_plain(result)


def _get_recent_task_history(session: Session, limit: int = 20) -> list[TaskHistoryEntry]:
    """Get recent completed task history across all commitments.

    Args:
        session: Database session.
        limit: Maximum entries to return.

    Returns:
        List of completed task history entries, most recent first.
    """
    statement = (
        select(TaskHistoryEntry)
        .where(TaskHistoryEntry.event_type == TaskEventType.COMPLETED)
        .order_by(TaskHistoryEntry.created_at.desc())  # type: ignore[arg-type]
        .limit(limit)
    )
    return list(session.exec(statement).all())


def _format_task_history_entries(entries: list[TaskHistoryEntry], limit: int) -> str:
    """Format task history entries as a string for AI consumption.

    Args:
        entries: Task history entries to format.
        limit: Maximum entries to include.

    Returns:
        Formatted string with one entry per line.
    """
    result_lines = []
    for entry in entries[:limit]:
        line = f"- {entry.event_type.value}: {entry.created_at.strftime('%Y-%m-%d')}"
        if entry.estimated_hours:
            line += f" (est: {entry.estimated_hours}h"
            if entry.actual_hours_category:
                line += f", actual: {entry.actual_hours_category.value}"
            line += ")"
        result_lines.append(line)
    return "\n".join(result_lines)


def _get_coaching_areas(metrics: IntegrityMetrics) -> list[str]:
    """Identify areas needing coaching attention from metrics.

    Args:
        metrics: IntegrityMetrics instance.

    Returns:
        List of area names needing attention.
    """
    coaching_areas = []
    if metrics.on_time_rate < COACHING_ON_TIME_THRESHOLD:
        coaching_areas.append("on-time delivery")
    if metrics.notification_timeliness < COACHING_NOTIFICATION_THRESHOLD:
        coaching_areas.append("earlier at-risk notification")
    if metrics.cleanup_completion_rate < COACHING_CLEANUP_THRESHOLD:
        coaching_areas.append("completing cleanup tasks")
    if (
        metrics.estimation_accuracy < COACHING_ESTIMATION_THRESHOLD
        and metrics.tasks_with_estimates >= MIN_TASKS_FOR_ESTIMATION_COACHING
    ):
        coaching_areas.append("estimation accuracy")
    return coaching_areas


def _register_time_coaching_tools(agent: Agent[JDODependencies, str]) -> None:
    """Register time management and coaching query tools."""

    @agent.tool
    def query_user_time_context(ctx: RunContext[JDODependencies]) -> str:
        """Get the user's current time context for coaching decisions.

        Returns available hours, allocated hours, remaining capacity, and utilization.
        Use this to check if user is over-committed before accepting new tasks.
        """
        # Use a dedicated session to avoid concurrency issues with parallel tool calls
        with get_session() as session:
            context = get_time_context(
                session,
                available_hours=ctx.deps.available_hours_remaining,
            )
            return format_time_context_for_ai(context)

    @agent.tool_plain
    def query_task_history(
        commitment_id: str | None = None,
        limit: int = 20,
    ) -> str:
        """Get task completion history for pattern analysis.

        Use this to check user's estimation accuracy and completion patterns.
        Can filter by commitment_id for commitment-specific history.

        Args:
            commitment_id: Optional commitment UUID to filter history.
            limit: Maximum entries to return (default 20).

        Returns:
            Task history with timestamps, estimates, and actual hours categories.
        """
        # Use a dedicated session to avoid concurrency issues with parallel tool calls
        with get_session() as session:
            service = TaskHistoryService(session)

            if commitment_id:
                entries = service.get_history_for_commitment(UUID(commitment_id))
            else:
                entries = _get_recent_task_history(session, limit)

            if not entries:
                return "No task history found."

            return _format_task_history_entries(entries, limit)

    @agent.tool_plain
    def query_commitment_time_rollup(commitment_id: str) -> str:
        """Get time rollup for a specific commitment.

        Shows total/remaining/completed estimated hours and task counts.
        Use this to understand workload breakdown for a commitment.

        Args:
            commitment_id: UUID of the commitment.

        Returns:
            Time breakdown including estimate coverage percentage.
        """
        # Use a dedicated session to avoid concurrency issues with parallel tool calls
        with get_session() as session:
            service = TimeRollupService(session)
            rollup = service.get_rollup(UUID(commitment_id))

            lines = [
                f"Total estimated hours: {rollup.total_estimated_hours:.1f}",
                f"Remaining estimated hours: {rollup.remaining_estimated_hours:.1f}",
                f"Completed estimated hours: {rollup.completed_estimated_hours:.1f}",
                f"Tasks: {rollup.task_count} total, {rollup.completed_task_count} completed",
                f"Tasks with estimates: {rollup.tasks_with_estimates}/{rollup.task_count} "
                f"({rollup.estimate_coverage * 100:.0f}% coverage)",
            ]

            return "\n".join(lines)

    @agent.tool_plain
    def query_integrity_with_context() -> str:
        """Get user's integrity metrics with coaching context.

        Returns letter grade, component scores, and areas needing attention.
        Use this to provide integrity-based coaching and feedback.
        """
        # Use a dedicated session to avoid concurrency issues with parallel tool calls
        with get_session() as session:
            service = IntegrityService()
            metrics = service.calculate_integrity_metrics(session)

        notification_pct = metrics.notification_timeliness * 100
        lines = [
            f"Integrity Grade: {metrics.letter_grade}",
            f"Composite Score: {metrics.composite_score:.0f}/100",
            "",
            "Component Scores:",
            f"  On-time rate: {metrics.on_time_rate * 100:.0f}% (weight: 35%)",
            f"  Notification timeliness: {notification_pct:.0f}% (weight: 25%)",
            f"  Cleanup completion: {metrics.cleanup_completion_rate * 100:.0f}% (weight: 25%)",
            f"  Estimation accuracy: {metrics.estimation_accuracy * 100:.0f}% (weight: 10%)",
            f"  Streak bonus: {min(metrics.current_streak_weeks * 2, 5)}% (max 5%)",
            "",
            "History:",
            f"  Completed: {metrics.total_completed}",
            f"  On-time: {metrics.total_on_time}",
            f"  At-risk: {metrics.total_at_risk}",
            f"  Abandoned: {metrics.total_abandoned}",
            f"  Current streak: {metrics.current_streak_weeks} weeks",
        ]

        # Add coaching hints for areas needing attention
        coaching_areas = _get_coaching_areas(metrics)
        if coaching_areas:
            lines.append("")
            lines.append("Areas to focus on: " + ", ".join(coaching_areas))

        return "\n".join(lines)


def _register_mutation_tools(agent: Agent[JDODependencies, str]) -> None:
    """Register data mutation tools for creating/updating entities."""

    @agent.tool_plain
    def create_commitment(
        deliverable: str,
        stakeholder: str,
        due_date: str,
        due_time: str | None = None,
        goal_id: str | None = None,
        milestone_id: str | None = None,
    ) -> str:
        """Create a new commitment.

        Args:
            deliverable: What will be delivered.
            stakeholder: Who the commitment is for.
            due_date: When it's due (YYYY-MM-DD format).
            due_time: Optional time (HH:MM format).
            goal_id: Optional UUID of linked goal.
            milestone_id: Optional UUID of linked milestone.

        Returns:
            Confirmation message with commitment ID.
        """
        with get_session() as session:
            service = PersistenceService(session)

            try:
                commitment = service.save_commitment(
                    {
                        "deliverable": deliverable,
                        "stakeholder": stakeholder,
                        "due_date": due_date,
                        "due_time": due_time,
                        "goal_id": goal_id,
                        "milestone_id": milestone_id,
                    }
                )
                session.commit()
            except ValidationError as e:
                session.rollback()
                return f"Error creating commitment: {e}"
            else:
                return f"Created commitment '{commitment.deliverable}' (ID: {commitment.id})"

    @agent.tool_plain
    def add_task_to_commitment(
        title: str,
        commitment_id: str,
        scope: str | None = None,
        estimated_hours: float | None = None,
    ) -> str:
        """Add a task to an existing commitment.

        Args:
            title: Task title.
            commitment_id: UUID of parent commitment.
            scope: What "done" means (defaults to title).
            estimated_hours: Optional time estimate.

        Returns:
            Confirmation message with task ID.
        """
        with get_session() as session:
            service = PersistenceService(session)

            try:
                task = service.save_task(
                    {
                        "title": title,
                        "scope": scope,
                        "commitment_id": commitment_id,
                        "estimated_hours": estimated_hours,
                    }
                )
                session.commit()
            except ValidationError as e:
                session.rollback()
                return f"Error adding task: {e}"
            else:
                return f"Added task '{task.title}' to commitment (Task ID: {task.id})"


def register_tools(agent: Agent[JDODependencies, str]) -> None:
    """Register all query and mutation tools with the agent.

    Args:
        agent: The PydanticAI agent to register tools with.
    """
    logger.debug("Registering AI agent tools")
    _register_commitment_tools(agent)
    _register_milestone_vision_tools(agent)
    _register_time_coaching_tools(agent)
    _register_mutation_tools(agent)
    logger.debug("AI agent tools registered")
