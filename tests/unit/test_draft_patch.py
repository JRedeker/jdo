"""Tests for draft_patch module."""

from __future__ import annotations

import pytest

from jdo.commands.draft_patch import (
    PatchResult,
    apply_patch,
    parse_entity_type,
)
from jdo.models.draft import EntityType


class TestParseEntityType:
    """Tests for parse_entity_type function."""

    def test_parse_commitment(self) -> None:
        """Test parsing commitment entity type."""
        result = parse_entity_type("commitment")
        assert result == EntityType.COMMITMENT

    def test_parse_goal(self) -> None:
        """Test parsing goal entity type."""
        result = parse_entity_type("goal")
        assert result == EntityType.GOAL

    def test_parse_task(self) -> None:
        """Test parsing task entity type."""
        result = parse_entity_type("task")
        assert result == EntityType.TASK

    def test_parse_vision(self) -> None:
        """Test parsing vision entity type."""
        result = parse_entity_type("vision")
        assert result == EntityType.VISION

    def test_parse_milestone(self) -> None:
        """Test parsing milestone entity type."""
        result = parse_entity_type("milestone")
        assert result == EntityType.MILESTONE

    def test_parse_case_insensitive(self) -> None:
        """Test that parsing is case insensitive."""
        assert parse_entity_type("COMMITMENT") == EntityType.COMMITMENT
        assert parse_entity_type("Goal") == EntityType.GOAL
        assert parse_entity_type("TASK") == EntityType.TASK

    def test_parse_with_whitespace(self) -> None:
        """Test parsing with surrounding whitespace."""
        result = parse_entity_type("  commitment  ")
        assert result == EntityType.COMMITMENT

    def test_parse_unknown_returns_none(self) -> None:
        """Test that unknown types return None."""
        assert parse_entity_type("something") is None
        assert parse_entity_type("unknown") is None
        assert parse_entity_type("") is None


class TestApplyPatch:
    """Tests for apply_patch function."""

    def test_apply_patch_to_unknown_entity_fails(self) -> None:
        """Test that patching an UNKNOWN entity type fails."""
        draft: dict[str, object] = {"raw_text": "test"}
        result = apply_patch(EntityType.UNKNOWN, draft, "change stakeholder to Bob")

        assert result.applied is False
        error_msg = result.error
        assert error_msg is not None
        assert "must be typed before" in error_msg

    def test_apply_patch_unimplemented_type_fails(self) -> None:
        """Test that unimplemented entity types return error."""
        draft: dict[str, object] = {"raw_text": "test"}
        result = apply_patch(EntityType.GOAL, draft, "change title to New Title")

        assert result.applied is False
        error_msg = result.error
        assert error_msg is not None
        assert "No patch rules implemented" in error_msg

    def test_apply_patch_commitment_stakeholder(self) -> None:
        """Test patching commitment stakeholder."""
        draft: dict[str, object] = {"stakeholder": "Alice", "deliverable": "Write code"}
        result = apply_patch(EntityType.COMMITMENT, draft, "change stakeholder to Bob")

        assert result.applied is True
        updated = result.updated
        assert updated["stakeholder"] == "Bob"
        summary = result.summary
        assert summary is not None
        assert "Updated stakeholder" in summary

    def test_apply_patch_commitment_stakeholder_variations(self) -> None:
        """Test various stakeholder change phrasings."""
        draft: dict[str, object] = {"stakeholder": "Alice"}

        result = apply_patch(EntityType.COMMITMENT, draft, "stakeholder to Bob")
        assert result.applied is True
        assert result.updated["stakeholder"] == "Bob"

        result = apply_patch(EntityType.COMMITMENT, draft, "change stakeholder to Charlie")
        assert result.applied is True
        assert result.updated["stakeholder"] == "Charlie"

    def test_apply_patch_commitment_deliverable(self) -> None:
        """Test patching commitment deliverable."""
        draft: dict[str, object] = {"deliverable": "Old deliverable"}
        result = apply_patch(EntityType.COMMITMENT, draft, "change deliverable to New deliverable")

        assert result.applied is True
        assert result.updated["deliverable"] == "New deliverable"
        summary = result.summary
        assert summary is not None
        assert "Updated deliverable" in summary

    def test_apply_patch_commitment_due_date(self) -> None:
        """Test patching commitment due date."""
        draft: dict[str, object] = {"due_date": "2024-01-01"}
        result = apply_patch(EntityType.COMMITMENT, draft, "change due date to 2024-12-31")

        assert result.applied is True
        assert result.updated["due_date"] == "2024-12-31"
        summary = result.summary
        assert summary is not None
        assert "Updated due_date" in summary

    def test_apply_patch_commitment_due_time(self) -> None:
        """Test patching commitment due time."""
        draft: dict[str, object] = {"due_time": "09:00"}
        result = apply_patch(EntityType.COMMITMENT, draft, "change due time to 14:30")

        assert result.applied is True
        assert result.updated["due_time"] == "14:30"
        summary = result.summary
        assert summary is not None
        assert "Updated due_time" in summary

    def test_apply_patch_commitment_invalid_pattern(self) -> None:
        """Test that invalid patch pattern returns error message."""
        draft: dict[str, object] = {"stakeholder": "Alice"}
        result = apply_patch(EntityType.COMMITMENT, draft, "make it faster please")

        assert result.applied is False
        error_msg = result.error
        assert error_msg is not None
        assert "couldn't apply that change" in error_msg
        assert "stakeholder to" in error_msg
        assert "deliverable to" in error_msg
        assert "due date to" in error_msg
        assert "due time to" in error_msg

    def test_apply_patch_empty_value_fails(self) -> None:
        """Test that empty values fail validation."""
        draft: dict[str, object] = {"stakeholder": "Alice"}

        result = apply_patch(EntityType.COMMITMENT, draft, "change stakeholder to ")
        assert result.applied is False
        error_msg = result.error
        assert error_msg is not None
        assert "couldn't apply that change" in error_msg


class TestPatchResult:
    """Tests for PatchResult dataclass."""

    def test_patch_result_success(self) -> None:
        """Test successful patch result."""
        result = PatchResult(applied=True, updated={"key": "value"}, summary="Updated key.")

        assert result.applied is True
        assert result.updated == {"key": "value"}
        assert result.summary == "Updated key."
        assert result.error is None

    def test_patch_result_error(self) -> None:
        """Test error patch result."""
        result = PatchResult(
            applied=False,
            updated={"key": "old"},
            error="Something went wrong",
        )

        assert result.applied is False
        assert result.updated == {"key": "old"}
        assert result.error == "Something went wrong"
        assert result.summary is None
