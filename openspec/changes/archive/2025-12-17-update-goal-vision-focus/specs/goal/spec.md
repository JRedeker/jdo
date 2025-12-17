# Capability: Goal Management (Vision-Focus Extension)

Goals provide forward-looking vision that gives commitments meaning. Unlike commitments which enforce integrity through concrete deadlines, goals are aspirational directions that users review periodically to ensure alignment with their growth.

**Cross-reference**: See `add-core-domain-models/specs/goal` for base Goal model. See `add-vision-milestone-hierarchy/specs/goal` for `vision_id` field that links Goals to Visions.

## MODIFIED Requirements

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

## ADDED Requirements

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

## Notes

**Design Decision**: Goals intentionally do not have due dates (`target_date` field). This reflects the vision-focused philosophy where goals are aspirational directions reviewed periodically, not deadline-based targets.
