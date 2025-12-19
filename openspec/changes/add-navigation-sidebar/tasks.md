# Tasks: Add Navigation Sidebar

## 1. Foundation - NavSidebar Widget (TDD)

- [x] 1.1 Write unit tests for NavSidebar widget
  - Test: Widget renders with expected navigation items
  - Test: Up/down keys navigate items
  - Test: Enter key posts Selected message
  - Test: Collapse toggle changes display mode
  - Test: Number keys (1-9) select items directly
  
- [x] 1.2 Implement NavSidebar widget
  - Create `src/jdo/widgets/nav_sidebar.py`
  - Extend from `Widget`, compose `OptionList`
  - Define ITEMS list with id, label, shortcut
  - Implement Selected message class
  - Add collapse/expand functionality

- [x] 1.3 Add NavSidebar CSS styling
  - Collapsed mode: 3-char width, single letters
  - Expanded mode: full labels (no shortcuts)
  - Active item highlight
  - Separator styling

## 2. Integration - App Layout (TDD)

- [x] 2.1 Write integration tests for sidebar in app
  - Test: Sidebar visible on app startup
  - Test: Sidebar selection changes DataPanel content
  - Test: Settings selection pushes SettingsScreen
  - Test: Sidebar collapse persists during session

- [x] 2.2 Modify JdoApp to include NavSidebar
  - Add NavSidebar to compose()
  - Handle NavSidebar.Selected messages
  - Remove HomeScreen from startup flow
  - Add `[` binding for collapse toggle

- [x] 2.3 Wire sidebar selections to DataPanel
  - Map item IDs to DataPanel modes
  - Query and pass data for list views
  - Handle hierarchy and integrity modes

## 3. Navigation Behavior (TDD)

- [x] 3.1 Write tests for navigation bindings
  - Test: `Tab` cycles focus: sidebar → prompt → panel
  - Test: `Escape` behavior is context-aware
  - Test: `q` quits from any state
  - Test: Arrow / Enter / mouse interactions select items

- [x] 3.2 Implement global navigation bindings
  - Implement focus cycling with Tab
  - Update Escape handling for new layout
  - Ensure mouse/arrow/Enter navigation is wired

- [x] 3.3 Write tests for collapsed mode navigation
  - Test: Arrow keys and Enter work when collapsed
  - Test: Focus management still behaves correctly

## 4. HomeScreen Deprecation (DEFERRED)

**Status**: Deferred to future work. The full layout refactor requires:
- Moving ChatContainer, PromptInput, DataPanel from ChatScreen to JdoApp
- Significant test updates
- AI agent logic migration

For now, NavSidebar widget and handlers are ready for integration.

- [ ] 4.1 Update startup flow
  - App mounts directly to main layout (no HomeScreen push)
  - Preserve draft restoration modal
  - Preserve AI configuration check

- [ ] 4.2 Migrate HomeScreen features to sidebar
  - Triage indicator as badge on sidebar item
  - Integrity grade shown in sidebar header
  - Vision review notification as system message

- [ ] 4.3 Mark HomeScreen as deprecated
  - Add deprecation warning to HomeScreen class
  - Update imports to not expose HomeScreen
  - Keep for backwards compatibility

## 5. Visual Polish (PARTIAL)

- [x] 5.2 Add triage badge support to sidebar
  - NavSidebar.set_triage_count() implemented
  - Badge displays in expanded mode

- [ ] 5.1 Add snapshot tests for sidebar states
  - Expanded state with all items
  - Collapsed state with letters
  - Active item highlighting

## 6. Documentation

- [ ] 6.1 Update tui-core spec with new patterns
- [ ] 6.2 Archive HomeScreen-related requirements
- [ ] 6.3 Update AGENTS.md with navigation info

## Dependencies

- Task 1 must complete before Task 2 (widget needed for integration)
- Task 2 must complete before Task 3 (layout needed for bindings)
- Tasks 4-6 can run in parallel after Task 3

## Validation

After each task group:
```
uv run ruff check --fix src/ tests/
uv run ruff format src/ tests/
uv run pytest tests/tui/ -v
uv run pytest tests/unit/ -v
```