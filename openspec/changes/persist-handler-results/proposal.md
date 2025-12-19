# Change: Persist Handler Results to Database

## Why

Command handlers build draft data (e.g., `CommitHandler` creates `draft_data` with deliverable, stakeholder, due_date) but never persist entities to the database. When users confirm a commitment, nothing is saved. This breaks the core create-confirm-save workflow and blocks all downstream features.

## What Changes

- Handlers return a `HandlerResult` with `draft_data` + `needs_confirmation`; ChatScreen drives persistence when user confirms
- A new `PersistenceService` saves confirmed entities to the database
- ChatScreen coordinates: handler result -> user confirmation -> persistence
- Created entities get displayed in the data panel with success message
- Draft is cleared after successful save

## Impact

- Affected specs: `data-persistence`, `tui-chat`
- Affected code:
  - `src/jdo/commands/handlers.py` - Add `entity_to_save` to `HandlerResult`
  - `src/jdo/db/persistence.py` (new) - Service for saving entities
  - `src/jdo/screens/chat.py` - Wire up confirmation -> persistence flow
  - `src/jdo/widgets/data_panel.py` - Show success state after save
- Dependencies: None (uses existing SQLModel patterns from `data-persistence` spec)
