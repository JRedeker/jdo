# tui-chat Specification Delta

## MODIFIED Requirements

### Requirement: Keyboard Navigation (Extended)

The system SHALL support keyboard shortcuts for Vision and Milestone navigation via NavSidebar.

#### Scenario: Quick access visions
- **WHEN** user presses '4' (Visions nav item) or selects from sidebar
- **THEN** the data panel shows visions list

#### Scenario: Quick access milestones
- **WHEN** user presses '5' (Milestones nav item) or selects from sidebar
- **THEN** the data panel shows milestones list (filtered to current goal if in goal context)

#### Scenario: Quick access hierarchy
- **WHEN** user presses '6' (Hierarchy nav item) or selects from sidebar
- **THEN** the data panel shows the full planning hierarchy tree

### Requirement: Home Screen (Extended)

The system SHALL integrate Vision and Milestone access into the NavSidebar.

#### Scenario: Sidebar shows navigation shortcuts
- **WHEN** viewing the main layout
- **THEN** NavSidebar includes: Visions, Milestones, Hierarchy alongside existing items

#### Scenario: Vision review notification
- **WHEN** user opens the app and visions are due for review
- **THEN** a subtle notification appears in chat: "1 vision due for quarterly review"

### Requirement: Integrity Always Visible

The system SHALL display integrity grade prominently in the NavSidebar header.

#### Scenario: Integrity grade in sidebar
- **WHEN** user views the main layout
- **THEN** current integrity letter grade is displayed in NavSidebar header (e.g., "Integrity: A-")

#### Scenario: Integrity grade color coding
- **WHEN** integrity grade is displayed
- **THEN** grade is color-coded: A-range = green, B-range = blue, C-range = yellow, D/F = red

### Requirement: Time-Aware Risk Warning

The system SHALL enhance risk warnings with time-based analysis.

#### Scenario: Daily capacity warning
- **WHEN** user's allocated hours exceed available hours
- **THEN** a warning message appears in chat: "Over-committed today: X hours allocated, Y hours available"
