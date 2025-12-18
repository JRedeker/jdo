"""AI agent tools for querying domain objects.

These tools provide the AI agent with database query capabilities
to help users manage their commitments, goals, milestones, and visions.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from loguru import logger
from pydantic_ai import Agent, RunContext
from sqlmodel import Session, select

from jdo.ai.agent import JDODependencies
from jdo.models import (
    Commitment,
    CommitmentStatus,
    Milestone,
    Stakeholder,
    Vision,
    VisionStatus,
)


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
    today = datetime.now(UTC).date()
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
    today = datetime.now(UTC).date()
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

    @agent.tool
    def query_current_commitments(ctx: RunContext[JDODependencies]) -> str:
        """Get all pending and in-progress commitments.

        Returns a list of current commitments with deliverable, stakeholder, due date, and status.
        """
        result = get_current_commitments(ctx.deps.session)
        if not result:
            return "No pending or in-progress commitments found."
        return str(result)

    @agent.tool
    def query_overdue_commitments(ctx: RunContext[JDODependencies]) -> str:
        """Get all commitments that are past their due date.

        Returns a list of overdue commitments with days overdue.
        """
        result = get_overdue_commitments(ctx.deps.session)
        if not result:
            return "No overdue commitments found."
        return str(result)

    @agent.tool
    def query_commitments_for_goal(ctx: RunContext[JDODependencies], goal_id: str) -> str:
        """Get all commitments linked to a specific goal.

        Args:
            ctx: Runtime context with database session.
            goal_id: The UUID of the goal to query commitments for.

        Returns:
            Commitments for the specified goal as a string.
        """
        result = get_commitments_for_goal(ctx.deps.session, goal_id)
        if not result:
            return f"No commitments found for goal {goal_id}."
        return str(result)


def _register_milestone_vision_tools(agent: Agent[JDODependencies, str]) -> None:
    """Register milestone and vision-related query tools."""

    @agent.tool
    def query_milestones_for_goal(ctx: RunContext[JDODependencies], goal_id: str) -> str:
        """Get all milestones for a specific goal.

        Args:
            ctx: Runtime context with database session.
            goal_id: The UUID of the goal to query milestones for.

        Returns:
            Milestones for the specified goal sorted by target date.
        """
        result = get_milestones_for_goal(ctx.deps.session, goal_id)
        if not result:
            return f"No milestones found for goal {goal_id}."
        return str(result)

    @agent.tool
    def query_visions_due_for_review(ctx: RunContext[JDODependencies]) -> str:
        """Get all visions that are due for review.

        Returns visions where next_review_date is today or in the past.
        """
        result = get_visions_due_for_review(ctx.deps.session)
        if not result:
            return "No visions are due for review."
        return str(result)


def register_tools(agent: Agent[JDODependencies, str]) -> None:
    """Register all query tools with the agent.

    Args:
        agent: The PydanticAI agent to register tools with.
    """
    logger.debug("Registering AI agent tools")
    _register_commitment_tools(agent)
    _register_milestone_vision_tools(agent)
    logger.debug("AI agent tools registered")
