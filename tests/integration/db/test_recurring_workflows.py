"""Integration tests for recurring commitment workflows."""

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from sqlmodel import Session, select

from jdo.db.engine import get_engine, reset_engine
from jdo.db.migrations import create_db_and_tables
from jdo.db.session import (
    check_and_generate_recurring_instances,
    generate_next_instance_for_recurring,
    get_active_recurring_commitments,
)
from jdo.models import Commitment, CommitmentStatus, Stakeholder, StakeholderType
from jdo.models.recurring_commitment import (
    RecurrenceType,
    RecurringCommitment,
    RecurringCommitmentStatus,
)


@pytest.fixture
def db_session_with_tables(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Create a database with tables for integration testing."""
    from jdo.config.settings import reset_settings

    db_path = tmp_path / "recurring_test.db"
    monkeypatch.setenv("JDO_DATABASE_PATH", str(db_path))
    reset_settings()
    reset_engine()

    create_db_and_tables()
    engine = get_engine()

    with Session(engine) as session:
        yield session

    reset_engine()
    reset_settings()


@pytest.fixture
def stakeholder(db_session_with_tables: Session) -> Stakeholder:
    """Create a stakeholder for tests."""
    session = db_session_with_tables
    stakeholder = Stakeholder(name="Test User", type=StakeholderType.SELF)
    session.add(stakeholder)
    session.commit()
    session.refresh(stakeholder)
    return stakeholder


@pytest.mark.integration
class TestRecurringCommitmentWorkflows:
    """End-to-end tests for recurring commitment workflows."""

    def test_create_recurring_and_generate_first_instance(
        self, db_session_with_tables: Session, stakeholder: Stakeholder
    ) -> None:
        """Create recurring -> generate first instance workflow."""
        session = db_session_with_tables

        # Create recurring commitment
        recurring = RecurringCommitment(
            deliverable_template="Daily standup update",
            stakeholder_id=stakeholder.id,
            recurrence_type=RecurrenceType.DAILY,
        )
        session.add(recurring)
        session.commit()
        session.refresh(recurring)

        # Initial state checks
        assert recurring.instances_generated == 0
        assert recurring.last_generated_date is None

        # Trigger generation check
        current_date = datetime.now(UTC)
        recurring_id = recurring.id  # Save ID before session changes
        generated = check_and_generate_recurring_instances(session, current_date)

        # Should have generated one instance
        assert len(generated) == 1
        commitment, tasks = generated[0]
        assert commitment.deliverable == "Daily standup update"
        assert commitment.recurring_commitment_id == recurring_id

        # Re-query recurring to get updated state
        updated_recurring = session.get(RecurringCommitment, recurring_id)
        assert updated_recurring is not None
        assert updated_recurring.instances_generated == 1
        assert updated_recurring.last_generated_date is not None

    def test_complete_instance_and_generate_next(
        self, db_session_with_tables: Session, stakeholder: Stakeholder
    ) -> None:
        """Complete instance -> generate next workflow."""
        session = db_session_with_tables

        # Create recurring commitment
        recurring = RecurringCommitment(
            deliverable_template="Weekly report",
            stakeholder_id=stakeholder.id,
            recurrence_type=RecurrenceType.WEEKLY,
            days_of_week=[0],  # Monday
        )
        session.add(recurring)
        session.commit()
        session.refresh(recurring)

        # Generate first instance
        current_date = datetime.now(UTC)
        recurring_id = recurring.id  # Save ID
        generated = check_and_generate_recurring_instances(session, current_date)
        assert len(generated) == 1

        first_commitment, _ = generated[0]
        first_due_date = first_commitment.due_date

        # Mark first commitment complete
        first_commitment.status = CommitmentStatus.COMPLETED
        first_commitment.completed_at = datetime.now(UTC)
        session.commit()

        # Generate next instance
        next_result = generate_next_instance_for_recurring(session, recurring_id, current_date)
        assert next_result is not None

        next_commitment, _ = next_result
        assert next_commitment.due_date > first_due_date

        # Re-query recurring to get updated state
        updated_recurring = session.get(RecurringCommitment, recurring_id)
        assert updated_recurring is not None
        assert updated_recurring.instances_generated == 2

    def test_paused_recurring_no_generation(
        self, db_session_with_tables: Session, stakeholder: Stakeholder
    ) -> None:
        """Paused recurring commitment should not generate instances."""
        session = db_session_with_tables

        # Create and pause recurring commitment
        recurring = RecurringCommitment(
            deliverable_template="Daily task",
            stakeholder_id=stakeholder.id,
            recurrence_type=RecurrenceType.DAILY,
            status=RecurringCommitmentStatus.PAUSED,
        )
        session.add(recurring)
        session.commit()

        # Attempt generation
        current_date = datetime.now(UTC)
        generated = check_and_generate_recurring_instances(session, current_date)

        # Should not generate anything
        assert len(generated) == 0

    def test_resume_paused_recurring_generates(
        self, db_session_with_tables: Session, stakeholder: Stakeholder
    ) -> None:
        """Resuming paused recurring should allow generation."""
        session = db_session_with_tables

        # Create paused recurring
        recurring = RecurringCommitment(
            deliverable_template="Daily task",
            stakeholder_id=stakeholder.id,
            recurrence_type=RecurrenceType.DAILY,
            status=RecurringCommitmentStatus.PAUSED,
        )
        session.add(recurring)
        session.commit()
        session.refresh(recurring)

        # Verify no generation while paused
        current_date = datetime.now(UTC)
        generated = check_and_generate_recurring_instances(session, current_date)
        assert len(generated) == 0

        # Resume
        recurring.status = RecurringCommitmentStatus.ACTIVE
        session.commit()

        # Now should generate
        generated = check_and_generate_recurring_instances(session, current_date)
        assert len(generated) == 1

    def test_delete_recurring_instances_remain(
        self, db_session_with_tables: Session, stakeholder: Stakeholder
    ) -> None:
        """Delete recurring -> instances remain with NULL reference."""
        session = db_session_with_tables

        # Create recurring and generate instance
        recurring = RecurringCommitment(
            deliverable_template="Daily task",
            stakeholder_id=stakeholder.id,
            recurrence_type=RecurrenceType.DAILY,
        )
        session.add(recurring)
        session.commit()
        session.refresh(recurring)
        recurring_id = recurring.id

        # Generate instance
        current_date = datetime.now(UTC)
        generated = check_and_generate_recurring_instances(session, current_date)
        commitment, _ = generated[0]
        commitment_id = commitment.id

        # Verify link exists on the generated commitment
        assert commitment.recurring_commitment_id == recurring_id

        # Re-query recurring to delete
        recurring_to_delete = session.get(RecurringCommitment, recurring_id)
        assert recurring_to_delete is not None
        session.delete(recurring_to_delete)
        session.commit()

        # Expire and refresh to get fresh data
        session.expire_all()

        # Instance should still exist with NULL link
        result = session.get(Commitment, commitment_id)
        assert result is not None
        assert result.deliverable == "Daily task"
        assert result.recurring_commitment_id is None

    def test_multiple_recurring_commitments(
        self, db_session_with_tables: Session, stakeholder: Stakeholder
    ) -> None:
        """Multiple recurring commitments generate independently."""
        session = db_session_with_tables

        # Create two recurring commitments
        daily = RecurringCommitment(
            deliverable_template="Daily standup",
            stakeholder_id=stakeholder.id,
            recurrence_type=RecurrenceType.DAILY,
        )
        weekly = RecurringCommitment(
            deliverable_template="Weekly report",
            stakeholder_id=stakeholder.id,
            recurrence_type=RecurrenceType.WEEKLY,
            days_of_week=[4],  # Friday
        )
        session.add_all([daily, weekly])
        session.commit()

        # Check active recurring commitments
        active = get_active_recurring_commitments(session)
        assert len(active) == 2

        # Generate instances
        current_date = datetime.now(UTC)
        generated = check_and_generate_recurring_instances(session, current_date)

        # Should have generated for both
        assert len(generated) == 2

        # Verify they're different
        deliverables = {c.deliverable for c, _ in generated}
        assert "Daily standup" in deliverables
        assert "Weekly report" in deliverables

    def test_generation_respects_count_limit(
        self, db_session_with_tables: Session, stakeholder: Stakeholder
    ) -> None:
        """Generation stops at end_after_count limit."""
        from jdo.models.recurring_commitment import EndType

        session = db_session_with_tables

        # Create recurring with count limit of 2
        recurring = RecurringCommitment(
            deliverable_template="Limited task",
            stakeholder_id=stakeholder.id,
            recurrence_type=RecurrenceType.DAILY,
            end_type=EndType.AFTER_COUNT,
            end_after_count=2,
        )
        session.add(recurring)
        session.commit()
        session.refresh(recurring)

        # Generate first
        current_date = datetime.now(UTC)
        recurring_id = recurring.id  # Save ID
        generated1 = check_and_generate_recurring_instances(session, current_date)
        assert len(generated1) == 1

        # Generate second
        generated2 = generate_next_instance_for_recurring(session, recurring_id, current_date)
        assert generated2 is not None

        # Re-query recurring to check state
        updated_recurring = session.get(RecurringCommitment, recurring_id)
        assert updated_recurring is not None
        assert updated_recurring.instances_generated == 2

        # Third should not generate (at limit)
        generated3 = generate_next_instance_for_recurring(session, recurring_id, current_date)
        assert generated3 is None

    def test_query_commitments_by_recurring(
        self, db_session_with_tables: Session, stakeholder: Stakeholder
    ) -> None:
        """Can query all instances of a recurring commitment."""
        session = db_session_with_tables

        # Create recurring
        recurring = RecurringCommitment(
            deliverable_template="Daily task",
            stakeholder_id=stakeholder.id,
            recurrence_type=RecurrenceType.DAILY,
        )
        session.add(recurring)
        session.commit()
        session.refresh(recurring)
        recurring_id = recurring.id

        # Generate multiple instances
        current_date = datetime.now(UTC)
        check_and_generate_recurring_instances(session, current_date)
        generate_next_instance_for_recurring(session, recurring_id, current_date)
        generate_next_instance_for_recurring(session, recurring_id, current_date)

        # Query by recurring_commitment_id
        results = session.exec(
            select(Commitment).where(Commitment.recurring_commitment_id == recurring_id)
        ).all()

        assert len(results) == 3
        for c in results:
            assert c.deliverable == "Daily task"
            assert c.recurring_commitment_id == recurring_id


@pytest.mark.integration
class TestRecurringGenerationTriggers:
    """Tests for generation trigger behavior (Phase 6)."""

    def test_viewing_upcoming_commitments_triggers_generation(
        self, db_session_with_tables: Session, stakeholder: Stakeholder
    ) -> None:
        """Test: Viewing upcoming commitments triggers generation check."""
        session = db_session_with_tables

        # Create recurring commitment
        recurring = RecurringCommitment(
            deliverable_template="Daily standup",
            stakeholder_id=stakeholder.id,
            recurrence_type=RecurrenceType.DAILY,
        )
        session.add(recurring)
        session.commit()

        # No instances yet
        all_commitments = session.exec(select(Commitment)).all()
        assert len(all_commitments) == 0

        # Simulate viewing upcoming (triggers generation)
        current_date = datetime.now(UTC)
        check_and_generate_recurring_instances(session, current_date)

        # Now there should be an instance
        all_commitments = session.exec(select(Commitment)).all()
        assert len(all_commitments) == 1
        assert all_commitments[0].deliverable == "Daily standup"

    def test_completing_instance_triggers_next_generation(
        self, db_session_with_tables: Session, stakeholder: Stakeholder
    ) -> None:
        """Test: Completing instance triggers next generation."""
        session = db_session_with_tables

        # Create recurring commitment
        recurring = RecurringCommitment(
            deliverable_template="Weekly report",
            stakeholder_id=stakeholder.id,
            recurrence_type=RecurrenceType.WEEKLY,
            days_of_week=[0],  # Monday
        )
        session.add(recurring)
        session.commit()
        session.refresh(recurring)
        recurring_id = recurring.id

        # Generate first instance
        current_date = datetime.now(UTC)
        generated = check_and_generate_recurring_instances(session, current_date)
        assert len(generated) == 1
        first_commitment, _ = generated[0]

        # Complete the first instance
        first_commitment.status = CommitmentStatus.COMPLETED
        first_commitment.completed_at = datetime.now(UTC)
        session.commit()

        # Completing should trigger next generation
        next_result = generate_next_instance_for_recurring(session, recurring_id, current_date)

        assert next_result is not None
        next_commitment, _ = next_result
        assert next_commitment.due_date > first_commitment.due_date

        # Now should have 2 instances
        all_instances = session.exec(
            select(Commitment).where(Commitment.recurring_commitment_id == recurring_id)
        ).all()
        assert len(all_instances) == 2

    def test_show_commitments_includes_generated_instances(
        self, db_session_with_tables: Session, stakeholder: Stakeholder
    ) -> None:
        """Test: /show commitments includes generated instances."""
        session = db_session_with_tables

        # Create a regular commitment
        regular = Commitment(
            deliverable="Regular one-time task",
            stakeholder_id=stakeholder.id,
            due_date=date.today() + timedelta(days=7),
        )
        session.add(regular)

        # Create recurring commitment
        recurring = RecurringCommitment(
            deliverable_template="Daily standup",
            stakeholder_id=stakeholder.id,
            recurrence_type=RecurrenceType.DAILY,
        )
        session.add(recurring)
        session.commit()

        # Generate instance from recurring
        current_date = datetime.now(UTC)
        check_and_generate_recurring_instances(session, current_date)

        # Query all commitments (simulates /show commitments)
        all_commitments = session.exec(select(Commitment)).all()

        # Should include both regular and generated
        assert len(all_commitments) == 2
        deliverables = {c.deliverable for c in all_commitments}
        assert "Regular one-time task" in deliverables
        assert "Daily standup" in deliverables

        # Verify the generated one has recurring link
        recurring_instance = next(c for c in all_commitments if c.deliverable == "Daily standup")
        assert recurring_instance.recurring_commitment_id is not None
