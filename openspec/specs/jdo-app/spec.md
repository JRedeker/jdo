# jdo-app Specification

## Purpose
Define the main JDO application shell including startup initialization, screen navigation, draft restoration, vision review notifications, global key bindings, and header/footer widgets.
## Requirements
### Requirement: Application Startup

The system SHALL initialize the application with database setup and screen display.

#### Scenario: AI configuration required on startup
- **GIVEN** the application is launched
- **AND** no credentials exist for the configured AI provider
- **WHEN** the Home screen is displayed
- **THEN** a blocking modal is shown
- **AND** the modal offers an option to open Settings
- **AND** the modal offers an option to quit

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

### Requirement: Goals Navigation

The system SHALL handle the ShowGoals message from HomeScreen by navigating to a view displaying the user's goals.

#### Scenario: Show goals list via keyboard shortcut
- **WHEN** user presses 'g' on HomeScreen
- **THEN** HomeScreen posts ShowGoals message
- **AND** JdoApp navigates to ChatScreen with goals list loaded in DataPanel

#### Scenario: Goals list empty
- **WHEN** ShowGoals message handled with no goals in database
- **THEN** DataPanel displays empty state with guidance on creating first goal

### Requirement: Commitments Navigation

The system SHALL handle the ShowCommitments message from HomeScreen by navigating to a view displaying the user's commitments.

#### Scenario: Show commitments list via keyboard shortcut
- **WHEN** user presses 'c' on HomeScreen
- **THEN** HomeScreen posts ShowCommitments message
- **AND** JdoApp navigates to ChatScreen with commitments list loaded in DataPanel

#### Scenario: Commitments sorted by priority
- **WHEN** ShowCommitments message handled
- **THEN** commitments are sorted with at_risk items first, then by due date

### Requirement: Visions Navigation

The system SHALL handle the ShowVisions message from HomeScreen by navigating to a view displaying the user's visions.

#### Scenario: Show visions list via keyboard shortcut
- **WHEN** user presses 'v' on HomeScreen
- **THEN** HomeScreen posts ShowVisions message
- **AND** JdoApp navigates to ChatScreen with visions list loaded in DataPanel

#### Scenario: Vision review indicators
- **WHEN** ShowVisions displays visions due for review
- **THEN** those visions are highlighted or marked with review indicator

### Requirement: Milestones Navigation

The system SHALL handle the ShowMilestones message from HomeScreen by navigating to a view displaying the user's milestones.

#### Scenario: Show milestones list via keyboard shortcut
- **WHEN** user presses 'm' on HomeScreen
- **THEN** HomeScreen posts ShowMilestones message
- **AND** JdoApp navigates to ChatScreen with milestones list loaded in DataPanel

#### Scenario: Milestones grouped by goal
- **WHEN** milestones are displayed
- **THEN** they can optionally be grouped by their parent goal

### Requirement: Orphan Commitments Navigation

The system SHALL handle the ShowOrphans message from HomeScreen by navigating to a view displaying commitments without goal/milestone linkage.

#### Scenario: Show orphan commitments via keyboard shortcut
- **WHEN** user presses 'o' on HomeScreen
- **THEN** HomeScreen posts ShowOrphans message
- **AND** JdoApp navigates to ChatScreen with orphan commitments list

#### Scenario: Orphan definition
- **WHEN** querying orphan commitments
- **THEN** return commitments where goal_id, milestone_id, and recurring_commitment_id are all null

#### Scenario: No orphan commitments
- **WHEN** ShowOrphans handled with no orphan commitments
- **THEN** DataPanel displays message "All commitments are linked to goals or milestones"

### Requirement: Hierarchy Navigation

The system SHALL handle the ShowHierarchy message from HomeScreen by navigating to a full hierarchy tree view.

#### Scenario: Show hierarchy tree via keyboard shortcut
- **WHEN** user presses 'h' on HomeScreen
- **THEN** HomeScreen posts ShowHierarchy message
- **AND** JdoApp navigates to ChatScreen with hierarchy view loaded

#### Scenario: Hierarchy shows all levels
- **WHEN** hierarchy view is displayed
- **THEN** it shows vision → goal → milestone → commitment hierarchy
- **AND** orphan commitments are shown in separate section

### Requirement: Integrity Dashboard Navigation

The system SHALL handle the ShowIntegrity message from HomeScreen by navigating to the integrity dashboard view.

#### Scenario: Show integrity dashboard via keyboard shortcut
- **WHEN** user presses 'i' on HomeScreen
- **THEN** HomeScreen posts ShowIntegrity message
- **AND** JdoApp navigates to ChatScreen with integrity dashboard loaded

#### Scenario: Integrity metrics calculated on navigation
- **WHEN** ShowIntegrity message is handled
- **THEN** IntegrityService calculates current metrics
- **AND** letter grade and all metrics are displayed in DataPanel

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

