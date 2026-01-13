"""Session state management for the REPL.

Tracks conversation history, current entity context, and pending drafts.
Implements token-based history pruning per research findings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

# Approximate tokens per character (conservative estimate for English text)
# OpenAI uses ~4 chars per token on average
CHARS_PER_TOKEN = 4

# Maximum tokens for conversation history (reserve space for response + tools)
MAX_HISTORY_TOKENS = 8000

# Minimum messages to keep (one user + one assistant exchange)
MIN_HISTORY_MESSAGES = 2


@dataclass
class EntityContext:
    """Tracks the current entity being viewed/edited.

    Allows natural references like "edit it" or "delete this".
    """

    entity_type: str | None = None
    entity_id: UUID | None = None

    def set(self, entity_type: str, entity_id: UUID) -> None:
        """Set the current entity context.

        Args:
            entity_type: Type of entity (e.g., "commitment", "goal").
            entity_id: UUID of the entity.
        """
        self.entity_type = entity_type
        self.entity_id = entity_id

    def clear(self) -> None:
        """Clear the current entity context."""
        self.entity_type = None
        self.entity_id = None

    @property
    def is_set(self) -> bool:
        """Check if context is set."""
        return self.entity_type is not None and self.entity_id is not None


@dataclass
class PendingDraft:
    """A draft entity awaiting confirmation.

    Stores the proposed action until user confirms, refines, or cancels.
    """

    action: str  # "create", "update", "delete"
    entity_type: str  # "commitment", "goal", etc.
    data: dict[str, Any] = field(default_factory=dict)
    entity_id: UUID | None = None  # For update/delete operations


class Session:
    """Session state for the REPL.

    Tracks conversation history with token-based pruning,
    current entity context, pending drafts, snoozed vision IDs,
    and cached counts for toolbar display.
    """

    def __init__(self) -> None:
        """Initialize empty session state."""
        self.message_history: list[dict[str, str]] = []
        self.entity_context = EntityContext()
        self.pending_draft: PendingDraft | None = None
        self.snoozed_vision_ids: set[UUID] = set()
        # Cached counts for bottom toolbar (avoid DB queries per keystroke)
        self.cached_commitment_count: int = 0
        self.cached_triage_count: int = 0

    def add_user_message(self, content: str) -> None:
        """Add a user message to history.

        Args:
            content: The message content.
        """
        self.message_history.append({"role": "user", "content": content})
        self._prune_history_if_needed()

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to history.

        Args:
            content: The message content.
        """
        self.message_history.append({"role": "assistant", "content": content})
        self._prune_history_if_needed()

    def _estimate_tokens(self) -> int:
        """Estimate total tokens in message history.

        Uses character count divided by average chars per token.

        Returns:
            Estimated token count.
        """
        total_chars = sum(len(msg["content"]) for msg in self.message_history)
        return total_chars // CHARS_PER_TOKEN

    def _prune_history_if_needed(self) -> None:
        """Prune oldest messages if history exceeds token budget.

        Removes messages from the beginning (oldest) to stay under limit.
        Always keeps at least the most recent exchange (user + assistant).
        """
        while (
            self._estimate_tokens() > MAX_HISTORY_TOKENS
            and len(self.message_history) > MIN_HISTORY_MESSAGES
        ):
            # Remove oldest message
            self.message_history.pop(0)

    def set_entity_context(self, entity_type: str, entity_id: UUID) -> None:
        """Set the current entity context.

        Args:
            entity_type: Type of entity (e.g., "commitment", "goal").
            entity_id: UUID of the entity.
        """
        self.entity_context.set(entity_type, entity_id)

    def clear_entity_context(self) -> None:
        """Clear the current entity context."""
        self.entity_context.clear()

    def set_pending_draft(
        self,
        action: str,
        entity_type: str,
        data: dict[str, Any],
        entity_id: UUID | None = None,
    ) -> None:
        """Set a pending draft awaiting confirmation.

        Args:
            action: The action type ("create", "update", "delete").
            entity_type: Type of entity being modified.
            data: The draft data.
            entity_id: Entity ID for update/delete operations.
        """
        self.pending_draft = PendingDraft(
            action=action,
            entity_type=entity_type,
            data=data,
            entity_id=entity_id,
        )

    def clear_pending_draft(self) -> None:
        """Clear any pending draft."""
        self.pending_draft = None

    @property
    def has_pending_draft(self) -> bool:
        """Check if there's a pending draft."""
        return self.pending_draft is not None

    def get_history_for_ai(self) -> list[dict[str, str]]:
        """Get message history in format suitable for AI.

        Returns:
            List of message dicts with 'role' and 'content' keys.
        """
        return self.message_history.copy()

    def update_cached_counts(
        self, commitment_count: int | None = None, triage_count: int | None = None
    ) -> None:
        """Update cached counts for toolbar display.

        Args:
            commitment_count: Active commitment count (if provided).
            triage_count: Triage queue count (if provided).
        """
        if commitment_count is not None:
            self.cached_commitment_count = commitment_count
        if triage_count is not None:
            self.cached_triage_count = triage_count
