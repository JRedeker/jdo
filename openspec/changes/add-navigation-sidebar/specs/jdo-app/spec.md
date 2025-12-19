# jdo-app Specification Delta

## MODIFIED Requirements

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

#### Scenario: Number keys select navigation items
- **GIVEN** the application is running
- **WHEN** the user presses a number key (1-9)
- **THEN** the corresponding NavSidebar item is selected

#### Scenario: Tab cycles focus
- **GIVEN** the application is running
- **WHEN** the user presses Tab
- **THEN** focus cycles between NavSidebar, PromptInput, and DataPanel

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

## REMOVED Requirements

### Requirement: Home Screen Triage Indicator

**Reason**: HomeScreen is being replaced by NavSidebar. Triage indicator moves to NavSidebar as badge.

**Migration**: Use NavSidebar Triage Badge requirement in tui-nav spec instead.

### Requirement: Goals Navigation

**Reason**: Navigation is now handled by NavSidebar.Selected message handler.

**Migration**: See tui-nav spec "Navigation Item Selection" requirement.

### Requirement: Commitments Navigation

**Reason**: Navigation is now handled by NavSidebar.Selected message handler.

**Migration**: See tui-nav spec "Navigation Item Selection" requirement.

### Requirement: Visions Navigation

**Reason**: Navigation is now handled by NavSidebar.Selected message handler.

**Migration**: See tui-nav spec "Navigation Item Selection" requirement.

### Requirement: Milestones Navigation

**Reason**: Navigation is now handled by NavSidebar.Selected message handler.

**Migration**: See tui-nav spec "Navigation Item Selection" requirement.

### Requirement: Orphan Commitments Navigation

**Reason**: Navigation is now handled by NavSidebar.Selected message handler.

**Migration**: See tui-nav spec "Navigation Item Selection" requirement.

### Requirement: Hierarchy Navigation

**Reason**: Navigation is now handled by NavSidebar.Selected message handler.

**Migration**: See tui-nav spec "Navigation Item Selection" requirement.

### Requirement: Integrity Dashboard Navigation

**Reason**: Navigation is now handled by NavSidebar.Selected message handler.

**Migration**: See tui-nav spec "Navigation Item Selection" requirement.
