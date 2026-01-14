# Change: Enhance REPL Visual Styling

## Why

The current REPL has a plain input experience - a simple `> ` prompt with minimal visual separation from output, and a bottom toolbar showing stats that aren't immediately actionable. Users would benefit from clearer visual hierarchy, keyboard shortcut discoverability, and a more polished input area.

## What Changes

- Replace bottom toolbar content from stats (`3 active | 0 triage`) to keyboard shortcuts (`F1=Help  F5=Refresh  /c=commit  /l=list  /v=view`)
- Add visual styling to the input prompt area:
  - Bold cyan `>` prompt indicator for strong visual distinction
  - Padding (blank line) above the input area for breathing room
- Use theme-adaptive ANSI colors (no hex codes) to respect user's terminal theme
- Maintain existing functionality - changes are purely cosmetic

## Impact

- Affected specs: `output-formatting` (new requirements for prompt styling and toolbar content)
- Affected code:
  - `src/jdo/repl/loop.py` - `_create_toolbar_callback()`, `_create_prompt_session()`
- No breaking changes - purely visual enhancement
- No database schema changes

## Spec Conflicts

### cli-interface Bottom Toolbar Status Bar

The deployed `cli-interface` spec requires the bottom toolbar to display:
- Commitment count
- Triage queue count
- Pending draft indicator
- Current entity context

This change proposes replacing statistics with keyboard shortcuts.

**Resolution**: The deployed spec describes the *current* implementation. This change
intentionally modifies that behavior. The toolbar will show shortcuts instead of stats
because:
1. Stats are redundant with the dashboard (which shows all this info prominently)
2. Shortcuts improve discoverability of commands
3. The entity context display is preserved when viewing an entity

A follow-up change should update `cli-interface` spec's "Bottom Toolbar Status Bar"
requirement to reflect the new shortcut-based toolbar design.
