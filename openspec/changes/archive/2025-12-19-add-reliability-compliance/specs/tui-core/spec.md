## ADDED Requirements

### Requirement: Settings Screen Auth Status Refresh

The system SHALL update authentication status displays after successful OAuth or API key authentication.

#### Scenario: Refresh auth status after OAuth success
- **GIVEN** the Settings screen is displayed
- **WHEN** user completes OAuth authentication successfully
- **THEN** the auth status widget for that provider updates to show "Authenticated"
- **AND** the status widget style changes to success color

#### Scenario: Refresh auth status after API key save
- **GIVEN** the Settings screen is displayed
- **WHEN** user saves an API key successfully
- **THEN** the auth status widget for that provider updates to show "Authenticated"
- **AND** the status widget style changes to success color

#### Scenario: Bindings remain active after modal dismiss
- **GIVEN** the Settings screen displayed an OAuth or API key modal
- **WHEN** the modal is dismissed (success or cancel)
- **THEN** the Escape/Back binding remains responsive
- **AND** user can navigate back to the previous screen

### Requirement: Allocated Hours Calculation

The system SHALL calculate allocated hours from active tasks for AI context.

#### Scenario: Calculate from pending and in-progress tasks
- **WHEN** `_build_ai_context()` is called
- **THEN** `allocated_hours` is calculated as the sum of `estimated_hours` for all tasks with status PENDING or IN_PROGRESS
- **AND** tasks without `estimated_hours` are treated as 0

#### Scenario: Handle database errors gracefully
- **WHEN** the allocated hours query fails
- **THEN** `allocated_hours` returns 0.0
- **AND** a warning is logged with message "Failed to calculate allocated hours: {error}"
