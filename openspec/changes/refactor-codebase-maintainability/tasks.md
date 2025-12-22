# Tasks: Refactor Codebase Maintainability

## 1. Conversation Pruning (P1 - Memory Leak Fix)

- [x] 1.1 Add `MAX_CONVERSATION_HISTORY = 50` constant to `chat.py`
- [x] 1.2 Implement `_prune_conversation()` method in `ChatScreen`
- [x] 1.3 Call `_prune_conversation()` after user message append (line ~456)
- [x] 1.4 Call `_prune_conversation()` after AI response append (line ~985)
- [x] 1.5 Add unit test for pruning behavior
- [x] 1.6 Add integration test for long conversation handling

## 2. Handler Package Setup (P2 - God Class Split)

> **Caution:** Do **not** remove `HandlerResult`/`CommandHandler` from `handlers.py` or update consumer imports until the new package (Tasks 2.1–2.3) is fully wired and `handlers/__init__.py` exports the complete handler registry. Breaking this order strands `ChatScreen`/`commands` imports and forces a full revert.

- [x] 2.1 Create `handlers/` package directory structure
- [x] 2.2 Create `handlers/base.py` with `HandlerResult` dataclass and `CommandHandler` ABC
- [x] 2.3 Create `handlers/__init__.py` with lazy registry pattern and `get_handler()`
- [x] 2.4 Verify existing tests pass with new package structure (no handlers moved yet)
- [x] 2.5 After 2.1–2.4 pass, update consumers (e.g., `chat.py`, `commands/__init__.py`) to import from `jdo.commands.handlers.base`, then run `python -c "from jdo.commands.handlers import get_handler"` to confirm imports remain intact
- [x] 2.6 Only after 2.5 is green, delete the local `HandlerResult`/`CommandHandler` definitions from `handlers.py` (ensures no import downtime)

## 3. Migrate Handlers by Domain

- [x] 3.1 Move `MilestoneHandler` to `handlers/milestone_handlers.py` (smallest, ~150 lines)
- [x] 3.2 Move `VisionHandler` to `handlers/vision_handlers.py`
- [x] 3.3 Move `GoalHandler` to `handlers/goal_handlers.py`
- [x] 3.4 Move `TaskHandler`, `CompleteHandler` to `handlers/task_handlers.py`
- [x] 3.5 Move `IntegrityHandler` to `handlers/integrity_handlers.py` (from add-integrity-protocol)
- [x] 3.6 Move `RecurringHandler` to `handlers/recurring_handlers.py`
- [x] 3.7 Move commitment handlers to `handlers/commitment_handlers.py`:
  - `CommitHandler`
  - `AtRiskHandler` (from add-integrity-protocol)
  - `CleanupHandler` (from add-integrity-protocol)
  - `RecoverHandler` (from add-integrity-protocol)
  - `AbandonHandler` (from add-integrity-protocol)
- [x] 3.8 Move utility handlers to `handlers/utility_handlers.py`:
  - `HelpHandler`
  - `ShowHandler`
  - `ViewHandler`
  - `CancelHandler`
  - `EditHandler`
  - `TypeHandler`
  - `HoursHandler`
  - `TriageHandler`

## 4. Handler Cleanup and Verification

- [x] 4.1 Delete original `handlers.py` after all handlers migrated
- [x] 4.2 Update all test imports to use new paths
- [x] 4.3 Run `uv run ruff check --fix src/ tests/` and fix any issues
- [x] 4.4 Run `uvx pyrefly check src/` and document any false positives
- [x] 4.5 Run `uv run pytest` and verify all tests pass
- [x] 4.6 Verify no circular import issues with `python -c "from jdo.commands.handlers import get_handler"`

## 5. Navigation Consolidation (P3 - Duplicate Code Reduction) - DEFERRED

**Status**: Deferred to future work (lower priority than P1 and P2)

**Rationale**: The critical issues (memory leak and god class) have been resolved. Navigation consolidation would reduce app.py from ~290 to ~100 lines but doesn't address a critical bug or maintainability blocker. Can be completed in a separate change when prioritized.

- [ ] 5.1 Create `src/jdo/db/navigation.py` with `NavigationService` class
- [ ] 5.2 Implement `get_goals_list()` static method
- [ ] 5.3 Implement `get_commitments_list()` static method
- [ ] 5.4 Implement `get_visions_list()` static method
- [ ] 5.5 Implement `get_milestones_list()` static method
- [ ] 5.6 Implement `get_orphans_list()` static method
- [ ] 5.6a Implement `get_integrity_data()` static method (for integrity dashboard)
- [ ] 5.7 Add `_navigate_to_view()` dispatcher method to `JdoApp`
- [x] 5.8 SKIP - `on_home_screen_show_*` handlers deprecated by add-navigation-sidebar
- [ ] 5.9 Refactor `on_nav_sidebar_selected` to use dispatcher for all items (Chat, Goals, Commitments, Visions, Milestones, Hierarchy, Integrity, Orphans, Triage, Settings)
- [ ] 5.10 Remove duplicate `_nav_to_*` methods from `app.py` (if any remain after add-navigation-sidebar)
- [ ] 5.11 Add unit tests for `NavigationService` methods
- [ ] 5.12 Verify navigation behavior unchanged with integration tests

## 6. Final Verification

- [x] 6.1 Run full test suite: `uv run pytest` - All 153 command tests passing
- [x] 6.2 Run lint and format: `uv run ruff check --fix src/ tests/ && uv run ruff format src/ tests/` - Clean
- [x] 6.3 Run type check: `uvx pyrefly check src/` - 0 errors (29 suppressed)
- [ ] 6.4 Manual smoke test: start app, navigate all screens, run commands

## Completion Summary

**Completed (Tasks 1-4, 6.1-6.3)**: 
- ✅ Memory leak fix with conversation pruning (P1)
- ✅ Handler god class split into modular package (P2)
- ✅ All handlers migrated (20+ handlers across 8 domain modules)
- ✅ Comprehensive test coverage added
- ✅ All automated verification passing

**Deferred (Task 5)**:
- ⏸️ Navigation service consolidation (P3) - Lower priority, can be separate change

**Commit**: `0aa0ba1` - "Refactor: fix memory leak and split handler god class into modular package"

**Results**:
- Deleted: 2,409-line monolithic `handlers.py`
- Created: 8 domain-focused handler modules (90-800 lines each)
- Added: Conversation pruning with MAX_HISTORY=50
- Tests: 153 passing, 0 failures
- Quality: Lint clean, type check clean (0 errors)

## Dependencies

- Tasks 1.x (pruning) are independent of all other tasks
- Tasks 2.x must complete before 3.x
- Task 3.1 should complete first (smallest handler, proves pattern works)
- Tasks 3.2-3.8 can be done in parallel or sequentially
- Task 4.1 depends on all 3.x tasks completing
- Tasks 5.x (navigation) are independent of 2.x-4.x (can run in parallel)
- Task 6.x runs after all other tasks complete

## Sequencing with Other Changes

This change should be implemented AFTER:
1. `add-navigation-sidebar` - establishes NavSidebar architecture, deprecates HomeScreen handlers
2. `add-integrity-protocol` - creates integrity handlers that will be moved to new locations

The refactor moves handlers created by `add-integrity-protocol` to their final modular locations.
