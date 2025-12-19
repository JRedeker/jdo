# tui-views Specification

## Purpose
Define the TUI screens and views for managing commitments, goals, stakeholders, and tasks, including list views, detail views, and creation flows with keyboard-first navigation.
## Requirements
### Requirement: TUI Design Principles

The system SHALL implement a text-focused TUI with minimal panels and impeccable formatting.

#### Scenario: Consistent alignment across screens
- **WHEN** any screen is displayed
- **THEN** all labels and values are aligned on consistent column boundaries

#### Scenario: Monospace-friendly layout
- **WHEN** content is displayed
- **THEN** spacing and alignment work correctly in monospace fonts

#### Scenario: Keyboard-first navigation
- **WHEN** user interacts with the application
- **THEN** all actions are accessible via keyboard shortcuts shown in footer

#### Scenario: Status indicators use symbols
- **WHEN** status is displayed
- **THEN** Unicode symbols indicate state (e.g., ● for active, ✓ for complete, ○ for pending)

### Requirement: Home Screen

The system SHALL provide a main view showing commitments due soon and quick actions via the NavSidebar.

#### Scenario: Display due soon commitments
- **WHEN** user selects "Commitments" from NavSidebar
- **THEN** commitments due within 7 days are listed, sorted by due date ascending

#### Scenario: Display overdue commitments prominently
- **WHEN** there are overdue commitments
- **THEN** they appear at the top of the commitments list with visual distinction

#### Scenario: Quick create commitment
- **WHEN** user types `/commit` in PromptInput
- **THEN** the Commitment creation flow starts

#### Scenario: Display goals due for review
- **WHEN** user selects "Goals" from NavSidebar and goals are due for review
- **THEN** a subtle indicator shows next to due goals in the list

#### Scenario: Goal review indicator is subtle
- **WHEN** goals are due for review
- **THEN** the indicator does not block or interrupt the primary view

#### Scenario: Navigate to goal review
- **WHEN** user selects a goal due for review and activates it
- **THEN** the `/goal review` flow starts

#### Scenario: Quick access goals via sidebar
- **WHEN** user presses '2' (Goals nav item) or selects "Goals" from NavSidebar
- **THEN** the data panel shows the goals list

### Requirement: Commitment List Screen

The system SHALL provide a screen listing all commitments with filtering and sorting.

#### Scenario: List all commitments
- **WHEN** user opens the Commitment List screen
- **THEN** all commitments are displayed with deliverable, stakeholder name, due date, and status

#### Scenario: Filter by status
- **WHEN** user applies a status filter
- **THEN** only commitments matching the selected status are shown

#### Scenario: Filter by stakeholder
- **WHEN** user applies a stakeholder filter
- **THEN** only commitments for the selected stakeholder are shown

#### Scenario: Sort by due date
- **WHEN** user selects due date sorting
- **THEN** commitments are ordered by due date (ascending or descending based on selection)

### Requirement: Commitment Detail Screen

The system SHALL provide a screen for viewing and editing a single commitment with its tasks.

#### Scenario: Display commitment details
- **WHEN** user opens a Commitment Detail screen
- **THEN** deliverable, stakeholder, due date/time, status, goal (if any), and notes are displayed with clear labels

#### Scenario: Display associated tasks
- **WHEN** viewing a commitment that has tasks
- **THEN** tasks are listed below commitment details with status indicators and sub-task progress

#### Scenario: Edit commitment fields
- **WHEN** user presses edit shortcut
- **THEN** editable fields become active for modification

#### Scenario: Mark commitment complete
- **WHEN** user presses complete shortcut on commitment detail
- **THEN** commitment status changes to completed and completed_at is set

#### Scenario: Add task to commitment
- **WHEN** user presses add task shortcut
- **THEN** a task creation form appears for the current commitment

### Requirement: Commitment Creation Flow

The system SHALL guide users through creating a commitment by collecting: deliverable, stakeholder, and due date.

#### Scenario: Step-by-step commitment creation
- **WHEN** user initiates commitment creation
- **THEN** the system prompts for deliverable, then stakeholder selection, then due date/time

#### Scenario: Stakeholder selection during creation
- **WHEN** user reaches stakeholder step
- **THEN** existing stakeholders are listed for selection, with option to create new

#### Scenario: Due date entry
- **WHEN** user reaches due date step
- **THEN** the system accepts date input with optional time component

#### Scenario: Optional goal association
- **WHEN** commitment creation completes basic fields
- **THEN** user can optionally select a parent goal before saving

### Requirement: Goal List Screen

The system SHALL provide a screen displaying goals in a hierarchical structure.

#### Scenario: Display goal hierarchy
- **WHEN** user opens the Goal List screen
- **THEN** goals are displayed with indentation showing parent-child relationships

#### Scenario: Expand/collapse goal children
- **WHEN** user interacts with a parent goal
- **THEN** child goals can be expanded or collapsed

#### Scenario: Show goal status
- **WHEN** goals are displayed
- **THEN** each goal shows its status and commitment count

#### Scenario: Show review due indicator in list
- **WHEN** a goal in the list has next_review_date <= today
- **THEN** a review indicator (e.g., 🔄 or "review") appears next to the goal title

#### Scenario: Show on-hold goals dimmed
- **WHEN** a goal has status on_hold
- **THEN** the goal appears with reduced emphasis (dimmed or different color)

### Requirement: Goal Detail Screen

The system SHALL provide a screen for viewing and editing a single goal with its commitments.

#### Scenario: Display goal details
- **WHEN** user opens a Goal Detail screen
- **THEN** title, problem statement, solution vision, and status are displayed

#### Scenario: Display motivation prominently
- **WHEN** viewing a goal that has a motivation set
- **THEN** the motivation is displayed under a "Why This Matters" heading, positioned prominently after the title

#### Scenario: Display commitment progress
- **WHEN** viewing a goal that has commitments
- **THEN** a progress summary shows: "Commitments: ✓ X completed, ● Y in progress, ○ Z pending, ✗ W abandoned"

#### Scenario: Display commitment progress percentage
- **WHEN** viewing a goal with non-abandoned commitments
- **THEN** completion rate is shown as percentage (completed / non-abandoned)

#### Scenario: Display review schedule
- **WHEN** viewing a goal with next_review_date set
- **THEN** the panel shows "Next Review: [date]" with interval label (Weekly/Monthly/Quarterly) if set

#### Scenario: Display due for review indicator
- **WHEN** viewing a goal where next_review_date <= today
- **THEN** a "Due for Review" indicator appears with option to start review

#### Scenario: Display child commitments
- **WHEN** viewing a goal that has commitments
- **THEN** associated commitments are listed with status summary

#### Scenario: Display child goals
- **WHEN** viewing a goal that has child goals
- **THEN** child goals are listed with status indicators

#### Scenario: Create commitment from goal
- **WHEN** user presses create commitment shortcut on goal detail
- **THEN** commitment creation starts with goal_id pre-filled

#### Scenario: De-emphasize achieved status
- **WHEN** viewing goal status options or displaying status
- **THEN** "achieved" is presented as a rare, intentional choice, not the expected outcome

### Requirement: Goal Creation Flow

The system SHALL guide users through creating a goal by collecting: title, problem statement, and solution vision.

#### Scenario: Step-by-step goal creation
- **WHEN** user initiates goal creation
- **THEN** the system prompts for title, then problem statement, then solution vision

#### Scenario: Optional parent goal selection
- **WHEN** goal creation completes basic fields
- **THEN** user can optionally select a parent goal for nesting

#### Scenario: Optional target date
- **WHEN** goal creation completes required fields
- **THEN** user can optionally set a target date

### Requirement: Stakeholder List Screen

The system SHALL provide a screen for managing stakeholders.

#### Scenario: List all stakeholders
- **WHEN** user opens the Stakeholder List screen
- **THEN** all stakeholders are displayed with name, type, and commitment count

#### Scenario: Create new stakeholder
- **WHEN** user presses create shortcut
- **THEN** a stakeholder creation form appears

#### Scenario: Edit stakeholder
- **WHEN** user selects a stakeholder and presses edit
- **THEN** stakeholder fields become editable

#### Scenario: View stakeholder commitments
- **WHEN** user selects a stakeholder and presses view commitments
- **THEN** the Commitment List screen opens filtered to that stakeholder

### Requirement: Task Detail View

The system SHALL provide inline task viewing and editing within the Commitment Detail screen.

#### Scenario: Expand task details
- **WHEN** user selects a task in the commitment detail
- **THEN** the task's scope and sub-tasks are displayed

#### Scenario: Toggle task status
- **WHEN** user presses status toggle on a task
- **THEN** the task cycles through pending → in_progress → completed

#### Scenario: Toggle sub-task completion
- **WHEN** user presses toggle on a sub-task
- **THEN** the sub-task completed status toggles

#### Scenario: Edit task inline
- **WHEN** user presses edit on a task
- **THEN** task title, scope, and sub-tasks become editable inline

### Requirement: Task Creation Flow

The system SHALL support adding tasks to commitments with clear scope definition.

#### Scenario: Add task to commitment
- **WHEN** user adds a task from Commitment Detail screen
- **THEN** the system prompts for title and scope

#### Scenario: Add sub-tasks during creation
- **WHEN** user is creating a task
- **THEN** they can add sub-tasks as part of the creation flow

#### Scenario: Scope clarity prompt
- **WHEN** user enters a scope shorter than 10 characters
- **THEN** a non-blocking hint suggests adding more detail

