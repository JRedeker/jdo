# output-formatting Specification

## Purpose
Define the Rich library output formatters for displaying JDO entities (commitments, goals, visions, milestones, tasks), integrity dashboard, confirmation proposals, triage items, error messages, and progress indicators in the terminal.
## Requirements
### Requirement: Commitment List Formatting

The system SHALL format commitment lists as Rich Tables.

#### Scenario: Display active commitments table
- **GIVEN** user has requested commitment list
- **WHEN** AI shows list of commitments
- **THEN** a table displays with columns: ID, Deliverable, Stakeholder, Due, Status
- **AND** rows are sorted by due date (soonest first)
- **AND** overdue items are highlighted in warning color

#### Scenario: Status color coding
- **GIVEN** a commitment is being displayed
- **WHEN** displaying commitment status
- **THEN** status uses colors: pending=default, in_progress=blue, completed=green, at_risk=yellow, abandoned=red

#### Scenario: Empty list message
- **GIVEN** user has requested commitment list
- **WHEN** no commitments exist
- **THEN** a friendly message is shown: "No commitments yet. Tell me what you need to do."

### Requirement: Goal List Formatting

The system SHALL format goal lists as Rich Tables.

#### Scenario: Display goals table
- **GIVEN** user has requested goal list
- **WHEN** AI shows list of goals
- **THEN** a table displays with columns: ID, Title, Status, Commitments
- **AND** commitment count shows active/total

#### Scenario: Goal hierarchy indicator
- **GIVEN** a goal is being displayed
- **WHEN** goal is linked to a vision
- **THEN** vision link is indicated in output

### Requirement: Vision List Formatting

The system SHALL format vision lists as Rich Tables.

#### Scenario: Display visions table
- **GIVEN** user has requested vision list
- **WHEN** AI shows list of visions
- **THEN** a table displays with columns: ID, Title, Timeframe, Status, Goals
- **AND** goal count shows linked goals

### Requirement: Entity Detail Formatting

The system SHALL format individual entity details with Rich Panels or structured text.

#### Scenario: Commitment detail view
- **GIVEN** user has requested commitment details
- **WHEN** AI shows a single commitment
- **THEN** display shows: Deliverable, Stakeholder, Due Date, Status, Goal (if linked), Tasks (if any)
- **AND** formatting uses indentation and labels for clarity

#### Scenario: Goal detail view
- **GIVEN** user has requested goal details
- **WHEN** AI shows a single goal
- **THEN** display shows: Title, Problem Statement, Status, Vision (if linked), Milestones, Commitments

#### Scenario: Vision detail view
- **GIVEN** user has requested vision details
- **WHEN** AI shows a single vision
- **THEN** display shows: Title, Narrative, Timeframe, Metrics, Status, Review Date, Goals

### Requirement: Integrity Dashboard Formatting

The system SHALL format the integrity dashboard with Rich components.

#### Scenario: Display integrity grade prominently
- **GIVEN** user has requested integrity dashboard
- **WHEN** AI shows integrity dashboard
- **THEN** letter grade is displayed large and colored
- **AND** grade color follows: A=green, B=blue, C=yellow, D/F=red

#### Scenario: Display integrity metrics
- **GIVEN** user has requested integrity dashboard
- **WHEN** AI shows integrity dashboard
- **THEN** metrics display: On-time delivery %, Notification timeliness, Cleanup completion %, Streak

#### Scenario: Empty history message
- **GIVEN** user has requested integrity dashboard
- **WHEN** no commitment history exists
- **THEN** message shows "Starting with a clean slate. Your actions will build your integrity score."

### Requirement: Confirmation Proposal Formatting

The system SHALL format confirmation proposals clearly.

#### Scenario: Commitment creation proposal
- **GIVEN** user has expressed intent to create a commitment
- **WHEN** AI proposes creating a commitment
- **THEN** proposal shows clearly labeled fields:
  ```
  Creating Commitment:
    Deliverable: [value]
    Stakeholder: [value]
    Due: [date]
    Goal: [optional]
  
  Does this look right?
  ```

#### Scenario: Entity modification proposal
- **GIVEN** user has expressed intent to modify an entity
- **WHEN** AI proposes modifying an entity
- **THEN** both old and new values are shown for changed fields
- **AND** unchanged fields may be omitted

#### Scenario: Deletion confirmation
- **GIVEN** user has expressed intent to delete an entity
- **WHEN** AI proposes deleting an entity
- **THEN** warning styling is used
- **AND** entity details are shown for verification

### Requirement: Triage Item Formatting

The system SHALL format triage items for processing.

#### Scenario: Display triage item
- **GIVEN** user is processing triage queue
- **WHEN** processing triage queue
- **THEN** item shows: original text, AI analysis, suggested type, confidence

#### Scenario: Display triage progress
- **GIVEN** user is processing multiple triage items
- **WHEN** processing multiple triage items
- **THEN** progress indicator shows "Item X of Y"

### Requirement: Error Formatting

The system SHALL format errors consistently.

#### Scenario: Display validation error
- **GIVEN** user has submitted invalid input
- **WHEN** a validation error occurs
- **THEN** error is displayed with warning styling
- **AND** specific field/issue is identified

#### Scenario: Display system error
- **GIVEN** user is interacting with the system
- **WHEN** a system error occurs
- **THEN** user-friendly message is shown
- **AND** technical details are logged (not shown to user)

### Requirement: Progress Indicators

The system SHALL show progress for long-running operations.

<!-- Research: console.status() is correct for spinner; must stop before Live starts -->
<!-- Source: https://rich.readthedocs.io/en/latest/reference/status.html -->

#### Scenario: AI thinking indicator with spinner
- **WHEN** waiting for AI response before streaming begins
- **THEN** an animated spinner is shown using `console.status()` with "Thinking..." text
- **AND** spinner uses "dots" animation style
- **AND** `status.stop()` is called BEFORE Rich `Live` display starts
- **AND** streaming then uses Rich `Live` display for flicker-free updates

#### Scenario: Database operation indicator
- **GIVEN** a bulk database operation is in progress
- **WHEN** performing database operations (rare, but for bulk)
- **THEN** progress is indicated if operation is slow

### Requirement: Milestone List Formatting

The system SHALL format milestone lists as Rich Tables.

#### Scenario: Display milestones table
- **GIVEN** user requests milestone list
- **WHEN** AI shows list of milestones
- **THEN** a table displays with columns: ID, Title, Target Date, Goal, Status
- **AND** rows are sorted by target date (soonest first)

#### Scenario: Milestone status color coding
- **WHEN** displaying milestone status
- **THEN** status uses colors: pending=default, in_progress=blue, completed=green, missed=red

#### Scenario: Empty milestones message
- **GIVEN** user requests milestone list
- **WHEN** no milestones exist
- **THEN** a friendly message is shown: "No milestones yet. Milestones help break goals into achievable chunks."

### Requirement: Task List Formatting

The system SHALL format task lists as Rich Tables.

#### Scenario: Display tasks table
- **GIVEN** user requests task list
- **WHEN** AI shows list of tasks
- **THEN** a table displays with columns: ID, Title, Status, Estimated Hours, Commitment
- **AND** rows are grouped by commitment if multiple commitments

#### Scenario: Task status color coding
- **WHEN** displaying task status
- **THEN** status uses colors: pending=default, in_progress=blue, completed=green, blocked=yellow

#### Scenario: Empty tasks message
- **GIVEN** user requests task list
- **WHEN** no tasks exist
- **THEN** a friendly message is shown: "No tasks yet. Tasks break down commitments into actionable steps."

### Requirement: Rounded Table Borders

The system SHALL use rounded box borders for all Rich Tables.

#### Scenario: Commitment table with rounded borders
- **GIVEN** user requests commitment list
- **WHEN** table is rendered
- **THEN** table uses `box.ROUNDED` style with curved corners

#### Scenario: Consistent rounded style across all tables
- **GIVEN** any entity list is displayed (goals, visions, milestones, tasks)
- **WHEN** table is rendered
- **THEN** all tables use the same `box.ROUNDED` style for visual consistency

#### Scenario: Non-list tables excluded from rounded style
- **GIVEN** a metrics or inline display table is rendered (e.g., integrity dashboard)
- **WHEN** table is used for compact data display, not entity lists
- **THEN** table may use `box=None` or other appropriate style
- **AND** rounded style only applies to entity list tables

### Requirement: Goals Progress Panel

The system SHALL provide a goals panel showing active goals with visual progress indicators.

#### Scenario: Display goals panel
- **GIVEN** user has active goals
- **WHEN** dashboard is rendered in full mode
- **THEN** panel shows active goals with progress bars
- **AND** panel has fixed width of 100 characters
- **AND** panel title shows "🎯 Goals (N active)" format

#### Scenario: Goal row with fixed columns
- **GIVEN** a goal is displayed in the panel
- **WHEN** row is rendered
- **THEN** row uses fixed-width columns for consistent alignment:
  - Column 1: Title (40 chars, left-aligned, truncate with ...)
  - Column 2: Progress bar (20 chars, using █ and ░ characters)
  - Column 3: Percentage (6 chars, right-aligned, e.g., "  80%")
  - Column 4: Status (18 chars, right-aligned, e.g., "3/4 done", "review ⚠")
- **AND** columns are separated by consistent spacing

#### Scenario: Progress bar coloring
- **GIVEN** goal progress is being rendered
- **WHEN** progress bar is displayed
- **THEN** bar uses green style for >= 80% progress
- **AND** bar uses yellow style for 50-79% progress
- **AND** bar uses red style for < 50% progress

#### Scenario: Goal needing review indicator
- **GIVEN** a goal is due for review
- **WHEN** displayed in panel
- **THEN** status text shows "review due" instead of completion fraction

### Requirement: Status Bar Panel

The system SHALL provide a compact status bar showing integrity, streak, and triage information.

#### Scenario: Display status bar with fixed columns
- **GIVEN** dashboard is being rendered
- **WHEN** status bar is displayed
- **THEN** bar uses 3 fixed-width sections of 32 chars each separated by │:
  - Section 1: Integrity with grade, score, trend arrow (📊)
  - Section 2: Streak in weeks (🔥)
  - Section 3: Triage count (📥)
- **AND** bar has fixed width of 100 characters
- **AND** sections are evenly spaced within the 96-char content area

#### Scenario: Integrity grade coloring
- **GIVEN** integrity grade is displayed
- **WHEN** grade is rendered
- **THEN** A grades use green styling
- **AND** B grades use blue styling
- **AND** C grades use yellow styling
- **AND** D and F grades use red styling

#### Scenario: Trend arrow display
- **GIVEN** integrity trend is available
- **WHEN** displayed in status bar
- **THEN** improving trend shows ↑ in green
- **AND** declining trend shows ↓ in red
- **AND** stable trend shows → in dim

### Requirement: Dashboard Assembly

The system SHALL assemble panels into a cohesive dashboard based on display level.

#### Scenario: Full display mode
- **GIVEN** user has 3+ commitments AND 1+ active goals
- **WHEN** dashboard is rendered
- **THEN** shows commitments panel, goals panel, and status bar stacked vertically

#### Scenario: Standard display mode
- **GIVEN** user has 3+ commitments but no active goals
- **WHEN** dashboard is rendered
- **THEN** shows commitments panel and status bar only

#### Scenario: Compact display mode
- **GIVEN** user has 1-2 commitments
- **WHEN** dashboard is rendered
- **THEN** shows merged panel with commitments and status bar separated by horizontal rule

#### Scenario: Minimal display mode
- **GIVEN** user has no active commitments or goals
- **WHEN** dashboard is rendered
- **THEN** shows status bar only

### Requirement: Column Alignment Utilities

The system SHALL provide alignment functions for consistent column formatting.

#### Scenario: Left-align text within column
- **GIVEN** text shorter than column width
- **WHEN** `_align_left(text, width)` is called
- **THEN** returns text padded with spaces on the right

#### Scenario: Left-align with truncation
- **GIVEN** text longer than column width
- **WHEN** `_align_left(text, width)` is called
- **THEN** returns text truncated to (width - 3) chars plus "..."

#### Scenario: Right-align text within column
- **GIVEN** text shorter than column width
- **WHEN** `_align_right(text, width)` is called
- **THEN** returns text padded with spaces on the left

#### Scenario: Right-align with truncation
- **GIVEN** text longer than column width
- **WHEN** `_align_right(text, width)` is called
- **THEN** returns "..." plus last (width - 3) chars of text

### Requirement: Consistent Right-Edge Alignment

The system SHALL pad all content lines to exact width for consistent right-edge alignment.

#### Scenario: Pad short line to full width
- **GIVEN** a content line shorter than CONTENT_WIDTH (96 chars)
- **WHEN** `_pad_line(content)` is called
- **THEN** returns content padded with spaces to exactly 96 chars

#### Scenario: Truncate long line to full width
- **GIVEN** a content line longer than CONTENT_WIDTH
- **WHEN** `_pad_line(content)` is called
- **THEN** returns content truncated to exactly 96 chars

#### Scenario: All panel rows have consistent width
- **GIVEN** a panel is being rendered with multiple rows
- **WHEN** rows are assembled
- **THEN** every row is padded to exactly CONTENT_WIDTH
- **AND** all right borders align vertically

### Requirement: Progress Bar Formatting

The system SHALL format progress as a visual bar using Unicode block characters.

#### Scenario: Full progress bar
- **GIVEN** progress is 100%
- **WHEN** bar is rendered with width 16
- **THEN** returns "████████████████" (16 full blocks)

#### Scenario: Partial progress bar
- **GIVEN** progress is 50%
- **WHEN** bar is rendered with width 16
- **THEN** returns "████████░░░░░░░░" (8 full, 8 empty)

#### Scenario: Empty progress bar
- **GIVEN** progress is 0%
- **WHEN** bar is rendered with width 16
- **THEN** returns "░░░░░░░░░░░░░░░░" (16 empty blocks)

### Requirement: IntegrityService Dashboard Integration

The system SHALL integrate with IntegrityService to display real-time integrity metrics in the dashboard status bar.

#### Scenario: Fetch integrity metrics on dashboard cache update
- **GIVEN** dashboard cache is being refreshed
- **WHEN** `_update_dashboard_cache()` is called in the REPL loop
- **THEN** system calls `IntegrityService.calculate_integrity_metrics_with_trends()`
- **AND** extracts `letter_grade`, `composite_score`, `overall_trend`, and `current_streak_weeks`
- **AND** stores values in session cache fields

#### Scenario: Display live integrity grade in status bar
- **GIVEN** integrity metrics have been fetched from IntegrityService
- **WHEN** status bar is rendered
- **THEN** displays the actual letter grade (A+, B-, etc.) instead of placeholder
- **AND** displays the actual composite score (0-100)
- **AND** displays the actual trend arrow based on `overall_trend`

#### Scenario: Handle new user with no commitment history
- **GIVEN** user has no completed commitments
- **WHEN** IntegrityService calculates metrics
- **THEN** metrics default to perfect scores (100%, grade A+)
- **AND** trend shows as stable (→)
- **AND** streak shows as 0 weeks

#### Scenario: Handle IntegrityService calculation errors gracefully
- **GIVEN** IntegrityService encounters a database error during calculation
- **WHEN** `_update_dashboard_cache()` catches the exception
- **THEN** logs the error for debugging
- **AND** uses fallback values (empty grade, score 0, stable trend, 0 streak)
- **AND** dashboard continues to render without crashing

#### Scenario: Map TrendDirection enum to display string
- **GIVEN** IntegrityService returns `TrendDirection.UP`, `DOWN`, or `STABLE`
- **WHEN** storing in session cache
- **THEN** converts enum to lowercase string: "up", "down", or "stable"
- **AND** status bar formatter uses string to select arrow and color

### Requirement: Commitment Summary Panel

The system SHALL provide a compact summary panel for displaying commitment status at a glance using Rich Panel with visual styling.

<!-- Research: box.ROUNDED produces rounded corners (╭╮╰╯); box.SIMPLE has NO borders -->
<!-- Source: Rich box.py source, https://rich.readthedocs.io/en/stable/appendix/box.html -->

#### Scenario: Display summary with active commitments
- **GIVEN** user has active commitments
- **WHEN** summary panel is rendered
- **THEN** panel shows total active count with emoji indicator (📋)
- **AND** panel shows at-risk/overdue count with warning styling if > 0
- **AND** panel shows next due item with truncated deliverable and relative date
- **AND** panel uses `Panel.fit()` for content-sized width

#### Scenario: Summary panel color coding
- **GIVEN** summary panel is being rendered
- **WHEN** there are at-risk commitments
- **THEN** at-risk count is displayed in `bold yellow` with ⚠️ emoji
- **AND** overdue items are displayed in `bold red` with ❗ emoji
- **AND** normal counts use `bold cyan` for values, `dim` for labels
- **AND** next due deliverable uses `cyan` styling

#### Scenario: Next due item truncation
- **GIVEN** user has commitments with long deliverables
- **WHEN** showing next due item in summary
- **THEN** deliverable is truncated to ~20 characters with ellipsis
- **AND** due date is shown as relative using `format_relative_date()`:
  - "Today" for same day
  - "Tomorrow" for next day
  - Weekday name ("Fri", "Mon") for 2-6 days out
  - "in X days" for 7+ days out

#### Scenario: No commitments returns nothing
- **GIVEN** user has no active commitments
- **WHEN** summary panel would be rendered
- **THEN** formatter returns None
- **AND** no panel is displayed

#### Scenario: Summary panel styling
- **GIVEN** summary panel is being rendered
- **WHEN** panel is displayed
- **THEN** panel uses `box.ROUNDED` for rounded corners (╭─╮╰─╯)
- **AND** panel uses `border_style="dim"` for subtle border
- **AND** panel uses `padding=(0, 1)` for minimal internal spacing
- **AND** panel content uses `Text.assemble()` for inline styled segments

### Requirement: Relative Date Formatting

The system SHALL format dates as human-friendly relative strings for compact displays.

<!-- Research: humanize.naturalday() returns "Jun 05" not weekday names; custom ~15 lines preferred -->
<!-- Source: PyPI humanize docs, https://pypi.org/project/humanize/ -->

#### Scenario: Format today's date
- **GIVEN** a date that is today
- **WHEN** `format_relative_date()` is called
- **THEN** returns "Today"

#### Scenario: Format tomorrow's date
- **GIVEN** a date that is tomorrow
- **WHEN** `format_relative_date()` is called
- **THEN** returns "Tomorrow"

#### Scenario: Format same-week date
- **GIVEN** a date 2-6 days in the future
- **WHEN** `format_relative_date()` is called
- **THEN** returns abbreviated weekday name (e.g., "Fri", "Mon", "Wed")

#### Scenario: Format future date beyond week
- **GIVEN** a date 7+ days in the future
- **WHEN** `format_relative_date()` is called
- **THEN** returns "in X days" format (e.g., "in 10 days")

#### Scenario: Format past date fallback
- **GIVEN** a date in the past
- **WHEN** `format_relative_date()` is called
- **THEN** returns ISO format "YYYY-MM-DD" as fallback

## Cross-Cutting Concerns

### Performance

> **Note**: Output formatting performance is not a concern for this change. Rich Tables render sub-millisecond for typical data sizes (<1000 rows). No caching or optimization needed.

### Accessibility

> **Note**: Rich library handles terminal accessibility (color contrast, screen reader support via semantic output). No additional accessibility work needed for initial release.
