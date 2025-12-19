# Capability: JDO App (Navigation Message Handlers)

This spec adds the missing navigation message handlers that connect HomeScreen keyboard shortcuts to actual navigation behavior.

**Cross-reference**: See `tui-views` for HomeScreen implementation and message definitions.

## ADDED Requirements

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

## MODIFIED Requirements

None - all changes are additive.

## REMOVED Requirements

None.
