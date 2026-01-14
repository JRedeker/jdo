# output-formatting Specification

## Purpose
Define the Rich library output formatters for displaying JDO entities (commitments, goals, visions, milestones, tasks), integrity dashboard, confirmation proposals, triage items, error messages, and progress indicators in the terminal.
## Requirements
### Requirement: Commitment List Formatting

The system SHALL format commitment lists as Rich Tables with explicit selection shortcuts.

#### Scenario: Display active commitments table
- **GIVEN** user has requested commitment list
- **WHEN** AI shows list of commitments
- **THEN** a table displays with columns: Shortcut, ID, Deliverable, Stakeholder, Due, Status
- **AND** Shortcut column shows: `[/1]`, `[/2]`, etc.
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

#### Scenario: List footer with hints
- **GIVEN** commitment list is displayed
- **WHEN** list has items
- **THEN** footer shows: "Use /1, /2, etc. to view details, or /help for more commands"

### Requirement: Goal List Formatting

The system SHALL format goal lists as Rich Tables with explicit selection shortcuts.

#### Scenario: Display goals table
- **GIVEN** user has requested goal list
- **WHEN** AI shows list of goals
- **THEN** a table displays with columns: Shortcut, ID, Title, Status, Commitments
- **AND** Shortcut column shows: `[/1]`, `[/2]`, etc.
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

### Requirement: Onboarding Screen Formatting

The system SHALL format onboarding and "What's New" screens using Rich Panels.

#### Scenario: Format first-run onboarding
- **GIVEN** user starts JDO for the first time
- **WHEN** onboarding screen is formatted
- **THEN** Rich Panel displays with:
  - Title: "Welcome to JDO"
  - Subtitle: version number
  - Body: Brief explanation of purpose + key commands
  - Footer: "Press Enter to continue"
- **AND** uses ROUNDED box style

#### Scenario: Format "What's New" screen
- **GIVEN** new version has features to announce
- **WHEN** what's new screen is formatted
- **THEN** Rich Panel displays with:
  - Title: "What's New in v[version]"
  - Body: Bullet list of new features
  - Footer: "Press Enter to continue"
- **AND** new features use highlight styling

#### Scenario: Onboarding screen testable in isolation
- **GIVEN** test needs to verify onboarding output
- **WHEN** formatter is called with version and feature list
- **THEN** returns Rich Panel object (not printed)
- **AND** panel content can be inspected programmatically

### Requirement: Help Text Formatting

The system SHALL format help text with categories, examples, and visual styling.

#### Scenario: Format categorized help
- **GIVEN** `/help` is invoked
- **WHEN** help text is formatted
- **THEN** commands are grouped under bold category headers
- **AND** each command shows: name, abbreviation (if any), brief description
- **AND** format uses Rich Table for alignment

#### Scenario: Format command-specific help
- **GIVEN** `/help commit` is invoked
- **WHEN** detailed help is formatted
- **THEN** Panel displays:
  - Command name and abbreviation
  - Usage syntax
  - Description
  - Examples with expected output
  - Related commands
- **AND** examples use code styling

#### Scenario: Format shortcuts section
- **GIVEN** help text includes shortcuts
- **WHEN** shortcuts section is formatted
- **THEN** displays table: `/c` -> `/commit`, `/l` -> `/list`, etc.
- **AND** keyboard shortcuts listed: Ctrl+L (clear), F5 (refresh), F1 (help)

### Requirement: Numbered List Formatting with Explicit Shortcuts

The system SHALL format lists with explicit shortcut numbers for navigation. Uses `/1`, `/2` syntax for unambiguous selection per POLA.

#### Scenario: Format numbered commitment list
- **GIVEN** user runs `/list commitments`
- **WHEN** list is formatted
- **THEN** each row shows shortcut prefix: `[/1]`, `[/2]`, etc.
- **AND** shortcuts are right-aligned in fixed-width column
- **AND** hint at bottom: "Use /1, /2, etc. to view details"

#### Scenario: Format numbered goal list
- **GIVEN** user runs `/list goals`
- **WHEN** list is formatted
- **THEN** each row shows shortcut prefix
- **AND** same hint displayed

#### Scenario: Shortcut column styling
- **GIVEN** list items have shortcuts
- **WHEN** shortcut column is displayed
- **THEN** shortcuts use dim styling to not distract from content
- **AND** format: `[dim][/1][/dim]`

### Requirement: Entity Detail Panel Formatting

The system SHALL format detailed entity views with structured panels using Rich ROUNDED box style.

#### Scenario: Format commitment detail panel
- **GIVEN** user views a commitment with `/view abc123`
- **WHEN** detail panel is formatted
- **THEN** Panel displays:
  - Header: Deliverable text (bold)
  - Fields: Stakeholder, Due Date/Time, Status, Created
  - Goal link (if any)
  - Tasks (if any, with checkboxes)
  - Actions hint: "Use /complete to mark done, /atrisk if at risk"
- **AND** Panel uses ROUNDED box style

#### Scenario: Format goal detail panel
- **GIVEN** user views a goal with `/view abc123`
- **WHEN** detail panel is formatted
- **THEN** Panel displays:
  - Header: Title (bold)
  - Fields: Problem Statement, Status, Progress
  - Vision link (if any)
  - Milestones (if any)
  - Commitments (if any)
- **AND** progress bar shows completion percentage

#### Scenario: Format task detail panel
- **GIVEN** user views a task with `/view abc123`
- **WHEN** detail panel is formatted
- **THEN** Panel displays:
  - Header: Title (bold)
  - Fields: Status, Estimated Hours, Actual Hours
  - Parent Commitment link
  - Subtasks (if any)

### Requirement: Error Message Formatting

The system SHALL format error messages with recovery suggestions.

#### Scenario: Format entity not found error
- **GIVEN** user enters `/view xyz123` and entity doesn't exist
- **WHEN** error is formatted
- **THEN** message shows:
  - Error text in red: "Entity not found: xyz123"
  - Suggestion in dim: "Use /list to see available entities"
- **AND** no stack trace shown

#### Scenario: Format invalid input error
- **GIVEN** user enters `/complete` without ID
- **WHEN** error is formatted
- **THEN** message shows:
  - Error text: "Missing entity ID"
  - Usage hint: "Usage: /complete <id>"
  - Example: "Example: /complete abc123"

#### Scenario: Format ambiguous ID error
- **GIVEN** user enters `/view ab` and multiple entities match
- **WHEN** error is formatted
- **THEN** message shows:
  - Text: "Multiple entities match 'ab'"
  - List of matching IDs with types
  - Suggestion: "Use a longer ID prefix to select one"

#### Scenario: Format invalid shortcut error
- **GIVEN** user enters `/7` but list only has 5 items
- **WHEN** error is formatted
- **THEN** message shows:
  - Text: "No item 7"
  - Hint: "Use /1 through /5, or /list to see items"

### Requirement: Success Confirmation Formatting

The system SHALL format success messages confirming what changed.

#### Scenario: Format commitment completion confirmation
- **GIVEN** user completes a commitment
- **WHEN** success is formatted
- **THEN** message shows:
  - Checkmark emoji: "[green]checkmark[/green] Completed: [deliverable]"
  - Integrity update (if changed): "Integrity: A- (was B+)"
- **AND** uses green styling

#### Scenario: Format entity creation confirmation
- **GIVEN** user confirms creating an entity
- **WHEN** success is formatted
- **THEN** message shows:
  - Plus emoji: "[green]+[/green] Created [type]: [name/deliverable]"
  - ID shown: "ID: abc123"
  - Next action hint: "Use /view abc123 to see details"

#### Scenario: Format status change confirmation
- **GIVEN** user changes entity status (at-risk, abandon, recover)
- **WHEN** success is formatted
- **THEN** message shows:
  - Status-appropriate emoji
  - Change description: "Marked commitment abc123 as at-risk"
  - Reason if provided

### Requirement: Action-Specific Progress Indicators

The system SHALL show context-specific progress messages during operations.

#### Scenario: Commitment extraction progress
- **GIVEN** user enters `/commit "send report to Sarah"`
- **WHEN** AI extraction runs
- **THEN** progress shows: "Extracting commitment details..."
- **AND** then: "Identifying stakeholder..."
- **AND** then proposal displayed

#### Scenario: Entity lookup progress
- **GIVEN** user enters `/view abc123`
- **WHEN** database lookup runs
- **THEN** progress shows: "Finding entity..."
- **AND** minimal delay for fast operations (no spinner for <100ms)

#### Scenario: List query progress
- **GIVEN** user enters `/list commitments` with many items
- **WHEN** database query runs
- **THEN** progress shows: "Loading commitments..."
- **AND** spinner only if query takes >200ms

#### Scenario: Progress indicator graceful degradation
- **GIVEN** terminal does not support ANSI escape codes
- **WHEN** progress indicator would be shown
- **THEN** fallback to simple text output (no spinner)
- **AND** operation completes normally

### Requirement: Keyboard Shortcut Toolbar

The system SHALL display keyboard shortcuts in the bottom toolbar instead of statistics.

<!-- Research: prompt_toolkit supports HTML, FormattedText for styled toolbars -->
<!-- Source: https://python-prompt-toolkit.readthedocs.io/en/stable/pages/asking_for_input.html#adding-a-bottom-toolbar -->

#### Scenario: Display keyboard shortcuts in toolbar
- **GIVEN** the REPL is running
- **WHEN** the bottom toolbar is displayed
- **THEN** toolbar shows: `F1=Help  F5=Refresh  /c=commit  /l=list  /v=view`
- **AND** shortcuts are separated by double spaces for readability
- **AND** toolbar uses dim styling (`fg:ansibrightblack noreverse`) to not distract from main content
- **AND** colors adapt to user's terminal theme (uses ANSI color names, not hex codes)
- **AND** key names are bold for scannability

#### Scenario: Toolbar remains static
- **GIVEN** the REPL is running
- **WHEN** user navigates or views entities
- **THEN** toolbar content remains constant (shows shortcuts, not dynamic stats)

#### Scenario: Toolbar graceful degradation on non-color terminal
- **GIVEN** terminal does not support ANSI colors (e.g., dumb terminal, CI environment)
- **WHEN** bottom toolbar is displayed
- **THEN** toolbar shows plain text shortcuts without styling
- **AND** bold tags are stripped or ignored gracefully
- **AND** no error or exception is raised

> **Note**: Terminal compatibility is handled by prompt_toolkit's built-in detection.
> No explicit fallback code is needed; prompt_toolkit degrades automatically.

### Requirement: Visual Prompt Styling

The system SHALL provide a visually distinct input prompt area with spacing and color accent.

<!-- Research: prompt_toolkit show_frame=True creates fixed-width box, not suitable -->
<!-- Full-width frame requires custom Application - too complex for cosmetic change -->
<!-- Industry standard (Starship, IPython, ptpython): colored prompt + spacing -->

#### Scenario: Spacing before prompt
- **GIVEN** the REPL is ready for input
- **WHEN** prompt is displayed after dashboard or command output
- **THEN** one blank line appears above the prompt for visual separation

#### Scenario: Colored prompt indicator
- **GIVEN** the REPL is ready for input
- **WHEN** prompt is displayed
- **THEN** prompt uses cyan color via prompt_toolkit HTML: `HTML('<ansicyan><b>></b></ansicyan> ')`
- **AND** the `>` character is bold cyan for strong visual distinction
- **AND** the prompt indicator stands out from surrounding text

<!-- Note: prompt_toolkit HTML uses nested tags, not attributes like `<ansicyan bold>` -->
<!-- Correct: <ansicyan><b>text</b></ansicyan>, Wrong: <ansicyan bold>text</ansicyan> -->

<!-- Note: Rich markup [cyan]...[/cyan] does NOT work in prompt_toolkit -->
<!-- prompt_toolkit uses its own HTML syntax: <ansicyan>, <ansired>, etc. -->
<!-- Source: https://python-prompt-toolkit.readthedocs.io/en/stable/pages/printing_text.html -->

### Requirement: prompt_toolkit Styling Implementation

The system SHALL use prompt_toolkit's native styling system for all input-related formatting.

<!-- Research: Rich and prompt_toolkit are separate rendering systems -->
<!-- Rich for output (tables, panels), prompt_toolkit for input (prompts, toolbars) -->

#### Scenario: Correct styling syntax
- **GIVEN** prompt or toolbar needs color styling
- **WHEN** style is applied
- **THEN** uses prompt_toolkit HTML format: `HTML('<ansicyan>text</ansicyan>')`
- **AND** NOT Rich markup format: `[cyan]text[/cyan]` (which would display as literal text)

#### Scenario: Style via Style.from_dict with theme-adaptive colors
- **GIVEN** consistent styling is needed across prompt and toolbar
- **WHEN** PromptSession is created
- **THEN** a Style object is passed using ANSI color names (NOT hex codes):
  ```python
  Style.from_dict({
      "bottom-toolbar": "fg:ansibrightblack noreverse",
  })
  ```
- **AND** toolbar uses `noreverse` to disable default bright/inverted styling
- **AND** colors use ANSI names (`ansicyan`, `ansibrightblack`) that adapt to terminal theme
- **AND** hex codes (`#888888`) are avoided to ensure light/dark theme compatibility

### Requirement: Consistent Theme-Adaptive Colors

The system SHALL use ANSI color names consistently, matching the existing JDO codebase pattern.

<!-- Research: JDO already uses theme-adaptive colors throughout (green, yellow, red, cyan, dim, bold) -->
<!-- No hex codes exist in the current codebase - this change should maintain that pattern -->

#### Scenario: Match existing color conventions
- **GIVEN** new styling is being added to prompt_toolkit components
- **WHEN** colors are specified
- **THEN** uses the same ANSI color names as existing Rich output (`cyan`, `green`, `yellow`, `red`, `dim`, `bold`)
- **AND** prompt_toolkit equivalents are used (`ansicyan`, `ansigreen`, `ansiyellow`, `ansired`)
- **AND** no hex codes (`#rrggbb`) are introduced
- **AND** colors adapt automatically to user's terminal theme (light/dark mode)

#### Scenario: Color mapping between Rich and prompt_toolkit
- **GIVEN** JDO uses Rich for output and prompt_toolkit for input
- **WHEN** similar styling is needed in both systems
- **THEN** equivalent colors are used:
  | Rich (output) | prompt_toolkit (input) |
  |---------------|------------------------|
  | `cyan` | `ansicyan` |
  | `dim` | `ansibrightblack` or `noreverse` |
  | `bold` | `bold` |
  | `green` | `ansigreen` |

## Cross-Cutting Concerns

### Performance

> **Note**: Output formatting performance is not a concern for this change. Rich Tables render sub-millisecond for typical data sizes (<1000 rows). No caching or optimization needed.

### Accessibility

> **Note**: Rich library handles terminal accessibility (color contrast, screen reader support via semantic output). No additional accessibility work needed for initial release.
