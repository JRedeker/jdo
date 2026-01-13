# Design: Conversational Flow CLI Architecture

## Context

JDO is a productivity tool for managing commitments, goals, visions, and tasks. The current Textual TUI has grown complex (3,700+ LOC) with incomplete features. The core backend (AI, database, handlers) is solid and well-tested.

The goal is to create an interface that:
1. Feels like conversing with an intelligent assistant (like OpenCode, Claude, ChatGPT)
2. Requires no command memorization
3. Is simple to maintain and extend
4. Works well in terminal environments

**Stakeholders**: Solo developer (Jon), AI coding assistants

**Constraints**:
- Must preserve all backend functionality (models, handlers, database)
- Must work in standard terminal (no GUI dependencies)
- Must support streaming AI responses
- Should be testable without complex frameworks

## Goals / Non-Goals

### Goals
- **G1**: Single REPL loop as primary interaction mode
- **G2**: Natural language is primary input; slash commands available as power-user shortcuts (hybrid approach per research)
- **G3**: Rich terminal output (tables, trees, colors) via Rich library
- **G4**: Streaming AI responses for responsive feel using Rich `Live` display
- **G5**: < 2,000 LOC for entire interface layer
- **G6**: Simple testing with pytest (no Pilot)

### Non-Goals
- **NG1**: Multi-window/pane TUI layouts
- **NG2**: Mouse interaction support
- **NG3**: Keyboard shortcut navigation
- **NG4**: Background notifications/alerts
- **NG5**: Session persistence across runs (conversation history resets)

## Decisions

### D1: Use prompt_toolkit for Input, Rich for Output

**Decision**: Use prompt_toolkit for readline-like input and Rich for formatted output.

**Why**:
- prompt_toolkit: History, completion, multi-line input, async support
- Rich: Tables, trees, markdown, syntax highlighting, streaming
- Both are mature, well-documented, actively maintained
- Click for CLI structure (already in use, no migration to Typer needed)

**Alternatives considered**:
- Pure input(): Too basic, no history/completion
- Textual in "simple" mode: Still brings TUI complexity
- Click REPL plugins: Less control over streaming/formatting

### D2: Hybrid Intent Parsing (Updated per Research)

**Decision**: AI assists with natural language understanding while slash commands provide deterministic shortcuts. Both route to the same underlying tool handlers.

**Why**:
- Natural language is more intuitive for new users and complex requests
- Slash commands provide instant response for power users (no AI latency)
- Hybrid approach is industry best practice (Aider, GitHub Copilot)
- OWASP LLM08 "Excessive Agency" recommends deterministic escape hatches
- Both paths share the same handlers, reducing code duplication

**Implementation**:
- Input starting with `/` → Direct handler invocation (instant, no AI)
- Natural language → AI agent with function calling to same handlers
- All mutating operations require confirmation regardless of input method

**Slash commands retained**:
- `/commit [text]` - Create commitment
- `/list [type]` - List entities
- `/complete [id]` - Mark complete
- `/help` - Show available commands

**Alternatives considered**:
- Pure AI-first: Higher risk (OWASP LLM08), slower for power users
- Command-first with AI assist: Still requires learning commands

### D3: Confirmation Flow via Conversation

**Decision**: Confirmations happen in natural conversation, not modal dialogs.

**Example flow**:
```
User: I need to send the quarterly report to Sarah by next Friday
AI: I'll create a commitment:
    Deliverable: Send quarterly report
    Stakeholder: Sarah
    Due: Friday, Jan 17
    
    Does this look right?
User: change the date to Thursday
AI: Updated to Thursday, Jan 16. Confirm?
User: yes
AI: Created commitment #42. You now have 3 active commitments.
```

**Why**:
- Feels natural, like talking to a person
- Easy to refine before confirming
- No modal state management

### D4: Streaming Output Architecture (Updated per Research)

**Decision**: AI responses stream token-by-token using Rich's `Live` display.

**Implementation** (corrected pattern):
```python
from rich.live import Live
from rich.text import Text

# Show thinking indicator first
console.print("[dim]Thinking...[/dim]", end="")

async with agent.run_stream(input, deps=deps, message_history=history) as result:
    output = Text()
    first_chunk = True
    with Live(output, console=console, refresh_per_second=10) as live:
        async for chunk in result.stream_text():
            if first_chunk:
                console.print("\r", end="")  # Clear "Thinking..."
                first_chunk = False
            output.append(chunk)
            live.update(output)
```

**Why**:
- Responsive feel (no waiting for complete response)
- Rich `Live` display handles terminal redraw without flicker
- `run_stream()` returns async context manager (not direct iterator)
- `console.status()` is for spinners, not streaming text

**Research note**: Original pattern was incorrect. PydanticAI's `run_stream()` must be used with `async with`, and Rich's `Live` is the documented approach for streaming text.

### D5: Session State in Memory

**Decision**: Keep session state (conversation history, current context) in memory; reset on exit.

**Why**:
- Simpler than persisting/restoring complex state
- Each session starts fresh
- Database provides persistence for actual data
- Can add session persistence later if needed

**What's in session state**:
- Conversation history (list of messages)
- Current entity context (e.g., "viewing goal #5")
- Pending draft (entity being created/edited)

### D6: Minimal CLI Commands

**Decision**: Only these CLI commands exist:
- `jdo` - Launch REPL (default)
- `jdo capture "text"` - Quick capture for later triage
- `jdo db status|upgrade|downgrade|revision` - Database migrations

**Why**:
- Keeps CLI simple
- Fire-and-forget capture useful for scripts/shortcuts
- Database commands needed for admin
- Everything else via conversational REPL

### D7: Handler Architecture Preserved

**Decision**: Keep existing handler classes, invoke via AI tools.

**Current flow**: Slash command → Parser → Handler → Result → Widget update
**New flow**: User intent → AI → Tool call → Handler → Result → Rich output

**Why**:
- Handlers contain business logic (validation, database ops)
- AI tools wrap handlers, not replace them
- Easier migration, less rewriting

### D8: Output Formatting Layer

**Decision**: Create dedicated formatters for Rich output.

**Structure**:
```
src/jdo/output/
├── __init__.py
├── formatters.py      # Base classes
├── commitment.py      # Commitment table/detail formatters
├── goal.py            # Goal formatters
├── integrity.py       # Integrity dashboard formatter
└── ...
```

**Why**:
- Separation of concerns (handler logic vs. display)
- Reusable across different contexts
- Easy to test formatting independently

## Risks / Trade-offs

### R1: AI Parsing Failures
**Risk**: AI misunderstands user intent, creates wrong entities.
**Mitigation**: Always show proposed action and require confirmation. User can refine before confirming.

### R2: Slower for Power Users
**Risk**: Users who knew slash commands may find typing more verbose.
**Mitigation**: Slash commands retained as escape hatch (`/commit`, `/list`, etc.) for instant response without AI latency. Power users have deterministic option.

### R3: Token Costs
**Risk**: Every interaction goes through AI, increasing API costs.
**Mitigation**: Use efficient prompts, local models as option. Acceptable trade-off for UX.

### R4: Loss of At-a-Glance Views
**Risk**: No persistent sidebar/panel showing commitments.
**Mitigation**: AI shows relevant data proactively. User can ask "show my commitments" anytime.

### R5: Testing AI Intent
**Risk**: Harder to test "user says X, system does Y" than explicit commands.
**Mitigation**: Use mock AI with deterministic responses for tests. Test handlers independently.

## Migration Plan

### Phase 1: Foundation (Week 1)
1. Create `src/jdo/repl/` module with basic loop
2. Integrate prompt_toolkit for input
3. Integrate Rich for output
4. Basic AI agent connection (no tools yet)

### Phase 2: Core Functionality (Week 2)
1. Implement AI tools wrapping handlers
2. Implement confirmation flow
3. Implement output formatters
4. Test core workflow: create commitment, list, complete

### Phase 3: Full Feature Parity (Week 3)
1. Implement all entity types (goals, visions, milestones, tasks)
2. Implement integrity dashboard
3. Implement triage workflow
4. Test all scenarios

### Phase 4: Cleanup (Week 4)
1. Remove old TUI code (screens, widgets, app.py)
2. Update dependencies (remove textual, add prompt_toolkit)
3. Update tests
4. Documentation

### Rollback Plan
- Keep TUI code on a branch until new interface is stable
- Can revert to TUI if critical issues found
- Database schema unchanged, no data migration needed

## Research Validation (Jan 2026)

### Validated Decisions ✅

#### D1: prompt_toolkit for Input ✅
**Status**: Fully validated as industry best practice.

**Research findings**:
- prompt_toolkit is the de facto standard, powering IPython, pgcli, aws-shell, and 40+ major CLI tools
- Native asyncio support in v3.0+ via `run_async()` method
- Active maintenance (v3.0.52, Aug 2025)
- No simpler alternative meets requirements (history, completion, async)

**Source**: python-prompt-toolkit.readthedocs.io, PyPI (Production/Stable)

#### D5: Session State in Memory ✅
**Status**: Validated with minor modification needed.

**Research findings**:
- In-memory session state is canonical pattern (Google ADK, Arize AI, LangGraph)
- Pydantic AI has native `message_history` support
- The proposed state components (history, context, draft) are minimal and appropriate

**Minor concern**: See "Concerns Identified" below for pruning strategy.

**Source**: ai.pydantic.dev/message-history, Google ADK docs

#### D7: Handler Architecture Preserved ✅
**Status**: Validated as best approach.

**Research findings**:
- Martin Fowler CLI Agent article: "Specialisation matters" - domain handlers outperform generic tools
- PydanticAI tools are designed as thin wrappers delegating to business logic
- JDO already uses this pattern successfully in `src/jdo/ai/tools.py`
- Incremental migration is lower risk than wholesale rewrite

**Source**: martinfowler.com/articles/build-own-coding-agent.html, PydanticAI docs

#### D8: Output Formatting Layer ✅
**Status**: Validated - separate modules are appropriate.

**Research findings**:
- Proposed structure aligns with existing codebase patterns (domain packages of 500-3000 LOC)
- Follows Hitchhiker's Guide to Python best practices
- ~1,000 LOC with 7+ logical components justifies separation

**Source**: docs.python-guide.org/writing/structure/

### Concerns Identified ⚠️

#### D2: AI-First Intent Parsing ⚠️
**Status**: Partial concern - recommend hybrid approach.

**Research findings**:
- Industry leaders (Aider, GitHub Copilot) use **hybrid** approaches, not pure AI-first
- OWASP LLM08 "Excessive Agency": Pure AI parsing increases risk
- Power users prefer deterministic commands for frequent operations (instant vs. AI latency)
- Replit Agent incident (Aug 2025): Agent deleted 1,200 production records

**Risk mitigation in spec (R1 confirmation flow) is necessary but not sufficient.**

**Recommendation**: Add slash command escape hatch. Both input paths use same handlers:
- `/commit "X by Friday"` → Direct handler invocation (instant)
- "I need to commit to X by Friday" → AI parsing → same handler

**Source**: OWASP Top 10 for LLMs 2025, aider.chat/docs/usage/commands, promptfoo.dev

#### D4: Streaming Output Architecture ⚠️
**Status**: Implementation pattern is incorrect.

**Research findings**:
1. **PydanticAI API error**: `run_stream()` returns async context manager, not direct iterator
   - Wrong: `async for chunk in agent.run_stream(input):`
   - Correct: `async with agent.run_stream(input) as result: async for chunk in result.stream_text():`

2. **Rich pattern mismatch**: `console.status()` + `console.print(end="")` causes display conflicts
   - `console.status()` is for spinner animations, not streaming text
   - Rich's `Live` display is the documented approach for streaming

**Recommended pattern** (from PydanticAI examples):
```python
from rich.live import Live
from rich.text import Text

async with agent.run_stream(input, deps=deps, message_history=history) as result:
    output = Text()
    with Live(output, console=console, refresh_per_second=10) as live:
        async for chunk in result.stream_text():
            output.append(chunk)
            live.update(output)
```

**Source**: ai.pydantic.dev/output/#streamed-results, rich.readthedocs.io/live.html

#### Session History Pruning ⚠️
**Status**: Message-count limit should be token-based.

**Research findings**:
- 50-message limit is arbitrary - messages vary from 1 to 1000+ words
- Industry best practice uses token-based limits (OpenAI Cookbook, Semantic Kernel)
- Context windows are measured in tokens, not messages
- Pydantic AI provides `history_processors` for token-aware truncation

**Recommendation**: Replace "exceeds 50 messages" with token-based limit:
```python
MAX_HISTORY_TOKENS = 8000  # Reserve space for response + tools
```

**Source**: cookbook.openai.com, devblogs.microsoft.com/semantic-kernel

### Decisions Needing Update

#### D2: AI-First → Hybrid Intent Parsing
```diff
- **Decision**: AI is responsible for understanding user intent and calling appropriate tools.
+ **Decision**: AI assists with natural language understanding while slash commands provide
+ deterministic shortcuts. Both route to the same underlying tool handlers.
+
+ **Implementation**:
+ - Input starting with `/` → Direct handler invocation (no AI, instant)
+ - Natural language → AI agent with function calling to same handlers
+ - All mutating operations require confirmation regardless of input method
```

#### D4: Streaming Implementation Fix
Update implementation example to use correct patterns (see code above).

#### D6: Minimal CLI Commands → Keep Click
**Research finding**: JDO uses Click, not Typer. Click is more appropriate:
- Typer adds type-annotation overhead without benefit for minimal CLI
- `@click.group(invoke_without_command=True)` is the canonical pattern
- No migration to Typer needed

### Simplification Opportunities 🎯

#### Module Structure: Start Minimal
**Research recommendation**: Begin with fewer files, split when complexity warrants:
```
src/jdo/repl/
├── __init__.py
└── loop.py          # Contains loop + session (split later if needed)

src/jdo/output/
├── __init__.py
└── formatters.py    # All formatters (split by entity later if needed)
```

This follows YAGNI - don't pre-create empty files.

## Open Questions

### Q1: Should conversation history persist across sessions?
Currently: No, resets each run.
Possible: Store recent history in SQLite, restore on launch.
Defer until: User feedback indicates need.

### Q2: Should there be any keyboard shortcuts in REPL?
Currently: Only prompt_toolkit defaults (Ctrl+C, Ctrl+D, arrows, etc.)
Possible: Shortcuts for common actions (Ctrl+L to list, etc.)
Defer until: User feedback indicates need.

### Q3: How to handle multi-line input (e.g., long descriptions)?
Currently: prompt_toolkit supports multi-line with Meta+Enter.
Possible: Auto-detect based on content.
Decision: Use prompt_toolkit defaults initially.
