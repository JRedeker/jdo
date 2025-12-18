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

**Choice**: Add `jdo capture "text"` as a subcommand using Click/Typer.

**Rationale**:
- Single `jdo` command with subcommands is more discoverable
- Consistent with common CLI patterns (git, docker, etc.)
- Future subcommands (e.g., `jdo status`) share same entry point

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

### Decision 6: AI confidence threshold hardcoded

**Choice**: Use hardcoded reasonable defaults for classification confidence.

**Rationale**:
- Avoid premature optimization
- Can tune based on real user feedback
- Expose as setting later if needed

**Implementation**: If AI confidence < 0.7, ask clarifying question rather than suggesting type.

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
