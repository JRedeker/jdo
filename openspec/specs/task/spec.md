# task Specification

## Purpose
Define the Task domain model representing discrete work items within commitments, with clear scope definitions, ordered execution, and inline sub-task checklists.
## Requirements
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

### Requirement: SubTask Model

The system SHALL provide a `SubTask` Pydantic model (not a table, stored as JSON) embedded within Task with the following fields:
- `description` (str): What needs to be done, required, non-empty
- `completed` (bool): Whether the sub-task is done, defaults to False

#### Scenario: Create task with sub-tasks
- **WHEN** user creates a Task with sub_tasks containing multiple SubTask items
- **THEN** the Task stores the sub-tasks inline as part of the Task record

#### Scenario: Toggle sub-task completion
- **WHEN** user marks a sub-task as completed
- **THEN** the sub_task.completed is set to True and the parent Task's updated_at is refreshed

#### Scenario: All sub-tasks complete transitions task to in_progress
- **WHEN** all sub-tasks for a pending Task are marked completed
- **THEN** the Task status automatically transitions to "in_progress" (not "completed")

#### Scenario: Sub-task completion does not auto-complete task
- **WHEN** all sub-tasks are completed and Task is already "in_progress"
- **THEN** the Task status remains "in_progress" until user explicitly completes it

### Requirement: Task Ordering

The system SHALL maintain explicit ordering of tasks within a commitment with conversational reordering.

#### Scenario: Retrieve tasks in order
- **WHEN** user queries tasks for a Commitment
- **THEN** tasks are returned sorted by order ascending

#### Scenario: Reorder tasks conversationally
- **WHEN** user says "move task 3 before task 1" or "reorder tasks: review, draft, send"
- **THEN** the AI updates the order field for affected tasks and confirms the new order

#### Scenario: Reorder by task title
- **WHEN** user says "move 'send email' to the top"
- **THEN** the AI identifies the task by title and updates its order to 1, shifting others down

### Requirement: Task Persistence

The system SHALL persist Task entities to SQLite with full CRUD operations via SQLModel sessions. Sub-tasks are stored as JSON within the Task record.

#### Scenario: Save and retrieve task with sub-tasks
- **WHEN** user saves a Task with sub_tasks via a database session
- **THEN** the Task and its sub_tasks are persisted and can be retrieved together

#### Scenario: Update sub-task within task
- **WHEN** user updates a sub-task's completed status
- **THEN** the change is persisted in the Task's JSON sub_tasks field

#### Scenario: Delete task
- **WHEN** user deletes a Task
- **THEN** the Task and its sub_tasks are removed from the database

### Requirement: Task Status Transitions

The system SHALL track task completion status independently of commitment status. The "skipped" status indicates a task is not needed for the commitment to be fulfilled.

#### Scenario: Start working on task
- **WHEN** user changes Task status from "pending" to "in_progress"
- **THEN** the status is updated and updated_at is refreshed

#### Scenario: Complete task
- **WHEN** user changes Task status to "completed"
- **THEN** the status is updated and updated_at is refreshed

#### Scenario: Skip task as not needed
- **WHEN** user changes Task status to "skipped"
- **THEN** the status is updated to indicate the task is not required for the commitment
- **AND** updated_at is refreshed

#### Scenario: Skipped tasks do not block commitment completion
- **WHEN** a Commitment has tasks with status "skipped"
- **THEN** the Commitment can still be marked as "completed"

#### Scenario: Reopen completed task
- **WHEN** user changes Task status from "completed" or "skipped" back to "pending" or "in_progress"
- **THEN** the status is updated and updated_at is refreshed

### Requirement: Task Analysis Workflow

The system SHALL support a workflow where users analyze a commitment to identify required tasks.

#### Scenario: Add tasks during commitment analysis
- **WHEN** user opens a Commitment and enters task analysis mode
- **THEN** the system allows adding multiple tasks with titles and scopes

#### Scenario: Suggest scope clarity
- **WHEN** user creates a task with a vague scope (e.g., less than 10 characters)
- **THEN** the system warns that a clearer scope definition may be needed (non-blocking)

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

