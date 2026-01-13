# Simplify Interface Change - Summary

## Status
✅ **Proposal Complete and Validated**

## Quick Stats
- **Change ID**: `simplify-interface`
- **Deltas**: 35 requirements across 3 specs
- **Code Impact**: 
  - Remove: ~3,700 LOC (screens, widgets, TUI app)
  - Add: ~1,500 LOC (CLI, formatters, REPL)
  - Net: **-2,200 LOC** (59% reduction in interface layer)
- **Estimated Effort**: 15-20 hours over 5 phases

## Decision Made

**Chosen Architecture: Typer CLI** (Option B from proposal)

### Why Typer over Minimal TUI
1. **Simpler for AI maintainability** - Stateless commands vs. reactive state
2. **User's explicit request** - "either a TUI or a typer CLI"
3. **Testing/debugging easier** - Linear execution, no async coordination
4. **Dependency reduction** - Remove Textual entirely (528 KB → 20 KB)
5. **Flexibility** - Can add minimal Textual UI later if needed

### Interface Structure
```bash
# Interactive chat mode (default)
$ jdo
> Create a commitment for Friday
AI: Created commitment. Confirm? (y/n)
> yes
✓ Saved commitment #47

# Fire-and-forget commands
$ jdo list commitments
ID  Deliverable      Due        Status
1   Send proposal    Today      in_progress
47  Report           Friday     pending

$ jdo add commitment "Send report to Alice by Friday"
✓ Created commitment #48
```

## What's Changing

### Removed (Breaking)
- ❌ All Textual screens (MainScreen, SettingsScreen, etc.)
- ❌ All Textual widgets (NavSidebar, ChatContainer, DataPanel, etc.)
- ❌ Complex TUI app orchestration
- ❌ `textual` dependency
- ❌ `pytest-textual-snapshot` dev dependency
- ❌ Widget-based tests

### Kept (Unchanged)
- ✅ All domain models (Commitment, Goal, Task, Vision, Milestone, etc.)
- ✅ AI agent and PydanticAI integration
- ✅ Command handlers and parser
- ✅ Database (SQLModel, Alembic migrations)
- ✅ Authentication system
- ✅ All 621 backend tests

### Added (New)
- ➕ Typer CLI application structure
- ➕ Interactive chat REPL
- ➕ Rich formatters (tables, panels, trees)
- ➕ Simplified `CommandOutput` dataclass
- ➕ CLI-friendly error handling

## Implementation Phases

### Phase 1: Scaffold (Parallel to old TUI)
- Create Typer app structure
- Add output formatters
- Wire basic commands (list, chat)
- **Validation**: `jdo chat` works, old TUI accessible via `--legacy`

### Phase 2: Simplify Handlers
- Create `CommandOutput` dataclass
- Migrate handlers incrementally with adapters
- Old TUI still works via adapters
- **Validation**: Both interfaces work

### Phase 3: Complete Migration
- Remove `HandlerResult` and adapters
- Old TUI breaks (expected)
- **Validation**: New CLI fully functional

### Phase 4: Remove Old TUI
- Delete screens/, widgets/, app.py
- Remove `textual` dependency
- Update docs
- **Validation**: 621 backend tests + new CLI tests pass

### Phase 5: Polish
- Add remaining commands
- Improve chat UX (history, streaming)
- Add output format options (--format json)
- **Validation**: Production-ready

## Affected Specs

### Major Changes
1. **tui-core** - 22 requirements REMOVED, 6 requirements ADDED
   - Removes: Screens, Widgets, Navigation, CSS, Key Bindings
   - Adds: Typer structure, REPL, formatters, Rich output

2. **jdo-app** - 3 requirements MODIFIED
   - Entry point now launches Typer (not Textual App)
   - Same config/auth/db initialization
   - Simpler error handling

3. **command-handlers** - 4 requirements MODIFIED
   - `CommandHandler` returns `CommandOutput` (not `HandlerResult`)
   - No UI-specific fields (panel_update removed)
   - Handlers are now interface-agnostic

### Deprecated (No Changes Needed)
- **tui-chat**, **tui-nav**, **tui-views** - Requirements archived

### Unchanged
- **ai-provider**, **app-config**, **data-persistence**, **provider-auth**
- **commitment**, **goal**, **task**, **vision**, **milestone**, **stakeholder**
- **integrity**, **recurring-commitment**

## Migration for Users

### Before (Current)
```bash
jdo  # Launches complex TUI
# Navigate with sidebar, data panels, etc.
# Many features broken or incomplete
```

### After (New)
```bash
jdo  # Launches interactive chat
# OR
jdo list commitments  # Quick fire-and-forget
jdo add commitment "text"
jdo show commitment 47
```

### No Data Migration
- Database schema unchanged
- All existing data accessible
- Just a new frontend

## Next Steps

### To Approve This Proposal
1. Review `proposal.md` - High-level rationale
2. Review `design.md` - Technical decisions and trade-offs
3. Review `tasks.md` - Implementation checklist
4. Review spec deltas in `specs/*/spec.md`

### To Start Implementation
After approval, follow tasks.md sequentially:
1. Phase 1: Scaffold new CLI (parallel to old TUI)
2. Phase 2: Migrate handler return types
3. Phase 3: Complete migration
4. Phase 4: Remove old TUI
5. Phase 5: Polish and complete features

### Files to Create During Implementation
```
src/jdo/
├── interface/
│   ├── __init__.py
│   ├── commands.py      # Typer app and subcommands
│   └── chat.py          # Interactive REPL
├── output/
│   ├── __init__.py
│   ├── formatters.py    # Base formatter + CommandOutput
│   ├── list_formatter.py
│   ├── entity_formatter.py
│   ├── table_formatter.py
│   └── tree_formatter.py
└── cli.py              # New entry point (replaces app.py)
```

## Validation Commands

```bash
# Validate proposal
openspec validate simplify-interface --strict

# Show proposal
openspec show simplify-interface

# Show deltas only
openspec show simplify-interface --json --deltas-only

# Check active changes
openspec list
```

---

**Status**: ✅ Ready for approval  
**Blockers**: None  
**Dependencies**: None (can start immediately after approval)
