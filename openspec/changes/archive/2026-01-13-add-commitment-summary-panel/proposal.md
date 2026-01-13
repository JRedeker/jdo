# Change: Add Commitment Summary Panel

## Why

Users lose context of their active commitments while using the REPL. Currently, the only way to see commitments is via `/list`, which interrupts the conversational flow. Showing a compact summary panel before each prompt keeps users informed of their current obligations without requiring explicit queries.

## What Changes

- **New formatter**: Create a compact commitment summary panel that shows:
  - Count of active commitments with status breakdown
  - Next upcoming due item (if any)
  - At-risk/overdue count (highlighted)
- **REPL integration**: Display the summary panel above the prompt after each command completion
- **Session caching**: Leverage existing cached counts; extend to cache "next due" commitment for performance

## Impact

- Affected specs: `output-formatting`, `cli-interface`
- Affected code:
  - `src/jdo/output/formatters.py` - New summary panel formatter
  - `src/jdo/repl/loop.py` - Display panel before prompt
  - `src/jdo/repl/session.py` - Optional: cache next-due commitment

## Design Notes

This is Option 3 from the visual enhancement research: **simple sequential printing** rather than Rich Layout/Live complexity. The approach:

1. Print a compact panel after each command completes (before the next prompt)
2. No `Live` context management needed - just `console.print()`
3. User perceives it as "always visible" because it appears at a consistent location
4. Minimal changes to existing architecture - no prompt_toolkit modifications

Alternative considered: Rich Layout + Live for true persistent display. Rejected due to:
- Complex integration with prompt_toolkit async input
- Previous project experience showed Textual/TUI frameworks difficult to integrate with AI streaming
- Marginal UX benefit doesn't justify complexity

## Research Validation

✅ **Validated**: Simple `console.print(Panel(...))` is correct for REPL - Layout/Live are for full-screen TUI apps  
✅ **Validated**: prompt_toolkit + Rich are compatible; 70+ existing uses in codebase prove this  
✅ **Validated**: Custom relative date formatter (~15 lines) preferred over adding humanize dependency  
⚠️ **Updated**: Box style changed from `box.SIMPLE` to `box.ROUNDED` (SIMPLE has no borders)

## Visual Design

### Panel Styling Options

Using Rich's visual capabilities for an informative, attractive summary:

**Option A: Minimal with emoji indicators**
```
╭─ 📋 Commitments ─────────────────────────╮
│ 3 active (⚠️ 1 at-risk)  Next: Report → Fri │
╰──────────────────────────────────────────╯
```

**Option B: Color-coded status circles**
```
╭─ Commitments ────────────────────────────╮
│ 🟢 2 on-track  🟡 1 at-risk  → Report Fri │
╰──────────────────────────────────────────╯
```

**Option C: Compact with arrow separator**
```
╭────────────────────────────────────────────╮
│ 📋 3 active (1 ⚠️)  │  Next: Report → Fri  │
╰────────────────────────────────────────────╯
```

### Rich Styling Implementation

```python
from rich.panel import Panel
from rich.text import Text
from rich import box

content = Text.assemble(
    ("📋 ", ""),
    ("3", "bold"),
    (" active ", "dim"),
    ("(", "dim"),
    ("1", "bold yellow"),
    (" ⚠️)", ""),
    ("  │  ", "dim"),
    ("Next: ", "dim"),
    ("Report", "cyan"),
    (" → ", "dim"),
    ("Fri", "bold cyan"),
)

panel = Panel.fit(
    content,
    box=box.ROUNDED,
    border_style="dim",
    padding=(0, 1),
)
```

### Color Semantics (consistent with existing codebase)

| Status | Color | Emoji |
|--------|-------|-------|
| On-track/Active | `cyan` / `green` | 🟢 ✓ |
| At-risk | `yellow` | 🟡 ⚠️ |
| Overdue | `red` | 🔴 ❗ |
| Completed | `green` | ✅ |
| Labels/Secondary | `dim` | - |

### Relative Date Formatting

Custom ~15-line function (libraries don't match exact format needed):

| Days Until | Display |
|------------|---------|
| 0 | "Today" |
| 1 | "Tomorrow" |
| 2-6 | Weekday name ("Fri", "Mon") |
| 7+ | "in X days" |
| Past | "YYYY-MM-DD" (fallback) |
