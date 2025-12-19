# integrity Specification

## Purpose
TBD - created by archiving change add-ai-coaching-time-management. Update Purpose after archive.
## Requirements
### Requirement: Task History Logging

The system SHALL maintain an immutable audit log of task lifecycle events for AI learning and pattern analysis.

#### Scenario: Log task creation
- **WHEN** a Task is created
- **THEN** a TaskHistoryEntry is created with event_type="created", new_status=pending, and estimated_hours snapshot

#### Scenario: Log task status change
- **WHEN** a Task status changes from pending to in_progress
- **THEN** a TaskHistoryEntry is created with event_type="started", previous_status=pending, new_status=in_progress

#### Scenario: Log task completion with actual hours
- **WHEN** a Task status changes to completed
- **THEN** a TaskHistoryEntry is created with event_type="completed", actual_hours recorded, and estimated_hours snapshot

#### Scenario: Log task skip with reason
- **WHEN** a Task status changes to skipped
- **THEN** a TaskHistoryEntry is created with event_type="skipped" and notes containing skip reason if provided

#### Scenario: History entries are immutable at application layer
- **WHEN** a TaskHistoryEntry is created
- **THEN** the application layer provides no update or delete methods for the entry
- **AND** only insert operations are supported by the TaskHistoryService

#### Scenario: Query history by commitment
- **WHEN** system queries task history for a commitment_id
- **THEN** all TaskHistoryEntry records with matching commitment_id are returned ordered by created_at

#### Scenario: History survives task deletion
- **WHEN** a Task is deleted
- **THEN** associated TaskHistoryEntry records are preserved with task_id reference

### Requirement: Estimation Accuracy Metric

The system SHALL calculate estimation accuracy from task history to measure how well users predict effort, using exponential time decay weighting.

#### Scenario: Calculate estimation accuracy for completed tasks
- **WHEN** system calculates estimation_accuracy metric
- **THEN** it compares estimated_hours vs actual_hours_category for completed tasks with both values
- **AND** returns 1.0 minus normalized variance (perfect accuracy = 1.0, >100% variance = 0.0)

#### Scenario: Actual hours from category labels
- **WHEN** calculating actual hours for accuracy
- **THEN** category labels map to variance multipliers:
  - "much_shorter" = 0.25x estimate (75% under)
  - "shorter" = 0.675x estimate (32.5% under)
  - "on_target" = 1.0x estimate (0% variance)
  - "longer" = 1.325x estimate (32.5% over)
  - "much_longer" = 2.0x estimate (100% over)

#### Scenario: Skip tasks without estimates in accuracy calculation
- **WHEN** calculating estimation_accuracy
- **AND** a completed task has no estimated_hours
- **THEN** that task is excluded from the calculation

#### Scenario: Default accuracy for insufficient history
- **WHEN** calculating estimation_accuracy
- **AND** fewer than 5 completed tasks have both estimated and actual hours category
- **THEN** return 1.0 (benefit of the doubt for new users)

#### Scenario: Exponential decay weighting
- **WHEN** calculating estimation_accuracy with sufficient data
- **THEN** tasks are weighted by recency using exponential decay
- **AND** tasks from last 7 days have full weight (1.0)
- **AND** weight halves every 7 days (14 days = 0.5, 21 days = 0.25, etc.)
- **AND** tasks older than 90 days are excluded

#### Scenario: Accuracy calculation formula
- **WHEN** calculating estimation_accuracy with sufficient data
- **THEN** for each task: variance = abs(actual_multiplier - 1.0)
- **AND** weighted average variance across all qualifying tasks
- **AND** accuracy = max(0, 1 - weighted_average_variance)

### Requirement: Integrity Score with Estimation Weight

The system SHALL include estimation_accuracy in the composite integrity score calculation.

#### Scenario: Updated composite score formula
- **WHEN** system calculates composite integrity score
- **THEN** it computes: (on_time_rate * 0.35 + notification_timeliness * 0.25 + cleanup_completion_rate * 0.25 + estimation_accuracy * 0.10 + streak_bonus) * 100
- **AND** streak_bonus = min(current_streak_weeks * 2, 5) / 100 (max 5%)

#### Scenario: Streak bonus cap reduced
- **WHEN** calculating streak_bonus component
- **THEN** streak_bonus is capped at 5% (was 10%) to make room for estimation_accuracy

#### Scenario: Letter grade thresholds unchanged
- **WHEN** converting composite score to letter grade
- **THEN** existing thresholds apply (A+: 97-100, A: 93-96, etc.)

### Requirement: AI Integrity Context Tool

The system SHALL provide an AI tool that returns integrity metrics with coaching context.

#### Scenario: Query integrity with context
- **WHEN** AI calls query_integrity_with_context tool
- **THEN** it returns: current letter grade, composite score, each metric component, recent trends, and at-risk count in last 30 days

#### Scenario: Include coaching suggestions
- **WHEN** integrity grade is below B
- **THEN** the tool response includes specific improvement suggestions (e.g., "Estimation accuracy is 45%. Focus on more realistic time estimates.")

#### Scenario: Include positive reinforcement
- **WHEN** integrity grade is A or higher
- **THEN** the tool response includes positive acknowledgment (e.g., "Excellent reliability! 5-week on-time streak.")

#### Scenario: Preserve at-risk history in context
- **WHEN** querying integrity context
- **THEN** at-risk commitments from last 30 days are included even if cleanup was completed
- **AND** AI can see pattern of struggles for coaching decisions

### Requirement: Task History Query Tool

The system SHALL provide an AI tool for querying task completion patterns.

#### Scenario: Query recent task history
- **WHEN** AI calls query_task_history with days=14
- **THEN** it returns TaskHistoryEntry records from last 14 days with event types, times, and estimation data

#### Scenario: Query history for commitment
- **WHEN** AI calls query_task_history with commitment_id parameter
- **THEN** it returns only TaskHistoryEntry records for that commitment

#### Scenario: Include estimation accuracy summary
- **WHEN** query_task_history returns results
- **THEN** response includes summary: "Average estimation accuracy: 65% (estimated 10h, took 15h)"

#### Scenario: Identify estimation patterns
- **WHEN** query_task_history returns results with >3 completed tasks
- **THEN** response includes pattern analysis: "Tends to underestimate by 40%" or "Consistent estimator (within 15%)"

### Requirement: Stakeholder Notification Credit

The system SHALL credit users for completing stakeholder notifications while preserving learning history.

#### Scenario: Notification completion improves cleanup rate
- **WHEN** user completes notification task for at-risk commitment
- **THEN** cleanup_completion_rate includes this as a completed cleanup

#### Scenario: At-risk timestamp preserved
- **WHEN** user completes notification and cleanup workflow
- **THEN** commitment.marked_at_risk_at timestamp remains set (not cleared)

#### Scenario: AI acknowledges notification positively
- **WHEN** AI detects completed notification task
- **THEN** AI responds positively: "Good job notifying the stakeholder. That takes integrity."

#### Scenario: AI maintains learning context
- **WHEN** AI queries task history after notification completion
- **THEN** the at-risk event and cleanup completion are both visible for future coaching

### Requirement: At-Risk Recovery

The system SHALL grant full integrity credit when a user delivers an at-risk commitment by the original due date.

#### Scenario: Full credit on timely delivery after at-risk
- **WHEN** a commitment was marked at_risk
- **AND** the commitment is later marked completed
- **AND** the completion date is on or before the original due_date
- **THEN** the commitment counts as on-time for integrity scoring (on_time_rate)
- **AND** the at-risk event does NOT count against the user's score

#### Scenario: At-risk flag preserved with recovered status
- **WHEN** an at-risk commitment is delivered on time
- **THEN** commitment.marked_at_risk_at timestamp is preserved
- **AND** commitment.at_risk_recovered is set to True
- **AND** AI can see the recovery for positive coaching context

#### Scenario: Late delivery still counts against score
- **WHEN** a commitment was marked at_risk
- **AND** the commitment is completed after the original due_date
- **THEN** the commitment counts as late for integrity scoring
- **AND** the at-risk event counts normally against the user's score

#### Scenario: AI celebrates recovery
- **WHEN** AI detects an at-risk commitment was delivered on time
- **THEN** AI responds positively: "You pulled it off! Delivered on time despite the risk. Great recovery."

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

#### Scenario: Transition to cancelled on recovery (Deferred)
- **WHEN** the associated Commitment recovers from "at_risk" to "in_progress"
- **THEN** CleanupPlan status changes to "cancelled" (commitment no longer needs cleanup)

**Note**: Recovery flow deferred to future iteration. Currently no automatic handling when commitment recovers.

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

