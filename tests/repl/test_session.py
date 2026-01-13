"""Tests for the REPL session state module."""

from uuid import uuid4

import pytest

from jdo.repl.session import (
    CHARS_PER_TOKEN,
    MAX_HISTORY_TOKENS,
    MIN_HISTORY_MESSAGES,
    EntityContext,
    PendingDraft,
    Session,
)


class TestEntityContext:
    """Tests for EntityContext dataclass."""

    def test_initial_state(self):
        """Context starts empty."""
        ctx = EntityContext()

        assert ctx.entity_type is None
        assert ctx.entity_id is None
        assert ctx.is_set is False

    def test_set_context(self):
        """Can set entity context."""
        ctx = EntityContext()
        entity_id = uuid4()

        ctx.set("commitment", entity_id)

        assert ctx.entity_type == "commitment"
        assert ctx.entity_id == entity_id
        assert ctx.is_set is True

    def test_clear_context(self):
        """Can clear entity context."""
        ctx = EntityContext()
        ctx.set("commitment", uuid4())

        ctx.clear()

        assert ctx.entity_type is None
        assert ctx.entity_id is None
        assert ctx.is_set is False


class TestPendingDraft:
    """Tests for PendingDraft dataclass."""

    def test_create_draft(self):
        """Can create a pending draft."""
        draft = PendingDraft(
            action="create",
            entity_type="commitment",
            data={"deliverable": "Test"},
        )

        assert draft.action == "create"
        assert draft.entity_type == "commitment"
        assert draft.data == {"deliverable": "Test"}
        assert draft.entity_id is None

    def test_update_draft_with_entity_id(self):
        """Update drafts include entity_id."""
        entity_id = uuid4()
        draft = PendingDraft(
            action="update",
            entity_type="commitment",
            data={"deliverable": "Updated"},
            entity_id=entity_id,
        )

        assert draft.action == "update"
        assert draft.entity_id == entity_id


class TestSession:
    """Tests for Session class."""

    def test_initial_state(self):
        """Session starts with empty state."""
        session = Session()

        assert session.message_history == []
        assert session.entity_context.is_set is False
        assert session.pending_draft is None
        assert session.has_pending_draft is False

    def test_add_user_message(self):
        """Can add user message."""
        session = Session()

        session.add_user_message("Hello")

        assert len(session.message_history) == 1
        assert session.message_history[0] == {"role": "user", "content": "Hello"}

    def test_add_assistant_message(self):
        """Can add assistant message."""
        session = Session()

        session.add_assistant_message("Hi there!")

        assert len(session.message_history) == 1
        assert session.message_history[0] == {"role": "assistant", "content": "Hi there!"}

    def test_message_history_ordering(self):
        """Messages maintain order."""
        session = Session()

        session.add_user_message("First")
        session.add_assistant_message("Second")
        session.add_user_message("Third")

        assert len(session.message_history) == 3
        assert session.message_history[0]["content"] == "First"
        assert session.message_history[1]["content"] == "Second"
        assert session.message_history[2]["content"] == "Third"

    def test_set_entity_context(self):
        """Can set entity context."""
        session = Session()
        entity_id = uuid4()

        session.set_entity_context("goal", entity_id)

        assert session.entity_context.entity_type == "goal"
        assert session.entity_context.entity_id == entity_id

    def test_clear_entity_context(self):
        """Can clear entity context."""
        session = Session()
        session.set_entity_context("goal", uuid4())

        session.clear_entity_context()

        assert session.entity_context.is_set is False

    def test_set_pending_draft(self):
        """Can set pending draft."""
        session = Session()

        session.set_pending_draft(
            action="create",
            entity_type="commitment",
            data={"deliverable": "Test"},
        )

        assert session.has_pending_draft is True
        assert session.pending_draft.action == "create"
        assert session.pending_draft.entity_type == "commitment"

    def test_clear_pending_draft(self):
        """Can clear pending draft."""
        session = Session()
        session.set_pending_draft("create", "commitment", {})

        session.clear_pending_draft()

        assert session.has_pending_draft is False
        assert session.pending_draft is None

    def test_get_history_for_ai(self):
        """Returns copy of message history."""
        session = Session()
        session.add_user_message("Test")
        session.add_assistant_message("Response")

        history = session.get_history_for_ai()

        assert len(history) == 2
        # Verify it's a copy
        history.append({"role": "user", "content": "New"})
        assert len(session.message_history) == 2


class TestTokenPruning:
    """Tests for token-based history pruning."""

    def test_estimate_tokens(self):
        """Token estimation works correctly."""
        session = Session()
        # 100 characters ≈ 25 tokens
        session.add_user_message("a" * 100)

        estimated = session._estimate_tokens()

        assert estimated == 100 // CHARS_PER_TOKEN

    def test_no_pruning_under_limit(self):
        """No pruning when under token limit."""
        session = Session()
        # Add a few short messages
        for i in range(5):
            session.add_user_message(f"Message {i}")
            session.add_assistant_message(f"Response {i}")

        assert len(session.message_history) == 10

    def test_pruning_when_over_limit(self):
        """Prunes oldest messages when over token limit."""
        session = Session()

        # Calculate message size to exceed limit
        # Each pair should be about 200 chars = 50 tokens
        # MAX_HISTORY_TOKENS = 8000, so ~160 pairs before pruning
        # Let's add enough to trigger pruning
        large_message = "x" * (CHARS_PER_TOKEN * 500)  # 500 tokens per message

        # Add many large messages to exceed limit
        for _ in range(20):
            session.add_user_message(large_message)
            session.add_assistant_message(large_message)

        # Should have pruned to stay under limit
        estimated_tokens = session._estimate_tokens()
        assert estimated_tokens <= MAX_HISTORY_TOKENS

    def test_keeps_minimum_messages(self):
        """Always keeps at least MIN_HISTORY_MESSAGES messages."""
        session = Session()

        # Add two very large messages
        huge_message = "y" * (CHARS_PER_TOKEN * MAX_HISTORY_TOKENS)
        session.add_user_message(huge_message)
        session.add_assistant_message(huge_message)

        # Should keep minimum despite being over limit
        assert len(session.message_history) >= MIN_HISTORY_MESSAGES

    def test_oldest_messages_removed_first(self):
        """Oldest messages are removed during pruning."""
        session = Session()

        # Add identifiable messages
        session.add_user_message("FIRST")
        session.add_assistant_message("FIRST_RESPONSE")

        # Add many large messages to trigger pruning
        large_message = "z" * (CHARS_PER_TOKEN * 1000)
        for i in range(10):
            session.add_user_message(large_message)
            session.add_assistant_message(f"Response {i}")

        # First messages should be gone
        assert not any(m["content"] == "FIRST" for m in session.message_history)
