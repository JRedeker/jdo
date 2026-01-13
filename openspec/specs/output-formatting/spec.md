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

<!-- Research Note: Thinking indicator should be separate from Rich Live streaming display.
     console.status() is for spinners, not combined with streaming. -->

#### Scenario: AI thinking indicator
- **WHEN** waiting for AI response before streaming begins
- **THEN** "Thinking..." text indicator is shown (separate from streaming display)
- **AND** indicator is cleared when first token arrives
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

## Cross-Cutting Concerns

### Performance

> **Note**: Output formatting performance is not a concern for this change. Rich Tables render sub-millisecond for typical data sizes (<1000 rows). No caching or optimization needed.

### Accessibility

> **Note**: Rich library handles terminal accessibility (color contrast, screen reader support via semantic output). No additional accessibility work needed for initial release.
