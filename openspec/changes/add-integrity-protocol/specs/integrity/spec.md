# Capability: Integrity Protocol

The Integrity Protocol implements MPI's Honor-Your-Word framework: when commitments can't be met, users follow a structured recovery process (notify stakeholders, clean up impact). This capability provides the CleanupPlan entity, notification task workflow, integrity metrics, and scoring.

## ADDED Requirements

### Requirement: CleanupPlan Model

The system SHALL provide a `CleanupPlan` SQLModel that tracks the recovery workflow when a commitment is at-risk or abandoned.

Fields:
- `id` (UUID): Unique identifier, auto-generated
- `commitment_id` (UUID): Reference to the at-risk/abandoned Commitment, required
- `impact_description` (str | None): Description of what harm missing this commitment causes
- `mitigation_actions` (list[str]): Actions the user will take to mitigate impact (stored as JSON)
- `notification_task_id` (UUID | None): Reference to the auto-created notification Task
- `status` (CleanupPlanStatus enum): One of `planned`, `in_progress`, `completed`, `skipped`, `cancelled`; defaults to `planned`
- `completed_at` (datetime | None): Timestamp when CleanupPlan was completed
- `skipped_reason` (str | None): User's acknowledgment when skipping cleanup
- `created_at` (datetime): Auto-set on creation
- `updated_at` (datetime): Auto-updated on modification

#### Scenario: Create cleanup plan when commitment marked at-risk
- **WHEN** a Commitment status changes to "at_risk"
- **THEN** a CleanupPlan is automatically created with status="planned" and linked to the commitment

#### Scenario: Cleanup plan requires commitment
- **WHEN** user attempts to create a CleanupPlan without a commitment_id
- **THEN** SQLModel validation raises an error

#### Scenario: One cleanup plan per commitment
- **WHEN** a Commitment already has a CleanupPlan and status changes to at_risk again
- **THEN** the existing CleanupPlan is reused (not duplicated)

### Requirement: Notification Task Creation

The system SHALL auto-create a notification Task when a commitment is marked at-risk, positioned as the first task to complete.

#### Scenario: Create notification task on at-risk
- **WHEN** a Commitment is marked as "at_risk"
- **THEN** a Task is created with:
  - `title`: "Notify [Stakeholder name] about at-risk commitment"
  - `order`: 0 (first position)
  - `is_notification_task`: True
  - `scope`: AI-drafted notification content

#### Scenario: Notification task scope contains draft
- **WHEN** a notification task is created
- **THEN** the scope field contains a structured notification draft including:
  - Stakeholder name and commitment deliverable
  - User-provided reason for risk (prompted during at-risk marking)
  - Due date and proposed resolution
  - Instruction to mark task complete after sending

#### Scenario: Notification task completion updates cleanup plan
- **WHEN** user marks the notification task as "completed"
- **THEN** the associated CleanupPlan status changes from "planned" to "in_progress"

#### Scenario: Notification task cannot be skipped
- **WHEN** user attempts to mark notification task as "skipped"
- **THEN** the system warns: "Skipping stakeholder notification affects your integrity. Are you sure?" and requires confirmation

### Requirement: CleanupPlan Status Transitions

The system SHALL track CleanupPlan progress through the recovery workflow.

#### Scenario: Transition to in_progress
- **WHEN** the notification task is completed
- **THEN** CleanupPlan status changes to "in_progress"

#### Scenario: Transition to completed via commitment completion
- **WHEN** the associated Commitment is marked "completed" (late recovery)
- **THEN** CleanupPlan status changes to "completed" with completed_at timestamp

#### Scenario: Transition to completed via abandonment with cleanup
- **WHEN** the associated Commitment is marked "abandoned" and notification task is completed
- **THEN** CleanupPlan status changes to "completed" with completed_at timestamp

#### Scenario: Transition to skipped
- **WHEN** user abandons commitment without completing notification task and confirms override
- **THEN** CleanupPlan status changes to "skipped" with skipped_reason recorded

#### Scenario: Transition to cancelled on recovery
- **WHEN** the associated Commitment recovers from "at_risk" to "in_progress"
- **THEN** CleanupPlan status changes to "cancelled" (commitment no longer needs cleanup)

### Requirement: Integrity Metrics Calculation

The system SHALL calculate integrity metrics from commitment history to measure reliability.

#### Scenario: Calculate on-time delivery rate
- **WHEN** system calculates on_time_rate metric
- **THEN** it returns (count of commitments where completed_on_time=True) / (total completed commitments)
- **AND** returns 1.0 if no commitments have been completed yet

#### Scenario: Calculate notification timeliness
- **WHEN** system calculates notification_timeliness metric
- **THEN** it returns 1.0 (clean slate default)

**Note**: Full timeliness calculation (measuring days between marked_at_risk_at and due_date) deferred to future iteration.

#### Scenario: Calculate cleanup completion rate
- **WHEN** system calculates cleanup_completion_rate metric
- **THEN** it returns (CleanupPlans with status=completed) / (total CleanupPlans)
- **AND** returns 1.0 if no cleanup plans exist

#### Scenario: Calculate reliability streak
- **WHEN** system calculates current_streak_weeks metric
- **THEN** it returns 0 (no streak tracking yet)

**Note**: Full streak calculation (counting consecutive on-time weeks) deferred to future iteration.

### Requirement: Integrity Score Calculation

The system SHALL calculate a composite integrity score from weighted metrics, displayed as a letter grade.

#### Scenario: Calculate composite score
- **WHEN** system calculates integrity score
- **THEN** it computes: (on_time_rate * 0.40) + (notification_timeliness * 0.25) + (cleanup_completion_rate * 0.25) + (streak_bonus * 0.10)
- **AND** streak_bonus is min(current_streak_weeks * 2, 10) / 100

#### Scenario: Convert score to letter grade
- **WHEN** displaying integrity score
- **THEN** the system converts percentage to letter grade:
  - A+: 97-100, A: 93-96, A-: 90-92
  - B+: 87-89, B: 83-86, B-: 80-82
  - C+: 77-79, C: 73-76, C-: 70-72
  - D+: 67-69, D: 63-66, D-: 60-62
  - F: below 60

#### Scenario: New user starts with A-
- **WHEN** user has no commitment history
- **THEN** integrity score displays as "A-" (90 score: 1.0 on_time + 1.0 timeliness + 1.0 cleanup + 0 streak bonus)

#### Scenario: Score updates on commitment status change
- **WHEN** any commitment status changes to completed, abandoned, or at_risk
- **THEN** integrity metrics are recalculated for next display

### Requirement: Integrity Dashboard

The system SHALL provide an integrity dashboard showing metrics breakdown.

#### Scenario: Display integrity dashboard
- **WHEN** user requests integrity view
- **THEN** the system displays:
  - Overall letter grade prominently
  - On-time delivery rate as percentage
  - Notification timeliness rating
  - Cleanup completion rate as percentage
  - Current reliability streak in weeks

#### Scenario: Display metric trends (Deferred)
- **WHEN** user views integrity dashboard
- **THEN** trend indicators are not yet implemented

**Note**: Metric trends deferred to future iteration.

#### Scenario: Display commitments affecting score (Deferred)
- **WHEN** user views integrity dashboard
- **THEN** commitment impact list is not yet implemented

**Note**: Commitment impact list deferred to future iteration.


