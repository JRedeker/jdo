"""Tests for IntegrityService - TDD Red phase."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from jdo.integrity.service import IntegrityService, RecoveryResult, RiskSummary
from jdo.models.cleanup_plan import CleanupPlan, CleanupPlanStatus
from jdo.models.commitment import Commitment, CommitmentStatus
from jdo.models.stakeholder import Stakeholder, StakeholderType
from jdo.models.task import Task, TaskStatus


@pytest.fixture(name="session")
def session_fixture():
    """Create in-memory SQLite session for testing.

    This follows SQLModel's recommended testing pattern:
    - Single in-memory database per test
    - StaticPool to prevent connection issues
    - Session yielded and kept open during test
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


class TestMarkCommitmentAtRisk:
    """Tests for marking a commitment as at-risk."""

    def test_changes_commitment_status_to_at_risk(self, session: Session) -> None:
        """Marking at-risk changes status from in_progress to at_risk."""
        # Setup
        stakeholder = Stakeholder(name="Alice", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Send report",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 12, 31),
            status=CommitmentStatus.IN_PROGRESS,
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)
        commitment_id = commitment.id

        # Act
        service = IntegrityService()
        service.mark_commitment_at_risk(
            session=session,
            commitment_id=commitment_id,
            reason="Won't finish in time",
        )

        # Assert - refresh to get updated state
        session.refresh(commitment)
        assert commitment.status == CommitmentStatus.AT_RISK
        assert commitment.marked_at_risk_at is not None

    def test_sets_marked_at_risk_at_timestamp(self, session: Session) -> None:
        """Marking at-risk sets marked_at_risk_at to current time."""
        stakeholder = Stakeholder(name="Bob", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Complete task",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 12, 31),
            status=CommitmentStatus.PENDING,
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)
        commitment_id = commitment.id

        before = datetime.now(UTC)

        service = IntegrityService()
        service.mark_commitment_at_risk(
            session=session,
            commitment_id=commitment_id,
            reason="Not starting in time",
        )

        after = datetime.now(UTC)

        session.refresh(commitment)
        assert commitment.marked_at_risk_at is not None
        # Handle timezone comparison
        marked_time = commitment.marked_at_risk_at
        if marked_time.tzinfo is None:
            marked_time = marked_time.replace(tzinfo=UTC)
        assert before <= marked_time <= after

    def test_creates_cleanup_plan(self, session: Session) -> None:
        """Marking at-risk creates a CleanupPlan for the commitment."""
        stakeholder = Stakeholder(name="Carol", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Deliver project",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 12, 31),
            status=CommitmentStatus.IN_PROGRESS,
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)
        commitment_id = commitment.id

        service = IntegrityService()
        service.mark_commitment_at_risk(
            session=session,
            commitment_id=commitment_id,
            reason="Timeline slipped",
        )

        # Assert CleanupPlan created
        plan = session.exec(
            select(CleanupPlan).where(CleanupPlan.commitment_id == commitment_id)
        ).first()
        assert plan is not None
        assert plan.status == CleanupPlanStatus.PLANNED

    def test_creates_notification_task(self, session: Session) -> None:
        """Marking at-risk creates a notification task at position 0."""
        stakeholder = Stakeholder(name="Dave", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Send update",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 12, 31),
            status=CommitmentStatus.IN_PROGRESS,
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)
        commitment_id = commitment.id

        service = IntegrityService()
        service.mark_commitment_at_risk(
            session=session,
            commitment_id=commitment_id,
            reason="Blocked by dependency",
        )

        # Assert notification task created
        tasks = session.exec(select(Task).where(Task.commitment_id == commitment_id)).all()
        assert len(tasks) == 1
        task = tasks[0]
        assert task.is_notification_task is True
        assert task.order == 0
        assert "Dave" in task.title or "Notify" in task.title

    def test_links_cleanup_plan_to_notification_task(self, session: Session) -> None:
        """CleanupPlan links to the created notification task."""
        stakeholder = Stakeholder(name="Eve", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Complete review",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 12, 31),
            status=CommitmentStatus.IN_PROGRESS,
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)
        commitment_id = commitment.id

        service = IntegrityService()
        service.mark_commitment_at_risk(
            session=session,
            commitment_id=commitment_id,
            reason="Need more time",
        )

        plan = session.exec(
            select(CleanupPlan).where(CleanupPlan.commitment_id == commitment_id)
        ).first()
        task = session.exec(
            select(Task).where(
                Task.commitment_id == commitment_id,
                Task.is_notification_task == True,  # noqa: E712
            )
        ).first()

        assert plan is not None
        assert task is not None
        assert plan.notification_task_id == task.id

    def test_returns_result_with_entities(self, session: Session) -> None:
        """mark_commitment_at_risk returns the updated commitment, plan, and task."""
        stakeholder = Stakeholder(name="Frank", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Finish project",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 12, 31),
            status=CommitmentStatus.IN_PROGRESS,
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)
        commitment_id = commitment.id

        service = IntegrityService()
        result = service.mark_commitment_at_risk(
            session=session,
            commitment_id=commitment_id,
            reason="Running behind",
        )

        assert result.commitment is not None
        assert result.cleanup_plan is not None
        assert result.notification_task is not None
        assert result.commitment.status == CommitmentStatus.AT_RISK

    def test_reuses_existing_cleanup_plan(self, session: Session) -> None:
        """If commitment already has CleanupPlan, reuse it."""
        stakeholder = Stakeholder(name="Grace", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Submit report",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 12, 31),
            status=CommitmentStatus.IN_PROGRESS,
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)
        commitment_id = commitment.id

        # Create existing plan
        existing_plan = CleanupPlan(
            commitment_id=commitment_id,
            impact_description="Previous impact",
        )
        session.add(existing_plan)
        session.commit()

        service = IntegrityService()
        service.mark_commitment_at_risk(
            session=session,
            commitment_id=commitment_id,
            reason="Still at risk",
        )

        # Should only have one plan
        plans = session.exec(
            select(CleanupPlan).where(CleanupPlan.commitment_id == commitment_id)
        ).all()
        assert len(plans) == 1


class TestCalculateIntegrityMetrics:
    """Tests for calculating integrity metrics."""

    def test_returns_clean_slate_for_no_history(self, session: Session) -> None:
        """Returns 1.0 for all rates when no commitment history."""
        service = IntegrityService()
        metrics = service.calculate_integrity_metrics(session)

        assert metrics.on_time_rate == 1.0
        assert metrics.notification_timeliness == 1.0
        assert metrics.cleanup_completion_rate == 1.0
        assert metrics.current_streak_weeks == 0
        assert metrics.total_completed == 0

    def test_calculates_on_time_rate(self, session: Session) -> None:
        """on_time_rate = completed_on_time / total_completed."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        # 3 completed on time, 1 late
        for i, on_time in enumerate([True, True, True, False]):
            commitment = Commitment(
                deliverable=f"Task {i}",
                stakeholder_id=stakeholder.id,
                due_date=date(2025, 1, i + 1),
                status=CommitmentStatus.COMPLETED,
                completed_on_time=on_time,
            )
            session.add(commitment)
        session.commit()

        service = IntegrityService()
        metrics = service.calculate_integrity_metrics(session)

        assert metrics.on_time_rate == pytest.approx(0.75)
        assert metrics.total_completed == 4
        assert metrics.total_on_time == 3

    def test_calculates_cleanup_completion_rate(self, session: Session) -> None:
        """cleanup_rate = completed_plans / total_plans."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        # Create 4 commitments with cleanup plans: 3 completed, 1 skipped
        statuses = [
            CleanupPlanStatus.COMPLETED,
            CleanupPlanStatus.COMPLETED,
            CleanupPlanStatus.COMPLETED,
            CleanupPlanStatus.SKIPPED,
        ]
        for i, plan_status in enumerate(statuses):
            commitment = Commitment(
                deliverable=f"Task {i}",
                stakeholder_id=stakeholder.id,
                due_date=date(2025, 1, i + 1),
                status=CommitmentStatus.ABANDONED,
            )
            session.add(commitment)
            session.commit()
            session.refresh(commitment)

            plan = CleanupPlan(
                commitment_id=commitment.id,
                status=plan_status,
            )
            session.add(plan)
        session.commit()

        service = IntegrityService()
        metrics = service.calculate_integrity_metrics(session)

        assert metrics.cleanup_completion_rate == pytest.approx(0.75)


class TestRiskSummary:
    """Tests for RiskSummary dataclass."""

    def test_total_risks_counts_all_categories(self) -> None:
        """total_risks returns sum of all risk categories."""
        # Create mock commitments
        c1 = Commitment(
            deliverable="Test 1",
            stakeholder_id=uuid4(),
            due_date=datetime.now(UTC).date(),
            status=CommitmentStatus.PENDING,
        )
        c2 = Commitment(
            deliverable="Test 2",
            stakeholder_id=uuid4(),
            due_date=datetime.now(UTC).date(),
            status=CommitmentStatus.PENDING,
        )
        c3 = Commitment(
            deliverable="Test 3",
            stakeholder_id=uuid4(),
            due_date=datetime.now(UTC).date(),
            status=CommitmentStatus.IN_PROGRESS,
        )

        summary = RiskSummary(
            overdue_commitments=[c1],
            due_soon_commitments=[c2],
            stalled_commitments=[c3],
        )

        assert summary.total_risks == 3

    def test_has_risks_true_when_risks_exist(self) -> None:
        """has_risks returns True when any category has items."""
        c = Commitment(
            deliverable="Test",
            stakeholder_id=uuid4(),
            due_date=datetime.now(UTC).date(),
            status=CommitmentStatus.PENDING,
        )
        summary = RiskSummary(overdue_commitments=[c])

        assert summary.has_risks is True

    def test_has_risks_false_when_empty(self) -> None:
        """has_risks returns False when no risks."""
        summary = RiskSummary()

        assert summary.has_risks is False

    def test_to_message_empty_returns_empty_string(self) -> None:
        """to_message returns empty string when no risks."""
        summary = RiskSummary()

        assert summary.to_message() == ""

    def test_to_message_formats_overdue(self) -> None:
        """to_message includes overdue commitments."""
        c = Commitment(
            deliverable="Overdue task",
            stakeholder_id=uuid4(),
            due_date=date(2025, 12, 1),
            status=CommitmentStatus.PENDING,
        )
        summary = RiskSummary(overdue_commitments=[c])

        msg = summary.to_message()
        assert "overdue" in msg.lower()
        assert "Overdue task" in msg

    def test_to_message_formats_due_soon(self) -> None:
        """to_message includes due soon commitments."""
        c = Commitment(
            deliverable="Urgent task",
            stakeholder_id=uuid4(),
            due_date=datetime.now(UTC).date(),
            status=CommitmentStatus.PENDING,
        )
        summary = RiskSummary(due_soon_commitments=[c])

        msg = summary.to_message()
        assert "24 hours" in msg
        assert "Urgent task" in msg


class TestDetectRisks:
    """Tests for IntegrityService.detect_risks."""

    def test_detects_overdue_pending_commitments(self, session: Session) -> None:
        """Detects commitments with due_date < today and status=pending."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        # Overdue pending commitment
        overdue = Commitment(
            deliverable="Overdue task",
            stakeholder_id=stakeholder.id,
            due_date=datetime.now(UTC).date() - timedelta(days=1),
            status=CommitmentStatus.PENDING,
        )
        session.add(overdue)
        session.commit()

        service = IntegrityService()
        summary = service.detect_risks(session)

        assert len(summary.overdue_commitments) == 1
        assert summary.overdue_commitments[0].deliverable == "Overdue task"

    def test_detects_overdue_in_progress_commitments(self, session: Session) -> None:
        """Detects commitments with due_date < today and status=in_progress."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        # Overdue in_progress commitment
        overdue = Commitment(
            deliverable="Overdue in progress",
            stakeholder_id=stakeholder.id,
            due_date=datetime.now(UTC).date() - timedelta(days=2),
            status=CommitmentStatus.IN_PROGRESS,
        )
        session.add(overdue)
        session.commit()

        service = IntegrityService()
        summary = service.detect_risks(session)

        assert len(summary.overdue_commitments) == 1

    def test_ignores_overdue_completed_commitments(self, session: Session) -> None:
        """Does not flag completed commitments as overdue."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        # Overdue but completed - should not be flagged
        completed = Commitment(
            deliverable="Done task",
            stakeholder_id=stakeholder.id,
            due_date=datetime.now(UTC).date() - timedelta(days=1),
            status=CommitmentStatus.COMPLETED,
        )
        session.add(completed)
        session.commit()

        service = IntegrityService()
        summary = service.detect_risks(session)

        assert len(summary.overdue_commitments) == 0

    def test_detects_due_soon_pending_commitments(self, session: Session) -> None:
        """Detects pending commitments due within 24 hours."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        # Due today (within 24h) - use UTC to match service
        utc_today = datetime.now(UTC).date()
        due_soon = Commitment(
            deliverable="Due today",
            stakeholder_id=stakeholder.id,
            due_date=utc_today,
            status=CommitmentStatus.PENDING,
        )
        session.add(due_soon)
        session.commit()

        service = IntegrityService()
        summary = service.detect_risks(session)

        assert len(summary.due_soon_commitments) == 1
        assert summary.due_soon_commitments[0].deliverable == "Due today"

    def test_ignores_due_soon_in_progress_commitments(self, session: Session) -> None:
        """Does not flag in_progress as due_soon (they're being worked on)."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        # Due today but in progress - use UTC to match service
        utc_today = datetime.now(UTC).date()
        in_progress = Commitment(
            deliverable="Working on it",
            stakeholder_id=stakeholder.id,
            due_date=utc_today,
            status=CommitmentStatus.IN_PROGRESS,
        )
        session.add(in_progress)
        session.commit()

        service = IntegrityService()
        summary = service.detect_risks(session)

        # Not in due_soon (they're being worked on)
        assert len(summary.due_soon_commitments) == 0

    def test_detects_stalled_commitments(self, session: Session) -> None:
        """Detects in_progress commitments due soon with no recent activity."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        # Stalled: due soon, in_progress, but not updated recently
        old_update = datetime.now(UTC) - timedelta(hours=48)
        stalled = Commitment(
            deliverable="Stalled task",
            stakeholder_id=stakeholder.id,
            due_date=datetime.now(UTC).date() + timedelta(days=1),  # Due within 48h
            status=CommitmentStatus.IN_PROGRESS,
            updated_at=old_update,
        )
        session.add(stalled)
        session.commit()

        service = IntegrityService()
        summary = service.detect_risks(session)

        assert len(summary.stalled_commitments) == 1
        assert summary.stalled_commitments[0].deliverable == "Stalled task"

    def test_returns_empty_when_no_risks(self, session: Session) -> None:
        """Returns empty RiskSummary when all commitments are healthy."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        # Future due date, not overdue
        healthy = Commitment(
            deliverable="Future task",
            stakeholder_id=stakeholder.id,
            due_date=datetime.now(UTC).date() + timedelta(days=30),
            status=CommitmentStatus.PENDING,
        )
        session.add(healthy)
        session.commit()

        service = IntegrityService()
        summary = service.detect_risks(session)

        assert summary.has_risks is False
        assert summary.total_risks == 0


class TestNotificationTimeliness:
    """Tests for notification timeliness calculation."""

    def test_returns_1_when_no_at_risk_history(self, session: Session) -> None:
        """Returns 1.0 (clean slate) when no commitments have been at-risk."""
        service = IntegrityService()
        timeliness = service._calculate_notification_timeliness(session)
        assert timeliness == 1.0

    def test_returns_1_when_marked_7_days_before_due(self, session: Session) -> None:
        """Returns 1.0 when marked at-risk 7+ days before due date."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        due = date(2025, 1, 15)
        marked = datetime(2025, 1, 7, 10, 0, tzinfo=UTC)  # 8 days before
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=stakeholder.id,
            due_date=due,
            status=CommitmentStatus.AT_RISK,
            marked_at_risk_at=marked,
        )
        session.add(commitment)
        session.commit()

        service = IntegrityService()
        timeliness = service._calculate_notification_timeliness(session)
        assert timeliness == 1.0

    def test_returns_0_when_marked_on_due_date(self, session: Session) -> None:
        """Returns 0.0 when marked at-risk on due date (no warning time)."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        due = date(2025, 1, 15)
        marked = datetime(2025, 1, 15, 10, 0, tzinfo=UTC)  # Same day
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=stakeholder.id,
            due_date=due,
            status=CommitmentStatus.AT_RISK,
            marked_at_risk_at=marked,
        )
        session.add(commitment)
        session.commit()

        service = IntegrityService()
        timeliness = service._calculate_notification_timeliness(session)
        assert timeliness == 0.0

    def test_returns_0_when_marked_after_due_date(self, session: Session) -> None:
        """Returns 0.0 when marked at-risk after due date (overdue)."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        due = date(2025, 1, 15)
        marked = datetime(2025, 1, 20, 10, 0, tzinfo=UTC)  # 5 days after
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=stakeholder.id,
            due_date=due,
            status=CommitmentStatus.AT_RISK,
            marked_at_risk_at=marked,
        )
        session.add(commitment)
        session.commit()

        service = IntegrityService()
        timeliness = service._calculate_notification_timeliness(session)
        assert timeliness == 0.0

    def test_returns_interpolated_value(self, session: Session) -> None:
        """Returns interpolated value for 0-7 days before due."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        due = date(2025, 1, 15)
        marked = datetime(2025, 1, 12, 10, 0, tzinfo=UTC)  # 3 days before
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=stakeholder.id,
            due_date=due,
            status=CommitmentStatus.AT_RISK,
            marked_at_risk_at=marked,
        )
        session.add(commitment)
        session.commit()

        service = IntegrityService()
        timeliness = service._calculate_notification_timeliness(session)
        assert timeliness == pytest.approx(3 / 7)  # 3 days / 7 days

    def test_averages_multiple_commitments(self, session: Session) -> None:
        """Returns average timeliness across multiple at-risk commitments."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        # First: 7 days before (score 1.0)
        c1 = Commitment(
            deliverable="Test 1",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 1, 15),
            status=CommitmentStatus.AT_RISK,
            marked_at_risk_at=datetime(2025, 1, 8, 10, 0, tzinfo=UTC),
        )
        # Second: 0 days before (score 0.0)
        c2 = Commitment(
            deliverable="Test 2",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 1, 20),
            status=CommitmentStatus.AT_RISK,
            marked_at_risk_at=datetime(2025, 1, 20, 10, 0, tzinfo=UTC),
        )
        session.add_all([c1, c2])
        session.commit()

        service = IntegrityService()
        timeliness = service._calculate_notification_timeliness(session)
        assert timeliness == pytest.approx(0.5)  # (1.0 + 0.0) / 2


class TestReliabilityStreak:
    """Tests for reliability streak calculation."""

    def test_returns_0_when_no_completions(self, session: Session) -> None:
        """Returns 0 when no commitments have been completed."""
        service = IntegrityService()
        streak = service._calculate_streak_weeks(session)
        assert streak == 0

    def test_returns_1_for_single_on_time_week(self, session: Session) -> None:
        """Returns 1 when one week has all on-time completions."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        # Complete one commitment this week, on time
        now = datetime.now(UTC)
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=stakeholder.id,
            due_date=now.date(),
            status=CommitmentStatus.COMPLETED,
            completed_at=now,
            completed_on_time=True,
        )
        session.add(commitment)
        session.commit()

        service = IntegrityService()
        streak = service._calculate_streak_weeks(session)
        assert streak == 1

    def test_returns_0_when_late_completion_in_week(self, session: Session) -> None:
        """Returns 0 when the only week has a late completion."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        now = datetime.now(UTC)
        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=stakeholder.id,
            due_date=now.date(),
            status=CommitmentStatus.COMPLETED,
            completed_at=now,
            completed_on_time=False,  # Late
        )
        session.add(commitment)
        session.commit()

        service = IntegrityService()
        streak = service._calculate_streak_weeks(session)
        assert streak == 0

    def test_counts_consecutive_weeks(self, session: Session) -> None:
        """Counts consecutive weeks with all on-time completions."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        # Create completions in 3 consecutive weeks, all on time
        now = datetime.now(UTC)
        for weeks_ago in range(3):
            completed_at = now - timedelta(weeks=weeks_ago)
            commitment = Commitment(
                deliverable=f"Task week {weeks_ago}",
                stakeholder_id=stakeholder.id,
                due_date=completed_at.date(),
                status=CommitmentStatus.COMPLETED,
                completed_at=completed_at,
                completed_on_time=True,
            )
            session.add(commitment)
        session.commit()

        service = IntegrityService()
        streak = service._calculate_streak_weeks(session)
        assert streak == 3

    def test_streak_breaks_on_late_completion(self, session: Session) -> None:
        """Streak breaks when there's a late completion."""
        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        now = datetime.now(UTC)

        # This week: on time
        c1 = Commitment(
            deliverable="Recent",
            stakeholder_id=stakeholder.id,
            due_date=now.date(),
            status=CommitmentStatus.COMPLETED,
            completed_at=now,
            completed_on_time=True,
        )
        # Last week: late (breaks streak)
        c2 = Commitment(
            deliverable="Late",
            stakeholder_id=stakeholder.id,
            due_date=(now - timedelta(weeks=1)).date(),
            status=CommitmentStatus.COMPLETED,
            completed_at=now - timedelta(weeks=1),
            completed_on_time=False,
        )
        # Two weeks ago: on time (doesn't count, streak broken)
        c3 = Commitment(
            deliverable="Old",
            stakeholder_id=stakeholder.id,
            due_date=(now - timedelta(weeks=2)).date(),
            status=CommitmentStatus.COMPLETED,
            completed_at=now - timedelta(weeks=2),
            completed_on_time=True,
        )
        session.add_all([c1, c2, c3])
        session.commit()

        service = IntegrityService()
        streak = service._calculate_streak_weeks(session)
        assert streak == 1  # Only this week counts


class TestEstimationAccuracy:
    """Tests for estimation accuracy calculation."""

    def test_returns_1_when_no_history(self, session: Session) -> None:
        """Returns 1.0 (clean slate) when no task history exists."""
        service = IntegrityService()
        accuracy, count = service._calculate_estimation_accuracy(session)
        assert accuracy == 1.0
        assert count == 0

    def test_returns_1_when_less_than_5_tasks(self, session: Session) -> None:
        """Returns 1.0 when fewer than 5 tasks with estimates exist."""
        from jdo.models.task import ActualHoursCategory
        from jdo.models.task_history import TaskEventType, TaskHistoryEntry

        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=stakeholder.id,
            due_date=date.today(),
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)

        task = Task(
            commitment_id=commitment.id,
            title="Test",
            scope="Scope",
            order=1,
            estimated_hours=2.0,
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        entry = TaskHistoryEntry(
            task_id=task.id,
            commitment_id=commitment.id,
            event_type=TaskEventType.COMPLETED,
            new_status=TaskStatus.COMPLETED,
            estimated_hours=2.0,
            actual_hours_category=ActualHoursCategory.ON_TARGET,
        )
        session.add(entry)
        session.commit()

        service = IntegrityService()
        accuracy, count = service._calculate_estimation_accuracy(session)
        assert accuracy == 1.0
        assert count == 1

    def test_returns_1_for_perfect_estimates(self, session: Session) -> None:
        """Returns 1.0 when all tasks were ON_TARGET."""
        from jdo.models.task import ActualHoursCategory
        from jdo.models.task_history import TaskEventType, TaskHistoryEntry

        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=stakeholder.id,
            due_date=date.today(),
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)

        task = Task(
            commitment_id=commitment.id,
            title="Test",
            scope="Scope",
            order=1,
            estimated_hours=2.0,
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        now = datetime.now(UTC)
        for i in range(5):
            entry = TaskHistoryEntry(
                task_id=task.id,
                commitment_id=commitment.id,
                event_type=TaskEventType.COMPLETED,
                new_status=TaskStatus.COMPLETED,
                estimated_hours=2.0,
                actual_hours_category=ActualHoursCategory.ON_TARGET,
                created_at=now - timedelta(days=i),
            )
            session.add(entry)
        session.commit()

        service = IntegrityService()
        accuracy, count = service._calculate_estimation_accuracy(session)
        assert accuracy == pytest.approx(1.0)
        assert count == 5

    def test_returns_lower_accuracy_for_inaccurate_estimates(self, session: Session) -> None:
        """Returns <1.0 when estimates were inaccurate."""
        from jdo.models.task import ActualHoursCategory
        from jdo.models.task_history import TaskEventType, TaskHistoryEntry

        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=stakeholder.id,
            due_date=date.today(),
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)

        task = Task(
            commitment_id=commitment.id,
            title="Test",
            scope="Scope",
            order=1,
            estimated_hours=2.0,
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        now = datetime.now(UTC)
        categories = [
            ActualHoursCategory.ON_TARGET,
            ActualHoursCategory.SHORTER,
            ActualHoursCategory.LONGER,
            ActualHoursCategory.MUCH_SHORTER,
            ActualHoursCategory.MUCH_LONGER,
        ]
        for cat in categories:
            entry = TaskHistoryEntry(
                task_id=task.id,
                commitment_id=commitment.id,
                event_type=TaskEventType.COMPLETED,
                new_status=TaskStatus.COMPLETED,
                estimated_hours=2.0,
                actual_hours_category=cat,
                created_at=now,
            )
            session.add(entry)
        session.commit()

        service = IntegrityService()
        accuracy, count = service._calculate_estimation_accuracy(session)
        assert count == 5
        assert accuracy < 1.0
        assert accuracy > 0.0

    def test_applies_exponential_decay_weight(self, session: Session) -> None:
        """Recent tasks are weighted more heavily than older ones."""
        from jdo.models.task import ActualHoursCategory
        from jdo.models.task_history import TaskEventType, TaskHistoryEntry

        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=stakeholder.id,
            due_date=date.today(),
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)

        task = Task(
            commitment_id=commitment.id,
            title="Test",
            scope="Scope",
            order=1,
            estimated_hours=2.0,
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        now = datetime.now(UTC)

        recent_on_target = TaskHistoryEntry(
            task_id=task.id,
            commitment_id=commitment.id,
            event_type=TaskEventType.COMPLETED,
            new_status=TaskStatus.COMPLETED,
            estimated_hours=2.0,
            actual_hours_category=ActualHoursCategory.ON_TARGET,
            created_at=now,
        )
        session.add(recent_on_target)

        for i in range(1, 5):
            old_inaccurate = TaskHistoryEntry(
                task_id=task.id,
                commitment_id=commitment.id,
                event_type=TaskEventType.COMPLETED,
                new_status=TaskStatus.COMPLETED,
                estimated_hours=2.0,
                actual_hours_category=ActualHoursCategory.MUCH_LONGER,
                created_at=now - timedelta(days=30 + i),
            )
            session.add(old_inaccurate)
        session.commit()

        service = IntegrityService()
        accuracy, count = service._calculate_estimation_accuracy(session)
        assert count == 5
        assert accuracy > 0.5

    def test_ignores_entries_older_than_90_days(self, session: Session) -> None:
        """Entries older than 90 days are not included."""
        from jdo.models.task import ActualHoursCategory
        from jdo.models.task_history import TaskEventType, TaskHistoryEntry

        stakeholder = Stakeholder(name="Test", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Test",
            stakeholder_id=stakeholder.id,
            due_date=date.today(),
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)

        task = Task(
            commitment_id=commitment.id,
            title="Test",
            scope="Scope",
            order=1,
            estimated_hours=2.0,
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        now = datetime.now(UTC)
        old_entry = TaskHistoryEntry(
            task_id=task.id,
            commitment_id=commitment.id,
            event_type=TaskEventType.COMPLETED,
            new_status=TaskStatus.COMPLETED,
            estimated_hours=2.0,
            actual_hours_category=ActualHoursCategory.ON_TARGET,
            created_at=now - timedelta(days=100),
        )
        session.add(old_entry)
        session.commit()

        service = IntegrityService()
        accuracy, count = service._calculate_estimation_accuracy(session)
        assert count == 0
        assert accuracy == 1.0


class TestRecoverCommitment:
    """Tests for recovering an at-risk commitment to in_progress."""

    def test_changes_status_from_at_risk_to_in_progress(self, session: Session) -> None:
        """Recovering changes commitment status from at_risk to in_progress."""
        # Setup
        stakeholder = Stakeholder(name="Alice", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Send report",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 12, 31),
            status=CommitmentStatus.AT_RISK,
            marked_at_risk_at=datetime.now(UTC),
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)
        commitment_id = commitment.id

        # Create cleanup plan
        cleanup_plan = CleanupPlan(
            commitment_id=commitment_id,
            status=CleanupPlanStatus.PLANNED,
        )
        session.add(cleanup_plan)
        session.commit()

        # Act
        service = IntegrityService()
        result = service.recover_commitment(
            session=session,
            commitment_id=commitment_id,
        )

        # Assert
        session.refresh(commitment)
        assert commitment.status == CommitmentStatus.IN_PROGRESS
        assert result.commitment.status == CommitmentStatus.IN_PROGRESS

    def test_sets_cleanup_plan_status_to_cancelled(self, session: Session) -> None:
        """Recovering sets the cleanup plan status to cancelled."""
        stakeholder = Stakeholder(name="Bob", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Complete task",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 12, 31),
            status=CommitmentStatus.AT_RISK,
            marked_at_risk_at=datetime.now(UTC),
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)
        commitment_id = commitment.id

        cleanup_plan = CleanupPlan(
            commitment_id=commitment_id,
            status=CleanupPlanStatus.PLANNED,
        )
        session.add(cleanup_plan)
        session.commit()
        session.refresh(cleanup_plan)
        cleanup_plan_id = cleanup_plan.id

        # Act
        service = IntegrityService()
        result = service.recover_commitment(
            session=session,
            commitment_id=commitment_id,
        )

        # Assert
        session.refresh(cleanup_plan)
        assert cleanup_plan.status == CleanupPlanStatus.CANCELLED
        assert result.cleanup_plan is not None
        assert result.cleanup_plan.status == CleanupPlanStatus.CANCELLED

    def test_raises_error_for_non_at_risk_commitment(self, session: Session) -> None:
        """Raises ValueError when trying to recover a non-at_risk commitment."""
        stakeholder = Stakeholder(name="Carol", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Regular task",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 12, 31),
            status=CommitmentStatus.IN_PROGRESS,
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)

        service = IntegrityService()
        with pytest.raises(ValueError, match="not at-risk"):
            service.recover_commitment(
                session=session,
                commitment_id=commitment.id,
            )

    def test_raises_error_for_nonexistent_commitment(self, session: Session) -> None:
        """Raises ValueError for non-existent commitment ID."""
        service = IntegrityService()
        fake_id = uuid4()

        with pytest.raises(ValueError, match="not found"):
            service.recover_commitment(
                session=session,
                commitment_id=fake_id,
            )

    def test_returns_notification_still_needed_when_task_pending(self, session: Session) -> None:
        """Returns notification_still_needed=True when notification task is pending."""
        stakeholder = Stakeholder(name="Dave", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Notify test",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 12, 31),
            status=CommitmentStatus.AT_RISK,
            marked_at_risk_at=datetime.now(UTC),
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)
        commitment_id = commitment.id

        # Create notification task
        notification_task = Task(
            commitment_id=commitment_id,
            title="Notify Dave",
            scope="Notification draft",
            order=0,
            is_notification_task=True,
            status=TaskStatus.PENDING,
        )
        session.add(notification_task)
        session.commit()
        session.refresh(notification_task)

        # Create cleanup plan linked to notification task
        cleanup_plan = CleanupPlan(
            commitment_id=commitment_id,
            status=CleanupPlanStatus.PLANNED,
            notification_task_id=notification_task.id,
        )
        session.add(cleanup_plan)
        session.commit()

        # Act
        service = IntegrityService()
        result = service.recover_commitment(
            session=session,
            commitment_id=commitment_id,
        )

        # Assert
        assert result.notification_still_needed is True
        # Notification task should NOT be marked skipped yet (user decides)
        session.refresh(notification_task)
        assert notification_task.status == TaskStatus.PENDING

    def test_skips_notification_task_when_resolved_flag_set(self, session: Session) -> None:
        """Marks notification task as SKIPPED when notification_resolved=True."""
        stakeholder = Stakeholder(name="Eve", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Skip notify test",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 12, 31),
            status=CommitmentStatus.AT_RISK,
            marked_at_risk_at=datetime.now(UTC),
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)
        commitment_id = commitment.id

        # Create notification task
        notification_task = Task(
            commitment_id=commitment_id,
            title="Notify Eve",
            scope="Notification draft",
            order=0,
            is_notification_task=True,
            status=TaskStatus.PENDING,
        )
        session.add(notification_task)
        session.commit()
        session.refresh(notification_task)

        # Create cleanup plan linked to notification task
        cleanup_plan = CleanupPlan(
            commitment_id=commitment_id,
            status=CleanupPlanStatus.PLANNED,
            notification_task_id=notification_task.id,
        )
        session.add(cleanup_plan)
        session.commit()

        # Act
        service = IntegrityService()
        result = service.recover_commitment(
            session=session,
            commitment_id=commitment_id,
            notification_resolved=True,
        )

        # Assert
        assert result.notification_still_needed is False
        session.refresh(notification_task)
        assert notification_task.status == TaskStatus.SKIPPED
        assert "Situation resolved" in notification_task.scope

    def test_returns_notification_not_needed_when_no_pending_task(self, session: Session) -> None:
        """Returns notification_still_needed=False when no pending notification task."""
        stakeholder = Stakeholder(name="Frank", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="No notify test",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 12, 31),
            status=CommitmentStatus.AT_RISK,
            marked_at_risk_at=datetime.now(UTC),
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)
        commitment_id = commitment.id

        # Create cleanup plan WITHOUT notification task
        cleanup_plan = CleanupPlan(
            commitment_id=commitment_id,
            status=CleanupPlanStatus.PLANNED,
        )
        session.add(cleanup_plan)
        session.commit()

        # Act
        service = IntegrityService()
        result = service.recover_commitment(
            session=session,
            commitment_id=commitment_id,
        )

        # Assert
        assert result.notification_still_needed is False

    def test_returns_result_with_all_entities(self, session: Session) -> None:
        """recover_commitment returns RecoveryResult with all entities."""
        stakeholder = Stakeholder(name="Grace", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="Full result test",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 12, 31),
            status=CommitmentStatus.AT_RISK,
            marked_at_risk_at=datetime.now(UTC),
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)
        commitment_id = commitment.id

        notification_task = Task(
            commitment_id=commitment_id,
            title="Notify Grace",
            scope="Notification",
            order=0,
            is_notification_task=True,
            status=TaskStatus.PENDING,
        )
        session.add(notification_task)
        session.commit()
        session.refresh(notification_task)

        cleanup_plan = CleanupPlan(
            commitment_id=commitment_id,
            status=CleanupPlanStatus.PLANNED,
            notification_task_id=notification_task.id,
        )
        session.add(cleanup_plan)
        session.commit()

        # Act
        service = IntegrityService()
        result = service.recover_commitment(
            session=session,
            commitment_id=commitment_id,
        )

        # Assert
        assert isinstance(result, RecoveryResult)
        assert result.commitment is not None
        assert result.cleanup_plan is not None
        assert result.notification_task is not None
        assert result.commitment.status == CommitmentStatus.IN_PROGRESS
        assert result.cleanup_plan.status == CleanupPlanStatus.CANCELLED

    def test_handles_commitment_without_cleanup_plan(self, session: Session) -> None:
        """Handles at-risk commitment that has no cleanup plan gracefully."""
        stakeholder = Stakeholder(name="Henry", type=StakeholderType.PERSON)
        session.add(stakeholder)
        session.commit()
        session.refresh(stakeholder)

        commitment = Commitment(
            deliverable="No plan test",
            stakeholder_id=stakeholder.id,
            due_date=date(2025, 12, 31),
            status=CommitmentStatus.AT_RISK,
            marked_at_risk_at=datetime.now(UTC),
        )
        session.add(commitment)
        session.commit()
        session.refresh(commitment)

        # Act - no cleanup plan exists
        service = IntegrityService()
        result = service.recover_commitment(
            session=session,
            commitment_id=commitment.id,
        )

        # Assert
        assert result.commitment.status == CommitmentStatus.IN_PROGRESS
        assert result.cleanup_plan is None
        assert result.notification_task is None
        assert result.notification_still_needed is False
