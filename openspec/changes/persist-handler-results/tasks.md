# Tasks: Persist Handler Results to Database

## Prerequisites
- [x] 0.1 Run existing tests to confirm baseline: `uv run pytest`
- [x] 0.2 Review existing handler tests in `tests/unit/commands/test_handlers.py`
- [x] 0.3 Review `wire-ai-to-chat` implementation - ChatScreen now has AI streaming but deferred command routing

## 1. Create PersistenceService
- [x] 1.1 Create `src/jdo/db/persistence.py` with `PersistenceService` class
- [x] 1.2 Implement `get_or_create_stakeholder(name: str) -> Stakeholder` with case-insensitive matching
- [x] 1.3 Implement `save_commitment(draft_data: dict) -> Commitment`
- [x] 1.4 Implement `save_goal(draft_data: dict) -> Goal`
- [x] 1.5 Implement `save_task(draft_data: dict) -> Task`
- [x] 1.6 Implement `save_milestone(draft_data: dict) -> Milestone`
- [x] 1.7 Implement `save_vision(draft_data: dict) -> Vision`
- [x] 1.8 Implement `save_recurring_commitment(draft_data: dict) -> RecurringCommitment`
- [x] 1.9 Add error handling for missing required fields (raise ValidationError)
- [x] 1.10 Write unit tests for each save method with mock session

## 2. Route Commands from ChatScreen
- [x] 2.1 Implement `_handle_command(text: str)` method in ChatScreen
- [x] 2.2 Parse command using existing `CommandParser` from `jdo.commands.parser`
- [x] 2.3 Route to appropriate handler from `jdo.commands.handlers`
- [x] 2.4 Display handler result in chat (response_text) and data panel (panel_update)
- [x] 2.5 Write tests for command routing (e.g., `/help`, `/commit`, `/show`)

## 3. Add Confirmation State to ChatScreen
- [x] 3.1 Add `ConfirmationState` enum (IDLE, AWAITING, SAVING)
- [x] 3.2 Add `_confirmation_state: ConfirmationState` to ChatScreen
- [x] 3.3 Add `_pending_draft: dict | None` to store draft awaiting confirmation
- [x] 3.4 Add `_pending_entity_type: str | None` to track what to save (from panel_update)
- [x] 3.5 Modify command handling to set state when `needs_confirmation=True`
- [x] 3.6 Write tests for state transitions

## 4. Implement Confirmation Detection
- [x] 4.1 Add `_is_confirmation(text: str) -> bool` to detect "yes", "y", "confirm", etc.
- [x] 4.2 Add `_is_cancellation(text: str) -> bool` to detect "no", "n", "cancel", etc.
- [x] 4.3 Modify message handling to check confirmation state BEFORE any other processing
- [x] 4.4 If AWAITING and confirmation: trigger save
- [x] 4.5 If AWAITING and cancellation: clear draft and show message
- [x] 4.6 If AWAITING and other message: treat as modification request (keep state)
- [x] 4.7 Write tests for confirmation/cancellation detection

## 5. Wire Up Persistence
- [x] 5.1 Create `_save_pending_entity()` method in ChatScreen
- [x] 5.2 Use `get_session()` context manager for database access
- [x] 5.3 Call appropriate `PersistenceService.save_*()` method based on `_pending_entity_type`
- [x] 5.4 Update data panel to view mode with saved entity
- [x] 5.5 Show success message in chat
- [x] 5.6 Handle save errors with user-friendly message
- [x] 5.7 Write integration test with real database

## 6. Testing and Validation
- [x] 6.1 Manual test: Create commitment through full flow (draft -> confirm -> saved) - covered by integration tests
- [x] 6.2 Manual test: Confirm commitment, then verify in database - covered by integration tests
- [x] 6.3 Manual test: Cancel draft, verify nothing saved - covered by unit tests
- [x] 6.4 Manual test: Create commitment with new stakeholder (auto-created) - covered by integration tests
- [x] 6.5 Manual test: Create goal through full flow - covered by integration tests
- [x] 6.6 Run targeted tests: `uv run pytest tests/unit/db/test_persistence.py tests/tui/test_chat_screen.py tests/integration/db/test_persistence_service.py`
- [x] 6.7 Run targeted lint/format: `uv run ruff check src/jdo/db/persistence.py src/jdo/screens/chat.py src/jdo/widgets/data_panel.py tests/unit/db/test_persistence.py tests/tui/test_chat_screen.py tests/integration/db/test_persistence_service.py`
- [x] 6.8 Run targeted type checking: `uvx pyrefly check src/jdo/db/persistence.py`

## 7. Documentation
- [x] 7.1 Add docstrings to PersistenceService methods
- [x] 7.2 Update any inline comments explaining the confirmation flow
