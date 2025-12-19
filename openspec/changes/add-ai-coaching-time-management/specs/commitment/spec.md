# Capability: Commitment (Delta)

## MODIFIED Requirements

### Requirement: Commitment Model

The system SHALL add an `at_risk_recovered` field to the Commitment model.

- `at_risk_recovered` (bool): True if commitment was at-risk but delivered by original due date, defaults to False

#### Scenario: Mark commitment as recovered
- **WHEN** a commitment with status "at_risk" is changed to "completed"
- **AND** the completion date is on or before the original due_date
- **THEN** at_risk_recovered is automatically set to True

#### Scenario: Recovery preserves at-risk timestamp
- **WHEN** at_risk_recovered is set to True
- **THEN** marked_at_risk_at timestamp remains set (not cleared)

#### Scenario: Late completion does not recover
- **WHEN** a commitment with status "at_risk" is changed to "completed"
- **AND** the completion date is after the original due_date
- **THEN** at_risk_recovered remains False

## ADDED Requirements

### Requirement: Commitment Time Rollup

The system SHALL provide computed properties for time rollup from child tasks to enable workload planning.

#### Scenario: Calculate total estimated hours
- **WHEN** system accesses commitment.total_estimated_hours
- **THEN** it returns the sum of estimated_hours for all tasks under this commitment
- **AND** returns 0.0 if no tasks have estimates

#### Scenario: Calculate remaining estimated hours
- **WHEN** system accesses commitment.remaining_estimated_hours
- **THEN** it returns the sum of estimated_hours for tasks with status pending or in_progress
- **AND** excludes completed and skipped tasks

#### Scenario: Calculate completed hours
- **WHEN** system accesses commitment.completed_hours
- **THEN** it returns the sum of estimated_hours for completed tasks (using actual_hours_category to adjust)
- **AND** applies category multiplier: much_shorter=0.25x, shorter=0.675x, on_target=1.0x, longer=1.325x, much_longer=2.0x
- **AND** falls back to estimated_hours if actual_hours_category is None

#### Scenario: Handle mixed estimates
- **WHEN** calculating time rollups
- **AND** some tasks have estimates while others do not
- **THEN** only tasks with estimates are included in calculations
- **AND** response indicates "X of Y tasks have estimates"

### Requirement: Commitment Time Context Tool

The system SHALL provide an AI tool for querying commitment time breakdown.

#### Scenario: Query commitment time rollup
- **WHEN** AI calls query_commitment_time_rollup with commitment_id
- **THEN** it returns: total_estimated_hours, remaining_estimated_hours, completed_hours, completion percentage by time, days until due, and hours needed per day to finish

#### Scenario: Calculate hours per day needed
- **WHEN** commitment has remaining hours and days until due
- **THEN** hours_per_day = remaining_estimated_hours / days_until_due
- **AND** warning if hours_per_day exceeds typical workday (8 hours)

#### Scenario: Flag unrealistic timeline
- **WHEN** hours_per_day calculation exceeds available hours
- **THEN** response includes: "Warning: This commitment requires X hours/day but you have Y hours available"

#### Scenario: Handle commitment without estimates
- **WHEN** AI queries time rollup for commitment with no task estimates
- **THEN** response indicates: "No time estimates available. Consider adding estimates to tasks."
