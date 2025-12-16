# Capability: Milestone Management

Milestones are concrete checkpoints with specific target dates that break down aspirational Goals into achievable chunks. Every Milestone belongs to a Goal, and Commitments can optionally link to Milestones for structured progress tracking. Unlike Goals, Milestones have a "missed" status to support integrity tracking.

## ADDED Requirements

### Requirement: Milestone Model

The system SHALL provide a `Milestone` SQLModel with the following validated fields:
- `id` (UUID): Unique identifier, auto-generated
- `goal_id` (UUID): Reference to parent Goal, required
- `title` (str): Short descriptive name, required, non-empty
- `description` (str | None): Additional context about what achieving this milestone looks like
- `target_date` (date): The concrete deadline for this milestone, required
- `status` (MilestoneStatus enum): One of `pending`, `in_progress`, `completed`, `missed`; defaults to `pending`
- `completed_at` (datetime | None): Timestamp when marked complete
- `created_at` (datetime): Auto-set on creation, timezone-aware (EST default)
- `updated_at` (datetime): Auto-updated on modification, timezone-aware (EST default)

#### Scenario: Create milestone with required fields
- **WHEN** user creates a Milestone with goal_id, title, and target_date
- **THEN** a valid Milestone is created with status="pending" and auto-generated timestamps

#### Scenario: Reject milestone without goal
- **WHEN** user creates a Milestone without a goal_id
- **THEN** SQLModel validation raises an error

#### Scenario: Reject milestone without title
- **WHEN** user creates a Milestone with an empty title
- **THEN** SQLModel validation raises an error

#### Scenario: Reject milestone without target date
- **WHEN** user creates a Milestone without a target_date
- **THEN** SQLModel validation raises an error

#### Scenario: Validate goal exists
- **WHEN** user creates a Milestone with a goal_id that doesn't exist
- **THEN** the system raises a foreign key validation error

### Requirement: Milestone Status Transitions

The system SHALL enforce valid status transitions for Milestones, including automatic "missed" detection.

#### Scenario: Start working on milestone
- **WHEN** user changes Milestone status from "pending" to "in_progress"
- **THEN** the status is updated and updated_at is refreshed

#### Scenario: Complete milestone
- **WHEN** user changes Milestone status to "completed"
- **THEN** the status is updated, completed_at is set to current timestamp, and updated_at is refreshed

#### Scenario: Auto-transition to missed
- **WHEN** a Milestone's target_date has passed and status is still "pending"
- **THEN** the system automatically transitions status to "missed" on next query or daily check

#### Scenario: Late completion allowed
- **WHEN** user marks a "missed" Milestone as "completed"
- **THEN** the status is updated to "completed" with completed_at timestamp
- **AND** the late completion is tracked for integrity metrics (future feature)

#### Scenario: Reopen missed milestone
- **WHEN** user changes Milestone status from "missed" to "in_progress"
- **THEN** the status is updated and updated_at is refreshed (representing active recovery)

### Requirement: Milestone Persistence

The system SHALL persist Milestone entities to SQLite with full CRUD operations via SQLModel sessions.

#### Scenario: Save and retrieve milestone
- **WHEN** user saves a new Milestone via a database session
- **THEN** the Milestone is persisted to SQLite and can be retrieved by id

#### Scenario: List milestones for goal
- **WHEN** user queries milestones for a specific Goal
- **THEN** the system returns all Milestones with goal_id matching the Goal's id, sorted by target_date ascending

#### Scenario: List milestones with filters
- **WHEN** user queries milestones with status filter (e.g., status="in_progress")
- **THEN** the system returns only milestones matching the filter criteria

#### Scenario: Delete milestone without commitments
- **WHEN** user deletes a Milestone that has no associated Commitments
- **THEN** the Milestone is removed from the database

#### Scenario: Prevent deletion of milestone with commitments
- **WHEN** user attempts to delete a Milestone that has associated Commitments
- **THEN** the system raises an error: "Cannot delete milestone with linked commitments. Unlink or delete the commitments first."

### Requirement: Milestone-Commitment Relationship

The system SHALL support optional association between Commitments and Milestones.

#### Scenario: Query commitments for milestone
- **WHEN** user queries for commitments linked to a specific Milestone
- **THEN** the system returns all Commitments with milestone_id matching the Milestone's id

#### Scenario: Milestone progress calculation
- **WHEN** user views a Milestone
- **THEN** the system displays progress as: "X of Y commitments completed"

#### Scenario: Milestone without commitments
- **WHEN** a Milestone has no linked Commitments
- **THEN** the Milestone exists independently and AI suggests: "This milestone has no commitments yet. Would you like to create a commitment to work toward it?"

### Requirement: Milestone Due Date Queries

The system SHALL support efficient queries for milestones based on target dates.

#### Scenario: Query upcoming milestones
- **WHEN** user queries for milestones with target_date within the next N days
- **THEN** the system returns matching milestones sorted by target_date ascending

#### Scenario: Query overdue milestones
- **WHEN** user queries for milestones where target_date is before today and status is not "completed"
- **THEN** the system returns all overdue milestones (including "missed" status)

#### Scenario: Query milestones at risk
- **WHEN** user queries for milestones with target_date within 7 days and status="pending"
- **THEN** the system returns milestones that may miss their deadline

### Requirement: Milestone AI Assistance

The system SHALL use AI to help users break goals into meaningful milestones.

#### Scenario: Suggest milestones for goal
- **WHEN** user creates a Goal without milestones
- **THEN** AI offers: "Would you like to break this goal into milestones? Milestones are concrete checkpoints with dates."

#### Scenario: Generate milestone suggestions
- **WHEN** user accepts milestone suggestions for a goal
- **THEN** AI analyzes the goal and proposes 2-4 milestones with suggested target dates

#### Scenario: Validate milestone dates
- **WHEN** AI suggests milestones
- **THEN** suggested target_dates are spaced reasonably and ordered chronologically

### Requirement: Goal Progress via Milestones

The system SHALL calculate goal progress based on milestone completion.

#### Scenario: Goal with milestones shows progress
- **WHEN** user views a Goal that has Milestones
- **THEN** the data panel shows: "Progress: X of Y milestones completed (Z%)"

#### Scenario: Goal without milestones shows no progress
- **WHEN** user views a Goal that has no Milestones
- **THEN** the data panel shows: "No milestones defined" with option to create

#### Scenario: Progress updates on milestone completion
- **WHEN** a Milestone is marked completed
- **THEN** the parent Goal's progress percentage is recalculated
