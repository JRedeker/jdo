# Change: Add TUI Core Architecture Specification

## Why

The JDO TUI components (`HomeScreen`, `ChatScreen`, `SettingsScreen`) were implemented as Textual `Widget` subclasses instead of `Screen` subclasses. This is **not idiomatic** per Textual documentation:

- **Screens** represent full-screen views that participate in the navigation stack (`push_screen`/`pop_screen`)
- **Widgets** are reusable components that compose within screens

The current architecture requires workarounds for navigation and doesn't leverage Textual's built-in screen management. This change establishes a formal `tui-core` specification defining:

1. The distinction between Screens and Widgets
2. Proper navigation patterns using Textual's screen stack
3. Message-based communication between components
4. Modal dialog patterns using `ModalScreen`

## What Changes

- **ADDED** `tui-core` capability spec: Foundational TUI architecture patterns
- **MODIFIED** `src/jdo/screens/home.py`: Refactor `HomeScreen(Widget)` → `HomeScreen(Screen)`
- **MODIFIED** `src/jdo/screens/chat.py`: Refactor `ChatScreen(Widget)` → `ChatScreen(Screen)`
- **MODIFIED** `src/jdo/screens/settings.py`: Refactor `SettingsScreen(Widget)` → `SettingsScreen(Screen)`
- **MODIFIED** Test fixtures to use proper Screen-based testing patterns

### Key Architecture Decisions

1. **Screen subclasses for navigation targets**: Any view that can be navigated to via `push_screen()` must be a `Screen` subclass
2. **Widget subclasses for composable components**: Reusable UI elements like `DataPanel`, `ChatContainer`, `PromptInput` remain as Widgets
3. **ModalScreen for dialogs**: Centered modal dialogs use `ModalScreen` with `align: center middle` CSS
4. **Message bubbling**: Child widgets communicate with parent screens/app via `post_message()`
5. **Screen registration**: App registers screens in `SCREENS` dict for name-based navigation

## Impact

- Affected specs:
  - `tui-core` (ADDED - new foundational architecture spec)
  - `tui-views` (unchanged - requirements still valid, implementation changes)
  - `tui-chat` (unchanged - requirements still valid, implementation changes)
- Affected code:
  - `src/jdo/screens/home.py` - Widget → Screen refactor
  - `src/jdo/screens/chat.py` - Widget → Screen refactor
  - `src/jdo/screens/settings.py` - Widget → Screen refactor
  - `tests/tui/test_home_screen.py` - Update test fixtures
  - `tests/tui/test_chat_screen.py` - Update test fixtures
  - `tests/tui/test_settings_screen.py` - Update test fixtures
  - `tests/integration/tui/test_flows.py` - Update test fixtures
- Relationship to other changes:
  - **Prerequisite for** `implement-jdo-app`: App shell requires proper Screen subclasses
  - **No conflict with** existing TUI specs: This adds architecture layer, doesn't change requirements
