# jdo-app Specification

## Purpose
Define the main JDO application shell including startup initialization, screen navigation, draft restoration, vision review notifications, global key bindings, and header/footer widgets.
## Requirements
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

### Requirement: Screen Navigation

The system SHALL support navigation between Home, Chat, and Settings screens.

#### Scenario: Navigate to Chat from Home
- **GIVEN** the user is on the Home screen
- **WHEN** the user triggers new chat action (n key or message)
- **THEN** the Chat screen is pushed onto the screen stack

#### Scenario: Navigate to Settings from Home
- **GIVEN** the user is on the Home screen
- **WHEN** the user triggers settings action (s key or message)
- **THEN** the Settings screen is pushed onto the screen stack

#### Scenario: Return to Home from Chat
- **GIVEN** the user is on the Chat screen
- **WHEN** the user presses Escape
- **THEN** the Chat screen is popped and Home screen is visible

#### Scenario: Return to Home from Settings
- **GIVEN** the user is on the Settings screen
- **WHEN** the user presses Escape
- **THEN** the Settings screen is popped and Home screen is visible

### Requirement: Draft Restoration

The system SHALL restore pending drafts on startup.

#### Scenario: Restore draft on startup
- **GIVEN** there is an unexpired draft in the database
- **WHEN** the application starts
- **THEN** the user is prompted to restore or discard the draft

#### Scenario: No prompt without draft
- **GIVEN** there are no pending drafts
- **WHEN** the application starts
- **THEN** no draft restoration prompt is shown

#### Scenario: Restore draft navigates to Chat
- **GIVEN** a draft restoration prompt is shown
- **WHEN** the user chooses to restore
- **THEN** the Chat screen opens with the draft loaded in the data panel

### Requirement: Vision Review Prompts

The system SHALL prompt for vision reviews when due.

#### Scenario: Vision review notification on startup
- **GIVEN** one or more visions have next_review_date <= today
- **WHEN** the application starts
- **THEN** a notification is shown indicating visions are due for review

#### Scenario: No notification when no reviews due
- **GIVEN** no visions have next_review_date <= today
- **WHEN** the application starts
- **THEN** no vision review notification is shown

#### Scenario: Snooze review for session
- **GIVEN** a vision review notification is shown
- **WHEN** the user dismisses the notification
- **THEN** the notification does not reappear during the current session

### Requirement: Global Key Bindings

The system SHALL provide consistent global key bindings.

#### Scenario: Quit application
- **GIVEN** the application is running
- **WHEN** the user presses 'q'
- **THEN** the application exits gracefully

#### Scenario: Toggle dark mode
- **GIVEN** the application is running
- **WHEN** the user presses 'd'
- **THEN** the theme toggles between dark and light mode

#### Scenario: Escape returns to previous screen
- **GIVEN** a screen is pushed onto the stack
- **WHEN** the user presses Escape
- **THEN** the current screen is popped (unless on Home)

### Requirement: Application Header and Footer

The system SHALL display consistent header and footer widgets.

#### Scenario: Header shows app title
- **GIVEN** the application is running
- **WHEN** any screen is displayed
- **THEN** the header shows "JDO" as the title

#### Scenario: Footer shows key bindings
- **GIVEN** the application is running
- **WHEN** any screen is displayed
- **THEN** the footer shows context-appropriate key bindings

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

