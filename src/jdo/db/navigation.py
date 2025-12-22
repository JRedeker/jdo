"""Navigation service for fetching entity lists and data.

Consolidates duplicate data-fetching logic from app.py navigation handlers.
"""

from __future__ import annotations

from typing import Any

from loguru import logger
from sqlmodel import Session, select

from jdo.integrity.service import IntegrityService
from jdo.models import Commitment, Goal, Milestone, Stakeholder, Vision


class NavigationService:
    """Service for fetching navigation data for different entity types.

    Consolidates the data-fetching logic previously duplicated across
    multiple navigation handler methods in app.py.
    """

    @staticmethod
    def get_goals_list(session: Session) -> list[dict[str, Any]]:
        """Fetch all goals as list items for display.

        Args:
            session: Database session.

        Returns:
            List of goal dicts with id, title, problem_statement, and status.
            Returns empty list if database query fails.
        """
        try:
            goals = list(session.exec(select(Goal)).all())
            return [
                {
                    "id": str(g.id),
                    "title": g.title,
                    "problem_statement": g.problem_statement,
                    "status": g.status.value,
                }
                for g in goals
            ]
        except Exception as e:
            logger.error(f"Failed to fetch goals list: {e}")
            return []

    @staticmethod
    def get_commitments_list(session: Session) -> list[dict[str, Any]]:
        """Fetch all commitments with stakeholder info as list items.

        Args:
            session: Database session.

        Returns:
            List of commitment dicts with id, deliverable, stakeholder_name, due_date, status.
            Returns empty list if database query fails.
        """
        try:
            results = list(session.exec(select(Commitment, Stakeholder).join(Stakeholder)).all())
            return [
                {
                    "id": str(c.id),
                    "deliverable": c.deliverable,
                    "stakeholder_name": s.name,
                    "due_date": c.due_date.isoformat(),
                    "status": c.status.value,
                }
                for c, s in results
            ]
        except Exception as e:
            logger.error(f"Failed to fetch commitments list: {e}")
            return []

    @staticmethod
    def get_visions_list(session: Session) -> list[dict[str, Any]]:
        """Fetch all visions as list items for display.

        Args:
            session: Database session.

        Returns:
            List of vision dicts with id, title, timeframe, and status.
            Returns empty list if database query fails.
        """
        try:
            visions = list(session.exec(select(Vision)).all())
            return [
                {
                    "id": str(v.id),
                    "title": v.title,
                    "timeframe": v.timeframe,
                    "status": v.status.value,
                }
                for v in visions
            ]
        except Exception as e:
            logger.error(f"Failed to fetch visions list: {e}")
            return []

    @staticmethod
    def get_milestones_list(session: Session) -> list[dict[str, Any]]:
        """Fetch all milestones as list items for display.

        Args:
            session: Database session.

        Returns:
            List of milestone dicts with id, description, target_date, and status.
            Returns empty list if database query fails.
        """
        try:
            milestones = list(session.exec(select(Milestone)).all())
            return [
                {
                    "id": str(m.id),
                    "description": m.description,
                    "target_date": m.target_date.isoformat(),
                    "status": m.status.value,
                }
                for m in milestones
            ]
        except Exception as e:
            logger.error(f"Failed to fetch milestones list: {e}")
            return []

    @staticmethod
    def get_orphans_list(session: Session) -> list[dict[str, Any]]:
        """Fetch orphan commitments (no goal) with stakeholder info.

        Args:
            session: Database session.

        Returns:
            List of orphan commitment dicts with same structure as get_commitments_list.
            Returns empty list if database query fails.
        """
        try:
            results = list(
                session.exec(
                    select(Commitment, Stakeholder)
                    .join(Stakeholder)
                    .where(Commitment.goal_id == None)  # noqa: E711
                ).all()
            )
            return [
                {
                    "id": str(c.id),
                    "deliverable": c.deliverable,
                    "stakeholder_name": s.name,
                    "due_date": c.due_date.isoformat(),
                    "status": c.status.value,
                }
                for c, s in results
            ]
        except Exception as e:
            logger.error(f"Failed to fetch orphans list: {e}")
            return []

    @staticmethod
    def get_integrity_data(session: Session) -> dict[str, Any]:
        """Fetch integrity dashboard metrics.

        Args:
            session: Database session.

        Returns:
            Dict with integrity metrics (composite_score, letter_grade, rates, etc.).
            Returns default A+ metrics if calculation fails.
        """
        try:
            service = IntegrityService()
            metrics = service.calculate_integrity_metrics(session)
            return {
                "composite_score": metrics.composite_score,
                "letter_grade": metrics.letter_grade,
                "on_time_rate": metrics.on_time_rate,
                "notification_timeliness": metrics.notification_timeliness,
                "cleanup_completion_rate": metrics.cleanup_completion_rate,
                "current_streak_weeks": metrics.current_streak_weeks,
                "total_completed": metrics.total_completed,
                "total_on_time": metrics.total_on_time,
                "total_at_risk": metrics.total_at_risk,
                "total_abandoned": metrics.total_abandoned,
            }
        except Exception as e:
            logger.error(f"Failed to calculate integrity metrics: {e}")
            # Return default perfect score for new users
            return {
                "composite_score": 100.0,
                "letter_grade": "A+",
                "on_time_rate": 1.0,
                "notification_timeliness": 1.0,
                "cleanup_completion_rate": 1.0,
                "current_streak_weeks": 0,
                "total_completed": 0,
                "total_on_time": 0,
                "total_at_risk": 0,
                "total_abandoned": 0,
            }
