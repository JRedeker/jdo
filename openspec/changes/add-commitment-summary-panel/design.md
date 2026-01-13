# Design: Commitment Summary Panel

## Context

Users lose context of their active commitments while using the REPL. This design adds a compact visual summary that appears before each prompt.

## Goals / Non-Goals

**Goals:**
- Keep users informed of commitment status without explicit queries
- Minimal visual noise - compact, single-line where possible
- Consistent with existing Rich styling patterns
- No interruption to conversational flow

**Non-Goals:**
- Full-screen dashboard (use `/list` for detailed view)
- Real-time updates during AI streaming
- Persistent display that doesn't scroll away

## Research Findings

### Rich Panel vs Layout/Live

**Decision:** Use `Panel.fit()` with `console.print()` - NOT Layout/Live

**Rationale:**
- Rich Layout is explicitly for "full-screen applications" per Rich docs
- Rich Live is for animated/updating displays, not static output
- Panel with sequential print is the correct pattern for REPLs
- Already proven by 70+ existing `console.print()` calls in codebase

**Sources:**
- Rich Panel docs: https://rich.readthedocs.io/en/stable/panel.html
- Rich Live docs: https://rich.readthedocs.io/en/stable/live.html
- Rich Layout docs: https://rich.readthedocs.io/en/stable/layout.html

### Box Style Selection

**Decision:** Use `box.ROUNDED` for rounded corners (╭─╮╰─╯)

**Rationale:**
- `box.SIMPLE` has NO visible borders - only horizontal separator lines
- `box.ROUNDED` produces the rounded corner aesthetic from the visual concept
- Consistent with existing tables in codebase that use `box.ROUNDED`

**Available box styles:**
| Style | Appearance | Best For |
|-------|------------|----------|
| `ROUNDED` | ╭─╮╰─╯ | Modern, friendly UI ✓ |
| `SQUARE` | ┌─┐└─┘ | Classic, structured |
| `DOUBLE` | ╔═╗╚═╝ | Emphasis |
| `HEAVY` | ┏━┓┗━┛ | Strong emphasis |
| `MINIMAL` | Light lines | Clean, minimal |
| `SIMPLE` | Horizontal only | NO visible border |

**Source:** Rich box.py source code

### Relative Date Formatting

**Decision:** Custom ~15-line implementation, not external library

**Rationale:**
- `humanize.naturalday()` returns "Jun 05" format, not weekday names
- `arrow.humanize()` outputs "in 3 days" but not "Fri" for same-week dates
- Exact format needed: "Today", "Tomorrow", "Fri", "in X days"
- Adding 132KB dependency for single function is overkill
- Custom implementation is easy to test and maintain

**Implementation:**
```python
def format_relative_date(d: date, today: date | None = None) -> str:
    today = today or date.today()
    delta = (d - today).days
    if delta == 0:
        return "Today"
    if delta == 1:
        return "Tomorrow"
    if 2 <= delta <= 6:
        return d.strftime("%a")  # Mon, Tue, etc.
    if delta > 6:
        return f"in {delta} days"
    return d.strftime("%Y-%m-%d")  # Past dates: fallback
```

**Source:** PyPI humanize, arrow, pendulum docs

### Session Caching Strategy

**Decision:** Keep existing caching pattern with rate-limited updates

**Rationale:**
- SQLite queries are fast (~0.01ms) but toolbar callback runs every keystroke
- Existing pattern caches `commitment_count` and `triage_count`
- Extend to cache `at_risk_count` and `next_due` info
- Update cache only when commitments change (create/complete)

**Trade-off accepted:**
- Cache may be stale if DB modified externally
- Acceptable for single-user CLI app
- Simplifies implementation vs rate-limited live queries

**Source:** prompt_toolkit bottom_toolbar docs, SQLite isolation docs

## Decisions

### Panel Content Structure

Using `Text.assemble()` for inline styled segments:

```python
content = Text.assemble(
    ("📋 ", ""),           # Clipboard emoji
    ("3", "bold"),          # Count in bold
    (" active ", "dim"),    # Label dimmed
    ("(", "dim"),
    ("1", "bold yellow"),   # At-risk count in yellow
    (" ⚠️)", ""),           # Warning emoji
    ("  │  ", "dim"),       # Separator
    ("Next: ", "dim"),      # Label dimmed
    ("Report", "cyan"),     # Deliverable in cyan
    (" → ", "dim"),         # Arrow separator
    ("Fri", "bold cyan"),   # Date in bold cyan
)
```

### Color Semantics

Consistent with existing codebase patterns:

| Status | Color | Emoji |
|--------|-------|-------|
| Active/Normal | `cyan` / `bold` | 📋 |
| At-risk | `bold yellow` | ⚠️ 🟡 |
| Overdue | `bold red` | ❗ 🔴 |
| Labels | `dim` | - |
| Success | `green` | ✅ 🟢 |

### Panel Styling

```python
Panel.fit(
    content,
    box=box.ROUNDED,      # Rounded corners
    border_style="dim",   # Subtle border
    padding=(0, 1),       # Minimal padding
)
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Panel adds visual noise | Use `border_style="dim"` for subtle appearance |
| Cache staleness from external changes | Acceptable for single-user CLI; `/list` shows live data |
| Emoji rendering on older terminals | Emoji are informational only; text is primary |

## Open Questions

1. **Should panel appear after EVERY command or only commitment-related ones?**
   - Current decision: After every command for consistent positioning
   - Can revisit if users find it noisy

2. **What if terminal is narrow?**
   - `Panel.fit()` will wrap content
   - Could add `max_width` parameter if needed
