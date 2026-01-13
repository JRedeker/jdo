## MODIFIED Requirements

### Requirement: Dashboard Display in REPL

The system SHALL display a multi-panel dashboard before each REPL prompt based on current data volume.

#### Scenario: Dashboard shown after startup
- **GIVEN** the REPL has started
- **WHEN** startup guidance messages complete
- **THEN** dashboard is displayed with appropriate display level
- **AND** the prompt appears below the dashboard

#### Scenario: Dashboard shown after command completion
- **GIVEN** user has executed a command or received AI response
- **WHEN** command processing completes
- **THEN** dashboard is displayed with current data
- **AND** the prompt appears below the dashboard

#### Scenario: Dashboard updates after data changes
- **GIVEN** user creates, completes, or modifies commitments/goals
- **WHEN** the operation succeeds
- **THEN** the next dashboard reflects updated counts and items

## ADDED Requirements

### Requirement: Dashboard Data Caching

The system SHALL cache dashboard data in session state for efficient display.

#### Scenario: Cache includes commitment list
- **GIVEN** dashboard is being prepared
- **WHEN** session cache is updated
- **THEN** cache includes up to 5 upcoming commitments with display data
- **AND** commitments are ordered by due date ascending

#### Scenario: Cache includes goal progress
- **GIVEN** dashboard is being prepared
- **WHEN** session cache is updated
- **THEN** cache includes active goals with progress percentages
- **AND** goals include review due status

#### Scenario: Cache includes integrity summary
- **GIVEN** dashboard is being prepared
- **WHEN** session cache is updated
- **THEN** cache includes integrity grade, score, and trend
- **AND** cache includes current streak in weeks

#### Scenario: Cache updated on commitment changes
- **GIVEN** user creates or completes a commitment
- **WHEN** commitment is saved to database
- **THEN** dashboard cache is refreshed with new data

#### Scenario: Cache updated on goal changes
- **GIVEN** goal progress changes (via commitment completion)
- **WHEN** change is saved
- **THEN** dashboard cache is refreshed with new goal progress

### Requirement: Display Level Selection

The system SHALL automatically select display level based on data volume.

#### Scenario: Select minimal display
- **GIVEN** user has 0 commitments AND 0 goals
- **WHEN** display level is determined
- **THEN** returns MINIMAL (status bar only)

#### Scenario: Select compact display
- **GIVEN** user has 1-2 commitments
- **WHEN** display level is determined
- **THEN** returns COMPACT (merged panel)

#### Scenario: Select standard display
- **GIVEN** user has 3+ commitments AND 0 goals
- **WHEN** display level is determined
- **THEN** returns STANDARD (commitments + status bar)

#### Scenario: Select full display
- **GIVEN** user has 3+ commitments AND 1+ goals
- **WHEN** display level is determined
- **THEN** returns FULL (all panels)
