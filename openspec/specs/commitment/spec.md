# commitment Specification

## Purpose
Define the Commitment domain model representing promises made to stakeholders with specific deliverables and due dates, including status tracking, goal/milestone associations, and task breakdown support.
## Requirements
### Requirement: Commitment Model

The system SHALL provide a `Commitment` SQLModel with the following validated fields:
- `id` (UUID): Unique identifier, auto-generated
- `deliverable` (str): What is being delivered, required, non-empty
- `stakeholder_id` (UUID): Reference to Stakeholder, required
- `goal_id` (UUID | None): Optional reference to parent Goal
- `due_date` (date): The date the commitment is due, required
- `due_time` (time | None): Optional specific time of day when due; defaults to 09:00 if not specified
- `timezone` (str): Timezone for due_time interpretation, defaults to "America/New_York"
- `status` (CommitmentStatus enum): One of `pending`, `in_progress`, `completed`, `abandoned`; defaults to `pending`. Note: Commitments cannot be "skipped" - they are either completed (met) or abandoned (missed/cancelled).
- `completed_at` (datetime | None): Timestamp when marked complete
- `notes` (str | None): Optional additional context
- `created_at` (datetime): Auto-set on creation, timezone-aware (EST default)
- `updated_at` (datetime): Auto-updated on modification, timezone-aware (EST default)

#### Scenario: Create commitment with required fields
- **WHEN** user creates a Commitment with deliverable="Send report", stakeholder_id, and due_date
- **THEN** a valid Commitment is created with status="pending" and auto-generated timestamps

#### Scenario: Create commitment with specific due time
- **WHEN** user creates a Commitment with due_date and due_time="15:00" and timezone="America/New_York"
- **THEN** the Commitment records both date and time for precise deadline tracking

#### Scenario: Create commitment without specific time
- **WHEN** user creates a Commitment with due_date but no due_time
- **THEN** the due_time defaults to 09:00 (start of business) in the user's timezone

#### Scenario: Reject commitment without deliverable
- **WHEN** user creates a Commitment with an empty deliverable
- **THEN** SQLModel validation raises an error

#### Scenario: Reject commitment without stakeholder
- **WHEN** user creates a Commitment without a stakeholder_id
- **THEN** SQLModel validation raises an error

#### Scenario: Reject commitment without due date
- **WHEN** user creates a Commitment without a due_date
- **THEN** SQLModel validation raises an error

### Requirement: Commitment-Goal Association

The system SHALL support optional association between a Commitment and a single parent Goal.

#### Scenario: Create commitment under goal
- **WHEN** user creates a Commitment with goal_id referencing an existing Goal
- **THEN** the Commitment is associated with that Goal

#### Scenario: List commitments for goal
- **WHEN** user queries commitments for a specific Goal
- **THEN** the system returns all Commitments with goal_id matching the Goal's id

#### Scenario: Create commitment without goal
- **WHEN** user creates a Commitment without specifying goal_id
- **THEN** the Commitment exists independently without a parent Goal

### Requirement: Commitment Persistence

The system SHALL persist Commitment entities to SQLite with full CRUD operations via SQLModel sessions.

#### Scenario: Save and retrieve commitment
- **WHEN** user saves a new Commitment via a database session
- **THEN** the Commitment is persisted to SQLite and can be retrieved by id

#### Scenario: List commitments with filters
- **WHEN** user queries commitments with filters (e.g., status="pending", due before date)
- **THEN** the system returns only commitments matching all filter criteria

#### Scenario: Delete commitment
- **WHEN** user deletes a Commitment
- **THEN** the Commitment and all associated Tasks are removed from the database

### Requirement: Commitment Status Transitions

The system SHALL enforce explicit user completion of commitments. Completing all tasks does not automatically complete the commitment. However, starting a task automatically transitions the commitment to in_progress.

#### Scenario: Start working on commitment
- **WHEN** user changes Commitment status from "pending" to "in_progress"
- **THEN** the status is updated and updated_at is refreshed

#### Scenario: Task start auto-transitions commitment
- **WHEN** a Task under a pending Commitment is changed to "in_progress"
- **THEN** the parent Commitment status automatically transitions to "in_progress"

#### Scenario: Task start does not change non-pending commitment
- **WHEN** a Task is changed to "in_progress" under a Commitment that is already "in_progress", "completed", or "abandoned"
- **THEN** the Commitment status remains unchanged

#### Scenario: Complete commitment explicitly
- **WHEN** user changes Commitment status to "completed"
- **THEN** the status is updated, completed_at is set to current timestamp, and updated_at is refreshed

#### Scenario: Completing tasks does not auto-complete commitment
- **WHEN** all Tasks for a Commitment are marked completed
- **THEN** the Commitment status remains unchanged until user explicitly marks it complete

#### Scenario: Abandon commitment
- **WHEN** user changes Commitment status to "abandoned"
- **THEN** the status is updated and updated_at is refreshed

#### Scenario: Reopen completed commitment
- **WHEN** user changes Commitment status from "completed" back to "in_progress"
- **THEN** the status is updated, completed_at is cleared, and updated_at is refreshed

### Requirement: Commitment Due Date Queries

The system SHALL support efficient queries for commitments based on due dates.

#### Scenario: Query overdue commitments
- **WHEN** user queries for commitments where due_date is before today and status is not "completed" or "abandoned"
- **THEN** the system returns all overdue commitments sorted by due_date ascending

#### Scenario: Query commitments due soon
- **WHEN** user queries for commitments due within the next N days
- **THEN** the system returns matching commitments sorted by due_date ascending

#### Scenario: Query commitments due today with time
- **WHEN** user queries for commitments due today
- **THEN** the system returns commitments sorted by due_date time component ascending

### Requirement: Commitment Status Semantics

The system SHALL enforce clear semantics for commitment outcomes: completed means the commitment was met, abandoned means it was missed or cancelled.

#### Scenario: No skipped status for commitments
- **WHEN** user attempts to set Commitment status to "skipped"
- **THEN** the system rejects the status (skipped is only valid for Tasks)

#### Scenario: Abandoned indicates missed commitment
- **WHEN** user marks a Commitment as "abandoned"
- **THEN** it represents either a missed deadline or an intentional cancellation of the commitment

### Requirement: Commitment-Milestone Association

The system SHALL support optional association between a Commitment and a Milestone.

**Field Addition**:
- `milestone_id` (UUID | None): Optional reference to parent Milestone

#### Scenario: Create commitment linked to milestone
- **WHEN** user creates a Commitment with milestone_id referencing an existing Milestone
- **THEN** the Commitment is associated with that Milestone

#### Scenario: Create commitment without milestone
- **WHEN** user creates a Commitment without specifying milestone_id
- **THEN** the Commitment exists independently without a parent Milestone

#### Scenario: Query commitments for milestone
- **WHEN** user queries for commitments linked to a specific Milestone
- **THEN** the system returns all Commitments with milestone_id matching the Milestone's id

#### Scenario: Validate milestone exists
- **WHEN** user creates a Commitment with a milestone_id that doesn't exist
- **THEN** the system raises a foreign key validation error

### Requirement: Flexible Commitment Linkage

The system SHALL support commitments linked through either Goal or Milestone (or both, or neither).

#### Scenario: Commitment with milestone only
- **WHEN** user creates a Commitment with milestone_id but no goal_id
- **THEN** the Commitment is valid and inherits Goal context through the Milestone's goal_id

#### Scenario: Commitment with goal only
- **WHEN** user creates a Commitment with goal_id but no milestone_id
- **THEN** the Commitment is valid and directly linked to the Goal (simpler case)

#### Scenario: Commitment with both
- **WHEN** user creates a Commitment with both milestone_id and goal_id
- **THEN** the Commitment is valid (goal_id should match milestone's goal_id for consistency)

#### Scenario: Commitment with neither (orphan)
- **WHEN** user creates a Commitment with neither milestone_id nor goal_id
- **THEN** the Commitment is valid but surfaced in orphan tracking

### Requirement: Orphan Commitment Tracking (Extended)

The system SHALL track commitments not linked to goals OR milestones.

#### Scenario: Orphan definition
- **WHEN** determining if a commitment is an orphan
- **THEN** a commitment is orphan if BOTH goal_id IS NULL AND milestone_id IS NULL

#### Scenario: Partial linkage is not orphan
- **WHEN** a commitment has milestone_id but no goal_id
- **THEN** it is NOT considered orphan (it has hierarchy linkage through milestone)

#### Scenario: Display orphan status
- **WHEN** viewing an orphan commitment
- **THEN** the data panel shows an indicator that it's not linked to goals or milestones

### Requirement: Commitment Deletion with Milestone Link

The system SHALL handle commitment deletion consistently regardless of milestone linkage.

#### Scenario: Delete commitment with milestone link
- **WHEN** user deletes a Commitment that has a milestone_id
- **THEN** the Commitment and all associated Tasks are removed from the database
- **AND** the Milestone's commitment count is decremented

### Requirement: Milestone Progress via Commitments

The system SHALL calculate Milestone progress based on its linked Commitments.

#### Scenario: Commitment completion affects milestone
- **WHEN** a Commitment linked to a Milestone is marked completed
- **THEN** the Milestone's progress (X of Y commitments) is updated

#### Scenario: Milestone progress query
- **WHEN** viewing a Milestone
- **THEN** the system shows: "Commitments: X completed, Y in progress, Z pending"

### Requirement: AI Commitment Linking

The system SHALL guide users to link commitments appropriately.

#### Scenario: Prompt for milestone linkage
- **WHEN** AI creates a commitment draft and the selected goal has milestones
- **THEN** AI asks: "Which milestone is this commitment working toward?" and shows available milestones

#### Scenario: Prompt for goal linkage when no milestones
- **WHEN** AI creates a commitment draft and the selected goal has no milestones
- **THEN** AI links directly to the goal without asking about milestones

#### Scenario: Suggest creating milestone
- **WHEN** user creates multiple commitments for a goal without milestones
- **THEN** AI suggests: "You have several commitments for this goal. Would you like to organize them into milestones?"

