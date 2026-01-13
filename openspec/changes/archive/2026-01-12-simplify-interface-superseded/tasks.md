## Phase 1: Scaffold New Interface (Parallel)

### 1.1 Add Typer CLI entry point
- [ ] Create `src/jdo/interface/__init__.py`
- [ ] Create `src/jdo/interface/commands.py` with Typer app and basic commands (`chat`, `list`, `add`)
- [ ] Create `src/jdo/cli.py` with new main() that routes to Typer or legacy TUI (--legacy flag)
- [ ] Update `pyproject.toml` [project.scripts] to point to new cli:main
- [ ] Add `typer[all]>=0.9.0` to dependencies
- [ ] Test: `jdo --help` shows Typer help, `jdo --legacy` launches old TUI

### 1.2 Add output formatters
- [ ] Create `src/jdo/output/__init__.py`
- [ ] Create `src/jdo/output/formatters.py` with `CommandOutput` dataclass and base formatter
- [ ] Create `src/jdo/output/list_formatter.py` with `format_commitment_list()`, `format_goal_list()`
- [ ] Create `src/jdo/output/entity_formatter.py` with `format_commitment()`, `format_goal()`
- [ ] Create `src/jdo/output/table_formatter.py` using Rich Table
- [ ] Test: Unit tests for each formatter with sample data
  - Verify: Empty lists return "[i]No data available[/i]" message
  - Verify: None data returns appropriate message
  - Verify: Missing fields in dicts show "N/A" without raising exceptions
  - Verify: Large datasets (100+ rows) render without errors

### 1.3 Add interactive chat REPL
- [ ] Create `src/jdo/interface/chat.py` with `chat_repl()` function
- [ ] Implement: Input loop with Rich Prompt
- [ ] Implement: Conversation history management (list of dicts, max 50 messages)
- [ ] Implement: AI streaming with Rich status indicator and 30s timeout
- [ ] Implement: Error handling for AI streaming failures (network, timeout, rate limit)
- [ ] Implement: Exit on "quit", "exit", or Ctrl+C
- [ ] Wire to `jdo chat` command in commands.py
- [ ] Test: Manual smoke test (launch chat, send message, receive response, quit)
  - Verify: AI streaming error shows friendly message and allows retry
  - Verify: Conversation history trimmed after 50 messages
  - Verify: Timeout after 30s shows error and allows new message
  - Verify: Ctrl+C exits gracefully without traceback

### 1.4 Wire basic list commands
- [ ] Add `jdo list commitments` command calling existing handlers
- [ ] Add `jdo list goals` command
- [ ] Format handler output with new formatters
- [ ] Test: Run commands, verify output matches expected format

## Phase 2: Simplify Handler Return Types

### 2.1 Create adapter layer
- [ ] Add `src/jdo/commands/adapters.py` with `handlerresult_to_commandoutput()`
- [ ] Add `commandoutput_to_handlerresult()` for backward compat
- [ ] Test: Adapter round-trips preserve all data

### 2.2 Migrate commitment handlers
- [ ] Update `CommitHandler` to return `CommandOutput`
- [ ] Update `AtRiskHandler` to return `CommandOutput`
- [ ] Update `CleanupHandler` to return `CommandOutput`
- [ ] Add adapter call in MainScreen to convert back to HandlerResult
- [ ] Test: Old TUI still works with migrated handlers

### 2.3 Migrate goal/task/vision handlers
- [ ] Update `GoalHandler` to return `CommandOutput`
- [ ] Update `TaskHandler` to return `CommandOutput`
- [ ] Update `VisionHandler` to return `CommandOutput`
- [ ] Update `MilestoneHandler` to return `CommandOutput`
- [ ] Test: Old TUI works, new CLI `jdo list` commands work

### 2.4 Migrate utility handlers
- [ ] Update `HelpHandler`, `ShowHandler`, `ViewHandler` to return `CommandOutput`
- [ ] Update `CancelHandler`, `EditHandler`, `TypeHandler` to return `CommandOutput`
- [ ] Update `HoursHandler`, `TriageHandler` to return `CommandOutput`
- [ ] Test: All commands work in both interfaces

## Phase 3: Complete Migration

### 3.1 Remove HandlerResult and adapters
- [ ] Delete `src/jdo/commands/adapters.py`
- [ ] Update `src/jdo/commands/handlers/base.py` to use `CommandOutput`
- [ ] Update all handler type hints and imports
- [ ] Test: New CLI tests pass

### 3.2 Update CLI to consume CommandOutput directly
- [ ] Remove adapter calls from `src/jdo/interface/commands.py`
- [ ] Wire formatters directly to handler outputs
- [ ] Test: All `jdo list`, `jdo add` commands work

### 3.3 Mark old TUI as deprecated
- [ ] Add deprecation warning to `jdo --legacy`
- [ ] Update README to note legacy TUI is deprecated
- [ ] Test: Warning displays, TUI still launches (but expect failures)

## Phase 4: Remove Old TUI

### 4.1 Delete TUI code
- [ ] Delete `src/jdo/screens/` directory (7 files, ~1,500 LOC)
- [ ] Delete `src/jdo/widgets/` directory (8 files, ~2,200 LOC)
- [ ] Delete `src/jdo/app.py` (458 LOC)
- [ ] Delete `src/jdo/theme.py` (TUI-specific themes)
- [ ] Test: New CLI still works

### 4.2 Update dependencies
- [ ] Remove `textual>=6.11.0` from dependencies
- [ ] Remove `pytest-textual-snapshot>=1.0.0` from dev dependencies
- [ ] Run `uv lock` to update lockfile
- [ ] Test: `uv run jdo` works without textual

### 4.3 Remove TUI tests
- [ ] Delete `tests/tui/` directory if exists
- [ ] Remove TUI test fixtures from `tests/conftest.py`
- [ ] Remove textual-specific test markers
- [ ] Test: `uv run pytest` passes (621 backend tests remain)

### 4.4 Clean up CLI entry point
- [ ] Remove `--legacy` flag from `src/jdo/cli.py`
- [ ] Simplify main() to only launch Typer app
- [ ] Update `jdo` (no args) to default to chat mode
- [ ] Test: `jdo` launches chat, `jdo --help` shows commands

### 4.5 Update documentation
- [ ] Update README.md with new CLI usage examples
- [ ] Remove TUI keyboard shortcuts section
- [ ] Add CLI command reference
- [ ] Update "How It Works" section for CLI
- [ ] Update installation instructions (no Textual)
- [ ] Test: README examples work as documented

## Phase 5: Polish & Complete Features

### 5.1 Add remaining commands
- [ ] Implement `jdo add commitment <text>` fire-and-forget
- [ ] Implement `jdo add goal <text>`
- [ ] Implement `jdo show <entity-type> <id>`
- [ ] Implement `jdo complete <task-id>`
- [ ] Test: All commands work as expected

### 5.2 Improve chat mode UX
- [ ] Add conversation context display (last 3 exchanges)
- [ ] Add command history (up/down arrow)
- [ ] Add `jdo history` command to view full conversation log
- [ ] Improve AI streaming output (use Rich Live or similar)
- [ ] Test: Chat feels responsive and informative

### 5.3 Add output format options
- [ ] Add `--format json` flag for scripting
- [ ] Add `--format table` vs `--format list` options
- [ ] Wire to formatters
- [ ] Test: Each format produces valid output

### 5.4 Error handling and polish
- [ ] Add helpful error messages for common mistakes
- [ ] Add `jdo doctor` command to check config/credentials
- [ ] Improve validation messages
- [ ] Add input validation for entity IDs (must be positive integers)
- [ ] Add input validation for dates (YYYY-MM-DD format)
- [ ] Check .env file permissions and warn if world-readable
- [ ] Implement API key sanitization in all log outputs
- [ ] Test: Errors are clear and actionable
  - Verify: Invalid entity ID shows helpful error
  - Verify: Invalid date format shows helpful error
  - Verify: API keys never appear in logs

## Phase 6: Integration & Acceptance Testing

### 6.1 End-to-end integration tests
- [ ] Test: Full workflow - start chat → create commitment → list commitments → quit
  - Verify: Commitment appears in list after creation
  - Verify: All steps complete without errors
- [ ] Test: Non-interactive mode - `jdo add commitment "text" --yes`
  - Verify: Command completes without prompts
  - Verify: Exit code is 0 on success
- [ ] Test: Error recovery - AI unavailable during chat
  - Verify: Friendly error shown
  - Verify: User can retry after recovery
- [ ] Test: Database migration on fresh install
  - Verify: Tables created automatically
  - Verify: First command succeeds

### 6.2 Accessibility testing
- [ ] Test: Rich output with NO_COLOR=1 environment variable
  - Verify: Output is readable without color
- [ ] Test: Output in 80-column terminal
  - Verify: Tables wrap appropriately
- [ ] Test: Output piped to file (non-TTY)
  - Verify: No ANSI codes in piped output or `--no-color` flag works

### 6.3 Performance validation
- [ ] Benchmark: `jdo list commitments` with 100 records
  - Verify: Completes in <500ms
- [ ] Benchmark: `jdo list commitments` with 1000 records
  - Verify: Completes in <2s
- [ ] Benchmark: Chat message round-trip with AI
  - Verify: Typical response in <3s (excluding AI processing time)

## Validation

### After Phase 1
- [ ] `jdo chat` launches and can send messages
- [ ] `jdo list commitments` shows commitments
- [ ] Old TUI still works via `jdo --legacy`
- [ ] All 621 backend tests pass

### After Phase 2
- [ ] All handlers return `CommandOutput`
- [ ] Old TUI still works with adapter
- [ ] New CLI commands work
- [ ] All tests pass

### After Phase 3
- [ ] `HandlerResult` removed
- [ ] Old TUI broken (expected)
- [ ] New CLI fully functional
- [ ] 621 backend tests pass

### After Phase 4
- [ ] TUI code deleted (~3,700 LOC removed)
- [ ] `textual` dependency removed
- [ ] Only CLI works
- [ ] 621 backend tests + new CLI tests pass
- [ ] Documentation updated

### After Phase 5
- [ ] All core commands implemented
- [ ] Chat mode polished
- [ ] Output formats work
- [ ] User-facing errors helpful

### After Phase 6
- [ ] Integration tests pass
- [ ] Accessibility verified
- [ ] Performance meets requirements
- [ ] Ready for production use

## Dependencies
- Phase 1 is independent (can start immediately)
- Phase 2 depends on Phase 1 (need CommandOutput defined)
- Phase 3 depends on Phase 2 (all handlers migrated)
- Phase 4 depends on Phase 3 (HandlerResult removed)
- Phase 5 depends on Phase 4 (TUI removed, clean slate)

## Parallelizable Work
- 1.1 and 1.2 can be done in parallel (entry point + formatters)
- 2.2 and 2.3 can be done in parallel (different handler groups)
- 5.1 and 5.2 can be done in parallel (commands + chat UX)

## Estimated Effort
- Phase 1: ~800 LOC new code, 4-6 hours
- Phase 2: ~200 LOC adapters + migrations, 3-4 hours
- Phase 3: ~100 LOC changes, 1-2 hours
- Phase 4: Delete ~3,700 LOC, update deps/docs, 2-3 hours
- Phase 5: ~400 LOC polish, 4-5 hours

**Total**: ~1,500 LOC added, ~3,700 LOC removed, ~15-20 hours
