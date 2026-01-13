# Change: Enhance Dashboard Panels

## Why

The current single-line commitment summary panel provides minimal context. Users want to see more information at a glance including:
- Multiple upcoming commitments (not just the next one)
- Goal progress with visual indicators
- Integrity score and streak
- Triage queue status

Research shows that effective CLI dashboards should surface immediate action items, at-risk warnings, and motivational metrics (streaks, progress bars) to help users stay on track.

## What Changes

- **Multi-panel dashboard**: Replace single summary panel with stacked panels showing:
  1. **Commitments Panel**: Up to 5 upcoming commitments with status icons, stakeholders, and relative dates
  2. **Goals Panel**: Active goals with progress bars and completion percentages
  3. **Status Bar**: Compact row with integrity grade, streak, and triage count
- **Consistent 80-character width**: All panels use fixed width for visual alignment
- **Configurable display levels**: Minimal → Compact → Standard → Full based on data volume
- **Rich visual indicators**: Status icons (✓ ⚠ ✗), progress bars (████░░), trend arrows (↑↓→)

## Impact

- Affected specs: `output-formatting`, `cli-interface`
- Affected code:
  - `src/jdo/output/formatters.py` - New panel formatters
  - `src/jdo/output/dashboard.py` - New module for dashboard assembly
  - `src/jdo/repl/loop.py` - Updated display integration
  - `src/jdo/repl/session.py` - Extended caching for goals/integrity
  - `src/jdo/db/session.py` - New queries for goal counts

## Visual Design

Inspired by classic terminal interfaces - using fixed-width columns with consistent alignment.

### Panel Width: 100 characters

Wider panels provide more breathing room and better readability on modern terminals.

```
         1         2         3         4         5         6         7         8         9        10
1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890
```

### Column Layout

**Content area: 96 chars** (100 - 2 border chars - 2 padding)

**Commitment Row Columns:**
```
Col 1: Icon         4 chars   (emoji + 2 spaces)
Col 2: Deliverable 40 chars   (left-aligned, truncate with ...)
Col 3: Stakeholder 20 chars   (left-aligned)
Col 4: Due         20 chars   (right-aligned)
       Spacing     12 chars   (between columns)
                   ────────
                   96 chars
```

**Goal Row Columns:**
```
Col 1: Title       40 chars   (left-aligned, truncate with ...)
Col 2: Progress    20 chars   (progress bar using █░)
Col 3: Percent      6 chars   (right-aligned, e.g., "  80%")
Col 4: Status      18 chars   (right-aligned)
       Spacing     12 chars   (between columns)
                   ────────
                   96 chars
```

### Standard Dashboard (100 characters wide)

Every content line is padded to exactly 96 characters to ensure consistent right-edge alignment.

```
╭─ 📋 Commitments (3 active, 1 at-risk) ───────────────────────────────────────────────────────────╮
│                                                                                                  │
│  🔴  Send invoice to Client                    Client                       OVERDUE (2 days)    │
│  🟡  Submit Q1 report                          Finance                           Today 5:00pm    │
│  ⚪  Review PR #234                             Team                                 Tomorrow    │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ 🎯 Goals (2 active) ────────────────────────────────────────────────────────────────────────────╮
│                                                                                                  │
│  Launch MVP                                    ████████████████░░░░       80%        3/4 done    │
│  Health & Fitness                              ████████████░░░░░░░░       60%        review ⚠    │
│                                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭──────────────────────────────────────────────────────────────────────────────────────────────────╮
│  📊 Integrity: A- (91%) ↑         │         🔥 Streak: 3 weeks         │         📥 Triage: 5    │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Compact Mode (when < 3 commitments)

```
╭─ 📋 Commitments ─────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                  │
│  🟡  Submit Q1 report                          Finance                           Today 5:00pm    │
│  ⚪  Review PR #234                             Team                                 Tomorrow    │
│                                                                                                  │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│  📊 A- (91%) ↑            │            🔥 3 weeks            │            📥 5 in triage         │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### Minimal Mode (no commitments)

```
╭──────────────────────────────────────────────────────────────────────────────────────────────────╮
│  📊 Integrity: A- (91%) ↑         │         🔥 Streak: 3 weeks         │         📥 Triage: 5    │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Design Decisions

### Panel Width: 100 Characters

- Modern terminals easily support 100+ characters
- Provides breathing room for longer deliverables and stakeholder names
- Consistent alignment across all panels
- Falls back gracefully on narrower terminals (Rich handles wrapping)

### Information Hierarchy

| Priority | Element | Rationale |
|----------|---------|-----------|
| 1 | Overdue items (✗ red) | Immediate attention required |
| 2 | At-risk items (⚠ yellow) | Early warning |
| 3 | Due today/tomorrow | Time-sensitive |
| 4 | Integrity grade | Quick health check |
| 5 | Streak | Motivational |
| 6 | Goal progress | Strategic context |
| 7 | Triage count | Pending work indicator |

### Status Icons (Emoji)

| Icon | Meaning | Color |
|------|---------|-------|
| `🔴` | Overdue | red |
| `🟡` | At-risk | yellow |
| `🔵` | In progress | blue |
| `🟢` | Completed | green |
| `⚪` | Pending | dim |

### Progress Bar Characters

```
Full block:  █ (U+2588)
Empty block: ░ (U+2591)
Bar width:   16 characters (granularity of ~6%)
```

### Display Level Thresholds

| Level | Condition | Panels Shown |
|-------|-----------|--------------|
| Minimal | 0 commitments, 0 goals | Status bar only |
| Compact | 1-2 commitments | Commitments + status bar (merged) |
| Standard | 3+ commitments | Commitments + status bar |
| Full | 3+ commitments AND 1+ goals | All three panels |

## Research References

- Nielsen Norman Group: Dashboard UX best practices
- CLI Guidelines (clig.dev): Human-first terminal interfaces
- Rich library documentation: Panel, Table, Progress components
- Todoist/Things/OmniFocus: Task management UX patterns
