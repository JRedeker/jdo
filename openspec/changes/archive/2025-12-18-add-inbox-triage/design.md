# Design: Inbox Capture and Triage System

## Context

JDO users need to capture thoughts quickly from various contexts without interactive TUI sessions. The system should gracefully handle ambiguous input by queuing it for later AI-assisted classification rather than forcing immediate type decisions.

Key stakeholders:
- End users capturing ideas on-the-go
- External automation scripts (shell aliases, iOS Shortcuts, webhooks)
- The AI agent that assists with classification

## Goals / Non-Goals

### Goals
- Enable fire-and-forget capture from CLI without TUI
- Provide AI-assisted triage workflow for classifying captured items
- Handle vague chat input gracefully by creating triage items
- Show users when items need attention via home screen indicator

### Non-Goals
- Real-time push notifications to running TUI (deferred to future)
- Complex inbox management (folders, tags, priorities)
- External API/webhook server (CLI-only for v1)
- Automatic classification without user confirmation

## Decisions

### Decision 1: Reuse Draft model with UNKNOWN type

**Choice**: Add `UNKNOWN = "unknown"` to existing `EntityType` enum rather than creating a new `InboxItem` model.

**Rationale**:
- Draft already handles partial objects with `partial_data` JSON field
- Consistent pattern: triage items are just drafts without a known type
- When classified, simply update `entity_type` and continue normal creation flow
- Reduces schema complexity and migration needs

**Alternatives considered**:
- New `InboxItem` table: More explicit but duplicates Draft functionality
- Separate inbox file (JSON/SQLite): Adds sync complexity between inbox and main DB

### Decision 2: CLI subcommand vs separate entry point

**Choice**: Add `jdo capture "text"` as a subcommand using Click with `@click.group(invoke_without_command=True)`.

**Rationale**:
- Single `jdo` command with subcommands is more discoverable
- Click's `invoke_without_command=True` allows `jdo` (no args) to launch TUI, while `jdo capture` runs the subcommand
- Consistent with common CLI patterns (git, docker, etc.)
- Future subcommands (e.g., `jdo status`) share same entry point

**Implementation pattern** (from Click docs):
```python
@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        # Launch TUI
        from jdo.app import main
        main()

@cli.command()
@click.argument('text')
def capture(text):
    # Create triage item
    ...
```

**Alternatives considered**:
- Separate `jdo-capture` binary: Simpler initially but fragments UX
- Stdin mode (`echo "text" | jdo capture`): Added complexity for marginal benefit

### Decision 3: DB-only notification (no file watcher)

**Choice**: Check for triage items on home screen mount and `/triage` command only.

**Rationale**:
- File watching adds complexity (platform-specific, dependencies, race conditions)
- SQLite with WAL mode handles concurrent CLI/TUI access well
- Acceptable UX: users see count when they launch or navigate home
- Can add simple polling timer later if real-time becomes important

**Alternatives considered**:
- inotify/watchdog file watcher: Platform-specific, adds dependencies
- Unix socket IPC: Complex, overkill for this use case
- Polling timer: Could add as enhancement (check every 30s)

### Decision 4: Triage workflow in chat (not dedicated screen)

**Choice**: Implement triage as a chat-based conversation flow.

**Rationale**:
- Natural conversational UX consistent with existing creation flows
- Reuses existing chat infrastructure (messages, data panel)
- Users familiar with chat patterns for object creation
- AI responses feel natural in chat context

**Alternatives considered**:
- Dedicated TriageScreen: Cleaner separation but duplicates UI patterns
- Modal overlay: Too restrictive for multi-item workflow

### Decision 5: FIFO queue with skip-to-back behavior

**Choice**: Skipped items stay at front of queue (true FIFO).

**Rationale**:
- Prevents items getting "lost" at back of growing queue
- User explicitly chose to skip; they'll see it again next triage session
- Simple mental model: items processed in capture order

**Alternatives considered**:
- Skip moves to back: Item could get buried
- Priority system: Over-engineering for v1

### Decision 6: AI classification using PydanticAI structured output

**Choice**: Use PydanticAI agent with `output_type` for structured classification results.

**Rationale**:
- PydanticAI's `output_type` parameter enforces structured responses
- Pydantic models provide type safety and validation
- Can return either classification result or clarifying question using union types
- Consistent with existing AI agent patterns in codebase

**Implementation pattern** (from PydanticAI docs):
```python
from pydantic import BaseModel
from pydantic_ai import Agent

class TriageClassification(BaseModel):
    suggested_type: str  # commitment, goal, task, vision, milestone
    confidence: float
    detected_stakeholder: str | None
    detected_date: str | None
    reasoning: str

class ClarifyingQuestion(BaseModel):
    question: str

agent = Agent(
    'anthropic:claude-sonnet-4-20250514',
    output_type=[TriageClassification, ClarifyingQuestion],
)
```

**Confidence threshold**: If AI returns `ClarifyingQuestion` or confidence < 0.7, ask user rather than suggesting type.

### Decision 7: Textual reactive pattern for home screen indicator

**Choice**: Use Textual's `reactive` attribute with `watch_` method for triage count.

**Rationale**:
- Textual's reactive system automatically triggers UI updates when values change
- `watch_` methods allow responding to changes with custom logic
- Pattern is well-established in Textual documentation

**Implementation pattern** (from Textual docs):
```python
from textual.reactive import reactive
from textual.screen import Screen

class HomeScreen(Screen):
    triage_count = reactive(0)
    
    def watch_triage_count(self, count: int) -> None:
        """Called automatically when triage_count changes."""
        indicator = self.query_one("#triage-indicator", Static)
        if count > 0:
            indicator.update(f"{count} items need triage [t]")
            indicator.display = True
        else:
            indicator.display = False
```

### Decision 8: Chat message handling pattern

**Choice**: Add `on_prompt_input_submitted` handler to ChatScreen following Textual's message naming convention.

**Rationale**:
- Textual message handlers use pattern `on_<widget_class>_<message_class>`
- `PromptInput.Submitted` message already exists but is unhandled
- Handler can dispatch to command parser or AI intent detection

**Implementation pattern**:
```python
def on_prompt_input_submitted(self, message: PromptInput.Submitted) -> None:
    """Handle submitted text from prompt input."""
    text = message.text
    if text.startswith('/'):
        # Route to command handler
        self._handle_command(text)
    else:
        # Route to AI intent detection
        self._handle_message(text)
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| AI misclassifies items | User always confirms; easy to change type |
| Queue grows unbounded | Home screen count creates visibility/incentive |
| CLI/TUI DB contention | SQLite WAL mode; tested concurrent access |
| Scope creep (inbox features) | Explicit non-goals; defer enhancements |

## Migration Plan

No migration needed - all changes are additive:
1. `UNKNOWN` enum value is new, existing drafts unaffected
2. New CLI command doesn't affect existing `jdo` TUI entry point
3. Home screen indicator only shows when count > 0

## Open Questions

None - all questions resolved during design discussion:
- Real-time vs on-demand: On-demand (check on mount/command)
- Triage UI: Chat-based
- AI confidence: Ask simple clarifying questions when low
- `/triage` scope: Available from anywhere
