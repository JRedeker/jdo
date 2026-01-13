# Tasks: Improve REPL UI/UX

## Research Validation Complete

Research conducted 2026-01-13. Key changes from original proposal:
- Use existing `get_handler()` instead of new CommandDispatcher class
- Change Ctrl+R to F5 (avoid readline conflict)
- Raise fuzzy threshold from 60% to 75%
- Use explicit `/1`, `/2` shortcuts instead of implicit number selection
- Defer dynamic ID completion (keep simple WordCompleter)
- Add onboarding splash screen for first-run and version updates
- Fuzzy suggestions include command descriptions
- Handler state audit: remove `_current_draft` from 3 handlers

## 1. Command Dispatch Foundation

- [x] 1.1 Wire existing `get_handler()` to REPL loop
  - Replace inline if/else in `handle_slash_command()` with `get_handler(cmd.command_type)`
  - Keep existing handlers module structure
  - No new `CommandDispatcher` class needed (research finding)
  - Verify: existing `/help`, `/list`, `/commit`, `/complete` still work
- [x] 1.2 Make all handlers async - **DEFERRED** (not needed, /commit handled specially)
  - Most handlers are sync DB operations, async not needed for uniformity
  - `/commit` uses inline async `_handle_commit()` for AI extraction
- [x] 1.3 Remove handler instance state (audit finding)
  - Remove `CommitHandler._current_draft` from `commitment_handlers.py`
  - Remove `GoalHandler._current_draft` from `goal_handlers.py`
  - Remove `TaskHandler._current_draft` from `task_handlers.py`
  - All draft data already flows through `HandlerResult.draft_data`
  - Verify: handlers are stateless (no `self._*` mutable attributes)
  - Verify: `rg "self\._" src/jdo/commands/handlers/*.py` shows only ClassVar constants
- [x] 1.4 Create handler classes for inline REPL commands
  - `HelpHandler` for `/help` - already exists, wired via registry
  - `ListHandler` for `/list` - created in utility_handlers.py
  - `CommitHandler` - handled specially with inline async
  - `CompleteHandler` for `/complete` - handled specially with inline logic
  - `ReviewHandler` for `/review` - created in utility_handlers.py
  - Verify: each handler returns `HandlerResult` with expected fields
- [x] 1.5 Add fuzzy suggestion with 75% threshold and descriptions
  - Use rapidfuzz with 75% threshold (was 60%, raised per research)
  - Match existing pattern in `confirmation.py:66`
  - Include command descriptions in suggestions: "Did you mean: /commit (create a commitment)?"
  - Verify: `uv run pytest tests/repl/test_loop.py::TestFuzzySuggestions -v` passes
- [x] 1.6 Add tests for dispatch and migrated handlers
  - Test each command path works via `get_handler()`
  - Test unknown command with fuzzy suggestion
  - Verify existing tests still pass (1627 tests pass)

## 2. Wire Missing Command Handlers

All handlers were already registered in the handler registry. The REPL loop now routes
commands through `get_handler()` which returns the appropriate handler instance.

- [x] 2.1 Wire goal commands (`/goal`) - already in registry
- [x] 2.2 Wire task commands (`/task`) - already in registry
- [x] 2.3 Wire vision commands (`/vision`) - already in registry
- [x] 2.4 Wire milestone commands (`/milestone`) - already in registry
- [x] 2.5 Wire integrity commands (`/integrity`) - already in registry
- [x] 2.6 Wire commitment status commands - already in registry
  - `/atrisk` -> AtRiskHandler
  - `/abandon` -> AbandonHandler
  - `/recover` -> RecoverHandler
- [x] 2.7 Wire utility commands - already in registry
  - `/hours` -> HoursHandler
  - `/triage` -> TriageHandler
- [x] 2.8 Wire recurring commands (`/recurring`) - already in registry

## 3. Entity Navigation

- [x] 3.1 Add `EntityContext` dataclass to `Session`
  - Track current entity type, ID, short_id, display_name (already in session.py)
  - Add `last_list_items` for shortcut selection (already in session.py)
- [x] 3.2 Implement `/view <id>` command
  - Updated `ViewHandler` in `utility_handlers.py` to look up entities
  - Accept full UUID or short ID prefix
  - Display detailed entity panel using Rich Panels
  - Update session's current entity context
- [x] 3.3 Implement explicit `/1`, `/2` number shortcuts
  - Added aliases in parser.py: `"1": ("view", ["1"])`, etc. through `"5"`
  - Added abbreviations: `/c` -> `/commit`, `/l` -> `/list`, `/v` -> `/view`, `/h` -> `/help`
  - ViewHandler looks up entity from `last_list_items`
  - Error if no list context: "No list to select from. Use /list first."
  - Error if out of range: "No item 7. Use /1 through /3."
- [x] 3.4 Update list formatters for explicit shortcuts
  - ListHandler populates `session.last_list_items` (max 5 items)
  - Display shortcuts `/[1]`, `/[2]`, etc. in first column
  - Added footer hint: "Use /1, /2, etc. to view details"
  - Added `MAX_LIST_SHORTCUTS = 5` constant
- [x] 3.5 Update toolbar to show current entity context
  - Format: `3 active | 1 triage | [commitment:abc123 'deliverable...']`
  - Shows entity type, short ID, and truncated display name
  - Clear context on `/list` (via HandlerResult.clear_context)
- [x] 3.6 Add tests for navigation
  - Test `/view` requires db_session
  - Test `/view 1` without list context shows error
  - Test `/view 7` out of range shows error
  - Test parser aliases work correctly

## 4. Discoverability

- [x] 4.1 Enhance `/help` command
  - Group commands by category (commitments, goals, navigation, etc.)
  - Show brief description for each command
  - Include examples for common workflows
  - Add shortcuts section with abbreviations AND keyboard shortcuts
- [x] 4.2 Implement `/help <command>` detailed help
  - HelpHandler._COMMAND_HELP already provides detailed help
  - Shows full usage, options, and examples
  - Includes related commands
- [x] 4.3 Add context-aware help hints
  - After creating entity: suggest `/view`, `/complete`
  - After listing: mention `/1`, `/2` shortcuts (DONE - in footer)
  - On error: suggest recovery steps (DONE - HandlerResult.suggestions)
- [x] 4.4 Add command abbreviations
  - Added `/c` -> `/commit`, `/l` -> `/list`, `/v` -> `/view`, `/h` -> `/help`
  - Added `/1` through `/5` -> `/view 1` through `/view 5`
  - Alias map in parser.py: `_COMMAND_ALIASES`

## 5. Keyboard Shortcuts (Revised)

<!-- Research: Ctrl+R conflicts with reverse-i-search. Use F5 instead. -->

- [x] 5.1 Add keyboard shortcuts via prompt_toolkit KeyBindings
  - Ctrl+L: Clear screen, redisplay dashboard
  - F5: Refresh dashboard data (changed from Ctrl+R per research)
  - F1: Show help
- [x] 5.2 Pass KeyBindings to PromptSession
  - Created `_create_key_bindings()` factory in loop.py
  - Wire callbacks to dashboard refresh, help display
- [x] 5.3 Add tests for keyboard shortcuts
  - Test Ctrl+L clears screen
  - Test F5 refreshes dashboard
  - Test F1 shows help
  - Verify: `uv run pytest tests/repl/test_loop.py::TestKeyBindings -v` passes

## 6. Feedback & Error Handling

- [x] 6.1 Improve progress indicators
  - Action-specific status: "Extracting commitment..." already in _handle_commit
  - Replace generic "Thinking..." - kept for AI streaming (appropriate)
- [x] 6.2 Improve error messages
  - Entity not found: suggest `/list` - done in ViewHandler
  - Invalid input: explain what's wrong - done in handlers
  - Invalid shortcut: "No item 7. Use /1 through /5" - done in ViewHandler
  - Network errors: guidance in AI timeout handler
- [x] 6.3 Add success confirmations
  - Confirm what changed: "Marked commitment abc123 as complete" - done
  - HandlerResult.suggestions for follow-up actions
- [x] 6.4 Add tests for error handling
  - Tests in test_utility_handlers.py cover error cases
  - Tests in test_loop.py cover confirmation flow

## 7. Documentation & Polish

- [x] 7.1 Update `/help` output with all new commands
  - HelpHandler now groups by category with descriptions
- [x] 7.2 Update AGENTS.md with new command reference
  - Added keyboard shortcuts section
  - Updated Key Commands table with aliases
  - Updated Adding Slash Commands section
- [x] 7.3 Run full test suite and fix any regressions
  - All 1643 tests pass
- [x] 7.4 Manual testing of all command paths
  - UAT scenarios 8.1-8.6 all pass

## Dependencies

- Tasks 2.x depend on 1.x (dispatch foundation)
- Tasks 3.x depend on 1.x (need dispatch for /view)
- Tasks 4.x can partially parallel with 2.x and 3.x
- Tasks 5.x can parallel with other tasks
- Tasks 6.x can parallel with most tasks
- Task 7.x is final validation

## Parallelizable Work

- 2.1-2.8 can run in parallel (each handler is independent)
- 4.4 (abbreviations) can parallel with 2.x
- 5.1-5.2 (keyboard shortcuts) can parallel with most tasks
- 6.1-6.3 can parallel with most tasks

## 0. Pre-Implementation Setup

- [x] 0.1 Add onboarding splash screen
  - Created `src/jdo/output/onboarding.py`
  - First-run screen: app purpose, key commands
  - "What's New" screen for version updates
  - Track last seen version in config
  - Support `--quiet` flag to skip
  - Handle config write failure gracefully (log warning, continue)
- [x] 0.2 Update HandlerResult dataclass
  - Add `error: bool = False` field
  - Add `suggestions: list[str] | None = None` field
  - Add `entity_context: EntityContext | None = None` field
  - Add `clear_context: bool = False` field
  - Verified: existing handler tests still pass

## 8. User Acceptance Testing (UAT)

- [x] 8.1 UAT: First-run onboarding
  - Onboarding screen shows JDO title, purpose, key commands
  - What's New screen shows version info
  - Functions exist and work correctly
- [x] 8.2 UAT: Command dispatch
  - 22 command types have handlers (MESSAGE is special case)
  - All commands parse correctly
  - Typos get fuzzy suggestions with descriptions (75% threshold)
  - Unknown commands raise ParseError with helpful message
- [x] 8.3 UAT: Entity navigation
  - `/1` through `/5` shortcuts map to `/view 1-5`
  - Command abbreviations: `/c`, `/l`, `/v`, `/h`
  - MAX_LIST_SHORTCUTS = 5
  - ListHandler and ViewHandler exist and work
- [x] 8.4 UAT: Keyboard shortcuts
  - 3 key bindings configured: F1, F5, Ctrl+L
  - F1 shows help
  - F5 refreshes dashboard
  - Ctrl+L clears and shows dashboard
- [x] 8.5 UAT: Error recovery
  - `/help` always works (not an error)
  - "No list to select from" with `/list` suggestion
  - "No item N. Use /1 through /M" for out of range
  - ParseError for unknown commands
- [x] 8.6 UAT: Toolbar and context
  - Toolbar shows "N active | M triage"
  - With entity context: includes "[type:shortid 'display...']"
  - EntityContext.is_set, short_id, entity_type work
  - clear_entity_context() removes context from toolbar

## Deferred (Per Research)

- **Dynamic ID completion**: Requires custom Completer. Existing partial-ID matching in handlers is sufficient. Defer unless user feedback indicates need.
