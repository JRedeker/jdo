## ADDED Requirements

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
