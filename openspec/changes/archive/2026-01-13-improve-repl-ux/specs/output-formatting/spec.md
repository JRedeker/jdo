## ADDED Requirements

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

## MODIFIED Requirements

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

## Cross-Cutting Concerns

### Error Handling

> **Note**: Formatters never raise exceptions. Invalid input (None values, missing fields) results in placeholder text or empty output. All formatting functions are defensive.

### Logging

> **Note**: Logging is N/A for formatters. Pure functions with no side effects. Errors in entity data are handled at the handler layer before reaching formatters.

### Performance

> **Note**: Output formatting performance is not a concern. Rich Tables render sub-millisecond for typical data sizes. Numbered shortcut generation is O(n) where n is list size.

### Accessibility

> **Note**: Rich library handles terminal accessibility (color contrast, screen reader support). Error messages use semantic structure (error + hint) for clarity.
