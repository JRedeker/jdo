# Design: Enhanced Dashboard Panels

## Context

Users want more visibility into their commitments, goals, and integrity metrics without running explicit commands. The current single-line summary panel is too minimal.

## Goals / Non-Goals

**Goals:**
- Show multiple commitments at once with rich status information
- Display goal progress with visual progress bars
- Surface integrity score, streak, and triage count
- Maintain consistent 80-character width across all panels
- Support different display densities based on data volume

**Non-Goals:**
- Full-screen TUI dashboard (rejected due to AI streaming complexity)
- Interactive/selectable panels (this is display-only)
- Real-time updates during AI responses

## Architecture

### New Module: `src/jdo/output/dashboard.py`

Centralizes dashboard panel assembly, keeping formatters.py focused on individual entity formatting.

```python
# dashboard.py structure
DASHBOARD_WIDTH = 80

def format_commitments_panel(commitments: list[dict], width: int = DASHBOARD_WIDTH) -> Panel
def format_goals_panel(goals: list[dict], width: int = DASHBOARD_WIDTH) -> Panel
def format_status_bar(integrity: dict, triage_count: int, width: int = DASHBOARD_WIDTH) -> Panel
def format_dashboard(data: DashboardData) -> Group | None
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          REPL Loop                                       │
│                                                                         │
│  1. User completes action                                               │
│  2. Call _update_dashboard_cache(session, db_session)                   │
│  3. Call _show_dashboard(session)                                       │
│  4. Display prompt                                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       Session Cache                                      │
│                                                                         │
│  cached_commitments: list[dict]     # Up to 5 upcoming                  │
│  cached_goals: list[dict]           # Active goals with progress        │
│  cached_integrity: dict             # Grade, score, streak              │
│  cached_triage_count: int           # Queue size                        │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       Dashboard Formatter                                │
│                                                                         │
│  format_dashboard(data) → Group of Panels                               │
│    - Determines display level (minimal/compact/standard/full)           │
│    - Assembles appropriate panels                                       │
│    - Returns Rich Group for console.print()                             │
└─────────────────────────────────────────────────────────────────────────┘
```

### Display Level Logic

```python
def _determine_display_level(data: DashboardData) -> DisplayLevel:
    commitment_count = len(data.commitments)
    goal_count = len(data.goals)
    
    if commitment_count == 0 and goal_count == 0:
        return DisplayLevel.MINIMAL  # Status bar only
    elif commitment_count <= 2:
        return DisplayLevel.COMPACT  # Merged commitments + status
    elif goal_count == 0:
        return DisplayLevel.STANDARD  # Commitments + status bar
    else:
        return DisplayLevel.FULL  # All panels
```

## Visual Layout Specification

### Panel Anatomy (80 chars)

```
╭─ TITLE ──────────────────────────────────────────────────────────────────────╮
│                                                                              │
│  CONTENT LINE 1                                                              │
│  CONTENT LINE 2                                                              │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

- Border uses 2 characters (left + right): `│` + `│`
- Internal padding: 2 spaces each side
- Content area: 74 characters (80 - 6)

### Implementation: Table.grid() + Panel

Rich's `Table.grid()` handles column alignment automatically, eliminating manual padding issues.
Wrap the grid in a `Panel` for consistent borders.

**Key insight**: Don't manually calculate column widths and padding. Let Rich do it.

```python
from rich.table import Table
from rich.panel import Panel
from rich import box

DASHBOARD_WIDTH = 100

def format_commitments_panel(commitments: list[dict]) -> Panel:
    """Format commitments using Table.grid for automatic alignment."""
    
    # Grid handles column alignment automatically
    grid = Table.grid(padding=(0, 2), expand=True)
    grid.add_column("icon", width=1)
    grid.add_column("deliverable", ratio=2)  # ratio=2 means take more space
    grid.add_column("stakeholder", width=18)
    grid.add_column("due", width=18, justify="right")
    
    for c in commitments:
        icon_style = {
            "overdue": "[red]●[/]",
            "at_risk": "[yellow]●[/]",
            "in_progress": "[blue]●[/]",
            "completed": "[green]●[/]",
            "pending": "[dim]○[/]",
        }.get(c["status"], "[dim]○[/]")
        
        due_style = f"[red]{c['due']}[/]" if c.get("is_overdue") else c["due"]
        
        grid.add_row(icon_style, c["deliverable"], c["stakeholder"], due_style)
    
    return Panel(
        grid,
        title="[bold]📋 Commitments (N active, M at-risk)[/]",
        title_align="left",
        box=box.ROUNDED,
        width=DASHBOARD_WIDTH,
        padding=(1, 2),
    )


def format_goals_panel(goals: list[dict]) -> Panel:
    """Format goals with progress bars using Table.grid."""
    
    grid = Table.grid(padding=(0, 2), expand=True)
    grid.add_column("title", ratio=2)
    grid.add_column("progress", width=20)
    grid.add_column("percent", width=6, justify="right")
    grid.add_column("status", width=12, justify="right")
    
    for g in goals:
        # Build progress bar
        bar = format_progress_bar(g["progress_percent"], width=20)
        percent = f"{int(g['progress_percent'] * 100)}%"
        
        grid.add_row(g["title"], bar, percent, g["status_text"])
    
    return Panel(
        grid,
        title="[bold]🎯 Goals (N active)[/]",
        title_align="left",
        box=box.ROUNDED,
        width=DASHBOARD_WIDTH,
        padding=(1, 2),
    )


def format_status_bar(integrity: dict, streak_weeks: int, triage_count: int) -> Panel:
    """Format status bar with 3 centered sections."""
    
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="center", ratio=1)
    
    # Integrity with trend arrow
    grade = integrity["grade"]
    score = integrity["score"]
    trend = {"up": "[green]↑[/]", "down": "[red]↓[/]", "stable": "[dim]→[/]"}[integrity["trend"]]
    grade_color = {"A": "green", "B": "blue", "C": "yellow"}.get(grade[0], "red")
    
    grid.add_row(
        f"📊 Integrity: [{grade_color}]{grade}[/] ({score}%) {trend}",
        f"🔥 Streak: {streak_weeks} weeks",
        f"📥 Triage: {triage_count}",
    )
    
    return Panel(
        grid,
        box=box.ROUNDED,
        width=DASHBOARD_WIDTH,
        padding=(0, 2),
    )


def format_progress_bar(percent: float, width: int = 20) -> str:
    """Create colored progress bar."""
    filled = int(percent * width)
    empty = width - filled
    
    # Color based on progress
    if percent >= 0.8:
        color = "green"
    elif percent >= 0.5:
        color = "yellow"
    else:
        color = "red"
    
    return f"[{color}]{'█' * filled}[/][dim]{'░' * empty}[/]"
```

### Why Table.grid() Works

1. **Automatic column sizing**: `ratio=2` means "take proportionally more space"
2. **Automatic alignment**: `justify="right"` handles right-alignment
3. **expand=True**: Grid expands to fill panel width
4. **padding=(0, 2)**: Adds consistent spacing between columns
5. **No manual character counting**: Rich handles Unicode widths internally

### Status Icons (Unicode, single-width)

Using `●` (BLACK CIRCLE) and `○` (WHITE CIRCLE) instead of emoji:
- Guaranteed 1-character width
- Colorable via Rich markup: `[red]●[/]`
- Works on all terminals

| Status | Icon | Markup |
|--------|------|--------|
| Overdue | ● | `[red]●[/]` |
| At-risk | ● | `[yellow]●[/]` |
| In-progress | ● | `[blue]●[/]` |
| Completed | ● | `[green]●[/]` |
| Pending | ○ | `[dim]○[/]` |
│  🟡  Submit Q1 report                    → Finance      Today 5pm           │
   ^^  ^^^^^^^^^^^^^^^                     ^^^^^^^^^      ^^^^^^^^^^
   │   │                                   │              │
   │   │                                   │              └─ Due (12 chars, right-aligned)
   │   │                                   └─ Stakeholder (14 chars, prefixed with →)
   │   └─ Deliverable (35 chars, truncated with ...)
   └─ Status icon (3 chars: icon + 2 spaces)

Total: 3 + 35 + 2 + 14 + 2 + 12 + 6(padding) = 74
```

### Goal Row Layout (74 chars content)

```
│  Launch MVP                              ████████████░░░░  80%   3/4 done   │
   ^^^^^^^^^^                              ^^^^^^^^^^^^^^^^  ^^^   ^^^^^^^^
   │                                       │                 │     │
   │                                       │                 │     └─ Status (10 chars)
   │                                       │                 └─ Percentage (5 chars)
   │                                       └─ Progress bar (16 chars)
   └─ Goal title (30 chars, truncated)

Total: 30 + 4 + 16 + 2 + 5 + 3 + 10 + 4(padding) = 74
```

### Status Bar Layout (74 chars content)

```
│  📊 Integrity: A- (91%) ↑    │    🔥 Streak: 3 weeks    │    📥 Triage: 5   │
   ^^^^^^^^^^^^^^^^^^^^^^^^   ^   ^^^^^^^^^^^^^^^^^^^^   ^   ^^^^^^^^^^^^^^^
   │                          │   │                      │   │
   │                          │   │                      │   └─ Triage section (17 chars)
   │                          │   │                      └─ Separator
   │                          │   └─ Streak section (22 chars)
   │                          └─ Separator
   └─ Integrity section (24 chars)

Separators: │ with surrounding spaces
```

## Component Styling

### Rich Panel Configuration

```python
Panel(
    content,
    title=title,
    title_align="left",
    box=box.ROUNDED,
    border_style="dim",
    width=DASHBOARD_WIDTH,
    padding=(0, 1),  # 1 space horizontal, 0 vertical inside border
)
```

### Progress Bar Implementation

```python
def _format_progress_bar(percent: float, width: int = 16) -> str:
    """Create a progress bar using block characters.
    
    Args:
        percent: 0.0 to 1.0
        width: Total bar width in characters
        
    Returns:
        String like "████████░░░░░░░░"
    """
    filled = int(percent * width)
    empty = width - filled
    return "█" * filled + "░" * empty
```

### Status Icons

```python
# Commitment row status icons (emoji circles for consistency)
STATUS_ICONS = {
    "overdue": "🔴",
    "at_risk": "🟡", 
    "in_progress": "🔵",
    "completed": "🟢",
    "pending": "⚪",
}
icon = STATUS_ICONS.get(status, "⚪")
```

### Color Application

# Progress bar colors
if percent >= 0.8:
    bar_style = "green"
elif percent >= 0.5:
    bar_style = "yellow"
else:
    bar_style = "red"

# Integrity grade colors
grade_colors = {
    "A+": "bold green", "A": "green", "A-": "green",
    "B+": "blue", "B": "blue", "B-": "blue",
    "C+": "yellow", "C": "yellow", "C-": "yellow",
    "D": "red", "F": "bold red",
}
```

## Data Requirements

### Commitment Data (for panel)

```python
@dataclass
class DashboardCommitment:
    deliverable: str        # Truncated to 35 chars
    stakeholder: str        # Truncated to 12 chars
    due_display: str        # "Today 5pm", "Tomorrow", "Fri", "OVERDUE (2d)"
    status: str             # "overdue", "at_risk", "in_progress", "pending"
    is_overdue: bool
    days_overdue: int | None
```

### Goal Data (for panel)

```python
@dataclass
class DashboardGoal:
    title: str              # Truncated to 30 chars
    progress_percent: float # 0.0 to 1.0
    progress_text: str      # "3/4 done", "review due"
    needs_review: bool
```

### Integrity Data (for status bar)

```python
@dataclass
class DashboardIntegrity:
    grade: str              # "A-"
    score: int              # 91
    trend: str              # "↑", "↓", "→"
    streak_weeks: int       # 3
```

## Caching Strategy

### What to Cache

| Field | Update Trigger | Staleness Risk |
|-------|----------------|----------------|
| `commitments` | Create/complete/update | Low - user action triggers |
| `goals` | Goal progress changes | Low - linked to commitments |
| `integrity` | Any commitment change | Low - calculated on demand |
| `triage_count` | Triage add/process | Low - user action triggers |

### Cache Update Points

1. **After commitment creation** (`_confirm_draft`)
2. **After commitment completion** (`_handle_complete`)
3. **After triage processing** (`_handle_triage`)
4. **On REPL startup** (initial load)

## Performance Considerations

### Query Efficiency

- Commitments: Single query with `ORDER BY due_date LIMIT 5`
- Goals: Single query with progress subquery
- Integrity: Existing `IntegrityService.calculate_integrity_metrics()`
- Triage: Existing `get_triage_count()`

### Rendering Cost

- Panel assembly: ~1ms (Rich is fast)
- Console print: ~5ms (terminal I/O)
- Total per display: <10ms (imperceptible)

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Panel too tall (>20 lines) | Limit to 5 commitments, 3 goals |
| Slow on large datasets | Use LIMIT queries, cache results |
| Terminal width < 80 | Panel wraps gracefully (Rich handles) |
| Unicode issues on Windows | Use ASCII fallback for progress bars |

## Open Questions

1. **Should panels be collapsible?** - Defer to future iteration
2. **Should display level be user-configurable?** - Start with auto-detect, add config later
3. **Show completed items?** - No, focus on actionable items only
