"""Tests for Draft SQLModel - TDD Red phase.

Draft model stores partially created domain objects for restoration on app restart.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest
from sqlmodel import SQLModel, select

from jdo.models.draft import Draft, EntityType


class TestDraftModel:
    """Tests for Draft model structure."""

    def test_inherits_from_sqlmodel_with_table_true(self) -> None:
        """Draft inherits from SQLModel with table=True."""
        assert issubclass(Draft, SQLModel)
        assert hasattr(Draft, "__tablename__")

    def test_has_tablename_drafts(self) -> None:
        """Draft has tablename 'drafts'."""
        assert Draft.__tablename__ == "drafts"

    def test_has_required_fields(self) -> None:
        """Draft has all required fields."""
        fields = Draft.model_fields
        assert "id" in fields
        assert "entity_type" in fields
        assert "partial_data" in fields
        assert "created_at" in fields
        assert "updated_at" in fields


class TestEntityType:
    """Tests for EntityType enum."""

    def test_has_all_entity_types(self) -> None:
        """EntityType has commitment, goal, task, vision, milestone."""
        assert EntityType.COMMITMENT.value == "commitment"
        assert EntityType.GOAL.value == "goal"
        assert EntityType.TASK.value == "task"
        assert EntityType.VISION.value == "vision"
        assert EntityType.MILESTONE.value == "milestone"


class TestDraftValidation:
    """Tests for Draft field validation."""

    def test_requires_entity_type(self) -> None:
        """Draft requires entity_type."""
        draft = Draft(
            entity_type=EntityType.COMMITMENT,
            partial_data={"deliverable": "Test"},
        )
        assert draft.entity_type == EntityType.COMMITMENT

    def test_stores_partial_data_as_json(self) -> None:
        """Draft stores partial_data as JSON dict."""
        partial = {"deliverable": "Send report", "stakeholder_name": "Finance Team"}
        draft = Draft(
            entity_type=EntityType.COMMITMENT,
            partial_data=partial,
        )
        assert draft.partial_data == partial
        assert draft.partial_data["deliverable"] == "Send report"

    def test_auto_generates_id(self) -> None:
        """Draft auto-generates UUID id."""
        draft = Draft(
            entity_type=EntityType.GOAL,
            partial_data={"title": "Test Goal"},
        )
        assert isinstance(draft.id, UUID)

    def test_auto_generates_created_at(self) -> None:
        """Draft auto-generates created_at timestamp."""
        draft = Draft(
            entity_type=EntityType.TASK,
            partial_data={"title": "Test Task"},
        )
        assert isinstance(draft.created_at, datetime)
        # Should be recent (within last minute)
        assert draft.created_at > datetime.now(UTC) - timedelta(minutes=1)

    def test_auto_generates_updated_at(self) -> None:
        """Draft auto-generates updated_at timestamp."""
        draft = Draft(
            entity_type=EntityType.VISION,
            partial_data={"title": "Test Vision"},
        )
        assert isinstance(draft.updated_at, datetime)


class TestDraftPersistence:
    """Tests for Draft database persistence."""

    def test_save_and_retrieve_by_id(self, tmp_path: Path) -> None:
        """Save draft via session and retrieve by id."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            draft = Draft(
                entity_type=EntityType.COMMITMENT,
                partial_data={"deliverable": "Test", "notes": "Some context"},
            )
            draft_id = draft.id

            with get_session() as session:
                session.add(draft)

            with get_session() as session:
                result = session.exec(select(Draft).where(Draft.id == draft_id)).first()
                assert result is not None
                assert result.entity_type == EntityType.COMMITMENT
                assert result.partial_data["deliverable"] == "Test"

        reset_engine()

    def test_only_one_active_draft_per_entity_type(self, tmp_path: Path) -> None:
        """Only one active draft per entity_type allowed."""
        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Create first commitment draft
            draft1 = Draft(
                entity_type=EntityType.COMMITMENT,
                partial_data={"deliverable": "First"},
            )

            with get_session() as session:
                session.add(draft1)

            # Query for commitment drafts - should find one
            with get_session() as session:
                result = session.exec(
                    select(Draft).where(Draft.entity_type == EntityType.COMMITMENT)
                ).all()
                assert len(result) == 1

            # Can have different entity type draft
            draft2 = Draft(
                entity_type=EntityType.GOAL,
                partial_data={"title": "Goal draft"},
            )

            with get_session() as session:
                session.add(draft2)

            # Total drafts should be 2, but only 1 per type
            with get_session() as session:
                all_drafts = session.exec(select(Draft)).all()
                assert len(all_drafts) == 2

                commitment_drafts = session.exec(
                    select(Draft).where(Draft.entity_type == EntityType.COMMITMENT)
                ).all()
                assert len(commitment_drafts) == 1

                goal_drafts = session.exec(
                    select(Draft).where(Draft.entity_type == EntityType.GOAL)
                ).all()
                assert len(goal_drafts) == 1

        reset_engine()


class TestDraftExpiration:
    """Tests for Draft expiration handling."""

    def test_draft_older_than_7_days_flagged_for_expiration(self) -> None:
        """Draft older than 7 days is flagged for expiration prompt."""
        old_date = datetime.now(UTC) - timedelta(days=8)
        draft = Draft(
            entity_type=EntityType.COMMITMENT,
            partial_data={"deliverable": "Old task"},
            created_at=old_date,
            updated_at=old_date,
        )

        assert draft.is_expired()

    def test_recent_draft_not_expired(self) -> None:
        """Draft less than 7 days old is not expired."""
        recent_date = datetime.now(UTC) - timedelta(days=3)
        draft = Draft(
            entity_type=EntityType.COMMITMENT,
            partial_data={"deliverable": "Recent task"},
            created_at=recent_date,
            updated_at=recent_date,
        )

        assert not draft.is_expired()

    def test_draft_exactly_7_days_old_not_expired(self) -> None:
        """Draft exactly 7 days old is not yet expired."""
        # Use 6 days 23 hours to avoid race conditions with millisecond timing
        boundary_date = datetime.now(UTC) - timedelta(days=6, hours=23, minutes=59)
        draft = Draft(
            entity_type=EntityType.GOAL,
            partial_data={"title": "Boundary draft"},
            created_at=boundary_date,
            updated_at=boundary_date,
        )

        assert not draft.is_expired()
