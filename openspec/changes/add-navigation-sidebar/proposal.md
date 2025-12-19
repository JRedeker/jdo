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
- **MODIFIED** `tui-core` - simplified screen architecture (MainScreen with embedded widgets)
- **MODIFIED** `jdo-app` - integrate sidebar into main layout
- **MODIFIED** `tui-views` - letter-key shortcuts replaced by sidebar navigation
- **MODIFIED** `tui-chat` - letter-key shortcuts and footer shortcuts updated
- **DEPRECATED** HomeScreen navigation shortcuts (g, c, v, m, h, i, o) - replaced by sidebar

### Key Architectural Decisions

1. **MainScreen layout**: App uses MainScreen with NavSidebar + embedded content widgets
2. **Sidebar always visible**: Docked left, can collapse to icons with `[` key
3. **Content area**: Shows chat/data based on sidebar selection (ChatContainer, PromptInput, DataPanel)
4. **Consistent bindings**: `1-9` for quick nav, `Tab` cycles focus, `Escape` context-aware
5. **ChatScreen embedded**: ChatScreen widgets are composed within MainScreen, not as separate Screen

### Phased Implementation

**Phase 1 (This Change)**:
- NavSidebar widget implementation
- MainScreen with embedded content widgets
- Letter-key shortcuts deprecated (still functional but discouraged)
- Number key shortcuts (1-9) for quick navigation

**Phase 2 (Deferred)**:
- Full HomeScreen removal
- Complete migration of HomeScreen features to MainScreen
- Removal of deprecated letter-key bindings

## Impact

- Affected specs:
  - `tui-nav` (NEW) - Navigation sidebar widget and behavior
  - `tui-core` - Screen architecture changes (MainScreen with embedded widgets)
  - `jdo-app` - Startup, navigation, layout changes
  - `tui-views` - Letter-key shortcuts removed, sidebar navigation added
  - `tui-chat` - Letter-key shortcuts removed, footer shortcuts updated
  - `inbox` - Triage access via sidebar with badge
  - `provider-auth` - Settings access via sidebar
- Affected code:
  - `src/jdo/app.py` - Main app layout
  - `src/jdo/screens/home.py` - Deprecated (not removed in Phase 1)
  - `src/jdo/widgets/nav_sidebar.py` - NEW widget
- **BREAKING**: Letter-key navigation shortcuts (g, c, v, m, h, i, o, t, s) replaced by sidebar navigation and number keys
- Migration: Users will see sidebar immediately; no data migration needed
