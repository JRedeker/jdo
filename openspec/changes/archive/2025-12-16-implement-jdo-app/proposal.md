# Change: Implement JDO App Shell

## Why

The TUI components (screens, widgets, handlers) have been built and tested in isolation, but the main `JdoApp` class remains a placeholder stub. The `add-tui-core` change established the Screen architecture (HomeScreen, ChatScreen, SettingsScreen are now proper Screen subclasses), but they are not wired into the application entry point. Key features still need implementation:

- Full end-to-end creation flows
- Draft restore on app restart
- Vision review prompts on startup
- Screen navigation between Home, Chat, and Settings

The current `app.py` displays only "Welcome to JDO!" and doesn't use any of the built components.

## What Changes

- **ADDED** `jdo-app` capability spec: Application shell that integrates all screens and manages lifecycle
- **MODIFIED** `src/jdo/app.py`: Replace stub with fully functional JdoApp that:
  - Registers screens in SCREENS dict for name-based navigation
  - Initializes database on startup
  - Handles screen navigation messages from child screens
  - Restores pending drafts on startup
  - Prompts for vision reviews when due
  - Manages global application state

### Key Design Decisions

1. **Screen-based architecture**: Screens are already Screen subclasses (via `add-tui-core`); use `push_screen`/`pop_screen` for navigation
2. **Message-based navigation**: Child screens post messages (e.g., `HomeScreen.NewChat`), app handles routing
3. **Startup initialization**: Database creation, draft restoration, review prompts happen in `on_mount`
4. **State management**: App holds session-level state (snoozed reviews, current context)

## Impact

- Affected specs:
  - `jdo-app` (ADDED - new capability for application shell)
  - `tui-core` (no changes - Screen architecture already established)
  - `tui-views` (no changes - already defines screen requirements)
  - `tui-chat` (no changes - already defines chat requirements)
- Affected code:
  - `src/jdo/app.py` - Complete rewrite
  - `tests/tui/test_app.py` - Enable skipped tests, add new tests
- Enables:
  - 5 currently skipped tests in `test_app.py`
  - Deferred end-to-end integration tasks
