# Tasks: Add Commitment Guardrails (Velocity-Based)

## Prerequisites
- [x] Review ROADMAP.yaml commitment_guardrails feature
- [x] Review existing commitment specs
- [x] Review CommitHandler implementation
- [x] Run existing tests to confirm baseline: `uv run pytest`

## 1. Add Commitment Velocity Query
- [x] 1.1 Add `get_commitment_velocity(session: Session, days: int = 7) -> tuple[int, int]` to `PersistenceService`
  - [x] Calculate cutoff: `cutoff = datetime.now(UTC) - timedelta(days=days)`
  - [x] Created count: `select(func.count()).select_from(Commitment).where(Commitment.created_at >= cutoff)`
  - [x] Completed count: `select(func.count()).select_from(Commitment).where(Commitment.completed_at >= cutoff, Commitment.status == CommitmentStatus.COMPLETED)`
  - [x] Return tuple: `(created_count, completed_count)`
- [x] 1.2 Add integration tests in `tests/integration/db/test_persistence_service.py`:
  - [x] Test velocity with time windows
  - [x] Test empty database returns (0, 0)
  - [x] Test velocity excludes abandoned commitments

## 2. Integrate Velocity Check into CommitHandler
- [x] 2.1 Update `CommitHandler._build_confirmation_message()` signature to accept velocity parameters
- [x] 2.2 In `execute()`, get velocity before calling `_build_confirmation_message()`
  - [x] `with get_session() as session: created, completed = PersistenceService(session).get_commitment_velocity()`
  - [x] Wrap in try/except for graceful degradation
  - [x] Pass to `_build_confirmation_message()` as parameters
- [x] 2.3 In `_build_confirmation_message()`, add velocity check:
  - [x] If `created > completed`, append: `"**Note**: You've created {created} commitments this week but only completed {completed}. Are you overcommitting?"`
- [x] 2.4 Write unit tests in `tests/unit/commands/test_handlers.py`:
  - [x] Test no warning when velocity is balanced
  - [x] Test velocity warning when creating faster than completing

## 3. Testing and Validation
- [ ] 3.1 Manual test: Create multiple commitments in a week, verify velocity warning
- [ ] 3.2 Manual test: Complete some commitments, verify warning disappears when balanced
- [ ] 3.3 Manual test: Confirm despite warning, verify commitment is created
- [x] 3.4 Run full test suite: `uv run pytest` (1,290 tests passing)
- [x] 3.5 Run lint/format: `uv run ruff check && uv run ruff format` (all passed)
- [x] 3.6 Run type check: `uvx pyrefly check src/` (0 errors)

## 4. Documentation
- [x] 4.1 Add docstrings to velocity query method (included in implementation)
- [x] 4.2 Update ROADMAP.yaml to mark feature as completed
- [x] 4.3 Update design.md to reflect removal of ceiling
- [x] 4.4 Update proposal.md to reflect velocity-only approach

## Design Change Notes
- **Removed**: `max_active_commitments` setting and threshold-based warnings
- **Reason**: Fixed ceiling doesn't account for temporal distribution (commitment due in 3 months ≠ commitment due tomorrow)
- **Kept**: Velocity-based warning (created > completed) - catches the actual problem
- **Tests removed**: 4 config tests, 2 integration tests for `count_active_commitments`, 2 handler tests for threshold warnings

## Notes
- Keep implementation simple - velocity warning only, no hard blocks
- Preserve user autonomy - they can always override
- Focus on coaching language, not punitive messages
- Graceful degradation if database queries fail
