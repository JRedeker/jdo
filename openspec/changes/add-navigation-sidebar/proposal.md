# Change: Add Navigation Sidebar

## Why

Current navigation relies on memorized keyboard shortcuts (g, c, v, m, h, i, o) that:
1. Conflict across screens - bindings on HomeScreen behave differently on ChatScreen
2. Lack visual discoverability - users must memorize shortcuts
3. Create confusing flow - HomeScreen pushes ChatScreen with different data views

This creates a poor user experience, especially for new users who can't discover available navigation options.

## What Changes

- **ADDED** `NavSidebar` widget - persistent, collapsible navigation sidebar
- **ADDED** `tui-nav` capability - dedicated spec for navigation patterns
- **MODIFIED** `tui-core` - simplified screen architecture (single main screen)
- **MODIFIED** `jdo-app` - integrate sidebar, remove HomeScreen as entry point
- **REMOVED** HomeScreen navigation shortcuts (g, c, v, m, h, i, o) - replaced by sidebar

### Key Architectural Decisions

1. **Single main layout**: App starts directly on main screen with sidebar + content area
2. **Sidebar always visible**: Docked left, can collapse to icons with `[` key
3. **Content area**: Shows chat/data based on sidebar selection
4. **Consistent bindings**: `1-9` for quick nav, `Tab` cycles focus, `Escape` context-aware

## Impact

- Affected specs:
  - `tui-nav` (NEW) - Navigation sidebar widget and behavior
  - `tui-core` - Screen architecture changes (MainScreen replaces HomeScreen)
  - `jdo-app` - Startup, navigation, layout changes
  - `tui-views` - Home Screen requirement updated for sidebar
  - `tui-chat` - Keyboard navigation and integrity display updates
  - `inbox` - Triage access via sidebar
  - `provider-auth` - Settings access via sidebar
- Affected code:
  - `src/jdo/app.py` - Main app layout
  - `src/jdo/screens/home.py` - Deprecated/removed
  - `src/jdo/widgets/nav_sidebar.py` - NEW widget
- **BREAKING**: HomeScreen shortcuts (g, c, v, m, h, i, o, t, s) replaced by sidebar navigation
- Migration: Users will see sidebar immediately; no data migration needed
