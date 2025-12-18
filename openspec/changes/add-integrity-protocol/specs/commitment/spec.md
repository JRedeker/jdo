# Capability: Commitment Management (Integrity Protocol Extension)

This spec extends the base Commitment model to add the `at_risk` status and fields supporting the Honor-Your-Word protocol.

**Cross-reference**: See `specs/commitment/spec.md` for the base Commitment model definition.

## ADDED Requirements

### Requirement: At-Risk Status

The system SHALL support an `at_risk` status for commitments that may not be met and require stakeholder notification.

**Field Additions to Commitment model**:
- `marked_at_risk_at` (datetime | None): Timestamp when marked at-risk
- `completed_on_time` (bool | None): Whether commitment was completed by due date (set on completion)

**CommitmentStatus enum addition**:
- `at_risk`: Commitment is in jeopardy and stakeholder notification is required

#### Scenario: Mark commitment at-risk
- **WHEN** user changes Commitment status to "at_risk"
- **THEN** the status is updated, marked_at_risk_at is set to current timestamp, and updated_at is refreshed

#### Scenario: Complete commitment on time
- **WHEN** user marks Commitment as "completed" and current datetime is before or equal to due_date + due_time
- **THEN** completed_on_time is set to True

#### Scenario: Complete commitment late
- **WHEN** user marks Commitment as "completed" and current datetime is after due_date + due_time
- **THEN** completed_on_time is set to False

### Requirement: At-Risk Status Transitions

The system SHALL enforce valid status transitions involving the `at_risk` status.

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
