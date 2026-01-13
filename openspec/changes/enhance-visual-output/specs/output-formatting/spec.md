## ADDED Requirements

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

## MODIFIED Requirements

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
