# Design: Refactor Codebase Maintainability

## Context

Analysis of the codebase revealed:
- `chat.py:169` initializes `_conversation: list[dict[str, str]] = []`
- Every message appends without bounds checking (lines 456, 984-985)
- `handlers.py` contains 20 handler classes spanning commitments, goals, tasks, visions, milestones, integrity, recurring, and utility commands
- `app.py` has 10 `on_home_screen_*` handlers (lines 234-415) and 10 `_nav_to_*` methods (lines 453-611) with heavily duplicated entity-fetching patterns

## Goals

- Prevent memory exhaustion in long chat sessions
- Reduce handler file size from 2,396 lines to ~200-400 lines per module
- Reduce app.py navigation duplication (~290 lines to ~100 lines)
- Maintain backward compatibility for command routing
- Improve test isolation per domain

## Non-Goals

- Changing the conversation format (still `list[dict[str, str]]`)
- Altering command parsing logic
- Modifying the `CommandHandler` ABC interface
- Changing navigation behavior or screen transitions

## Decisions

### Decision 1: Conversation Pruning Strategy

**Choice**: Sliding window with configurable limit (default 50 messages)

**Rationale**:
- Simple to implement and understand
- Preserves recent context for AI coherence
- 50 messages = ~25 exchanges, sufficient for most workflows
- Configurable via constant for easy tuning

**Alternatives considered**:
- Token-based pruning: More accurate but adds tokenizer dependency and complexity
- Session-based clearing: Loses context mid-session
- Summarization: Requires AI calls, adds latency and cost

**Implementation**:
```python
MAX_CONVERSATION_HISTORY = 50  # Configurable

def _prune_conversation(self) -> None:
    """Keep only the last MAX_CONVERSATION_HISTORY messages."""
    if len(self._conversation) > MAX_CONVERSATION_HISTORY:
        self._conversation = self._conversation[-MAX_CONVERSATION_HISTORY:]
```

Call `_prune_conversation()` after each append in `_process_message()` and after AI response in `_stream_response()`.

### Decision 2: Handler Module Split

**Choice**: Domain-based package with lazy-loaded registry

**Rationale**:
- Groups related handlers (e.g., all commitment-related commands together)
- Registry pattern maintains single entry point
- Lazy loading prevents circular imports
- Mirrors model package structure for consistency

**Package structure**:
```
commands/
├── __init__.py
├── parser.py           # Existing
├── types.py            # Existing
└── handlers/
    ├── __init__.py     # Registry: get_handler(), _HANDLERS
    ├── base.py         # HandlerResult, CommandHandler ABC
    ├── commitment_handlers.py   # CommitHandler, AtRiskHandler, CleanupHandler, RecoverHandler, AbandonHandler
    ├── goal_handlers.py         # GoalHandler
    ├── task_handlers.py         # TaskHandler, CompleteHandler
    ├── vision_handlers.py       # VisionHandler
    ├── milestone_handlers.py    # MilestoneHandler
    ├── integrity_handlers.py    # IntegrityHandler
    ├── recurring_handlers.py    # RecurringHandler
    ├── utility_handlers.py      # HelpHandler, ShowHandler, ViewHandler, CancelHandler, EditHandler, TypeHandler, HoursHandler, TriageHandler
```

**Handler groupings** (by domain):
| Module | Handlers | Lines (est.) |
|--------|----------|--------------|
| base.py | HandlerResult, CommandHandler | ~50 |
| commitment_handlers.py | Commit, AtRisk, Cleanup, Recover, Abandon | ~500 |
| goal_handlers.py | Goal | ~200 |
| task_handlers.py | Task, Complete | ~250 |
| vision_handlers.py | Vision | ~200 |
| milestone_handlers.py | Milestone | ~150 |
| integrity_handlers.py | Integrity | ~200 |
| recurring_handlers.py | Recurring | ~300 |
| utility_handlers.py | Help, Show, View, Cancel, Edit, Type, Hours, Triage | ~550 |

**Registry pattern**:
```python
# handlers/__init__.py
from jdo.commands.types import CommandType
from jdo.commands.handlers.base import CommandHandler, HandlerResult

_HANDLERS: dict[CommandType, type[CommandHandler]] = {}
_handler_instances: dict[CommandType, CommandHandler] = {}

def _register_handlers() -> None:
    """Lazy registration to avoid circular imports."""
    if _HANDLERS:
        return
    from jdo.commands.handlers.commitment_handlers import (
        CommitHandler, AtRiskHandler, CleanupHandler, RecoverHandler, AbandonHandler
    )
    # ... other imports
    _HANDLERS.update({
        CommandType.COMMIT: CommitHandler,
        # ...
    })

def get_handler(command_type: CommandType) -> CommandHandler:
    _register_handlers()
    if command_type not in _handler_instances:
        handler_class = _HANDLERS.get(command_type)
        if handler_class:
            _handler_instances[command_type] = handler_class()
    return _handler_instances.get(command_type)

__all__ = ["get_handler", "CommandHandler", "HandlerResult"]
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Pruning loses important context | 50 messages is ~25 exchanges; increase if needed |
| Handler split breaks imports | Keep `get_handler()` in same module path; add deprecation re-export if needed |
| Circular imports in handler registry | Lazy registration pattern defers imports |
| Test changes required | Update test imports; registry pattern means minimal test changes |

### Decision 3: Navigation Consolidation

**Choice**: Extract entity-fetching into `NavigationService` and use dispatcher pattern

**Rationale**:
- `on_home_screen_show_goals` and `_nav_to_goals` are near-duplicates (same fetch, same push)
- Entity-to-dict transformations are repeated for each entity type
- A service layer enables testing without UI

**Current duplication** (example from app.py:260-280 and 457-478):
```python
# on_home_screen_show_goals - fetches goals, transforms, pushes screen
# _nav_to_goals - fetches goals, transforms, pushes screen (same code)
```

**Proposed structure**:
```python
# db/navigation.py
class NavigationService:
    """Service for fetching entity lists for navigation."""

    @staticmethod
    def get_goals_list(session: Session) -> list[dict[str, Any]]:
        goals = list(session.exec(select(Goal)).all())
        return [
            {"id": str(g.id), "title": g.title, "status": g.status.value, ...}
            for g in goals
        ]

    @staticmethod
    def get_commitments_list(session: Session) -> list[dict[str, Any]]:
        ...

    @staticmethod
    def get_integrity_data(session: Session) -> dict[str, Any]:
        """Fetch integrity dashboard metrics."""
        ...

    # Similar for: visions, milestones, orphans, hierarchy
```

**App.py consolidation** (aligned with add-navigation-sidebar):
```python
# After add-navigation-sidebar: HomeScreen handlers deprecated
# NavSidebar.Selected is the primary navigation mechanism

def _navigate_to_view(self, view_id: str) -> None:
    """Navigate to view, updating DataPanel or pushing screen."""
    fetchers = {
        "goal": NavigationService.get_goals_list,
        "commitment": NavigationService.get_commitments_list,
        "vision": NavigationService.get_visions_list,
        "milestone": NavigationService.get_milestones_list,
        "orphan": NavigationService.get_orphans_list,
        "integrity": NavigationService.get_integrity_data,
    }
    if view_id == "settings":
        self.push_screen(SettingsScreen())
        return
    fetcher = fetchers.get(view_id)
    if not fetcher:
        return
    with get_session() as session:
        data = fetcher(session)
    # Update DataPanel instead of pushing screen (per add-navigation-sidebar)
    self._update_data_panel(view_id, data)

def on_nav_sidebar_selected(self, message: NavSidebar.Selected) -> None:
    self._navigate_to_view(message.item_id)
```

**Estimated reduction**: ~290 lines → ~100 lines in app.py

**Alignment with add-navigation-sidebar**:
- HomeScreen handlers (`on_home_screen_show_*`) are deprecated by add-navigation-sidebar
- Navigation is now primarily through `NavSidebar.Selected` messages
- This refactor consolidates the remaining navigation logic into a single dispatcher

## Migration Plan

1. **Phase 1: Conversation pruning** (low risk, immediate value)
   - Add pruning method and constant
   - Call after each append
   - No breaking changes

2. **Phase 2: Handler split** (medium risk, high maintainability value)
   - Create `handlers/` package with `base.py`
   - Move handlers one domain at a time, starting with smallest (milestone)
   - Update imports in `chat.py` and tests
   - Delete original `handlers.py` only after all handlers migrated

3. **Phase 3: Navigation consolidation** (low risk, moderate value)
   - Create `db/navigation.py` with `NavigationService`
   - Add `_navigate_to_entity_list()` dispatcher to app.py
   - Refactor message handlers to use dispatcher
   - Delete duplicate `_nav_to_*` methods

4. **Verification**
   - Run full test suite after each domain migration
   - Verify `get_handler()` returns correct instances
   - Check no regressions in command routing
   - Verify navigation behavior unchanged

## Alignment with Other Changes

This change is designed to execute AFTER:

1. **add-navigation-sidebar** (14/17 tasks)
   - Establishes NavSidebar as primary navigation mechanism
   - Deprecates HomeScreen `on_home_screen_show_*` handlers
   - Defines MainScreen with embedded widgets

2. **add-integrity-protocol** (95/121 tasks)
   - Creates integrity handlers in handlers.py: IntegrityHandler, AtRiskHandler, CleanupHandler, RecoverHandler, AbandonHandler
   - Adds integrity display to NavSidebar header
   - Uses sidebar item for integrity access

This refactor then:
- Moves integrity handlers to their final modular locations
- Consolidates NavSidebar navigation into a clean dispatcher pattern
- Skips deprecated HomeScreen handler refactoring (already handled)

## Open Questions

None - design is straightforward refactoring with no architectural decisions pending.
