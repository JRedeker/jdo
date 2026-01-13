# Change: Simplify Interface to Minimal TUI or Typer CLI

## Why

The current multi-widget Textual TUI (3,700+ LOC across screens/widgets) is proving difficult to maintain and extend with AI assistance due to:

1. **Complex state management**: Conversation state, confirmation flow, draft state, and panel updates are distributed across MainScreen (914 lines), multiple widgets, and 8 handler modules
2. **Tight coupling**: Changes require coordinating MainScreen + ChatContainer + DataPanel + PromptInput + NavSidebar + handlers
3. **Async coordination complexity**: Textual's reactive model, message passing, and worker contexts create error-prone interactions
4. **Testing friction**: TUI tests require Textual Pilot, which is verbose and fragile
5. **AI assistance gaps**: Large context windows needed to understand full flow; cascading changes across 4-5 files per feature

Most TUI features are incomplete or broken. Core backend (models, AI, handlers, database) is solid and well-tested (621 passing tests).

## What Changes

Replace the complex multi-widget Textual TUI with **one of two simpler interfaces** (decision in design.md):

### Option A: Minimal Single-Screen TUI
- Single scrolling chat area (like `htop` or `lazygit`)
- Simple text-based output for lists and data
- One PromptInput at bottom
- No sidebars, no data panels, no complex widgets
- Keep keyboard-first UX

### Option B: Typer CLI
- Interactive chat mode via `jdo chat`
- Fire-and-forget commands: `jdo list commitments`, `jdo add commitment`, etc.
- Rich formatted output (tables, trees)
- REPL-style for sustained interaction

### Common Changes (both options)
- **Remove**: MainScreen, NavSidebar, ChatContainer, DataPanel, all complex widgets (~3,700 LOC)
- **Keep**: All backend (models, AI agent, handlers, database, auth)
- **Keep**: Command parser and handler architecture (refactored in recent changes)
- **Simplify**: Command handlers return structured data instead of complex HandlerResult with panel updates
- **Add**: Simple output formatters (text/rich) for lists and entity views

### Breaking Changes
- **BREAKING**: TUI architecture completely replaced (tui-core, tui-chat, tui-nav, tui-views specs deprecated)
- **BREAKING**: Widget-based tests removed (pytest-textual-snapshot no longer needed)

## Impact

### Affected Specs
- **MAJOR CHANGES**:
  - `tui-core` - Screen/Widget architecture deprecated; replaced with minimal interface
  - `jdo-app` - Application entry point and lifecycle simplified
  - `command-handlers` - HandlerResult simplified (no panel_update, simpler output)
  
- **DEPRECATED** (requirements moved to archive or removed):
  - `tui-chat` - Chat interface patterns replaced
  - `tui-nav` - Navigation sidebar removed
  - `tui-views` - Data panel views removed

- **UNCHANGED**:
  - `ai-provider`, `app-config`, `data-persistence`, `provider-auth` - Backend unchanged
  - `commitment`, `goal`, `task`, `vision`, `milestone`, `stakeholder` - Domain models unchanged
  - `integrity`, `recurring-commitment` - Business logic unchanged

### Affected Code
- **Removed** (~3,700 LOC):
  - `src/jdo/screens/` (7 files: main.py, chat.py, home.py, settings.py, ai_required.py, draft_restore.py, __init__.py)
  - `src/jdo/widgets/` (8 files)
  - `src/jdo/app.py` (458 LOC - complex TUI app)
  - `src/jdo/app.tcss` (TUI styling)
  - `src/jdo/theme.py` (TUI-specific themes)
  - `tests/tui/` (if exists - TUI-specific tests)
  
- **Modified** (~500 LOC):
  - `src/jdo/cli.py` - New entry point (modified from 3116 bytes)
  - `src/jdo/commands/handlers/base.py` - CommandOutput base class replaces HandlerResult
  - `src/jdo/commands/handlers/commitment_handlers.py` - Return CommandOutput
  - `src/jdo/commands/handlers/goal_handlers.py` - Return CommandOutput
  - `src/jdo/commands/handlers/task_handlers.py` - Return CommandOutput
  - `src/jdo/commands/handlers/vision_handlers.py` - Return CommandOutput
  - `src/jdo/commands/handlers/milestone_handlers.py` - Return CommandOutput
  - `src/jdo/commands/handlers/utility_handlers.py` - Return CommandOutput
  - `src/jdo/commands/handlers/integrity_handlers.py` - Return CommandOutput
  - `src/jdo/commands/handlers/recurring_handlers.py` - Return CommandOutput
  - `src/jdo/commands/confirmation.py` - Adapt for CLI prompts (Rich Confirm.ask)
  - `pyproject.toml` - Add `typer[all]>=0.9.0` and `rich>=13.0.0`, remove `textual>=6.11.0` and `pytest-textual-snapshot`
  - `tests/conftest.py` - Remove TUI fixtures, add CLI test fixtures
  
- **Added** (~800 LOC):
  - `src/jdo/interface/__init__.py` - Interface module
  - `src/jdo/interface/commands.py` - Typer app with all CLI commands
  - `src/jdo/interface/chat.py` - Interactive chat REPL
  - `src/jdo/output/__init__.py` - Output module
  - `src/jdo/output/formatters.py` - CommandOutput dataclass and base formatter
  - `src/jdo/output/list_formatter.py` - List formatters (commitments, goals, tasks, etc.)
  - `src/jdo/output/entity_formatter.py` - Entity detail formatters
  - `src/jdo/output/table_formatter.py` - Rich Table utilities
  - `tests/interface/` - New CLI tests (pytest with captured stdout)
  - `tests/output/` - Formatter unit tests

### Migration Path
- No data migration needed (database unchanged)
- Users get simpler, working interface
- Old TUI code archived (can reference for features to rebuild)

## Success Criteria

1. ✅ Core workflow works: Start app → chat with AI → create commitment → view list → quit
2. ✅ All existing backend tests pass (621 tests)
3. ✅ New interface tests added (simpler than Pilot tests)
4. ✅ Less than 1,500 LOC for entire interface layer (vs. 3,700 LOC current)
5. ✅ AI agents can understand and modify interface code end-to-end in single context window
6. ✅ Adding a new command requires changes in 2 files max (handler + output formatter)
