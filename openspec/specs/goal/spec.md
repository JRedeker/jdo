# goal Specification

## Purpose
Define the Goal domain model representing desired outcomes with problem statements and solution visions, supporting hierarchical nesting, vision associations, milestone tracking, and periodic review workflows.
## Requirements
### Requirement: Goal Model

The system SHALL provide a `Goal` SQLModel with the following validated fields:
- `id` (UUID): Unique identifier, auto-generated
- `title` (str): Short descriptive name, required, non-empty
- `problem_statement` (str): Description of the problem being solved, required, non-empty
- `solution_vision` (str): Description of the desired end state, required, non-empty
- `motivation` (str | None): Why this goal matters to the user (growth mindset reinforcement)
- `parent_goal_id` (UUID | None): Optional reference to parent Goal for nesting
- `status` (GoalStatus enum): One of `active`, `on_hold`, `achieved`, `abandoned`; defaults to `active`
- `next_review_date` (date | None): When the user should next review this goal
- `review_interval_days` (int | None): Recurring review cadence; only 7 (weekly), 30 (monthly), or 90 (quarterly) allowed
- `last_reviewed_at` (datetime | None): When the user last reviewed this goal
- `created_at` (datetime): Auto-set on creation, timezone-aware (EST default)
- `updated_at` (datetime): Auto-updated on modification, timezone-aware (EST default)

**Future extension**: FRC defines a Vision entity that will sit above Goals. The `problem_statement` and `solution_vision` fields may be restructured when Vision is introduced.

#### Scenario: Create goal with required fields
- **WHEN** user creates a Goal with title, problem_statement, and solution_vision
- **THEN** a valid Goal is created with status="active" and auto-generated timestamps

#### Scenario: Reject goal without problem statement
- **WHEN** user creates a Goal with an empty problem_statement
- **THEN** SQLModel validation raises an error

#### Scenario: Reject goal without solution vision
- **WHEN** user creates a Goal with an empty solution_vision
- **THEN** SQLModel validation raises an error

### Requirement: Goal Nesting

The system SHALL support hierarchical goal organization through parent-child relationships with a soft limit of 3 nesting levels.

#### Scenario: Create nested goal
- **WHEN** user creates a Goal with parent_goal_id referencing an existing Goal
- **THEN** the new Goal is associated as a child of the parent Goal

#### Scenario: Retrieve child goals
- **WHEN** user queries for children of a parent Goal
- **THEN** the system returns all Goals with parent_goal_id matching the parent's id

#### Scenario: Prevent circular nesting
- **WHEN** user attempts to set a Goal's parent_goal_id to itself or to a descendant Goal
- **THEN** the system raises a validation error

#### Scenario: Warn on deep nesting
- **WHEN** user creates a Goal that would be at nesting level 4 or deeper
- **THEN** the AI warns "This goal would be 4 levels deep. Consider simplifying your goal hierarchy." but allows creation

#### Scenario: Display nesting depth
- **WHEN** viewing a deeply nested goal
- **THEN** the system shows the full hierarchy path (e.g., "Parent > Child > Grandchild > This Goal")

### Requirement: Goal Persistence

The system SHALL persist Goal entities to SQLite with full CRUD operations via SQLModel sessions.

#### Scenario: Save and retrieve goal
- **WHEN** user saves a new Goal via a database session
- **THEN** the Goal is persisted to SQLite and can be retrieved by id

#### Scenario: List goals with filters
- **WHEN** user queries goals with status filter (e.g., status="active")
- **THEN** the system returns only goals matching the filter criteria

#### Scenario: Delete goal without commitments or children
- **WHEN** user deletes a Goal that has no associated commitments and no child goals
- **THEN** the Goal is removed from the database

#### Scenario: Prevent deletion of goal with commitments
- **WHEN** user attempts to delete a Goal that has associated commitments
- **THEN** the system raises an error indicating the Goal cannot be deleted

#### Scenario: Prevent deletion of goal with children
- **WHEN** user attempts to delete a Goal that has child goals
- **THEN** the system raises an error indicating the Goal cannot be deleted

#### Scenario: Prevent deletion of goal with recurring commitments
- **WHEN** user attempts to delete a Goal that has associated RecurringCommitments
- **THEN** the system raises an error indicating the Goal cannot be deleted

### Requirement: Goal Status Transitions

The system SHALL enforce valid status transitions for Goals.

#### Scenario: Mark goal achieved
- **WHEN** user changes Goal status from "active" to "achieved"
- **THEN** the status is updated and updated_at is refreshed

#### Scenario: Mark goal abandoned
- **WHEN** user changes Goal status from "active" to "abandoned"
- **THEN** the status is updated and updated_at is refreshed

#### Scenario: Put goal on hold
- **WHEN** user changes Goal status from "active" to "on_hold"
- **THEN** the status is updated and updated_at is refreshed

#### Scenario: Reactivate goal
- **WHEN** user changes Goal status from "achieved", "abandoned", or "on_hold" back to "active"
- **THEN** the status is updated and updated_at is refreshed

### Requirement: Goal-Vision Association

The system SHALL support optional association between a Goal and a parent Vision.

**Field Addition**:
- `vision_id` (UUID | None): Optional reference to parent Vision

#### Scenario: Create goal linked to vision
- **WHEN** user creates a Goal with vision_id referencing an existing Vision
- **THEN** the Goal is associated with that Vision

#### Scenario: Create goal without vision
- **WHEN** user creates a Goal without specifying vision_id
- **THEN** the Goal exists independently without a parent Vision

#### Scenario: Query goals for vision
- **WHEN** user queries for goals linked to a specific Vision
- **THEN** the system returns all Goals with vision_id matching the Vision's id

#### Scenario: Validate vision exists
- **WHEN** user creates a Goal with a vision_id that doesn't exist
- **THEN** the system raises a foreign key validation error

#### Scenario: Prompt for vision linkage
- **WHEN** AI creates a goal draft without a vision_id and active visions exist
- **THEN** AI asks: "Would you like to link this goal to one of your visions?" and shows available visions

#### Scenario: Allow unlinked goal
- **WHEN** user declines to link goal to a vision
- **THEN** the goal is created with vision_id=NULL (allowed)

### Requirement: Goal-Milestone Relationship

The system SHALL support Milestones as children of Goals.

#### Scenario: Query milestones for goal
- **WHEN** user queries for milestones belonging to a Goal
- **THEN** the system returns all Milestones with goal_id matching the Goal's id

#### Scenario: Goal progress via milestones
- **WHEN** user views a Goal that has Milestones
- **THEN** the system displays milestone-based progress: "X of Y milestones completed"

#### Scenario: Suggest milestone creation
- **WHEN** user creates a Goal and confirms it
- **THEN** AI offers: "Would you like to break this into milestones? Milestones have concrete dates and make progress measurable."

### Requirement: Goal Deletion with Milestones

The system SHALL prevent deletion of Goals that have Milestones.

#### Scenario: Prevent deletion of goal with milestones
- **WHEN** user attempts to delete a Goal that has associated Milestones
- **THEN** the system raises an error: "Cannot delete goal with linked milestones. Delete the milestones first."

### Requirement: Goal Field Behavior with Vision

The system SHALL adjust field requirements based on Vision context.

#### Scenario: Goal with vision inherits context
- **WHEN** a Goal is linked to a Vision
- **THEN** the Goal's `problem_statement` and `solution_vision` fields remain available but are understood as goal-specific context (not the overarching vision)

#### Scenario: Standalone goal requires vision fields
- **WHEN** a Goal has no vision_id
- **THEN** the `problem_statement` and `solution_vision` fields are especially important for context

### Requirement: Vision Orphan Tracking

The system SHALL surface Goals without Vision linkage for user attention.

#### Scenario: List orphan goals
- **WHEN** user executes `/show orphan-goals`
- **THEN** the data panel shows all Goals where vision_id is NULL and status is "active"

#### Scenario: Orphan goal indicator
- **WHEN** displaying a goal without vision_id
- **THEN** an optional indicator can show it's not linked to a vision (configurable)

#### Scenario: Suggest linking orphan goals
- **WHEN** user views an orphan goal and active visions exist
- **THEN** AI may suggest: "This goal isn't connected to a vision. Would you like to link it?"

