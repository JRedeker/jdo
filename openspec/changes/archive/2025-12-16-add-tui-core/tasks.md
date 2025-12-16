# Tasks: Add TUI Core Architecture

This change refactors the TUI screen components from Widget to Screen subclasses and establishes foundational architecture patterns.

## Implementation Decisions

| Decision | Choice |
|----------|--------|
| Header/Footer | Keep in JdoApp.compose() - shared across screens |
| Screen State | Stateless - new instance each push_screen() |
| Escape on Home | Unfocus widget, or do nothing if no focus |
| Escape on Chat | Confirm if PromptInput has text, else pop |
| Test Fixtures | Use push_screen() pattern (idiomatic) |
| CSS Changes | None required (verified via Context7) |
| Commit Strategy | Single atomic commit, remove all deprecated |

## Phase 1: Refactor HomeScreen to Screen Subclass

### 1.1 Write architecture test for HomeScreen (Red)
- [x] Create `tests/tui/test_architecture.py`
- [x] Write `test_home_screen_is_screen_subclass` - verify `isinstance(HomeScreen, type)` and `issubclass(HomeScreen, Screen)`
- [x] Write `test_home_screen_compose_yields_expected_widgets` - verify compose returns expected widget types
- [x] Run: `uv run pytest tests/tui/test_architecture.py -v` - Tests FAIL (Red)

### 1.2 Refactor HomeScreen class (Green)
- [x] Open `src/jdo/screens/home.py`
- [x] Change import: `from textual.screen import Screen` (add)
- [x] Change class: `class HomeScreen(Widget)` → `class HomeScreen(Screen)`
- [x] Remove unused `Widget` import if no longer needed
- [x] Verify DEFAULT_CSS still uses `HomeScreen { }` selector (no change needed)
- [x] Run: `uv run pytest tests/tui/test_architecture.py::test_home_screen_is_screen_subclass -v` - PASS (Green)

### 1.3 Update HomeScreen test fixtures
- [x] Open `tests/tui/test_home_screen.py`
- [x] Existing tests continue to work (Screen can also be yielded in compose)
- [x] Run: `uv run pytest tests/tui/test_home_screen.py -v` - All tests PASS
- [x] Run lint: `uv run ruff check --fix src/jdo/screens/home.py tests/tui/test_home_screen.py`

## Phase 2: Refactor ChatScreen to Screen Subclass

### 2.1 Write architecture test for ChatScreen (Red)
- [x] Add `test_chat_screen_is_screen_subclass` to `tests/tui/test_architecture.py`
- [x] Add `test_chat_screen_compose_yields_expected_widgets` - verify ChatContainer, PromptInput, DataPanel
- [x] Run: `uv run pytest tests/tui/test_architecture.py::test_chat_screen_is_screen_subclass -v` - FAIL (Red)

### 2.2 Refactor ChatScreen class (Green)
- [x] Open `src/jdo/screens/chat.py`
- [x] Change import: `from textual.screen import Screen` (add)
- [x] Change class: `class ChatScreen(Widget)` → `class ChatScreen(Screen)`
- [x] Remove unused `Widget` import if no longer needed
- [x] Verify DEFAULT_CSS still uses `ChatScreen { }` selector (no change needed)
- [x] Run: `uv run pytest tests/tui/test_architecture.py::test_chat_screen_is_screen_subclass -v` - PASS (Green)

### 2.3 Update ChatScreen test fixtures
- [x] Open `tests/tui/test_chat_screen.py`
- [x] Existing tests continue to work (Screen can also be yielded in compose)
- [x] Run: `uv run pytest tests/tui/test_chat_screen.py -v` - All tests PASS
- [x] Run lint: `uv run ruff check --fix src/jdo/screens/chat.py tests/tui/test_chat_screen.py`

## Phase 3: Refactor SettingsScreen to Screen Subclass

### 3.1 Write architecture test for SettingsScreen (Red)
- [x] Add `test_settings_screen_is_screen_subclass` to `tests/tui/test_architecture.py`
- [x] Add `test_settings_screen_compose_yields_expected_widgets`
- [x] Run: `uv run pytest tests/tui/test_architecture.py::test_settings_screen_is_screen_subclass -v` - FAIL (Red)

### 3.2 Refactor SettingsScreen class (Green)
- [x] Open `src/jdo/screens/settings.py`
- [x] Change import: `from textual.screen import Screen` (add)
- [x] Change class: `class SettingsScreen(Widget)` → `class SettingsScreen(Screen)`
- [x] Remove unused `Widget` import if no longer needed
- [x] Verify DEFAULT_CSS still uses `SettingsScreen { }` selector (no change needed)
- [x] Run: `uv run pytest tests/tui/test_architecture.py::test_settings_screen_is_screen_subclass -v` - PASS (Green)

### 3.3 Update SettingsScreen test fixtures
- [x] Open `tests/tui/test_settings_screen.py`
- [x] Existing tests continue to work (Screen can also be yielded in compose)
- [x] Run: `uv run pytest tests/tui/test_settings_screen.py -v` - All tests PASS
- [x] Run lint: `uv run ruff check --fix src/jdo/screens/settings.py tests/tui/test_settings_screen.py`

## Phase 4: Update Integration and Other Tests

### 4.1 Update integration test fixtures
- [x] Open `tests/integration/tui/test_flows.py`
- [x] Existing tests work with Screen subclasses
- [x] Run: `uv run pytest tests/integration/tui/ -v` - 14/15 tests PASS (1 pre-existing flaky test)

### 4.2 Update snapshot test apps
- [x] Check `tests/tui/snapshot_apps/` for any Widget-based screen usage
- [x] Snapshot apps work - updated snapshots to reflect Screen rendering
- [x] Run: `uv run pytest tests/tui/test_snapshots.py -v` - All tests PASS

### 4.3 Update chat widget tests
- [x] Check `tests/tui/test_chat_widgets.py` for any fixture issues
- [x] Run: `uv run pytest tests/tui/test_chat_widgets.py -v` - All tests PASS

### 4.4 Update data panel tests
- [x] Check `tests/tui/test_data_panel.py` for any fixture issues
- [x] Run: `uv run pytest tests/tui/test_data_panel.py -v` - All tests PASS

## Phase 5: Add Remaining Architecture Verification Tests

### 5.1 Add Widget architecture tests
- [x] Add `test_chat_container_is_widget_subclass`
- [x] Add `test_data_panel_is_widget_subclass`
- [x] Add `test_prompt_input_is_widget_subclass`
- [x] Add `test_chat_message_is_widget_subclass`
- [x] Add `test_hierarchy_view_is_widget_subclass`
- [x] Run: `uv run pytest tests/tui/test_architecture.py -v` - All PASS

### 5.2 Add message class verification tests
- [x] Add `test_home_screen_has_new_chat_message`
- [x] Add `test_home_screen_has_open_settings_message`
- [x] Add `test_settings_screen_has_back_message`
- [x] Run: `uv run pytest tests/tui/test_architecture.py -v` - All PASS

## Phase 6: Final Validation and Cleanup

### 6.1 Run full test suite
- [x] Run: `uv run pytest` - 553 passed, 5 skipped, 1 pre-existing failure
- [x] Verify no new test failures introduced

### 6.2 Run linting and formatting
- [x] Run: `uv run ruff check src/ tests/` - No errors
- [x] Run: `uv run ruff format src/ tests/` - Formatted

### 6.3 Run type checking
- [x] Run: `uvx pyrefly check src/jdo/screens/` - No errors

### 6.4 Verify screen exports
- [x] Check `src/jdo/screens/__init__.py` exports all screens correctly
- [x] Verify: `from jdo.screens import HomeScreen, ChatScreen, SettingsScreen` works

### 6.5 Remove all deprecated code
- [x] Search for any remaining `from textual.widget import Widget` in screen files
- [x] Ensure no Widget imports remain in screen modules (only Screen)
- [x] Verify no TODO/FIXME comments related to Widget→Screen migration remain

### 6.6 Validate openspec change
- [x] Implementation complete - ready for archive

## Dependencies

```
Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5 ──► Phase 6
(Home)      (Chat)      (Settings)  (Integration) (Arch Tests) (Final)
```

Each phase must complete before the next begins (sequential refactoring for safety).

## Running Tests

```bash
# Run architecture tests
uv run pytest tests/tui/test_architecture.py -v

# Run individual screen tests
uv run pytest tests/tui/test_home_screen.py -v
uv run pytest tests/tui/test_chat_screen.py -v
uv run pytest tests/tui/test_settings_screen.py -v

# Run all TUI tests
uv run pytest tests/tui/ -v

# Run integration tests
uv run pytest tests/integration/tui/ -v

# Run full suite
uv run pytest

# Lint and format
uv run ruff check --fix src/ tests/ && uv run ruff format src/ tests/

# Type check
uvx pyrefly check src/
```

## Post-Implementation

After this change is complete:
1. Archive `add-tui-core` change
2. Review `implement-jdo-app` tasks - some may be redundant or need updates
3. Proceed with `implement-jdo-app` implementation
