# Design: Navigation Sidebar

## Context

JDO is a TUI application built with Textual. Current navigation uses:
- HomeScreen with shortcuts (g, c, v, m, h, i, o, n, s, t, q)
- Each shortcut pushes ChatScreen with different data pre-loaded
- Bindings don't work consistently across screens

This creates discoverability and consistency problems, especially as letter-key shortcuts produce conflicts on certain layouts.

## Goals

- **Discoverable navigation**: Users can see available views without memorization
- **Consistent behavior**: Navigation works the same from any screen
- **Keyboard-first**: Quick navigation via Tab, arrow keys, Enter, mouse clicks, and optional number keys
- **Space-efficient**: Sidebar can collapse to icon-only mode

## Non-Goals

- Touchscreen/mouse-first design
- Nested navigation menus
- Command palette (Ctrl+P style) - may add later
- Breadcrumb navigation

## Decisions

### Decision 1: Replace HomeScreen with persistent sidebar

**What**: Remove HomeScreen as separate screen; integrate navigation into main layout.

**Why**: 
- Eliminates screen transition confusion
- Provides always-visible navigation
- Reduces code complexity (one less screen)

**Alternatives considered**:
- Keep HomeScreen, add sidebar only to ChatScreen - Creates inconsistency
- Add command palette - Less discoverable for new users
- Top tab bar - Uses more vertical space, less TUI-native

### Decision 2: Use OptionList for sidebar

**What**: Implement NavSidebar using Textual's `OptionList` widget.

**Why**:
- Built-in keyboard navigation (up/down, enter)
- Efficient rendering for lists
- Supports separators for grouping
- Can render Rich Text for icons/formatting

**Alternatives considered**:
- Custom widget with Static elements - More code, less functionality
- Tree widget - Overkill for flat navigation
- Button list - Poor keyboard navigation

### Decision 3: Sidebar state stored in App

**What**: App tracks current nav selection and sidebar collapsed state.

**Why**:
- Survives modal screens
- Single source of truth
- Easy to persist to settings later

### Decision 4: Content area uses DataPanel modes

**What**: Sidebar selection triggers DataPanel mode changes, not screen transitions.

**Why**:
- Reuses existing DataPanel infrastructure
- No screen stack complexity
- Instant transitions (no push/pop)

## Architecture

```
JdoApp
├── Header
├── Horizontal (main content)
│   ├── NavSidebar (docked left, collapsible)
│   │   └── OptionList (navigation items)
│   └── Vertical (content area)
│       ├── ChatContainer
│       ├── PromptInput
│       └── DataPanel (hidden when sidebar selection = chat)
└── Footer
```

### NavSidebar Widget

```python
class NavSidebar(Widget):
    """Persistent navigation sidebar."""
    
    ITEMS = [
        ("chat", "Chat", "C"),
        None,                         # Separator
        ("goals", "Goals", "G"),
        ("commitments", "Commitments", "Cm"),
        ("visions", "Visions", "V"),
        ("milestones", "Milestones", "M"),
        None,                         # Separator
        ("hierarchy", "Hierarchy", "H"),
        ("integrity", "Integrity", "I"),
        ("orphans", "Orphans", "O"),
        None,                         # Separator
        ("settings", "Settings", "S"),
    ]
    
    class Selected(Message):
        """Posted when navigation item selected."""
        def __init__(self, item_id: str) -> None:
            self.item_id = item_id
            super().__init__()
```

### Key Bindings

| Key | Action | Scope |
|-----|--------|-------|
| `[` | Toggle sidebar collapse | Global |
| Arrow keys / Enter / Mouse click | Navigate and select sidebar items | Global |
| `Tab` | Cycle focus: sidebar → chat → data panel | Global |
| `Escape` | Context-aware (clear input, unfocus, or quit confirmation) | Global |
| `q` | Quit | Global |

### Navigation Item IDs

| ID | Data Panel Mode | Description |
|----|-----------------|-------------|
| `chat` | Hidden | Default chat-only view |
| `goals` | `list:goal` | Goals list |
| `commitments` | `list:commitment` | Commitments list |
| `visions` | `list:vision` | Visions list |
| `milestones` | `list:milestone` | Milestones list |
| `hierarchy` | `hierarchy` | Full tree view |
| `integrity` | `integrity` | Dashboard |
| `orphans` | `list:commitment` (filtered) | Orphan commitments |
| `settings` | N/A | Push SettingsScreen |

## Risks / Trade-offs

### Risk: Sidebar takes horizontal space
- **Mitigation**: Collapse mode reduces to ~3 chars wide
- **Trade-off**: Acceptable loss of ~15 chars on 80-col terminal

### Risk: Breaking change for existing users
- **Mitigation**: Shortcuts (g, c, v, etc.) still work via sidebar
- **Trade-off**: Small learning curve, but improved long-term UX

### Risk: Testing complexity
- **Mitigation**: TDD approach - tests first, then implementation
- **Trade-off**: More upfront work, but better coverage

## Migration Plan

1. Create NavSidebar widget with tests
2. Integrate into JdoApp layout
3. Wire up navigation messages
4. Deprecate HomeScreen (keep for one release)
5. Remove HomeScreen in next release

## Open Questions

1. Should collapsed sidebar show single-letter shortcuts or icons?
   - **Proposed**: Single letters for consistency with footer
   
2. Should we add triage (t) to sidebar?
   - **Proposed**: Yes, with badge showing count
   
3. Should sidebar remember collapsed state across sessions?
   - **Proposed**: Yes, store in settings
