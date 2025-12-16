"""Tests for Vision SQLModel - TDD Red phase."""

from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import UUID

import pytest
from sqlmodel import SQLModel

from jdo.models.vision import Vision, VisionStatus


def utc_today() -> date:
    """Get today's date in UTC."""
    return datetime.now(UTC).date()


class TestVisionModel:
    """Tests for Vision model structure."""

    def test_inherits_from_sqlmodel_with_table_true(self) -> None:
        """Vision inherits from SQLModel with table=True."""
        assert issubclass(Vision, SQLModel)
        assert hasattr(Vision, "__tablename__")

    def test_has_tablename_visions(self) -> None:
        """Vision has tablename 'visions'."""
        assert Vision.__tablename__ == "visions"

    def test_has_required_fields(self) -> None:
        """Vision has all required fields."""
        fields = Vision.model_fields
        assert "id" in fields
        assert "title" in fields
        assert "narrative" in fields
        assert "timeframe" in fields
        assert "metrics" in fields
        assert "why_it_matters" in fields
        assert "status" in fields
        assert "next_review_date" in fields
        assert "last_reviewed_at" in fields
        assert "created_at" in fields
        assert "updated_at" in fields


class TestVisionValidation:
    """Tests for Vision field validation."""

    def test_creates_with_required_fields(self) -> None:
        """Create vision with required fields."""
        vision = Vision(
            title="Be a thought leader in AI ethics",
            narrative="I'm invited to speak at major conferences...",
        )

        assert vision.title == "Be a thought leader in AI ethics"
        assert vision.narrative == "I'm invited to speak at major conferences..."
        assert vision.status == VisionStatus.ACTIVE
        assert isinstance(vision.id, UUID)

    def test_validates_title_non_empty(self) -> None:
        """Reject empty title via model_validate."""
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            Vision.model_validate(
                {
                    "title": "",
                    "narrative": "Some narrative",
                }
            )

    def test_validates_narrative_non_empty(self) -> None:
        """Reject empty narrative via model_validate."""
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            Vision.model_validate(
                {
                    "title": "Some title",
                    "narrative": "",
                }
            )

    def test_optional_fields_default_to_none(self) -> None:
        """Optional fields default to None."""
        vision = Vision(
            title="Test Vision",
            narrative="Test narrative",
        )

        assert vision.timeframe is None
        assert vision.why_it_matters is None
        assert vision.last_reviewed_at is None

    def test_metrics_defaults_to_empty_list(self) -> None:
        """Metrics defaults to empty list."""
        vision = Vision(
            title="Test Vision",
            narrative="Test narrative",
        )

        assert vision.metrics == []

    def test_metrics_stored_as_list(self) -> None:
        """Metrics are stored as a list."""
        vision = Vision(
            title="Test Vision",
            narrative="Test narrative",
            metrics=["Metric 1", "Metric 2", "Metric 3"],
        )

        assert vision.metrics == ["Metric 1", "Metric 2", "Metric 3"]
        assert len(vision.metrics) == 3

    def test_status_defaults_to_active(self) -> None:
        """Status defaults to active."""
        vision = Vision(
            title="Test Vision",
            narrative="Test narrative",
        )

        assert vision.status == VisionStatus.ACTIVE

    def test_next_review_date_defaults_to_90_days(self) -> None:
        """next_review_date defaults to 90 days from creation."""
        vision = Vision(
            title="Test Vision",
            narrative="Test narrative",
        )

        expected = utc_today() + timedelta(days=90)
        assert vision.next_review_date == expected

    def test_auto_generates_id_and_timestamps(self) -> None:
        """Auto-generates id, created_at, updated_at."""
        vision = Vision(
            title="Test Vision",
            narrative="Test narrative",
        )

        assert isinstance(vision.id, UUID)
        assert isinstance(vision.created_at, datetime)
        assert isinstance(vision.updated_at, datetime)


class TestVisionStatus:
    """Tests for VisionStatus enum."""

    def test_has_required_values(self) -> None:
        """VisionStatus has active, achieved, evolved, abandoned."""
        assert VisionStatus.ACTIVE.value == "active"
        assert VisionStatus.ACHIEVED.value == "achieved"
        assert VisionStatus.EVOLVED.value == "evolved"
        assert VisionStatus.ABANDONED.value == "abandoned"


class TestVisionReview:
    """Tests for Vision review functionality."""

    def test_vision_due_for_review_when_date_is_today(self) -> None:
        """Vision is due for review when next_review_date <= today."""
        vision = Vision(
            title="Test Vision",
            narrative="Test narrative",
            next_review_date=date.today(),
        )

        assert vision.is_due_for_review()

    def test_vision_due_for_review_when_date_in_past(self) -> None:
        """Vision is due for review when next_review_date is in past."""
        vision = Vision(
            title="Test Vision",
            narrative="Test narrative",
            next_review_date=date.today() - timedelta(days=7),
        )

        assert vision.is_due_for_review()

    def test_vision_not_due_when_date_in_future(self) -> None:
        """Vision is not due for review when next_review_date is in future."""
        vision = Vision(
            title="Test Vision",
            narrative="Test narrative",
            next_review_date=date.today() + timedelta(days=30),
        )

        assert not vision.is_due_for_review()

    def test_complete_review_updates_timestamps(self) -> None:
        """Completing review sets last_reviewed_at and next_review_date."""
        vision = Vision(
            title="Test Vision",
            narrative="Test narrative",
            next_review_date=utc_today() - timedelta(days=7),
        )

        vision.complete_review()

        assert vision.last_reviewed_at is not None
        assert vision.next_review_date == utc_today() + timedelta(days=90)


class TestVisionPersistence:
    """Tests for Vision database persistence."""

    def test_save_and_retrieve(self, tmp_path: Path) -> None:
        """Save vision via session and retrieve by id."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            vision = Vision(
                title="Test Vision",
                narrative="Test narrative",
                metrics=["Metric 1", "Metric 2"],
            )
            original_id = vision.id

            with get_session() as session:
                session.add(vision)

            with get_session() as session:
                result = session.exec(select(Vision).where(Vision.id == original_id)).first()

                assert result is not None
                assert result.title == "Test Vision"
                assert result.status == VisionStatus.ACTIVE
                assert result.metrics == ["Metric 1", "Metric 2"]

        reset_engine()

    def test_list_visions_with_status_filter(self, tmp_path: Path) -> None:
        """List visions filtered by status."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            active_vision = Vision(
                title="Active Vision",
                narrative="Narrative 1",
                status=VisionStatus.ACTIVE,
            )
            achieved_vision = Vision(
                title="Achieved Vision",
                narrative="Narrative 2",
                status=VisionStatus.ACHIEVED,
            )

            with get_session() as session:
                session.add(active_vision)
                session.add(achieved_vision)

            with get_session() as session:
                result = session.exec(
                    select(Vision).where(Vision.status == VisionStatus.ACTIVE)
                ).all()

                assert len(result) == 1
                assert result[0].title == "Active Vision"

        reset_engine()

    def test_query_visions_due_for_review(self, tmp_path: Path) -> None:
        """Query visions where next_review_date <= today."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            due_vision = Vision(
                title="Due Vision",
                narrative="Narrative 1",
                next_review_date=date.today() - timedelta(days=7),
            )
            future_vision = Vision(
                title="Future Vision",
                narrative="Narrative 2",
                next_review_date=date.today() + timedelta(days=30),
            )

            with get_session() as session:
                session.add(due_vision)
                session.add(future_vision)

            with get_session() as session:
                result = session.exec(
                    select(Vision).where(
                        Vision.status == VisionStatus.ACTIVE,
                        Vision.next_review_date <= date.today(),
                    )
                ).all()

                assert len(result) == 1
                assert result[0].title == "Due Vision"

        reset_engine()
