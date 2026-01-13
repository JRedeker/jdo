# Change: Add /exit and /quit slash commands

## Why

Users expect slash commands to work consistently for all REPL operations. Currently, typing `/exit` or `/quit` returns "Unknown command" even though `exit` and `quit` (without the slash) work. This inconsistency confuses users who have learned the slash command pattern from `/help`, `/list`, etc.

## What Changes

- Add `/exit` and `/quit` as recognized exit commands in `_process_user_input()`
- Update `/help` output to include exit commands
- Add exit commands to auto-completion list
- Update welcome message to mention slash command exit options

## Impact

- Affected specs: `cli-interface`
- Affected code: `src/jdo/repl/loop.py`, `tests/repl/test_loop.py`
- Breaking changes: None
- Migration: None required

## Research Validation

### Validated Decisions
- **WordCompleter for auto-completion**: Appropriate for small command sets (~10 commands)
- **Exit as special-case handling**: Matches prompt_toolkit's design philosophy where exit is a signal, not a command

### Simplification Applied
Research identified that instead of modifying `handle_slash_command()` return semantics, the simplest approach is to expand the existing exit check in `_process_user_input()`:

```python
# Handle exit with or without slash, with optional trailing args
lower_input = user_input.lower()
if lower_input in ("exit", "quit") or lower_input.startswith(("/exit", "/quit")):
    console.print(GOODBYE_MESSAGE)
    return False
```

This avoids:
- Changing `handle_slash_command()` return value semantics
- Using exceptions for control flow (anti-pattern)
- Duplicating exit logic

### Research Sources
- prompt_toolkit REPL tutorial: exit via EOFError/KeyboardInterrupt is the canonical pattern
- IPython: uses namespace magic for exit/quit, not text command processing
- prompt_toolkit WordCompleter docs: appropriate for small static command sets

## Related Changes

### Tech Debt Addressed by `improve-repl-ux`

During research, significant tech debt was identified in the REPL system. This tech debt is **already addressed** by the existing `improve-repl-ux` change proposal:

| Issue | Status | Addressed By |
|-------|--------|--------------|
| Duplicate command routing (`loop.py:355-397`) | ✅ Covered | `improve-repl-ux` Task 1.1-1.5 |
| Command set mismatch (8 vs 19 commands) | ✅ Covered | `improve-repl-ux` Tasks 2.1-2.8 |
| Missing `/list` and `/review` handlers | ✅ Covered | `improve-repl-ux` Task 1.4 |
| Help content mismatch | ✅ Covered | `improve-repl-ux` Tasks 4.1-4.2 |
| Fuzzy command suggestions | ✅ Covered | `improve-repl-ux` Task 1.5 |

### Deferred (per P20 - prefer simple solutions)

| Issue | Reason |
|-------|--------|
| NestedCompleter for hierarchical commands | `improve-repl-ux` explicitly defers this; existing WordCompleter is sufficient for current needs |

### Coordination Note

This change (`add-exit-slash-commands`) can be implemented independently and merged before `improve-repl-ux`. When `improve-repl-ux` is implemented:
- Exit handling will remain as special-case (not go through handler infrastructure) per design decision D1 in `improve-repl-ux`
- The `/exit` and `/quit` entries in `SLASH_COMMANDS` will be migrated to the unified command list
