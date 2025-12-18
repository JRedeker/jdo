"""Tests for CleanupPlan SQLModel - TDD Red phase."""

from __future__ import annotations

from datetime import UTC, date, datetime, timezone
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlmodel import SQLModel

from jdo.models.cleanup_plan import CleanupPlan, CleanupPlanStatus


class TestCleanupPlanStatus:
    """Tests for CleanupPlanStatus enum."""

    def test_has_required_values(self) -> None:
        """CleanupPlanStatus has planned, in_progress, completed, skipped, cancelled."""
        assert CleanupPlanStatus.PLANNED.value == "planned"
        assert CleanupPlanStatus.IN_PROGRESS.value == "in_progress"
        assert CleanupPlanStatus.COMPLETED.value == "completed"
        assert CleanupPlanStatus.SKIPPED.value == "skipped"
        assert CleanupPlanStatus.CANCELLED.value == "cancelled"


class TestCleanupPlanModel:
    """Tests for CleanupPlan model structure."""

    def test_inherits_from_sqlmodel_with_table_true(self) -> None:
        """CleanupPlan inherits from SQLModel with table=True."""
        assert issubclass(CleanupPlan, SQLModel)
        assert hasattr(CleanupPlan, "__tablename__")

    def test_has_tablename_cleanup_plans(self) -> None:
        """CleanupPlan has tablename 'cleanup_plans'."""
        assert CleanupPlan.__tablename__ == "cleanup_plans"

    def test_has_required_fields(self) -> None:
        """CleanupPlan has all required fields."""
        fields = CleanupPlan.model_fields
        assert "id" in fields
        assert "commitment_id" in fields
        assert "impact_description" in fields
        assert "mitigation_actions" in fields
        assert "notification_task_id" in fields
        assert "status" in fields
        assert "completed_at" in fields
        assert "skipped_reason" in fields
        assert "created_at" in fields
        assert "updated_at" in fields


class TestCleanupPlanValidation:
    """Tests for CleanupPlan field validation."""

    def test_creates_with_required_fields(self) -> None:
        """Create CleanupPlan with required commitment_id."""
        commitment_id = uuid4()
        plan = CleanupPlan(commitment_id=commitment_id)

        assert plan.commitment_id == commitment_id
        assert plan.status == CleanupPlanStatus.PLANNED
        assert isinstance(plan.id, UUID)

    def test_requires_commitment_id(self) -> None:
        """CleanupPlan requires commitment_id."""
        with pytest.raises(ValueError, match="commitment_id"):
            CleanupPlan.model_validate({})

    def test_status_defaults_to_planned(self) -> None:
        """Status defaults to 'planned'."""
        plan = CleanupPlan(commitment_id=uuid4())
        assert plan.status == CleanupPlanStatus.PLANNED

    def test_impact_description_optional(self) -> None:
        """impact_description is optional and defaults to None."""
        plan = CleanupPlan(commitment_id=uuid4())
        assert plan.impact_description is None

    def test_can_set_impact_description(self) -> None:
        """Can set impact_description."""
        plan = CleanupPlan(
            commitment_id=uuid4(),
            impact_description="Stakeholder won't receive report on time",
        )
        assert plan.impact_description == "Stakeholder won't receive report on time"

    def test_mitigation_actions_defaults_to_empty_list(self) -> None:
        """mitigation_actions defaults to empty list."""
        plan = CleanupPlan(commitment_id=uuid4())
        assert plan.mitigation_actions == []

    def test_can_set_mitigation_actions(self) -> None:
        """Can set mitigation_actions as list of strings."""
        plan = CleanupPlan(
            commitment_id=uuid4(),
            mitigation_actions=["Send partial report", "Schedule follow-up meeting"],
        )
        assert len(plan.mitigation_actions) == 2
        assert "Send partial report" in plan.mitigation_actions

    def test_notification_task_id_optional(self) -> None:
        """notification_task_id is optional and defaults to None."""
        plan = CleanupPlan(commitment_id=uuid4())
        assert plan.notification_task_id is None

    def test_can_set_notification_task_id(self) -> None:
        """Can set notification_task_id."""
        task_id = uuid4()
        plan = CleanupPlan(
            commitment_id=uuid4(),
            notification_task_id=task_id,
        )
        assert plan.notification_task_id == task_id

    def test_completed_at_optional(self) -> None:
        """completed_at is optional and defaults to None."""
        plan = CleanupPlan(commitment_id=uuid4())
        assert plan.completed_at is None

    def test_can_set_completed_at(self) -> None:
        """Can set completed_at timestamp."""
        now = datetime.now(UTC)
        plan = CleanupPlan(
            commitment_id=uuid4(),
            status=CleanupPlanStatus.COMPLETED,
            completed_at=now,
        )
        assert plan.completed_at == now

    def test_skipped_reason_optional(self) -> None:
        """skipped_reason is optional and defaults to None."""
        plan = CleanupPlan(commitment_id=uuid4())
        assert plan.skipped_reason is None

    def test_can_set_skipped_reason(self) -> None:
        """Can set skipped_reason when skipping cleanup."""
        plan = CleanupPlan(
            commitment_id=uuid4(),
            status=CleanupPlanStatus.SKIPPED,
            skipped_reason="User acknowledged impact to integrity score",
        )
        assert plan.skipped_reason == "User acknowledged impact to integrity score"

    def test_auto_generates_timestamps(self) -> None:
        """created_at and updated_at are auto-generated."""
        plan = CleanupPlan(commitment_id=uuid4())
        assert plan.created_at is not None
        assert plan.updated_at is not None


class TestCleanupPlanStatusTransitions:
    """Tests for CleanupPlan status transitions."""

    def test_can_transition_planned_to_in_progress(self) -> None:
        """Can transition from planned to in_progress."""
        plan = CleanupPlan(commitment_id=uuid4())
        plan.status = CleanupPlanStatus.IN_PROGRESS
        assert plan.status == CleanupPlanStatus.IN_PROGRESS

    def test_can_transition_in_progress_to_completed(self) -> None:
        """Can transition from in_progress to completed."""
        plan = CleanupPlan(
            commitment_id=uuid4(),
            status=CleanupPlanStatus.IN_PROGRESS,
        )
        plan.status = CleanupPlanStatus.COMPLETED
        plan.completed_at = datetime.now(UTC)
        assert plan.status == CleanupPlanStatus.COMPLETED
        assert plan.completed_at is not None

    def test_can_transition_to_skipped(self) -> None:
        """Can transition to skipped status."""
        plan = CleanupPlan(commitment_id=uuid4())
        plan.status = CleanupPlanStatus.SKIPPED
        plan.skipped_reason = "Acknowledged impact"
        assert plan.status == CleanupPlanStatus.SKIPPED

    def test_can_transition_to_cancelled(self) -> None:
        """Can transition to cancelled (commitment recovered)."""
        plan = CleanupPlan(
            commitment_id=uuid4(),
            status=CleanupPlanStatus.PLANNED,
        )
        plan.status = CleanupPlanStatus.CANCELLED
        assert plan.status == CleanupPlanStatus.CANCELLED


class TestCleanupPlanPersistence:
    """Tests for CleanupPlan database persistence."""

    def test_save_and_retrieve(self, tmp_path: Path) -> None:
        """Save CleanupPlan via session and retrieve by id."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Create stakeholder and commitment first
            stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            commitment = Commitment(
                deliverable="Test deliverable",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
            )
            commitment_id = commitment.id

            with get_session() as session:
                session.add(commitment)

            # Create CleanupPlan
            plan = CleanupPlan(
                commitment_id=commitment_id,
                impact_description="Test impact",
                mitigation_actions=["Action 1", "Action 2"],
            )
            plan_id = plan.id

            with get_session() as session:
                session.add(plan)

            # Retrieve
            with get_session() as session:
                result = session.exec(select(CleanupPlan).where(CleanupPlan.id == plan_id)).first()

                assert result is not None
                assert result.commitment_id == commitment_id
                assert result.impact_description == "Test impact"
                assert result.mitigation_actions == ["Action 1", "Action 2"]
                assert result.status == CleanupPlanStatus.PLANNED

        reset_engine()

    def test_query_by_commitment_id(self, tmp_path: Path) -> None:
        """Query CleanupPlan by commitment_id."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session
        from jdo.models.commitment import Commitment
        from jdo.models.stakeholder import Stakeholder, StakeholderType

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
            stakeholder_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            commitment = Commitment(
                deliverable="Test",
                stakeholder_id=stakeholder_id,
                due_date=date(2025, 12, 31),
            )
            commitment_id = commitment.id

            with get_session() as session:
                session.add(commitment)

            plan = CleanupPlan(commitment_id=commitment_id)

            with get_session() as session:
                session.add(plan)

            # Query by commitment_id
            with get_session() as session:
                result = session.exec(
                    select(CleanupPlan).where(CleanupPlan.commitment_id == commitment_id)
                ).first()

                assert result is not None
                assert result.commitment_id == commitment_id

        reset_engine()
