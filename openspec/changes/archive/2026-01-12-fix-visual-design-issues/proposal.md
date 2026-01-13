# Change: Fix Visual Design System Issues

## Why

Code review of the visual design system implementation identified one medium-severity usability issue and three low-severity polish issues that should be addressed to ensure optimal user experience and maintainability.

The most critical issue is that the collapsed sidebar loses visual indication of which navigation item is active, making it difficult for users to understand their current context.

## What Changes

- **Medium Priority**: Fix collapsed sidebar to maintain visual distinction for active navigation items
- **Low Priority**: Update theme toggle binding description from "Toggle Dark Mode" to "Toggle Theme"
- **Low Priority**: Add clarifying comment for CSS file path resolution
- **Low Priority**: Document universal selector performance consideration for future reference

## Impact

- Affected specs: `tui-nav`, `tui-core`
- Affected code: 
  - `src/jdo/widgets/nav_sidebar.py` (collapsed state styling)
  - `src/jdo/app.py` (binding description, CSS path comment)
  - `src/jdo/app.tcss` (potential performance note)
- User experience: Improved navigation feedback in collapsed state
- Technical debt: Better documentation for CSS architecture
