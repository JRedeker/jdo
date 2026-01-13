## ADDED Requirements

### Requirement: Commitment Summary Display

The system SHALL display a commitment summary panel before each REPL prompt to keep users informed of their current obligations.

#### Scenario: Summary shown after startup
- **GIVEN** the REPL has started
- **WHEN** startup guidance messages complete
- **THEN** commitment summary panel is displayed (if user has commitments)
- **AND** the prompt appears below the summary

#### Scenario: Summary shown after command completion
- **GIVEN** user has executed a command or received AI response
- **WHEN** command processing completes
- **THEN** commitment summary panel is displayed (if user has commitments)
- **AND** the prompt appears below the summary

#### Scenario: Summary updates after commitment changes
- **GIVEN** user creates or completes a commitment
- **WHEN** the operation succeeds
- **THEN** the next summary panel reflects the updated counts
- **AND** next due item is updated if changed

#### Scenario: Summary hidden when no commitments
- **GIVEN** user has no active commitments
- **WHEN** summary would be displayed
- **THEN** no summary panel is shown
- **AND** prompt appears without preceding panel

#### Scenario: Summary uses cached data for performance
- **GIVEN** summary panel is being rendered
- **WHEN** displaying commitment counts and next due item
- **THEN** data is retrieved from session cache (not live DB query)
- **AND** cache is updated only when commitments change

### Requirement: Summary Panel Session Caching

The system SHALL cache commitment summary data in session state for efficient display.

#### Scenario: Cache includes next due commitment
- **GIVEN** user has active commitments
- **WHEN** session cache is updated
- **THEN** cache includes: active_count, at_risk_count, overdue_count
- **AND** cache includes next_due commitment info (deliverable, due_date)

#### Scenario: Cache updated on commitment creation
- **GIVEN** user confirms a new commitment
- **WHEN** commitment is saved to database
- **THEN** session cache is updated with new summary data

#### Scenario: Cache updated on commitment completion
- **GIVEN** user completes a commitment
- **WHEN** commitment status is updated to completed
- **THEN** session cache is updated with new summary data
