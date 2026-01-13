# Tasks

## 1. Implementation

- [x] 1.1 Expand exit check tuple in `_process_user_input()` to include `/exit` and `/quit` (loop.py:802)
- [x] 1.2 Update `_handle_help()` to include `/exit` and `/quit` in command list (loop.py:542-563)
- [x] 1.3 Add `/exit` and `/quit` to `SLASH_COMMANDS` list for auto-completion (loop.py:1079-1088)
- [x] 1.4 Update welcome message to mention `/exit` or `/quit` alongside plain `exit`/`quit` (loop.py:86)

## 2. Tech Debt Fixes (Exit-Related)

- [x] 2.1 **Fix inconsistency**: `_handle_help()` currently has no exit instructions - add exit/quit section
- [x] 2.2 **Fix inconsistency**: Ensure `/exit foo` (with trailing args) works by using `.startswith()` check
- [x] 2.3 **Fix inconsistency**: Add exit hint to FIRST_RUN_MESSAGE or ensure /help mentions it

## 3. Testing

- [x] 3.1 Add unit test: `/exit` returns False from `_process_user_input()` and displays goodbye message
- [x] 3.2 Add unit test: `/quit` returns False from `_process_user_input()` and displays goodbye message
- [x] 3.3 Add unit test: `/exit foo` (with trailing args) still exits gracefully
- [x] 3.4 Add unit test: `/EXIT` and `/QUIT` work (case-insensitive)
- [x] 3.5 Add unit test: Verify plain `exit` and `quit` still work (regression)

## 4. Verification

- [x] 4.1 Run lint/format/typecheck: `uv run ruff check --fix src/ tests/ && uv run ruff format src/ tests/`
- [x] 4.2 Run full test suite: `uv run pytest -n auto`
- [ ] 4.3 Manual verification: `/exit` gracefully exits the REPL with goodbye message
- [ ] 4.4 Manual verification: `/quit` gracefully exits the REPL with goodbye message
- [ ] 4.5 Manual verification: `/help` shows exit commands
- [ ] 4.6 Manual verification: tab-completion includes `/exit` and `/quit`

## Implementation Notes

**Simplified approach per research:** Handle `/exit` and `/quit` in the same location as plain `exit`/`quit` (line 802), rather than adding to `handle_slash_command()`. This requires only expanding a tuple, not changing function return semantics.

**Trailing arguments handling:** The spec requires `/exit foo` to work. Use `.startswith()` instead of exact match:
```python
lower_input = user_input.lower()
if lower_input in ("exit", "quit") or lower_input.startswith(("/exit", "/quit")):
    console.print(GOODBYE_MESSAGE)
    return False
```

**Key code locations:**
- Exit check: `src/jdo/repl/loop.py:802`
- Help output: `src/jdo/repl/loop.py:542-563`
- Auto-completion list: `src/jdo/repl/loop.py:1079-1088`
- Welcome message: `src/jdo/repl/loop.py:86`
- First-run message: `src/jdo/repl/loop.py:93-105`
