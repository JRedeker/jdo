# Design: Improve REPL UI/UX

## Context

The JDO REPL currently has two disconnected command systems:
1. **Inline handlers** in `repl/loop.py`: Handles 5 commands via if/else chain
2. **Handler classes** in `commands/handlers/`: Full handler pattern with 8 domain modules, but not wired to REPL

The command parser (`commands/parser.py`) already recognizes 18+ command types, but most fail with "Unknown command" because the REPL doesn't dispatch to them.

### Stakeholders
- **End users**: Need intuitive, discoverable interface
- **Developers**: Need maintainable, testable command system

### Constraints
- Must preserve existing natural language + slash command hybrid approach
- Must not break existing AI conversation flow
- Must work with current prompt_toolkit integration
- Should follow clig.dev CLI UX best practices

## Goals / Non-Goals

### Goals
- Consolidate command handling into single dispatch system
- Wire all parsed commands to their handlers
- Enable entity navigation and context tracking
- Improve discoverability with better help system
- Add light interactivity (tab completion for IDs, shortcuts)
- Provide helpful error messages

### Non-Goals
- Full TUI with arrow-key navigation in lists (too complex)
- Persistent command history across sessions (low value)
- Custom color themes (low priority)
- Modal dialogs or split panes

## Research Validation

Research conducted 2026-01-13 validated architectural decisions against authoritative documentation.

### Validated Decisions ✅

| Decision | Validation |
|----------|------------|
| Async handler interface | Python community consensus: uniform async simplifies dispatch, negligible overhead |
| Rich ROUNDED box style | Confirmed in Rich docs, already used correctly in codebase |
| rapidfuzz for fuzzy matching | Appropriate scorer, already a dependency |
| Command abbreviations | Common CLI pattern, simple alias map sufficient |
| Toolbar context display | Valid prompt_toolkit pattern |

### Decisions Requiring Changes ⚠️

| Decision | Issue | Resolution |
|----------|-------|------------|
| **Ctrl+R shortcut** | Conflicts with readline reverse-i-search | Change to F5 |
| **60% fuzzy threshold** | Too permissive, causes false positives | Raise to 75% |
| **Implicit number selection** | Violates Principle of Least Astonishment | Use explicit `/1`, `/2` syntax |
| **CommandDispatcher class** | Over-engineering; module-level registry exists | Use existing `get_handler()` pattern |
| **Dynamic ID completion** | Complex custom Completer needed | Defer - keep WordCompleter for commands only |

### Sources
- prompt_toolkit docs: https://python-prompt-toolkit.readthedocs.io/
- rapidfuzz docs: https://rapidfuzz.github.io/RapidFuzz/
- Rich docs: https://rich.readthedocs.io/
- clig.dev: https://clig.dev/
- Python discuss.python.org async-sig threads

## Decisions

### Decision 1: Use Existing Handler Registry (Simplified)

**Research Finding**: A `CommandDispatcher` class is unnecessary. The codebase already has a module-level registry at `commands/handlers/__init__.py` with `get_handler()` function.

**What**: Wire existing `get_handler()` into REPL loop instead of creating new class.

**Why**: 
- Follows P20 (hierarchy: simple > complex)
- Registry pattern already implemented and tested
- Reduces new code by ~50 lines

**Implementation**:
```python
# In repl/loop.py handle_slash_command()
from jdo.commands.handlers import get_handler
from jdo.commands.parser import parse_command

cmd = parse_command(user_input)
handler = get_handler(cmd.command_type)
if handler:
    result = await handler.execute(cmd, build_context(session, db_session))
    # ... handle result
else:
    # ... fuzzy suggestion
```

### Decision 2: Async Handler Interface

**Research Finding**: Python community consensus (Guido van Rossum) recommends "be opinionated" - make all handlers async for uniformity.

**What**: Update `CommandHandler.execute()` to be `async def`.

**Why**: 
- Eliminates need for `iscoroutinefunction()` dispatch logic
- Async overhead on simple handlers (like `/help`) is negligible
- Future-proofs handlers that may need async operations

**Implementation**:
```python
class CommandHandler(ABC):
    @abstractmethod
    async def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute the command and return a result."""
```

### Decision 3: Entity Context in Session

**What**: Add `EntityContext` to `Session` tracking current entity type and ID.

**Why**: Enables "it"/"this" references and context-aware help.

**Implementation**:
```python
# repl/session.py
@dataclass
class EntityContext:
    entity_type: str  # "commitment", "goal", etc.
    entity_id: UUID
    short_id: str  # First 6 chars for display
    display_name: str  # Truncated deliverable/title

class Session:
    current_entity: EntityContext | None = None
```

### Decision 4: Explicit Number Selection (Changed from Implicit)

**Research Finding**: Implicit number interpretation violates Principle of Least Astonishment. Input like "2" could be meant literally, not as selection.

**What**: Use explicit shortcut syntax `/1`, `/2`, etc. instead of bare numbers.

**Why**:
- No hidden state needed
- Unambiguous intent
- Still saves keystrokes vs full IDs
- Matches bash `select` pattern (explicit prompt)

**Implementation**:
```python
# In parser, add number aliases
_ALIASES = {
    "1": "view 1", "2": "view 2", "3": "view 3",
    "4": "view 4", "5": "view 5",
    # ...
}
```

**Output format**: `[/1] abc123  Send report to Sarah`

### Decision 5: Keyboard Shortcuts (Revised)

**Research Finding**: Ctrl+R conflicts with readline reverse-i-search. F1 is safe across terminals.

**What**: Use F1 for help, Ctrl+L for clear, F5 for refresh (instead of Ctrl+R).

**Implementation**:
```python
from prompt_toolkit.key_binding import KeyBindings

bindings = KeyBindings()

@bindings.add('c-l')
def _(event):
    """Clear screen and redisplay dashboard."""
    event.app.renderer.clear()
    on_clear_dashboard()

@bindings.add('f5')  # Changed from c-r
def _(event):
    """Refresh data from database."""
    on_refresh()

@bindings.add('f1')
def _(event):
    """Show help."""
    on_help()
```

### Decision 6: Command Abbreviations via Alias Map

**What**: Support short aliases like `/c` for `/commit`, `/l` for `/list`.

**Why**: Power users want speed. Common pattern in CLIs.

**Implementation**: Add alias map to parser, resolve before dispatch.

```python
_ALIASES = {
    "c": "commit",
    "l": "list",
    "v": "view",
    "h": "help",
}
```

### Decision 7: Fuzzy Command Suggestions (Threshold Raised)

**Research Finding**: 60% threshold is too permissive for short command names. Testing showed false positives like "goat" → "goal".

**What**: Use rapidfuzz with 75% threshold (aligned with existing 80% in confirmation.py).

**Implementation**:
```python
from rapidfuzz import fuzz, process

def _suggest_similar(cmd: ParsedCommand) -> str | None:
    matches = process.extract(
        cmd.raw_text[1:].split()[0],
        list(_COMMAND_MAP.keys()),
        scorer=fuzz.ratio,
        limit=3,
    )
    if matches and matches[0][1] >= 75:  # 75% threshold (was 60%)
        suggestions = [f"/{m[0]}" for m in matches if m[1] >= 75]
        return f"Did you mean: {', '.join(suggestions)}?"
    return None
```

### Decision 8: Defer Dynamic ID Completion (Simplified)

**Research Finding**: Dynamic entity ID completion requires custom `Completer` class with session access. The existing partial-ID matching in handlers already provides good UX.

**What**: Keep current `WordCompleter` for slash commands only. Defer ID completion.

**Why**:
- Follows P04 (locality) and P20 (simple > complex)
- Users already see IDs in output before typing
- 6-char IDs are quick to type
- Existing partial-match in `/complete` handler works well

**Future consideration**: If users request it, implement minimal custom completer for `/complete` command only.

## Risks / Trade-offs

### Risk: Breaking existing behavior
**Mitigation**: Comprehensive test coverage for all command paths. Existing tests must pass.

### Risk: Increased complexity
**Mitigation**: Using existing registry pattern instead of new class reduces complexity.

### Trade-off: Explicit `/1` vs implicit number selection
**Pro**: Unambiguous, no hidden state, matches POLA
**Con**: One extra character to type
**Resolution**: Research showed implicit pattern causes confusion; explicit is better UX

### Trade-off: F5 instead of Ctrl+R for refresh
**Pro**: No conflict with history search
**Con**: Less discoverable than Ctrl+R
**Resolution**: F5 is standard refresh key (browsers, IDEs); show in help

## Migration Plan

### Phase 1: Foundation (No user-visible changes)
1. Wire existing `get_handler()` to REPL loop
2. Make all handlers async
3. Move handler state to context (not instance vars)
4. Verify all tests pass

### Phase 2: Wire Missing Commands
1. Wire handlers one domain at a time (goal, task, vision, etc.)
2. Add tests for each new command path
3. Update `/help` to show all commands

### Phase 3: Navigation
1. Add EntityContext to Session
2. Implement `/view` command
3. Add explicit `/1`, `/2` shortcuts
4. Update toolbar

### Phase 4: Discoverability
1. Enhanced help system
2. Fuzzy suggestions with 75% threshold
3. Command abbreviations

### Phase 5: Polish
1. Keyboard shortcuts (F1, Ctrl+L, F5)
2. Improved error messages
3. Consider ID completion if requested

### Rollback
Each phase is independently deployable. If issues arise, revert that phase while keeping earlier work.

## Handler State Audit (2026-01-13)

Audit of all handler modules found 3 handlers with problematic instance state:

| File | Handler | Issue | Fix |
|------|---------|-------|-----|
| `commitment_handlers.py` | `CommitHandler` | `self._current_draft` persists between calls | Remove, use `HandlerResult.draft_data` |
| `goal_handlers.py` | `GoalHandler` | `self._current_draft` persists between calls | Remove, use `HandlerResult.draft_data` |
| `task_handlers.py` | `TaskHandler` | `self._current_draft` persists between calls | Remove, use `HandlerResult.draft_data` |

**Why this matters**: Handlers are **singletons** (cached in `_handler_instances` dict). Instance variables persist between all calls, causing state leaks if handlers are called rapidly or concurrently.

**Resolution**: Remove `self._current_draft` from all three handlers. The draft data is already returned via `HandlerResult.draft_data`, making the instance variable redundant.

**Safe patterns found** (no action needed):
- `ShowHandler._ENTITY_MAP` - ClassVar constant
- `HelpHandler._COMMAND_HELP` - ClassVar constant  
- `CompleteHandler._HOURS_OPTIONS` - ClassVar constant

## Additional Research Findings (2026-01-13)

### Onboarding Best Practices
- Keep brief, skippable, value-focused
- Use Rich Panels for welcome screens
- Progressive disclosure - don't dump all info upfront
- Store last-seen version in config to trigger "What's New"

### Toolbar Mouse Support
- prompt_toolkit toolbar is display-only by default
- Making it clickable requires complex full-screen app setup
- **Decision**: Keep toolbar keyboard-only (standard CLI pattern)

### Error Handling for Keyboard Shortcuts
- Use `run_in_terminal()` for safe output during key bindings
- Wrap handlers in try/except, never crash REPL
- Show user-friendly message, log at INFO level

### Testing Keyboard Shortcuts
- Fully testable with `create_pipe_input()` + `DummyOutput()`
- Key mappings: `\x03` = Ctrl+C, `\x1b` = Escape, etc.
- Always send `\n` to accept prompt input

## Open Questions (Resolved)

1. **Should abbreviations be documented in help?** 
   - ✅ Yes, in a "shortcuts" section

2. **How many list items to support for explicit selection?**
   - ✅ 5 items (`/1` through `/5`), matching dashboard display limits

3. **Should number selection work across entity types?**
   - ✅ Yes, `/1` selects from whatever list was last displayed (simpler implementation)

4. **How will users learn shortcuts exist?**
   - ✅ Help menu + AI-guided suggestions + onboarding splash screen

5. **What if `/view` matches entities of different types?**
   - ✅ Show both with type labels, ask user which they meant (unless context is obvious)

6. **What happens if keyboard shortcut action fails?**
   - ✅ Show friendly error, log at INFO, continue REPL normally

7. **Should fuzzy suggestions include command descriptions?**
   - ✅ Yes, e.g., "Did you mean: /commit (create a commitment)?"

8. **Can keyboard shortcuts be unit tested?**
   - ✅ Yes, using prompt_toolkit's `create_pipe_input()` pattern

9. **What's the rollback plan if Phase 1 breaks?**
   - ✅ Fix forward (no feature flags needed)
