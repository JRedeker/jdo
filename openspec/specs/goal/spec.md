# goal Specification

## Purpose
Define the Goal domain model representing desired outcomes with problem statements and solution visions, supporting hierarchical nesting, vision associations, milestone tracking, and periodic review workflows.
## Requirements
### Requirement: Goal Model

The system SHALL provide a `Goal` SQLModel with the following validated fields:
- `id` (UUID): Unique identifier, auto-generated
- `title` (str): Short descriptive name, required, non-empty
- `problem_statement` (str): Description of the problem or gap being addressed, required, non-empty
- `solution_vision` (str): Description of the desired future state, required, non-empty
- `motivation` (str | None): Why this goal matters to the user (growth mindset reinforcement)
- `parent_goal_id` (UUID | None): Optional reference to parent Goal for nesting
- `status` (GoalStatus enum): One of `active`, `on_hold`, `achieved`, `abandoned`; defaults to `active`
- `next_review_date` (date | None): When the user should next review this goal
- `review_interval_days` (int | None): Optional recurring review cadence; only 7 (weekly), 30 (monthly), or 90 (quarterly) allowed
- `last_reviewed_at` (datetime | None): When the user last reviewed this goal
- `created_at` (datetime): Auto-set on creation, timezone-aware (EST default)
- `updated_at` (datetime): Auto-updated on modification, timezone-aware (EST default)

#### Scenario: Create goal with required fields
- **WHEN** user creates a Goal with title, problem_statement, and solution_vision
- **THEN** a valid Goal is created with status="active" and auto-generated timestamps

#### Scenario: Create goal with motivation
- **WHEN** user creates a Goal with title, problem_statement, solution_vision, and motivation
- **THEN** the Goal stores the motivation for display during reviews

#### Scenario: Create goal with review schedule
- **WHEN** user creates a Goal with next_review_date and review_interval_days=30
- **THEN** the Goal is scheduled for review on the specified date with monthly recurrence

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

The system SHALL support status transitions that reflect goal lifecycle without implying deadline-based completion. GoalStatus enum values: `active`, `on_hold`, `achieved`, `abandoned`.

#### Scenario: Mark goal active
- **WHEN** user sets Goal status to "active"
- **THEN** the goal is actively being pursued and updated_at is refreshed

#### Scenario: Put goal on hold
- **WHEN** user changes Goal status to "on_hold"
- **THEN** the goal is temporarily paused and updated_at is refreshed

#### Scenario: Mark goal achieved
- **WHEN** user changes Goal status to "achieved"
- **THEN** the vision is marked as realized and updated_at is refreshed

#### Scenario: Mark goal abandoned
- **WHEN** user changes Goal status to "abandoned"
- **THEN** the goal is explicitly discontinued and updated_at is refreshed

#### Scenario: Reactivate goal from any status
- **WHEN** user changes Goal status from "on_hold", "achieved", or "abandoned" to "active"
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

### Requirement: Goal Review System

The system SHALL support periodic goal reviews to maintain alignment and growth mindset.

#### Scenario: Identify goals due for review
- **WHEN** user queries goals due for review
- **THEN** the system returns all active goals where next_review_date <= today

#### Scenario: Complete goal review
- **WHEN** user completes a goal review
- **THEN** last_reviewed_at is set to current timestamp

#### Scenario: Schedule next review after completion
- **WHEN** user completes a review for a goal with review_interval_days set
- **THEN** next_review_date is updated to today + review_interval_days

#### Scenario: One-time review
- **WHEN** user completes a review for a goal without review_interval_days
- **THEN** next_review_date is cleared (no automatic next review)

#### Scenario: Skip review for on-hold goals
- **WHEN** querying goals due for review
- **THEN** goals with status="on_hold" are excluded from the results

### Requirement: Goal Commitment Progress

The system SHALL display aggregated commitment progress when viewing a goal.

#### Scenario: Show commitment counts
- **WHEN** user views a Goal that has associated commitments
- **THEN** the system displays counts of completed, in_progress, pending, and abandoned commitments

#### Scenario: Show progress for goal without commitments
- **WHEN** user views a Goal with no associated commitments
- **THEN** the system indicates no commitments are linked to this goal

#### Scenario: Progress does not determine status
- **WHEN** all commitments under a Goal are completed
- **THEN** the Goal status remains unchanged (user must explicitly change status)

### Requirement: Goal Review Commands

The system SHALL provide commands for goal review in the conversational TUI. These commands extend the `/goal` command defined in `tui-chat` capability.

#### Scenario: List goals due for review
- **WHEN** user types `/goal review`
- **THEN** the system lists all active goals where next_review_date <= today

#### Scenario: Review specific goal
- **WHEN** user types `/goal review <id>`
- **THEN** the system displays the goal review interface for that goal

#### Scenario: Review interface shows motivation
- **WHEN** user enters goal review
- **THEN** the motivation field is prominently displayed to reconnect with purpose

#### Scenario: Review interface shows commitment progress
- **WHEN** user enters goal review
- **THEN** commitment progress summary is displayed

#### Scenario: Review prompts reflection
- **WHEN** user enters goal review
- **THEN** the system prompts with reflection questions about alignment and next steps

### Requirement: Goal Creation Prompts

The system SHALL guide users to articulate vision and motivation during goal creation.

#### Scenario: Prompt for motivation during creation
- **WHEN** user creates a goal via conversational interface
- **THEN** AI asks "Why does this goal matter to you?" after collecting required fields

#### Scenario: Motivation is optional
- **WHEN** user declines to provide motivation
- **THEN** the goal is created with motivation=None

#### Scenario: Suggest review interval
- **WHEN** user creates a goal
- **THEN** AI presents fixed review interval options: weekly (7 days), monthly (30 days), or quarterly (90 days)

### Requirement: Review Interval Constraints

The system SHALL offer only fixed review interval options to keep the experience simple.

#### Scenario: Fixed interval options only
- **WHEN** user sets or modifies review_interval_days
- **THEN** only values 7 (weekly), 30 (monthly), or 90 (quarterly) are accepted

#### Scenario: Reject custom intervals
- **WHEN** user attempts to set review_interval_days to a non-standard value
- **THEN** the system prompts to choose from weekly, monthly, or quarterly

#### Scenario: Display interval as label
- **WHEN** displaying a goal with review_interval_days set
- **THEN** the system shows "Weekly", "Monthly", or "Quarterly" instead of raw day count

### Requirement: Goal Display Emphasis

The system SHALL display goals with emphasis on vision over completion.

#### Scenario: Display vision prominently
- **WHEN** viewing a goal in the data panel
- **THEN** solution_vision and motivation are displayed prominently above status

#### Scenario: Show next review date
- **WHEN** viewing an active goal with next_review_date set
- **THEN** the next review date is displayed

#### Scenario: Indicate goals due for review
- **WHEN** displaying a goal where next_review_date <= today
- **THEN** a visual indicator shows the goal is due for review

#### Scenario: De-emphasize achieved status
- **WHEN** displaying goal status options
- **THEN** "achieved" is presented as a rare, intentional choice, not the expected outcome

