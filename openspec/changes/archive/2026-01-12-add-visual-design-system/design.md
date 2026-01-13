# Design: Visual Design System

## Context

The JDO TUI currently uses:
- Inline `DEFAULT_CSS` in every widget/screen (13+ files)
- Textual's default theme variables (`$primary`, `$surface`, etc.)
- Uniform `border: solid $primary` everywhere
- Minimal background differentiation
- No external CSS file (no live editing capability)

Textual provides a rich styling system that we're underutilizing. The framework supports:
- Custom themes via `Theme` class with 10+ color variables plus custom `variables` dict
- External `.tcss` files with live reload (`textual run --dev`)
- Multiple border styles: `round`, `heavy`, `tall`, `wide`, `double`, `dashed`, `outer`, `inner`
- Background tints with alpha: `background: $primary 20%`
- Pseudo-class selectors: `:focus`, `:hover`, `.-collapsed`
- Scrollbar color customization (6+ properties)
- CSS variables for design tokens

## Goals

1. **Cohesive visual identity**: Define a recognizable JDO aesthetic
2. **Clear visual hierarchy**: Primary content > secondary > chrome
3. **Improved state communication**: Focus, hover, active, disabled states
4. **Maintainability**: Centralized styles, consistent tokens
5. **Developer experience**: Live CSS editing with `--dev` flag
6. **Testability**: Unit tests for theme, integration tests for CSS loading

## Non-Goals

1. Animated transitions (use Textual's built-in loading indicators)
2. Custom font rendering
3. Image/icon assets
4. Platform-specific styling
5. User-selectable theme library (beyond dark/light)

## Decisions

### Decision 1: Create Custom Theme Module

**What**: Create `src/jdo/theme.py` with `JDO_DARK_THEME` and `JDO_LIGHT_THEME` objects.

**Why**: 
- Separates theme definition from app logic
- Enables unit testing of theme properties
- Provides semantic color variables that adapt to light/dark mode
- Allows fine-grained control via `variables` dict

**Implementation**:
```python
from textual.theme import Theme

JDO_DARK_THEME = Theme(
    name="jdo-dark",
    primary="#5B8DEE",        # Calm blue - trust, stability
    secondary="#7C8FA6",      # Muted steel - secondary actions
    accent="#F5A623",         # Warm amber - attention, CTAs
    foreground="#E8E8E8",     # Light text
    background="#1A1D23",     # Deep dark base
    success="#4CAF50",        # Green - completion, health
    warning="#FFB74D",        # Orange - caution, at-risk
    error="#E57373",          # Soft red - errors, abandoned
    surface="#252932",        # Card/container backgrounds
    panel="#2E333D",          # Panel backgrounds
    dark=True,
    variables={
        "footer-key-foreground": "#5B8DEE",
        "input-selection-background": "#5B8DEE 40%",
        "block-cursor-foreground": "#E8E8E8",
        "block-cursor-text-style": "none",
        "scrollbar-background": "#252932",
        "scrollbar-color": "#5B8DEE 50%",
        "scrollbar-color-hover": "#5B8DEE 80%",
        "scrollbar-color-active": "#F5A623",
    },
)

JDO_LIGHT_THEME = Theme(
    name="jdo-light",
    primary="#3B6BC9",        # Deeper blue for light backgrounds
    secondary="#5A6A7A",
    accent="#D4850F",         # Darker amber
    foreground="#1A1D23",     # Dark text
    background="#F5F5F7",     # Light base
    success="#388E3C",
    warning="#F57C00",
    error="#D32F2F",
    surface="#FFFFFF",
    panel="#EAEAEC",
    dark=False,
    variables={
        "footer-key-foreground": "#3B6BC9",
        "input-selection-background": "#3B6BC9 30%",
        "block-cursor-foreground": "#1A1D23",
        "scrollbar-background": "#EAEAEC",
        "scrollbar-color": "#3B6BC9 40%",
        "scrollbar-color-hover": "#3B6BC9 70%",
        "scrollbar-color-active": "#D4850F",
    },
)
```

**Alternatives considered**:
- Use Textual's built-in themes: Rejected - too generic, no brand identity
- Hardcode colors: Rejected - no light/dark mode support
- Single theme with runtime color swapping: Rejected - Textual's theme system handles this natively

### Decision 2: External CSS File with Widget Overrides

**What**: Create `src/jdo/app.tcss` for shared styles, keep widget-specific `DEFAULT_CSS` for encapsulation.

**Why**: 
- Enables live editing with `textual run --dev`
- Centralizes shared styles (utility classes, base components)
- Widgets retain encapsulated styling for distribution/reuse
- Clear precedence: app.tcss < DEFAULT_CSS < inline styles

**Implementation**:
```python
class JdoApp(App):
    CSS_PATH = "app.tcss"
    
    def __init__(self) -> None:
        super().__init__()
        self.register_theme(JDO_DARK_THEME)
        self.register_theme(JDO_LIGHT_THEME)
        # Theme is auto-selected based on system preference
```

**Trade-off**: Two places to look for styles, but clear separation of concerns.

### Decision 3: Border Hierarchy System

**What**: Define semantic border usage based on widget importance level.

| Level | Element Type | Border Style | Color | Rationale |
|-------|-------------|--------------|-------|-----------|
| 1 | Primary containers | `round` | `$primary` | Modern, prominent |
| 2 | Secondary panels | `tall` | `$surface-lighten-1` | Subtle containment |
| 3 | Focused elements | `heavy` | `$accent` | Strong emphasis |
| 4 | Modal dialogs | `double` | `$accent` | Distinct overlay |
| 5 | Error states | `round` | `$error` | Alert attention |
| 6 | Separators | `dashed` or none | `$surface-lighten-2` | Minimal weight |

**Why**: Creates visual rhythm and communicates hierarchy without relying solely on color. Users can quickly identify element importance.

### Decision 4: Background Depth System

**What**: Use 4-layer background system to create depth perception.

```
Layer 0: $background     - Screen/app base
Layer 1: $surface        - Primary content containers  
Layer 2: $surface-lighten-1 - Raised elements (cards, hover)
Layer 3: $panel          - Distinct panels (sidebar, data panel)
Recessed: $surface-darken-1 - Sunken elements (collapsed areas)
```

**CSS Implementation**:
```css
Screen { background: $background; }
ChatContainer { background: $surface; }
DataPanel { background: $surface; }
NavSidebar { background: $surface-darken-1; }
.card { background: $surface-lighten-1; }
```

**Why**: Creates natural visual grouping. Users perceive related elements as belonging together.

### Decision 5: Focus State Strategy

**What**: Combine border changes with subtle background tints for focus indication.

```css
/* Base focus pattern */
:focus {
    border: heavy $accent;
}

/* Input-specific focus */
PromptInput:focus {
    border: round $accent;
    background-tint: $accent 5%;
}

/* List item focus */
.option-list--option-highlighted {
    background: $primary 20%;
    border-left: heavy $accent;
}
```

**Why**: 
- Border changes provide clear visual indication
- Tints add subtle emphasis without overwhelming
- Combination ensures visibility in all contexts

### Decision 6: Status Color Consistency

**What**: Define semantic status colors used across all entity types.

| Status | Color Variable | Visual Style |
|--------|---------------|--------------|
| pending | `$text-muted` | Dim, low weight |
| in_progress | `$primary` | Active, prominent |
| completed | `$success` | Green, satisfied |
| at_risk | `$warning` | Yellow/orange, bold |
| abandoned | `$error` | Red, distinct |
| draft | `$secondary` | Muted, temporary |

**CSS Classes**:
```css
.status-pending { color: $text-muted; }
.status-in-progress { color: $primary; }
.status-completed { color: $success; }
.status-at-risk { color: $warning; text-style: bold; }
.status-abandoned { color: $error; }
.status-draft { color: $secondary; text-style: italic; }
```

**Why**: Consistent status colors reduce cognitive load. Users learn the meaning once and recognize it everywhere.

### Decision 7: Scrollbar Theming

**What**: Customize scrollbar colors via theme `variables` dict.

**Implementation**:
```python
variables={
    "scrollbar-background": "#252932",
    "scrollbar-color": "#5B8DEE 50%",
    "scrollbar-color-hover": "#5B8DEE 80%",
    "scrollbar-color-active": "#F5A623",
}
```

**Why**: Default scrollbars clash with custom themes. Themed scrollbars complete the polished appearance.

## Component Styling Summary

| Component | Background | Border | Focus State |
|-----------|------------|--------|-------------|
| Screen | `$background` | none | n/a |
| MainScreen content | `$surface` | none | n/a |
| ChatContainer | `$surface` | `round $primary` | n/a |
| ChatMessage.-user | `$surface` | `left: heavy $accent` | n/a |
| ChatMessage.-assistant | `$panel` | `left: heavy $primary` | n/a |
| ChatMessage.-system | `$warning 10%` | `round $warning` | n/a |
| DataPanel | `$surface` | `tall $surface-lighten-1` | n/a |
| NavSidebar | `$surface-darken-1` | `right: tall $surface-lighten-1` | n/a |
| NavSidebar item active | `$primary 20%` | `left: heavy $accent` | same |
| PromptInput | `$surface` | `round $primary` | `round $accent` + tint |
| Modal dialogs | `$surface` | `double $accent` | n/a |
| IntegritySummary | `$surface-darken-1` | `top: solid $primary` | n/a |

## Testing Strategy

### Unit Tests (`tests/unit/test_theme.py`)
- Theme objects have required properties (name, primary, dark)
- Both themes have matching variable keys
- Color values are valid hex codes
- Theme names are unique

### Integration Tests (`tests/tui/test_styling.py`)
- App loads with CSS_PATH set
- Themes are registered on app init
- Theme toggle switches between jdo-dark and jdo-light
- CSS variables resolve correctly

### Snapshot Tests
- All 13 existing snapshots updated with new styling
- Add new snapshots for focus states if needed

## Migration Plan

1. **Phase 1: Foundation** (TDD)
   - Write unit tests for theme module
   - Create `theme.py` with both themes
   - Write tests for CSS loading
   - Create `app.tcss` skeleton
   - Register themes in app.py

2. **Phase 2: Core Widgets** (TDD per widget)
   - For each widget: write style test → update CSS → verify
   - Order: ChatMessage → ChatContainer → PromptInput → NavSidebar → DataPanel → IntegritySummary

3. **Phase 3: Screens** (TDD per screen)
   - MainScreen → SettingsScreen → Modal screens

4. **Phase 4: Utilities & Polish**
   - Add utility classes
   - Update scrollbar styling
   - Final visual review

5. **Phase 5: Snapshots**
   - Run all snapshot tests (expect failures)
   - Visual review of changes
   - Update snapshots in single commit

## Rollback

All changes are additive CSS. To rollback:
1. Remove `CSS_PATH` from JdoApp class
2. Remove theme registration from `__init__`
3. Delete `theme.py` and `app.tcss`
4. Restore original `DEFAULT_CSS` from git history

## Open Questions

1. ~~Should we support user-selectable themes beyond dark/light?~~
   - **Resolved**: No for v1; can extend later

2. ~~Should status colors be configurable?~~
   - **Resolved**: No; semantic colors should be consistent

3. Should we add a theme preview command?
   - **Resolved**: Not in scope; use `textual colors` for now
