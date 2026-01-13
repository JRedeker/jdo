# Design: Enhanced Visual Output

## Context

The JDO CLI uses Rich for output formatting and prompt_toolkit for REPL input. Both libraries have extensive visual features that are currently underutilized. This change adds visual polish without changing core functionality.

**Stakeholders**: End users who interact with the CLI daily
**Constraints**: Must work in standard terminals (no GUI dependencies)

## Goals / Non-Goals

**Goals:**
- Improve user experience with animated feedback (spinners)
- Enable faster input with auto-completion
- Provide always-visible context (bottom toolbar)
- Better readability for AI responses (markdown rendering)

**Non-Goals:**
- Changing any business logic or data models
- Adding new commands or features (tree view deferred)
- Persisting visual preferences
- Supporting graphical interfaces

## Research Validation

Research completed using Context7 documentation and industry sources. See detailed findings below.

| Feature | Result | Action |
|---------|--------|--------|
| Spinner | ✅ VALIDATED | Proceed with refinements |
| Auto-completion | ✅ VALIDATED | Simplify to WordCompleter |
| Bottom toolbar | ✅ VALIDATED | Add caching requirement |
| Markdown rendering | ⚠️ REVISED | Render during streaming |
| Rounded tables | ✅ VALIDATED | Proceed as-is |
| Tree view | 🔄 DEFERRED | Remove from this change |
| Progress bar | 🔄 DEFERRED | Existing text progress is sufficient |

## Decisions

### 1. Spinner Implementation ✅ VALIDATED
**Decision**: Use `console.status()` context manager for "Thinking..." indicator, separate from Rich Live streaming.

**Research Findings**:
- `console.status()` IS the recommended Rich API for temporary spinners
- Status wraps Live with `transient=True` for automatic cleanup
- CRITICAL: Must call `status.stop()` BEFORE starting Live streaming to avoid nesting conflicts
- No carriage return hacks needed - transient display clears automatically
<!-- Source: Rich Console API docs, rich/status.py source -->

**Implementation Pattern**:
```python
status = console.status("[dim]Thinking...[/dim]", spinner="dots")
status.start()

async for chunk in stream_response(...):
    if first_chunk:
        status.stop()  # Stop BEFORE starting Live
        live = Live(output, console=console)
        live.start()
        first_chunk = False
    # ... stream content
```

**Alternatives considered**:
- Keep plain text (rejected: misses opportunity for visual polish)
- Use Rich Live for spinner (rejected: conflicts with streaming Live display)

### 2. Auto-completion Approach ✅ SIMPLIFIED
**Decision**: Use `WordCompleter` with `ignore_case=True` for slash commands.

**Research Findings**:
- FuzzyCompleter wrapping WordCompleter is documented pattern
- However, for ~10-20 commands, fuzzy matching adds confusion
- Plain WordCompleter achieves 95% of benefit with less complexity
- `FuzzyWordCompleter` exists as shortcut if fuzzy needed later
<!-- Source: prompt_toolkit docs, fuzzy-custom-completer.py example -->

**Implementation Pattern**:
```python
from prompt_toolkit.completion import WordCompleter

commands = ["/help", "/list", "/commit", "/complete", "/review"]
completer = WordCompleter(commands, ignore_case=True)

prompt_session = PromptSession(
    completer=completer,
    complete_while_typing=False,  # Only on Tab
)
```

**Alternatives considered**:
- FuzzyCompleter wrapping WordCompleter (deferred: overkill for small list)
- Dynamic completion from DB (rejected: adds complexity)

### 3. Bottom Toolbar Content ✅ VALIDATED WITH CACHING
**Decision**: Show commitment count, triage queue size, and pending draft indicator with cached values.

**Research Findings**:
- `bottom_toolbar` callback is the correct prompt_toolkit pattern
- CRITICAL: Toolbar callable runs on every keystroke - blocking DB queries freeze UI
- Solution: Cache counts in session state, update only on data changes
- `refresh_interval` enables time-based refresh independent of input
<!-- Source: prompt_toolkit docs, bottom-toolbar.py example -->

**Implementation Pattern**:
```python
def get_status_toolbar():
    # Use CACHED values, not live DB queries
    active = session.cached_commitment_count
    triage = session.cached_triage_count
    draft = "[draft]" if session.has_pending_draft else ""
    return f" {active} active | {triage} triage {draft}"

prompt_session = PromptSession(
    bottom_toolbar=get_status_toolbar,
    refresh_interval=1.0,  # Refresh every second
)
```

**Alternatives considered**:
- Show stats only in welcome message (rejected: loses visibility)
- Show integrity grade (rejected: too noisy)

### 4. Markdown Rendering Strategy ⚠️ REVISED
**Decision**: Render AI responses as Markdown DURING streaming, not after.

**Research Findings**:
- PydanticAI's official `stream_markdown.py` example renders Markdown on every chunk
- Rendering only after streaming causes visual "pop" when plain text becomes formatted
- Re-parsing entire document has O(n²) complexity but acceptable for typical AI responses (<10KB)
- Fallback to plain text on parse errors
<!-- Source: pydantic-ai/examples/stream_markdown.py, Will McGugan's streaming markdown blog -->

**Implementation Pattern**:
```python
with Live('', console=console, vertical_overflow='visible') as live:
    full_response = ""
    async for chunk in stream_response(...):
        full_response += chunk
        try:
            live.update(Markdown(full_response))
        except Exception:
            live.update(Text(full_response))  # Fallback
```

**Alternatives considered**:
- Render markdown only after streaming (rejected: loses formatting during stream)
- Incremental markdown parsing (deferred: premature optimization)

### 5. Rounded Table Borders ✅ VALIDATED
**Decision**: Use `box.ROUNDED` style for all Rich Tables.

**Rationale**: One-line change per table, pure aesthetics improvement with minimal complexity.

### 6. Tree View Location 🔄 DEFERRED
**Original Decision**: Create new `/hierarchy` command with Tree view.

**Research Findings**:
- Rich Tree IS the appropriate component for hierarchical data
- However, current `/list` commands with tables are sufficient
- Tree view adds significant complexity (recursive queries, orphan handling)
- Marginal benefit for current use case

**Decision**: Defer to future change. Remove from this scope.

### 7. Progress Bar Scope 🔄 DEFERRED
**Original Decision**: Add progress bar to triage workflow.

**Research Findings**:
- Rich Progress with SpinnerColumn + BarColumn is valid pattern
- However, `output/triage.py` already has `format_triage_progress()` showing "Item X of Y"
- For 5-10 triage items, Progress bar is over-engineered
- SpinnerColumn shows per-task spinner, not global "working" indicator

**Decision**: Keep existing text-based progress. Defer Progress bar to future change if triage becomes more complex.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Spinner may not clear properly on error | Stop status in try/finally, transient=True auto-clears |
| Bottom toolbar DB queries block UI | Cache counts in session state |
| Markdown re-parsing slow for large responses | Acceptable for <10KB; optimize later if needed |
| Markdown parsing errors | try/except with plain text fallback |

## Migration Plan

No migration needed - all changes are additive visual enhancements.

**Rollback**: Simply revert commits. No data changes.

## Open Questions

None - research resolved all architectural questions.

## Research Sources

- Rich Console API docs: https://rich.readthedocs.io/en/latest/console.html
- Rich Status reference: https://rich.readthedocs.io/en/latest/reference/status.html
- Rich Live Display: https://rich.readthedocs.io/en/latest/live.html
- prompt_toolkit completion: https://python-prompt-toolkit.readthedocs.io/en/master/pages/asking_for_input.html
- prompt_toolkit toolbar: https://python-prompt-toolkit.readthedocs.io/en/stable/pages/asking_for_input.html#adding-a-bottom-toolbar
- PydanticAI stream_markdown.py: https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/stream_markdown.py
