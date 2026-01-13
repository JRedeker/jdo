# Tasks: Enhance Dashboard Panels

## 1. Create Dashboard Module

- [x] 1.1 Create `src/jdo/output/dashboard.py` with constants:
  - `DASHBOARD_WIDTH = 100`
  - `MAX_COMMITMENTS = 5`
  - `MAX_GOALS = 3`
  - `PROGRESS_BAR_WIDTH = 20`
  - `STATUS_ICONS` dict mapping status to colored Unicode circles

- [x] 1.2 Add `DisplayLevel` enum:
  - `MINIMAL` - status bar only
  - `COMPACT` - merged commitments + status
  - `STANDARD` - commitments + status bar
  - `FULL` - all three panels

- [x] 1.3 Add data classes for dashboard data:
  - `DashboardCommitment` - deliverable, stakeholder, due_display, status
  - `DashboardGoal` - title, progress_percent, progress_text, needs_review
  - `DashboardIntegrity` - grade, score, trend, streak_weeks
  - `DashboardData` - commitments, goals, integrity, triage_count

## 2. Implement Panel Formatters (using Table.grid())

- [x] 2.1 Add `format_progress_bar(percent: float, width: int = 20) -> str`:
  - Returns string of █ and ░ characters with color styling
  - Handles edge cases (0%, 100%, negative, >100%)
  - Colors: green (>=80%), yellow (>=50%), red (<50%)

- [x] 2.2 Add `format_commitments_panel(commitments, active_count, at_risk_count) -> Panel`:
  - Uses Table.grid() for automatic column alignment
  - Applies status-based icons (● colored, ○ pending)
  - Shows overdue in red

- [x] 2.3 Add `format_goals_panel(goals, active_count) -> Panel`:
  - Uses Table.grid() with progress bars
  - Shows review warning indicator for goals needing review

- [x] 2.4 Add `format_status_bar(integrity, triage_count) -> Panel`:
  - 3-column centered layout using Table.grid()
  - Shows integrity grade, streak, and triage count
  - Color-coded trend arrows

- [x] 2.5 Add `format_dashboard(data: DashboardData) -> Group | None`:
  - Determines display level based on data
  - Assembles appropriate panels into Rich Group
  - Returns None if nothing to display

## 3. Add Database Queries

- [x] 3.1 Add `get_dashboard_commitments(db_session, limit: int = 5) -> list[dict]`:
  - Queries active commitments ordered by due_date
  - Includes stakeholder name, calculates overdue status
  - Formats due date as relative string

- [x] 3.2 Add `get_dashboard_goals(db_session, limit: int = 3) -> list[dict]`:
  - Queries active goals with progress calculation
  - Includes review due status
  - Calculates completion percentage from linked commitments

- [x] 3.3 Integrate IntegrityService for dashboard integrity metrics:
  - Calls `IntegrityService.calculate_integrity_metrics_with_trends()`
  - Extracts `letter_grade`, `composite_score`, `overall_trend`, `current_streak_weeks`
  - Handles errors gracefully with fallback values
  - Maps `TrendDirection` enum to string for status bar display

## 4. Extend Session Caching

- [x] 4.1 Add new fields to `Session` class:
  - `cached_dashboard_commitments: list[dict[str, Any]] = []`
  - `cached_dashboard_goals: list[dict[str, Any]] = []`
  - `cached_integrity_grade: str = ""`
  - `cached_integrity_score: int = 0`
  - `cached_integrity_trend: str = "stable"`
  - `cached_streak_weeks: int = 0`

- [x] 4.2 Add `DashboardCacheUpdate` dataclass

- [x] 4.3 Add `update_dashboard_cache(update: DashboardCacheUpdate)` method to Session

## 5. Integrate into REPL Loop

- [x] 5.1 Add `_build_dashboard_data(session: Session) -> DashboardData`:
  - Assembles data from session cache fields
  - Converts dicts to dataclasses
  - Returns structured data for formatter

- [x] 5.2 Replace `_update_session_summary_cache()` with `_update_dashboard_cache()`:
  - Fetches all dashboard data from database
  - Updates all cache fields

- [x] 5.3 Replace `_show_commitment_summary()` with `_show_dashboard()`:
  - Builds dashboard data from cache
  - Calls format_dashboard()
  - Prints result if not None

- [x] 5.4 Update cache refresh points:
  - After commitment create/complete
  - On REPL startup

## 6. Testing

- [x] 6.1 Unit tests for `format_progress_bar()`:
  - 0%, 50%, 100% cases
  - Edge cases (negative, >100%)
  - Color thresholds

- [x] 6.2 Unit tests for panel formatters:
  - Empty list returns appropriate panel
  - Styling applied correctly
  - Title includes counts

- [x] 6.3 Unit tests for `format_dashboard()`:
  - Each display level produces correct output
  - Returns None when appropriate

- [x] 6.4 Unit tests for display level selection:
  - All threshold conditions

- [x] 6.5 Unit tests for data classes:
  - Default values work correctly

## 7. Validation

- [x] 7.1 Run lint/format: `uv run ruff check --fix src/ tests/ && uv run ruff format src/ tests/`
- [x] 7.2 Run type check: `uvx pyrefly check src/`
- [x] 7.3 Run tests: `uv run pytest` - 1598 tests pass
- [ ] 7.4 Manual testing: verify panel appearance in REPL at each display level
