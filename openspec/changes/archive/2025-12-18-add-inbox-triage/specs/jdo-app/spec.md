## MODIFIED Requirements

### Requirement: Application Startup

The system SHALL initialize the application with database setup and screen display.

#### Scenario: Database initialization on startup
- **GIVEN** the application is launched
- **WHEN** the app mounts
- **THEN** the database tables are created if they don't exist

#### Scenario: Home screen on startup
- **GIVEN** the application is launched
- **WHEN** initialization completes
- **THEN** the Home screen is displayed

#### Scenario: Startup completes without error
- **GIVEN** a valid configuration
- **WHEN** the application starts
- **THEN** no exceptions are raised and the UI is responsive

#### Scenario: Triage count checked on startup
- **GIVEN** the application is launched
- **WHEN** the home screen is displayed
- **THEN** the triage item count is checked and stored for display

## ADDED Requirements

### Requirement: Home Screen Triage Indicator

The system SHALL display a triage indicator on the home screen when items need attention.

#### Scenario: Triage indicator shown when items exist
- **WHEN** the home screen is displayed and triage count > 0
- **THEN** an indicator shows "N items need triage [t]" where N is the count

#### Scenario: Triage indicator hidden when queue empty
- **WHEN** the home screen is displayed and triage count = 0
- **THEN** no triage indicator is shown

#### Scenario: Triage indicator updates on return to home
- **WHEN** user returns to home screen after processing triage items
- **THEN** the indicator count is refreshed

#### Scenario: Triage shortcut from home
- **WHEN** user presses `t` on the home screen with triage items
- **THEN** the system navigates to chat and starts triage mode

#### Scenario: Triage shortcut with empty queue
- **WHEN** user presses `t` on the home screen with no triage items
- **THEN** the system displays a notification "No items to triage"
