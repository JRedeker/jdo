# Capability: Commitment Management (Integrity Protocol Extension)

This spec extends the base Commitment model from `add-core-domain-models` to add the `at_risk` status and fields supporting the Honor-Your-Word protocol.

**Cross-reference**: See `add-core-domain-models/specs/commitment` for the base Commitment model definition.

## MODIFIED Requirements

### Requirement: Commitment Model

The system SHALL provide a `Commitment` SQLModel with the following validated fields:
- `id` (UUID): Unique identifier, auto-generated
- `deliverable` (str): What is being delivered, required, non-empty
- `stakeholder_id` (UUID): Reference to Stakeholder, required
- `goal_id` (UUID | None): Optional reference to parent Goal
- `due_date` (date): The date the commitment is due, required
- `due_time` (time | None): Optional specific time of day when due; defaults to 09:00 if not specified
- `timezone` (str): Timezone for due_time interpretation, defaults to "America/New_York"
- `status` (CommitmentStatus enum): One of `pending`, `in_progress`, `at_risk`, `completed`, `abandoned`; defaults to `pending`
- `completed_at` (datetime | None): Timestamp when marked complete
- `marked_at_risk_at` (datetime | None): Timestamp when marked at-risk (NEW)
- `completed_on_time` (bool | None): Whether commitment was completed by due date (NEW, set on completion)
- `notes` (str | None): Optional additional context
- `created_at` (datetime): Auto-set on creation, timezone-aware (EST default)
- `updated_at` (datetime): Auto-updated on modification, timezone-aware (EST default)

#### Scenario: Create commitment with required fields
- **WHEN** user creates a Commitment with deliverable="Send report", stakeholder_id, and due_date
- **THEN** a valid Commitment is created with status="pending" and auto-generated timestamps

#### Scenario: Mark commitment at-risk
- **WHEN** user changes Commitment status to "at_risk"
- **THEN** the status is updated, marked_at_risk_at is set to current timestamp, and updated_at is refreshed

#### Scenario: Complete commitment on time
- **WHEN** user marks Commitment as "completed" and current datetime is before or equal to due_date + due_time
- **THEN** completed_on_time is set to True

#### Scenario: Complete commitment late
- **WHEN** user marks Commitment as "completed" and current datetime is after due_date + due_time
- **THEN** completed_on_time is set to False

### Requirement: Commitment Status Transitions

The system SHALL enforce valid status transitions for Commitments, including the new `at_risk` status.

#### Scenario: Transition to at-risk from in_progress
- **WHEN** user changes Commitment status from "in_progress" to "at_risk"
- **THEN** the status is updated, marked_at_risk_at is set, and a CleanupPlan is created

#### Scenario: Transition to at-risk from pending
- **WHEN** user changes Commitment status from "pending" to "at_risk"
- **THEN** the status is updated, marked_at_risk_at is set, and a CleanupPlan is created

#### Scenario: Recover from at-risk to in_progress
- **WHEN** user changes Commitment status from "at_risk" to "in_progress"
- **THEN** the status is updated (marked_at_risk_at is preserved for metrics)

#### Scenario: Complete at-risk commitment
- **WHEN** user changes Commitment status from "at_risk" to "completed"
- **THEN** the status is updated, completed_at is set, completed_on_time is calculated, and associated CleanupPlan status changes to "completed"

#### Scenario: Abandon at-risk commitment with cleanup
- **WHEN** user changes Commitment status from "at_risk" to "abandoned" and CleanupPlan notification task is completed
- **THEN** the status is updated and CleanupPlan status changes to "completed"

#### Scenario: Abandon at-risk commitment without cleanup (soft enforcement)
- **WHEN** user changes Commitment status from "at_risk" to "abandoned" and CleanupPlan notification task is NOT completed
- **THEN** the system warns: "You haven't notified [stakeholder] yet. This will affect your integrity score. Continue anyway?"
- **AND** if user confirms, status is updated and CleanupPlan status changes to "skipped"

#### Scenario: Abandon commitment directly (bypass at-risk)
- **WHEN** user changes Commitment status directly from "pending" or "in_progress" to "abandoned"
- **THEN** the system prompts: "Would you like to notify [stakeholder] before abandoning? This maintains your integrity." with options to mark at-risk first or abandon directly

### Requirement: At-Risk Commitment Queries

The system SHALL support efficient queries for at-risk commitments.

#### Scenario: Query at-risk commitments
- **WHEN** user queries for commitments with status="at_risk"
- **THEN** the system returns all at-risk commitments sorted by due_date ascending

#### Scenario: Query active commitments includes at-risk
- **WHEN** user queries for "active" commitments
- **THEN** the system returns commitments with status in ("pending", "in_progress", "at_risk")

#### Scenario: Query notification timeliness
- **WHEN** system calculates notification timeliness metric
- **THEN** it uses (due_date - marked_at_risk_at) for at-risk commitments to measure early warning
