# jdo-app Specification

## Purpose
Define the main JDO application shell including startup initialization, screen navigation, draft restoration, vision review notifications, global key bindings, and header/footer widgets.
## Requirements
### Requirement: Application Startup

The system SHALL initialize the application with database setup and main layout display.

#### Scenario: AI configuration required on startup
- **GIVEN** the application is launched
- **AND** no credentials exist for the configured AI provider
- **WHEN** the main layout is displayed
- **THEN** a blocking modal is shown
- **AND** the modal offers an option to open Settings
- **AND** the modal offers an option to quit

#### Scenario: Database initialization on startup
- **GIVEN** the application is launched
- **WHEN** the app mounts
- **THEN** the database tables are created if they don't exist

#### Scenario: Main layout on startup
- **GIVEN** the application is launched
- **WHEN** initialization completes
- **THEN** the main layout with NavSidebar and content area is displayed
- **AND** focus is on the PromptInput

#### Scenario: Startup completes without error
- **GIVEN** a valid configuration
- **WHEN** the application starts
- **THEN** no exceptions are raised and the UI is responsive

#### Scenario: Triage count checked on startup
- **GIVEN** the application is launched
- **WHEN** the main layout is displayed
- **THEN** the triage item count is checked and shown as badge on Triage nav item

### Requirement: Screen Navigation

The system SHALL support navigation via the NavSidebar and Settings screen.

#### Scenario: Navigate to Chat via sidebar
- **GIVEN** the main layout is displayed
- **WHEN** the user selects "Chat" from NavSidebar
- **THEN** the content area shows chat-only view with DataPanel hidden

#### Scenario: Navigate to Settings via sidebar
- **GIVEN** the main layout is displayed
- **WHEN** the user selects "Settings" from NavSidebar
- **THEN** the Settings screen is pushed onto the screen stack

#### Scenario: Return from Settings
- **GIVEN** the user is on the Settings screen
- **WHEN** the user presses Escape
- **THEN** the Settings screen is popped and main layout is visible

#### Scenario: Navigate to data views via sidebar
- **GIVEN** the main layout is displayed
- **WHEN** the user selects a data view (Goals, Commitments, etc.) from NavSidebar
- **THEN** the DataPanel updates to show the selected content
- **AND** the chat area remains visible

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

#### Scenario: Toggle sidebar collapse
- **GIVEN** the application is running
- **WHEN** the user presses '['
- **THEN** the NavSidebar toggles between expanded and collapsed states

#### Scenario: Number keys provide quick navigation
- **GIVEN** the application is running
- **WHEN** the user presses a number key (1-9)
- **THEN** the corresponding NavSidebar item is selected (1=Chat, 2=Goals, 3=Commitments, etc.)
- **AND** number keys work regardless of which widget has focus

#### Scenario: Tab cycles focus with visible widgets
- **GIVEN** the application is running with DataPanel visible
- **WHEN** the user presses Tab
- **THEN** focus cycles in order: NavSidebar → PromptInput → DataPanel → NavSidebar

#### Scenario: Tab skips hidden DataPanel
- **GIVEN** the application is running with DataPanel hidden (Chat view)
- **WHEN** the user presses Tab
- **THEN** focus cycles in order: NavSidebar → PromptInput → NavSidebar

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

### Requirement: Navigation State Initialization

The system SHALL support initializing ChatScreen with pre-loaded data in the DataPanel to enable instant data display on navigation.

#### Scenario: ChatScreen accepts initial data
- **WHEN** ChatScreen is constructed with initial_mode and initial_data parameters
- **THEN** on mount, DataPanel is initialized with the provided data
- **AND** data appears immediately without loading delay

#### Scenario: Navigation without initial data
- **WHEN** ChatScreen is constructed without initial data
- **THEN** DataPanel starts in empty state
- **AND** behaves as current implementation

### Requirement: Application Layout

The system SHALL display a three-panel layout with sidebar, chat, and data panel.

#### Scenario: NavSidebar docked left
- **GIVEN** the application is running
- **WHEN** the main layout is displayed
- **THEN** the NavSidebar is docked to the left edge

#### Scenario: Content area fills remaining space
- **GIVEN** the application is running
- **WHEN** the main layout is displayed
- **THEN** the content area (chat + data panel) fills the space to the right of NavSidebar

#### Scenario: Header shows app title
- **GIVEN** the application is running
- **WHEN** the main layout is displayed
- **THEN** the header shows "JDO" as the title

#### Scenario: Footer shows key bindings
- **GIVEN** the application is running
- **WHEN** the main layout is displayed
- **THEN** the footer shows context-appropriate key bindings

