# Change: Improve REPL UI/UX

## Why

The JDO REPL has a fragmented command system where the parser supports 18+ commands but only 5 are wired to the REPL loop (`/help`, `/list`, `/commit`, `/complete`, `/review`). The elaborate `CommandHandler` pattern in `commands/handlers/` exists but isn't connected to the REPL. Users cannot navigate entities, view details, or access key features like integrity dashboards and triage processing through slash commands.

This creates a poor user experience:
- Commands users expect to work (like `/goal`, `/view`, `/integrity`) fail with "Unknown command"
- No way to navigate between entities or maintain context
- Limited discoverability - users don't know what's available
- No tab completion for entity IDs
- Missing feedback when commands succeed or fail

## What Changes

### Phase 1: Command Dispatch System
- Create centralized `CommandDispatcher` class that routes commands to handlers
- Wire all 18+ parsed command types to their handlers
- Update REPL loop to use dispatcher instead of inline if/else chain
- Add fuzzy command matching for typo suggestions

### Phase 2: Entity Navigation
- Add `/view <id>` command to show entity details
- Add number-based selection from lists (type `2` after `/list` to view item 2)
- Track current entity context in session for "it"/"this" references
- Show context breadcrumb in toolbar

### Phase 3: Discoverability
- Enhanced `/help` with command categories and examples
- `/help <command>` for detailed command help
- Context-aware help based on current state
- Suggest next commands after actions

### Phase 4: Light Interactivity
- Tab completion for entity IDs (not just command names)
- Keyboard shortcuts (Ctrl+L clear, Ctrl+R refresh)
- Command abbreviations (`/c` for `/commit`, `/l` for `/list`)

### Phase 5: Feedback & Errors
- Action-specific status messages ("Extracting commitment..." vs generic "Thinking...")
- Friendly error messages with recovery suggestions
- Confirm what changed after successful operations

## Impact

- **Affected specs**: `cli-interface`, `command-handlers`, `output-formatting`
- **Affected code**: 
  - `src/jdo/repl/loop.py` - Major refactor to use dispatcher, add key bindings
  - `src/jdo/repl/session.py` - Add `last_list_items`, extend `EntityContext` with short_id/display_name
  - `src/jdo/commands/handlers/__init__.py` - Already has `get_handler()`, wire to REPL
  - `src/jdo/commands/handlers/utility_handlers.py` - Enhance `HelpHandler`, `ViewHandler`
  - `src/jdo/commands/parser.py` - Add command aliases (`/c`, `/l`, `/v`, `/h`) and number shortcuts (`/1`-`/5`)
  - `src/jdo/output/formatters.py` - Add help text formatter, numbered list shortcuts
  - `src/jdo/output/onboarding.py` - New onboarding and "What's New" screen formatters
  - Note: Error message formatters integrated into handlers (no separate errors.py needed)
  - `src/jdo/commands/handlers/base.py` - Extend `HandlerResult` with new fields
- **Testing**: Extensive test coverage needed for dispatcher and all command paths
  - `tests/unit/repl/` - Key binding tests, dispatch tests
  - `tests/unit/commands/` - Handler tests for new behaviors
  - `tests/unit/output/` - Formatter tests for new formatting
- **No breaking changes**: All existing natural language and slash command behavior preserved
