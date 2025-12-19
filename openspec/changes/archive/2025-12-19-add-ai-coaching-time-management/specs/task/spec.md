# Capability: Task (Delta)

## MODIFIED Requirements

### Requirement: Task Model

The system SHALL provide a `Task` SQLModel with the following validated fields:
- `id` (UUID): Unique identifier, auto-generated
- `commitment_id` (UUID): Reference to parent Commitment, required
- `title` (str): Short description, required, non-empty
- `scope` (str): Clear definition of done, required, non-empty
- `status` (TaskStatus enum): One of `pending`, `in_progress`, `completed`, `skipped`; defaults to `pending`
- `sub_tasks` (list[SubTask]): Inline checklist items, defaults to empty list
- `order` (int): Display/execution order within the commitment, required
- `estimated_hours` (float | None): Predicted effort in hours (15-minute increments), defaults to None
- `actual_hours_category` (ActualHoursCategory enum | None): Actual effort category after completion, one of `much_shorter`, `shorter`, `on_target`, `longer`, `much_longer`; defaults to None
- `estimation_confidence` (EstimationConfidence enum | None): User's confidence level, one of `high`, `medium`, `low`; defaults to None
- `is_notification_task` (bool): True if auto-created for at-risk notification, defaults to False
- `created_at` (datetime): Auto-set on creation, timezone-aware (EST default)
- `updated_at` (datetime): Auto-updated on modification, timezone-aware (EST default)

#### Scenario: Create task with required fields
- **WHEN** user creates a Task with commitment_id, title="Draft email", scope="Write email body with 3 key points", and order=1
- **THEN** a valid Task is created with status="pending" and auto-generated timestamps

#### Scenario: Reject task without title
- **WHEN** user creates a Task with an empty title
- **THEN** SQLModel validation raises an error

#### Scenario: Reject task without scope
- **WHEN** user creates a Task with an empty scope
- **THEN** SQLModel validation raises an error

#### Scenario: Reject task without commitment
- **WHEN** user creates a Task without a commitment_id
- **THEN** SQLModel validation raises an error

#### Scenario: Create task with time estimate
- **WHEN** user creates a Task with estimated_hours=2.5 and estimation_confidence="medium"
- **THEN** a valid Task is created with the time estimate fields populated

#### Scenario: Create task without time estimate
- **WHEN** user creates a Task without estimated_hours
- **THEN** a valid Task is created with estimated_hours=None (field is optional)

#### Scenario: Record actual hours category on completion
- **WHEN** user completes a Task and selects actual_hours_category="longer"
- **THEN** the Task is updated with actual_hours_category="longer" and status="completed"

## ADDED Requirements

### Requirement: Task Time Estimation

The system SHALL support time estimation for tasks to enable workload planning and AI coaching, using 15-minute increments.

#### Scenario: Valid estimation confidence values
- **WHEN** user sets estimation_confidence
- **THEN** only EstimationConfidence enum values (HIGH, MEDIUM, LOW) are accepted

#### Scenario: Estimate without confidence defaults to medium
- **WHEN** user provides estimated_hours but no estimation_confidence
- **THEN** estimation_confidence defaults to "medium"

#### Scenario: Estimated hours use 15-minute increments
- **WHEN** user provides estimated_hours
- **THEN** the value must be a multiple of 0.25 (15 minutes)
- **AND** ambiguous inputs are rounded up (e.g., "20 minutes" → 0.5 hours)

#### Scenario: Estimated hours validation
- **WHEN** user provides estimated_hours
- **THEN** the value must be positive (> 0)

#### Scenario: Valid actual hours category values
- **WHEN** user sets actual_hours_category
- **THEN** only ActualHoursCategory enum values (MUCH_SHORTER, SHORTER, ON_TARGET, LONGER, MUCH_LONGER) are accepted

#### Scenario: Actual hours category thresholds
- **WHEN** interpreting actual_hours_category for accuracy calculation
- **THEN** categories map to estimate multipliers:
  - "much_shorter" = <50% of estimate
  - "shorter" = 50-85% of estimate
  - "on_target" = 85-115% of estimate
  - "longer" = 115-150% of estimate
  - "much_longer" = >150% of estimate

### Requirement: Task Completion with Time Recording

The system SHALL prompt for actual hours category when completing tasks that have estimates, using a 5-point scale.

#### Scenario: Prompt for actual hours category on completion
- **WHEN** user marks a Task with estimated_hours as completed
- **AND** actual_hours_category is not provided
- **THEN** the system prompts with 5-point picker: "Much Shorter | Shorter | On Target | Longer | Much Longer"

#### Scenario: Allow completion without actual hours category
- **WHEN** user skips the 5-point picker (presses Escape or skip action)
- **THEN** the Task is completed with actual_hours_category=None

#### Scenario: Quick selection for on-target
- **WHEN** user selects "On Target" from the picker
- **THEN** actual_hours_category is set to "on_target"
- **AND** this counts as accurate estimation for integrity scoring
