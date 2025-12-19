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

