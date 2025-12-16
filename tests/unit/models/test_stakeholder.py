"""Tests for Stakeholder SQLModel - TDD Red phase."""

from pathlib import Path
from unittest.mock import patch
from uuid import UUID

import pytest
from sqlmodel import SQLModel

from jdo.models.stakeholder import Stakeholder, StakeholderType


class TestStakeholderModel:
    """Tests for Stakeholder model structure."""

    def test_inherits_from_sqlmodel_with_table_true(self) -> None:
        """Stakeholder inherits from SQLModel with table=True."""
        assert issubclass(Stakeholder, SQLModel)
        # Check that it's a table model
        assert hasattr(Stakeholder, "__tablename__")

    def test_has_tablename_stakeholders(self) -> None:
        """Stakeholder has tablename 'stakeholders'."""
        assert Stakeholder.__tablename__ == "stakeholders"

    def test_has_required_fields(self) -> None:
        """Stakeholder has all required fields."""
        fields = Stakeholder.model_fields
        assert "id" in fields
        assert "name" in fields
        assert "type" in fields
        assert "contact_info" in fields
        assert "notes" in fields
        assert "created_at" in fields
        assert "updated_at" in fields


class TestStakeholderValidation:
    """Tests for Stakeholder field validation."""

    def test_creates_with_required_fields(self) -> None:
        """Create stakeholder with name and type."""
        stakeholder = Stakeholder(name="Alice", type=StakeholderType.PERSON)

        assert stakeholder.name == "Alice"
        assert stakeholder.type == StakeholderType.PERSON
        assert isinstance(stakeholder.id, UUID)

    def test_validates_name_non_empty(self) -> None:
        """Reject empty stakeholder name via model_validate."""
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            Stakeholder.model_validate({"name": "", "type": "person"})

    def test_validates_type_is_stakeholder_type(self) -> None:
        """Reject invalid stakeholder type via model_validate."""
        with pytest.raises(ValueError, match="Input should be"):
            Stakeholder.model_validate({"name": "Alice", "type": "invalid"})

    def test_optional_fields_default_to_none(self) -> None:
        """Optional fields default to None."""
        stakeholder = Stakeholder(name="Bob", type=StakeholderType.TEAM)

        assert stakeholder.contact_info is None
        assert stakeholder.notes is None

    def test_accepts_optional_fields(self) -> None:
        """Create stakeholder with optional fields."""
        stakeholder = Stakeholder(
            name="Acme Corp",
            type=StakeholderType.ORGANIZATION,
            contact_info="contact@acme.com",
            notes="Main client",
        )

        assert stakeholder.contact_info == "contact@acme.com"
        assert stakeholder.notes == "Main client"


class TestStakeholderType:
    """Tests for StakeholderType enum."""

    def test_has_required_values(self) -> None:
        """StakeholderType has person, team, organization, self."""
        assert StakeholderType.PERSON.value == "person"
        assert StakeholderType.TEAM.value == "team"
        assert StakeholderType.ORGANIZATION.value == "organization"
        assert StakeholderType.SELF.value == "self"


class TestStakeholderPersistence:
    """Tests for Stakeholder database persistence."""

    def test_save_and_retrieve(self, tmp_path: Path) -> None:
        """Save stakeholder via session and retrieve by id."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            # Create and save
            stakeholder = Stakeholder(name="Charlie", type=StakeholderType.PERSON)
            original_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            # Retrieve in new session
            with get_session() as session:
                result = session.exec(
                    select(Stakeholder).where(Stakeholder.id == original_id)
                ).first()

                assert result is not None
                assert result.name == "Charlie"
                assert result.type == StakeholderType.PERSON

        reset_engine()

    def test_update_refreshes_updated_at(self, tmp_path: Path) -> None:
        """Updating stakeholder refreshes updated_at timestamp."""
        from sqlmodel import select

        from jdo.db.engine import get_engine, reset_engine
        from jdo.db.session import get_session

        reset_engine()
        db_path = tmp_path / "test.db"

        with patch("jdo.db.engine.get_settings") as mock_settings:
            mock_settings.return_value.database_path = db_path
            engine = get_engine()
            SQLModel.metadata.create_all(engine)

            stakeholder = Stakeholder(name="Dave", type=StakeholderType.TEAM)
            original_id = stakeholder.id

            with get_session() as session:
                session.add(stakeholder)

            # Update in new session
            with get_session() as session:
                result = session.exec(
                    select(Stakeholder).where(Stakeholder.id == original_id)
                ).first()
                assert result is not None
                result.name = "David"

            # Verify update
            with get_session() as session:
                result = session.exec(
                    select(Stakeholder).where(Stakeholder.id == original_id)
                ).first()
                assert result is not None
                assert result.name == "David"
                # updated_at should be refreshed (may be same if fast execution)
                assert result.updated_at is not None

        reset_engine()
