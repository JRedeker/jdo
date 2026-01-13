## Context

JDO is a terminal-based productivity app built on:
- **Backend** (solid): SQLModel models, PydanticAI agent, command handlers, Alembic migrations, 621 passing tests
- **Frontend** (problematic): Complex Textual multi-widget TUI with MainScreen coordinating NavSidebar, ChatContainer, DataPanel, PromptInput across 3,700+ LOC

The current TUI architecture emerged organically but has become unmaintainable:
- State fragmented across Screen/Widget hierarchy
- Message passing between 5+ widgets per user action
- Async lifecycle (on_mount, workers, push_screen_wait) error-prone
- High friction for AI-assisted development

User feedback: "The TUI is overly complex to easily make with an AI agent; it's still very broken with most features not working."

Most features (recurring commitments, integrity dashboard, vision reviews, triage workflow) are partially implemented with broken UI interactions.

**Constraint**: Keep all backend code. The domain models, AI agent, command handlers, and database layer are well-architected and tested.

## Goals / Non-Goals

### Goals
1. **Simplify maintainability**: Reduce interface LOC by 50%+ while keeping all core features
2. **Enable AI assistance**: Interface code should fit in single context window with clear control flow
3. **Preserve UX essence**: Terminal-native, keyboard-first, conversational interaction with AI
4. **Reduce coupling**: Interface should be thin adapter layer over backend, not tightly coupled state manager

### Non-Goals
- Rewrite backend (keep models, handlers, AI, database as-is)
- Add new features during simplification (focus on working core)
- Support both old and new interface simultaneously (clean break)
- Preserve exact UI layouts (acceptable to change from panels to simpler text output)

## Decisions

### Decision 1: Interface Architecture (Minimal TUI vs. Typer CLI)

**Options Considered:**

#### Option A: Minimal Single-Screen TUI (Textual)
```
┌─ JDO ──────────────────────────────────────┐
│ You: Create a commitment for Friday        │
│  AI: Created:                               │
│      • Deliverable: Report                  │
│      • Due: Friday                          │
│      Confirm? (y/n)                         │
│                                             │
│ You: yes                                    │
│  AI: ✓ Saved commitment #47                 │
│                                             │
│ You: /show commitments                      │
│  AI: Your commitments:                      │
│      1. [TODAY] Send proposal               │
│      2. [FRI] Report                        │
│                                             │
│ > _                                         │
└─────────────────────────────────────────────┘
```

**Pros:**
- Keep terminal-native aesthetic
- Single file (< 400 LOC) vs 8 screens/widgets
- Scrollback for history
- Familiar for users of existing TUI

**Cons:**
- Still depends on Textual (528 KB dependency)
- Still need to manage reactive state (simpler, but present)
- Async message handling (though much simpler with 1 widget)

#### Option B: Typer CLI
```bash
# Interactive mode
$ jdo chat
> Create a commitment for Friday
AI: Created:
    • Deliverable: Report
    • Due: Friday
    Confirm? (y/n)
> yes
✓ Saved commitment #47

# Or fire-and-forget
$ jdo list commitments
ID  Deliverable      Due        Status
1   Send proposal    Today      in_progress
47  Report           Friday     pending

$ jdo add commitment "Send report to Alice by Friday"
✓ Created commitment #48
```

**Pros:**
- Zero UI state management (stateless commands)
- Typer is 20KB vs Textual 528KB
- Easier to test (no async, no widgets)
- AI-friendly: single linear execution path
- Supports both interactive chat and fire-and-forget commands

**Cons:**
- Loses scrollback in interactive mode (each command clears)
- Slightly less "app-like" feel
- Need REPL loop for chat mode

**Decision**: **Option B: Typer CLI**

**Rationale**:
1. **Primary goal is simplification for AI maintainability** - Typer's stateless command model is dramatically simpler
2. **User's explicit request**: "either a TUI or a typer CLI" - user is open to CLI
3. **Testing/debugging easier**: Linear execution, no async coordination
4. **Dependency reduction**: Remove Textual entirely (also removes pytest-textual-snapshot, textual-specific patterns)
5. **Flexibility**: Can add Textual minimal TUI later if needed (Typer for commands, Textual for chat UI)

**Trade-off accepted**: Lose continuous scrollback in chat mode. Mitigated by showing conversation history in context.

### Decision 2: Chat Mode Architecture

**Chosen**: REPL loop with Rich formatting

```python
# src/jdo/interface/chat.py
def chat_repl():
    """Interactive chat REPL."""
    console = Console()
    conversation_history = []
    
    while True:
        user_input = Prompt.ask("> ")
        if user_input.strip().lower() in {"exit", "quit"}:
            break
        
        # Add to history
        conversation_history.append({"role": "user", "content": user_input})
        
        # Show thinking indicator
        with console.status("[bold green]Thinking..."):
            response = stream_ai_response(user_input, conversation_history)
        
        # Stream response
        console.print(f"[bold blue]AI:[/bold blue] {response}")
        conversation_history.append({"role": "assistant", "content": response})
```

**Why**:
- Simple loop, no state management
- Rich provides formatting without Textual complexity
- Can show context (last N messages) on each iteration
- Easy to test (mock stdin/stdout)

### Decision 3: Handler Return Type Simplification

**Current**: Handlers return complex `HandlerResult`:
```python
@dataclass
class HandlerResult:
    message: str | None
    panel_update: dict[str, Any] | None  # ← TUI-specific
    draft_data: dict[str, Any] | None
    needs_confirmation: bool
```

**New**: Handlers return simpler `CommandOutput`:
```python
@dataclass
class CommandOutput:
    message: str  # Human-readable response
    data: dict[str, Any] | list[dict] | None  # Structured data for formatting
    needs_confirmation: bool = False
    draft: dict[str, Any] | None = None
```

**Migration**:
- Remove `panel_update` (UI-specific, not reusable)
- Rename `message` (always required, not optional)
- Add `data` for structured output (lists, entities)
- Formatters consume `data` to produce tables/views

**Why**:
- Decouples handlers from UI concerns
- Reusable across CLI and future interfaces
- Simpler to test (just check message + data)

### Decision 4: Output Formatting Strategy

**Approach**: Separate formatters by output type

```
src/jdo/output/
├── formatters.py      # Base formatter interface
├── list_formatter.py  # Format lists (commitments, goals)
├── entity_formatter.py # Format single entities
├── tree_formatter.py  # Format hierarchies
└── table_formatter.py # Format tabular data
```

**Why**:
- Single Responsibility (each formatter = one output type)
- Easy to extend (add JSON formatter for scripting)
- Testable in isolation

**Example**:
```python
# Output from handler
output = CommandOutput(
    message="Found 3 commitments",
    data=[
        {"id": 1, "deliverable": "Report", "due": "2025-01-10"},
        {"id": 2, "deliverable": "Proposal", "due": "2025-01-07"},
    ]
)

# Format as table
table = format_commitment_list(output.data)
console.print(table)
```

## Risks / Trade-offs

### Risk 1: Loss of scrollback in chat mode
**Impact**: Users can't scroll back through conversation history in terminal  
**Mitigation**:
- Show last 3 exchanges in context on each prompt
- Add `jdo history` command to view full conversation log
- Consider Textual minimal UI later if scrollback is critical

### Risk 2: Removing Textual entirely limits future UI options
**Impact**: Can't easily add rich TUI features later  
**Mitigation**:
- Typer and Textual are not mutually exclusive
- Can add `jdo tui` command later that launches minimal Textual interface
- Keep interface layer thin so swapping is easy

### Risk 3: Breaking change for existing users
**Impact**: Users must learn new interface  
**Mitigation**:
- Current TUI is mostly broken anyway (per user feedback)
- Core workflow (chat → create → view) remains identical
- Document migration in README

### Risk 4: AI streaming output less elegant in CLI
**Impact**: Can't update message in place like TUI  
**Mitigation**:
- Use Rich `Live` display for streaming
- Or show full response after generation (simpler, still fast)

## Migration Plan

### Phase 1: Scaffold new interface (Parallel to old TUI)
1. Add `src/jdo/interface/chat.py` - REPL loop
2. Add `src/jdo/interface/commands.py` - Typer app
3. Add `src/jdo/output/formatters.py` - Output formatting
4. Add `src/jdo/cli.py` - New entry point with `--legacy` flag
5. Old TUI accessible via `jdo --legacy` (default to new CLI)

**Tests**: New CLI tests, old TUI tests still run

### Phase 2: Simplify handler return types
1. Create `CommandOutput` dataclass
2. Update 2-3 handlers to return `CommandOutput` (commitment, goal, task)
3. Add adapter in MainScreen to convert `CommandOutput` → `HandlerResult`
4. Verify old TUI still works with adapted handlers

**Tests**: Both old and new tests pass

### Phase 3: Complete handler migration
1. Update remaining handlers to `CommandOutput`
2. Remove `HandlerResult` and adapter
3. Old TUI breaks (expected, deprecated)

**Tests**: New CLI tests pass, old TUI tests deleted

### Phase 4: Remove old TUI
1. Delete `src/jdo/screens/`, `src/jdo/widgets/`, `src/jdo/app.py`
2. Remove `textual` from dependencies (keep in dev for minimal future use?)
3. Remove `pytest-textual-snapshot` from dev dependencies
4. Remove `--legacy` flag from CLI
5. Update README

**Tests**: Only new CLI tests remain

### Rollback Plan
- Phase 1-2: Just remove `--legacy` flag and new files
- Phase 3+: Revert commits, restore `textual` dependency

## Open Questions

1. **Q**: Should we keep `textual` as optional dependency for future minimal TUI?  
   **A**: No, remove entirely. Add back later if needed (typer + textual play nicely).

2. **Q**: How to handle draft confirmation flow in CLI?  
   **A**: Same as current - prompt user for y/n, loop until confirmed or cancelled.

3. **Q**: Should `jdo` (no args) default to chat mode or show help?  
   **A**: Default to chat mode (current behavior). Users can exit with `quit` or Ctrl+C.

4. **Q**: Do we need conversation persistence across sessions?  
   **A**: Not in v1. Add as separate feature later (save to DB, load on start).
