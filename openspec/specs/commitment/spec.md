# commitment Specification

## Purpose
Define the Commitment domain model representing promises made to stakeholders with specific deliverables and due dates, including status tracking, goal/milestone associations, and task breakdown support.
## Requirements
### Requirement: Commitment Model

The system SHALL extend the Commitment model with the following field:

**Field Addition**:
- `recurring_commitment_id` (UUID | None): Optional reference to parent RecurringCommitment template

#### Scenario: Create commitment from recurring template
- **WHEN** system generates a Commitment from a RecurringCommitment
- **THEN** the Commitment has recurring_commitment_id set to the template's id

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

### Requirement: Recurring Instance Linking

The system SHALL support linking Commitment instances to their RecurringCommitment template.

#### Scenario: Query instances by recurring template
- **WHEN** user queries commitments with recurring_commitment_id filter
- **THEN** the system returns all instances generated from that template

#### Scenario: Instance remains after template deletion
- **WHEN** a RecurringCommitment is deleted
- **THEN** existing Commitment instances retain their data and recurring_commitment_id is set to NULL (ON DELETE SET NULL)

#### Scenario: Trigger next generation on completion
- **WHEN** user completes a Commitment that has a recurring_commitment_id
- **THEN** the system checks whether to generate the next instance from the template

