"""Rule-based draft patching for conversational edits.

This module implements deterministic (non-AI) parsing of common edit requests.
Drafts must be typed (commitment/goal/task/vision/milestone) before patching.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from jdo.models.draft import EntityType


@dataclass(frozen=True)
class PatchResult:
    """Result from applying a patch."""

    applied: bool
    updated: dict[str, Any]
    summary: str | None = None
    error: str | None = None


_TYPE_ALIASES: dict[str, EntityType] = {
    "commitment": EntityType.COMMITMENT,
    "goal": EntityType.GOAL,
    "task": EntityType.TASK,
    "vision": EntityType.VISION,
    "milestone": EntityType.MILESTONE,
}


def parse_entity_type(text: str) -> EntityType | None:
    """Parse an entity type from plain text.

    Args:
        text: User input.

    Returns:
        EntityType if recognized (excluding UNKNOWN), otherwise None.
    """
    normalized = text.strip().lower()
    return _TYPE_ALIASES.get(normalized)


def apply_patch(entity_type: EntityType, draft: dict[str, Any], text: str) -> PatchResult:
    """Apply a rules-based patch to a typed draft.

    Args:
        entity_type: Typed entity type (must not be UNKNOWN).
        draft: Current draft data.
        text: User's modification request.

    Returns:
        PatchResult describing changes.
    """
    if entity_type == EntityType.UNKNOWN:
        return PatchResult(
            applied=False,
            updated=draft,
            error="Draft must be typed before it can be edited.",
        )

    if entity_type == EntityType.COMMITMENT:
        return _patch_commitment(draft, text)

    return PatchResult(
        applied=False,
        updated=draft,
        error=f"No patch rules implemented yet for {entity_type.value}.",
    )


_COMMITMENT_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^(?:change\s+)?stakeholder\s+to\s+(.+)$", re.IGNORECASE), "stakeholder"),
    (re.compile(r"^(?:change\s+)?deliverable\s+to\s+(.+)$", re.IGNORECASE), "deliverable"),
    (
        re.compile(r"^(?:change\s+)?due\s+date\s+to\s+(\d{4}-\d{2}-\d{2})$", re.IGNORECASE),
        "due_date",
    ),
    (re.compile(r"^(?:change\s+)?due\s+time\s+to\s+(\d{1,2}:\d{2})$", re.IGNORECASE), "due_time"),
]


def _patch_commitment(draft: dict[str, Any], text: str) -> PatchResult:
    """Patch commitment draft fields."""
    normalized = text.strip()

    for pattern, field in _COMMITMENT_PATTERNS:
        match = pattern.match(normalized)
        if not match:
            continue

        value = match.group(1).strip()
        if not value:
            return PatchResult(
                applied=False,
                updated=draft,
                error=f"{field} cannot be empty.",
            )

        updated = {**draft, field: value}
        return PatchResult(
            applied=True,
            updated=updated,
            summary=f"Updated {field}.",
        )

    return PatchResult(
        applied=False,
        updated=draft,
        error=(
            "I couldn't apply that change. Try one of: "
            "'stakeholder to <name>', 'deliverable to <text>', "
            "'due date to YYYY-MM-DD', 'due time to HH:MM'."
        ),
    )
