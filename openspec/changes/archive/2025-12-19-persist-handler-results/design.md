# Design: Persist Handler Results to Database

## Context

Command handlers in `handlers.py` follow this pattern:
1. Parse command and extract fields from conversation
2. Build `draft_data` dict with entity fields
3. Return `HandlerResult` with message, panel_update, draft_data, needs_confirmation

When `needs_confirmation=True`, the user should confirm before saving. However:
- There's no code path for handling confirmation
- Draft data is never converted to a database entity
- Users see drafts but nothing persists

## Goals

- Complete the create-confirm-save workflow for all entity types
- Provide consistent persistence patterns across handlers
- Show clear success/failure feedback to users
- Support the integrity protocol's draft -> confirmed -> saved lifecycle

## Non-Goals

- Batch saves of multiple entities (handled individually)
- Undo/rollback UI for saved entities (future enhancement)
- Draft auto-save to database (drafts are ephemeral in this change)

## Decisions

### 1. PersistenceService Pattern

**Decision**: Create a `PersistenceService` class that handles entity creation.

**Rationale**:
- Centralizes database logic outside handlers (handlers stay pure)
- Encapsulates entity construction from draft_data
- Provides consistent error handling
- Easy to test with mock session

**Interface**:
```python
class PersistenceService:
    def __init__(self, session: Session):
        self.session = session
    
    def save_commitment(self, draft_data: dict) -> Commitment:
        """Create and save a commitment from draft data."""
    
    def save_goal(self, draft_data: dict) -> Goal:
        """Create and save a goal from draft data."""
    
    # ... one method per entity type
```

### 2. Confirmation Flow

**Decision**: Use a state machine in ChatScreen to track pending confirmation.

**States**:
- `IDLE` - Normal chat mode
- `AWAITING_CONFIRMATION` - Draft shown, waiting for yes/no
- `SAVING` - Persistence in progress

**Transitions**:
```
IDLE -> [command with needs_confirmation=True] -> AWAITING_CONFIRMATION
AWAITING_CONFIRMATION -> [user says "yes"] -> SAVING -> IDLE
AWAITING_CONFIRMATION -> [user says "no" or /cancel] -> IDLE
```

**Rationale**: Explicit state prevents accidental saves and supports cancellation.

### 3. Entity Type from Panel Update

**Decision**: Use existing `panel_update["entity_type"]` for persistence dispatch.

**Current handlers already set this**:
```python
return HandlerResult(
    message=message,
    panel_update={
        "mode": "draft",
        "entity_type": "commitment",  # Already present!
        "data": draft_data,
    },
    draft_data=draft_data,
    needs_confirmation=needs_confirmation,
)
```

**No schema change needed**. When `needs_confirmation=True`, extract entity type from `panel_update["entity_type"]` to determine which `PersistenceService.save_*()` method to call.

**Rationale**: Avoids adding a redundant field to `HandlerResult` when the information already exists in `panel_update`.

### 4. Stakeholder Resolution

**Decision**: Create stakeholders on-the-fly if they don't exist.

**Flow**:
1. User says "commit to Sarah"
2. `draft_data["stakeholder"] = "Sarah"`
3. On save: `get_or_create_stakeholder("Sarah")` returns existing or new Stakeholder
4. Commitment is linked to stakeholder_id

**Rationale**: Users shouldn't have to pre-create stakeholders. This matches natural language usage.

### 5. Success Feedback

**Decision**: After successful save, update data panel to "view" mode showing the saved entity.

**Pattern**:
```python
# After save
result = HandlerResult(
    message="Commitment saved! I'll remind you when it's due.",
    panel_update={
        "mode": "view",
        "entity_type": "commitment",
        "data": commitment.model_dump(),
    },
    draft_data=None,  # Clear draft
    needs_confirmation=False,
)
```

**Rationale**: Immediate visual confirmation that save succeeded.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Duplicate stakeholders from typos | Future: fuzzy matching or autocomplete |
| Save fails mid-transaction | Session rollback; show error message |
| User confusion about confirmation | Clear prompt: "Does this look right? (yes to confirm)" |

## Migration Plan

1. Create `PersistenceService` in `src/jdo/db/persistence.py`
2. Add confirmation state tracking to `ChatScreen`
3. Wire up "yes" detection to trigger save (using `panel_update["entity_type"]`)
4. Add success/error handling for save results

No database schema changes required. No `HandlerResult` changes needed.

## Implementation Order

This change should be implemented **before** `wire-ai-to-chat` because:
1. Both modify `ChatScreen` message handling
2. Confirmation state is simpler than AI streaming
3. The message flow should be: `User message → Check confirmation state → If not awaiting: continue to AI`

The `wire-ai-to-chat` change will need to check confirmation state before invoking AI.

## Open Questions

- Should we save drafts to database periodically? (Deferred - current drafts are ephemeral)
- Should we support inline editing during confirmation? (Deferred - user can /cancel and retry)
