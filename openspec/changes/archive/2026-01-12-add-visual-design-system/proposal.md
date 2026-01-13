# Change: Add Visual Design System for TUI

## Why

The current TUI uses functional but visually monotonous styling - all borders are `solid $primary`, backgrounds lack depth, and there's no cohesive design language. Users deserve a polished, professional interface that communicates hierarchy, state, and focus clearly. A defined design system will improve usability, maintainability, and aesthetic appeal while staying strictly within Textual's documented capabilities.

## What Changes

### Theme & Foundation
- **NEW**: Define custom JDO dark and light themes with cohesive color palettes
- **NEW**: Create centralized external CSS file (`app.tcss`) for shared styles with live-reload support
- **NEW**: Add theme-level `variables` for fine-grained control (footer keys, input selection, cursors)

### Visual Hierarchy System
- **NEW**: Establish border hierarchy: `round` (primary), `tall` (secondary), `double` (modal), `heavy` (focus)
- **NEW**: Add background depth system with 4 layers: `$background` < `$surface` < `$surface-lighten-1` < `$panel`
- **NEW**: Create reusable utility classes for status colors, spacing, and states

### Widget Enhancements
- **NEW**: Chat message visual differentiation with colored left-border accents per role
- **NEW**: NavSidebar depth styling with recessed background and active item indicators
- **NEW**: Enhanced focus/hover states across all interactive widgets
- **NEW**: Scrollbar styling to match theme colors
- **NEW**: Loading indicator color customization

### Status & State System
- **NEW**: Consistent status indicator colors (pending, in_progress, completed, at_risk, abandoned)
- **NEW**: Grade color coding system (A=green, B=blue, C=yellow, D/F=red)
- **MODIFIED**: Update existing widget `DEFAULT_CSS` to use new design tokens

## Impact

- Affected specs:
  - `tui-core` - CSS Styling Conventions requirement (MODIFIED)
  - `tui-views` - TUI Design Principles requirement (MODIFIED)
  - NEW `tui-styling` capability for the design system itself

- Affected code:
  - `src/jdo/theme.py` (new) - Theme definitions
  - `src/jdo/app.py` - Theme registration and CSS_PATH
  - `src/jdo/app.tcss` (new) - Centralized stylesheet
  - `src/jdo/widgets/*.py` - Updated DEFAULT_CSS in all widgets (7 files)
  - `src/jdo/screens/*.py` - Updated DEFAULT_CSS in all screens (6 files)
  - `src/jdo/auth/screens.py` - Updated modal styling

- Test files affected:
  - `tests/unit/test_theme.py` (new) - Theme unit tests
  - `tests/tui/test_styling.py` (new) - CSS loading and styling tests
  - `tests/tui/__snapshots__/` - All 13 snapshot files need updates

## Non-Goals

- No behavioral changes - this is purely visual
- No new widgets or screens
- No changes to navigation or data flow
- No animated transitions beyond Textual defaults (loading indicators already exist)
- No external dependencies
- No user-selectable themes beyond dark/light toggle

## Risks

| Risk | Mitigation |
|------|------------|
| Visual regression | Update snapshots after visual review confirms improvements |
| Theme incompatibility with light mode | Define `jdo-light` theme variant with tested colors |
| CSS specificity conflicts | Document precedence rules; use scoped selectors |
| Snapshot test churn | Batch all visual changes; single snapshot update pass |

## Success Criteria

1. All widgets use theme variables (no hardcoded colors except in theme.py)
2. Border styles follow documented hierarchy consistently
3. Focus states are visible on all interactive elements
4. Status colors are semantic and consistent across views
5. Snapshot tests pass with updated baseline
6. Live reload works with `textual run --dev`
