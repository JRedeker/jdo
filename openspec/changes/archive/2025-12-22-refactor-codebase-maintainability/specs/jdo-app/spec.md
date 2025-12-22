## ADDED Requirements

### Requirement: Navigation Service

The system SHALL provide a centralized service for fetching entity list data for navigation.

#### Scenario: Fetch goals list
- **WHEN** `NavigationService.get_goals_list(session)` is called
- **THEN** a list of goal dictionaries is returned with id, title, problem_statement, and status fields

#### Scenario: Fetch commitments list
- **WHEN** `NavigationService.get_commitments_list(session)` is called
- **THEN** a list of commitment dictionaries is returned with id, deliverable, stakeholder_name, due_date, and status fields

#### Scenario: Fetch visions list
- **WHEN** `NavigationService.get_visions_list(session)` is called
- **THEN** a list of vision dictionaries is returned with id, title, timeframe, and status fields

#### Scenario: Fetch milestones list
- **WHEN** `NavigationService.get_milestones_list(session)` is called
- **THEN** a list of milestone dictionaries is returned with id, title, target_date, goal_id, and status fields

#### Scenario: Fetch orphan commitments list
- **WHEN** `NavigationService.get_orphans_list(session)` is called
- **THEN** a list of commitment dictionaries is returned containing only commitments where goal_id, milestone_id, and recurring_commitment_id are all null

#### Scenario: Fetch integrity dashboard data
- **WHEN** `NavigationService.get_integrity_data(session)` is called
- **THEN** integrity metrics are returned including letter_grade, on_time_rate, notification_timeliness, cleanup_completion_rate, and current_streak_weeks

### Requirement: Consolidated Navigation Dispatcher

The system SHALL use a single dispatcher method for entity list navigation.

#### Scenario: Navigate via dispatcher
- **WHEN** any navigation action requests an entity list or special view
- **THEN** the dispatcher method fetches data via NavigationService
- **AND** updates DataPanel with the appropriate content

#### Scenario: NavSidebar selection uses dispatcher
- **WHEN** NavSidebar posts a Selected message for any item
- **THEN** the selection handler delegates to the navigation dispatcher
- **AND** dispatcher handles Chat, Goals, Commitments, Visions, Milestones, Hierarchy, Integrity, Orphans, Triage, and Settings

#### Scenario: Settings navigation pushes screen
- **WHEN** NavSidebar selection is Settings
- **THEN** the dispatcher pushes SettingsScreen instead of updating DataPanel

## MODIFIED Requirements

### Requirement: Screen Navigation

The system SHALL support navigation between Home, Chat, and Settings screens.

#### Scenario: HomeScreen message handlers deprecated
- **WHEN** HomeScreen posts ShowGoals, ShowCommitments, ShowVisions, ShowMilestones, or ShowOrphans messages
- **THEN** these handlers are deprecated
- **AND** navigation is handled via NavSidebar.Selected dispatcher

#### Scenario: Navigate to Settings from NavSidebar
- **GIVEN** the user is viewing any screen with NavSidebar
- **WHEN** the user selects Settings from NavSidebar
- **THEN** the Settings screen is pushed onto the screen stack

#### Scenario: Return to previous screen from Settings
- **GIVEN** the user is on the Settings screen
- **WHEN** the user presses Escape
- **THEN** the Settings screen is popped and the previous screen is visible
