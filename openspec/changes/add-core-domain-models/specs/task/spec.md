# Capability: Task Management

Tasks represent scoped work items required to fulfill a commitment. Each task must have a clear scope defining what "done" means. Tasks may contain inline sub-tasks for granular tracking.

**Status Philosophy**: Tasks can be `skipped` (work deemed not needed) but not `abandoned`. Commitments can be `abandoned` (promise broken) but not `skipped`. This reflects the distinction: Tasks are work items that may become unnecessary; Commitments are promises that must be either kept or explicitly broken.

## ADDED Requirements

### Requirement: Task Model

The system SHALL provide a `Task` SQLModel with the following validated fields:
- `id` (UUID): Unique identifier, auto-generated
- `commitment_id` (UUID): Reference to parent Commitment, required
- `title` (str): Short description, required, non-empty
- `scope` (str): Clear definition of done, required, non-empty
- `status` (TaskStatus enum): One of `pending`, `in_progress`, `completed`, `skipped`; defaults to `pending`
- `sub_tasks` (list[SubTask]): Inline checklist items, defaults to empty list
- `order` (int): Display/execution order within the commitment, required
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
