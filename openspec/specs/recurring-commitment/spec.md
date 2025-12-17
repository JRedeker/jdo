# recurring-commitment Specification

## Purpose
TBD - created by archiving change add-recurring-commitments. Update Purpose after archive.
## Requirements
### Requirement: RecurringCommitment Model

The system SHALL provide a `RecurringCommitment` SQLModel with the following validated fields:
- `id` (UUID): Unique identifier, auto-generated
- `deliverable` (str): Template deliverable text, required, non-empty
- `stakeholder_id` (UUID): Reference to Stakeholder, required
- `goal_id` (UUID | None): Optional reference to parent Goal
- `due_time` (time | None): Time of day when instances are due
- `timezone` (str): Timezone for due_time, defaults to "America/New_York"
- `recurrence_type` (RecurrenceType enum): One of `daily`, `weekly`, `monthly`, `yearly`
- `recurrence_pattern` (dict): Pattern-specific configuration (interval, days, etc.)
- `end_type` (EndType enum): One of `never`, `after_count`, `by_date`
- `end_after_count` (int | None): Required when end_type is `after_count`
- `end_by_date` (date | None): Required when end_type is `by_date`
- `task_templates` (list[TaskTemplate]): Task blueprints to copy to instances
- `notes` (str | None): Optional template notes
- `is_active` (bool): Whether recurrence is active, defaults to True
- `last_generated_date` (date | None): Date of most recently generated instance
- `instances_generated` (int): Count of instances generated, defaults to 0
- `created_at` (datetime): Auto-set on creation
- `updated_at` (datetime): Auto-updated on modification

#### Scenario: Create daily recurring commitment
- **WHEN** user creates a RecurringCommitment with recurrence_type="daily" and pattern={"interval": 1}
- **THEN** a valid RecurringCommitment is created that will generate daily instances

#### Scenario: Create weekly recurring commitment
- **WHEN** user creates a RecurringCommitment with recurrence_type="weekly" and pattern={"interval": 1, "days": ["monday", "friday"]}
- **THEN** a valid RecurringCommitment is created that will generate instances on Mondays and Fridays

#### Scenario: Create monthly recurring commitment by day of month
- **WHEN** user creates a RecurringCommitment with recurrence_type="monthly" and pattern={"interval": 1, "day_of_month": 15}
- **THEN** a valid RecurringCommitment is created that will generate instances on the 15th of each month

#### Scenario: Create monthly recurring commitment by week and day
- **WHEN** user creates a RecurringCommitment with recurrence_type="monthly" and pattern={"interval": 1, "week": -1, "day": "friday"}
- **THEN** a valid RecurringCommitment is created that will generate instances on the last Friday of each month

#### Scenario: Reject recurring commitment without deliverable
- **WHEN** user creates a RecurringCommitment with an empty deliverable
- **THEN** SQLModel validation raises an error

#### Scenario: Reject recurring commitment without stakeholder
- **WHEN** user creates a RecurringCommitment without a stakeholder_id
- **THEN** SQLModel validation raises an error

### Requirement: Recurrence Pattern Validation

The system SHALL validate recurrence patterns based on recurrence type.

#### Scenario: Validate daily pattern
- **WHEN** user creates a daily RecurringCommitment
- **THEN** pattern must contain "interval" (positive integer)

#### Scenario: Validate weekly pattern
- **WHEN** user creates a weekly RecurringCommitment
- **THEN** pattern must contain "interval" (positive integer) and "days" (non-empty list of weekday names)

#### Scenario: Validate monthly pattern by day
- **WHEN** user creates a monthly RecurringCommitment with day_of_month
- **THEN** pattern must contain "interval" and "day_of_month" (1-31)

#### Scenario: Validate monthly pattern by week
- **WHEN** user creates a monthly RecurringCommitment with week and day
- **THEN** pattern must contain "interval", "week" (-1 to 5), and "day" (weekday name)

#### Scenario: Validate yearly pattern
- **WHEN** user creates a yearly RecurringCommitment
- **THEN** pattern must contain "interval", "month" (1-12), and either "day" (1-31) or "week" and "day"

#### Scenario: Reject invalid pattern for type
- **WHEN** user creates a RecurringCommitment with a pattern that doesn't match the recurrence_type
- **THEN** SQLModel validation raises an error

### Requirement: End Condition Validation

The system SHALL validate end conditions based on end type.

#### Scenario: No end date required for never
- **WHEN** user creates a RecurringCommitment with end_type="never"
- **THEN** end_after_count and end_by_date are ignored

#### Scenario: Count required for after_count
- **WHEN** user creates a RecurringCommitment with end_type="after_count"
- **THEN** end_after_count must be a positive integer

#### Scenario: Date required for by_date
- **WHEN** user creates a RecurringCommitment with end_type="by_date"
- **THEN** end_by_date must be a valid future date

### Requirement: Task Template Structure

The system SHALL store task templates as structured data within RecurringCommitment using a TaskTemplate Pydantic model (not a table, stored as JSON).

#### Scenario: TaskTemplate model definition
- **WHEN** defining a TaskTemplate
- **THEN** it contains: title (str, required), scope (str, required), sub_tasks (list[SubTaskTemplate], defaults to []), order (int, required)

#### Scenario: SubTaskTemplate model definition
- **WHEN** defining a SubTaskTemplate
- **THEN** it contains: description (str, required)

#### Scenario: Store task templates
- **WHEN** user creates a RecurringCommitment with task_templates
- **THEN** each template is validated as TaskTemplate and stored as JSON

#### Scenario: Empty task templates allowed
- **WHEN** user creates a RecurringCommitment without task_templates
- **THEN** task_templates defaults to empty list and spawned instances have no tasks

### Requirement: On-Demand Instance Generation

The system SHALL generate Commitment instances on-demand based on the recurrence schedule. The generation window is determined by the pattern frequency: daily patterns generate 1 week ahead, weekly patterns generate 2 weeks ahead, monthly patterns generate 1 month ahead, and yearly patterns generate 1 year ahead.

#### Scenario: Generate next instance when viewing upcoming
- **WHEN** user views upcoming commitments and a RecurringCommitment has no pending instance within the generation window
- **THEN** the system generates a new Commitment instance with the next due date

#### Scenario: Daily pattern generation window
- **WHEN** a RecurringCommitment has recurrence_type="daily"
- **THEN** the generation window is 1 week (7 days) from today

#### Scenario: Weekly pattern generation window
- **WHEN** a RecurringCommitment has recurrence_type="weekly"
- **THEN** the generation window is 2 weeks (14 days) from today

#### Scenario: Monthly pattern generation window
- **WHEN** a RecurringCommitment has recurrence_type="monthly"
- **THEN** the generation window is 1 month from today

#### Scenario: Yearly pattern generation window
- **WHEN** a RecurringCommitment has recurrence_type="yearly"
- **THEN** the generation window is 1 year from today

#### Scenario: Generate instance on previous completion
- **WHEN** user completes a Commitment that has a recurring_commitment_id
- **THEN** the system checks if the next instance should be generated

#### Scenario: Skip generation for inactive recurring
- **WHEN** a RecurringCommitment has is_active=false
- **THEN** no new instances are generated

#### Scenario: Skip generation when ended by count
- **WHEN** a RecurringCommitment has end_type="after_count" and instances_generated >= end_after_count
- **THEN** no new instances are generated

#### Scenario: Skip generation when ended by date
- **WHEN** a RecurringCommitment has end_type="by_date" and next due date > end_by_date
- **THEN** no new instances are generated

#### Scenario: Generate only current instance on catch-up
- **WHEN** user opens app after missing several recurrence periods
- **THEN** only the current/next due instance is generated, not historical ones

### Requirement: Instance Task Inheritance

The system SHALL copy task templates to spawned Commitment instances with reset status.

#### Scenario: Copy tasks to new instance
- **WHEN** a Commitment instance is generated from a RecurringCommitment with task_templates
- **THEN** each task template becomes a Task with status="pending"

#### Scenario: Reset sub-tasks
- **WHEN** a Commitment instance is generated with task templates containing sub_tasks
- **THEN** all sub_tasks have completed=false

#### Scenario: Preserve task order
- **WHEN** a Commitment instance is generated from task_templates
- **THEN** tasks maintain the order specified in templates

### Requirement: RecurringCommitment Persistence

The system SHALL persist RecurringCommitment entities to SQLite with full CRUD operations.

#### Scenario: Save and retrieve recurring commitment
- **WHEN** user saves a new RecurringCommitment via a database session
- **THEN** the RecurringCommitment is persisted and can be retrieved by id

#### Scenario: Update last_generated_date
- **WHEN** a new instance is generated
- **THEN** last_generated_date is updated to the instance's due_date

#### Scenario: Increment instances_generated
- **WHEN** a new instance is generated
- **THEN** instances_generated is incremented by 1

#### Scenario: List active recurring commitments
- **WHEN** user queries recurring commitments with is_active=true
- **THEN** only active recurring commitments are returned

#### Scenario: Delete recurring commitment preserves instances
- **WHEN** user deletes a RecurringCommitment
- **THEN** the template is deleted but spawned Commitment instances remain

### Requirement: Due Date Calculation

The system SHALL calculate the next due date based on recurrence pattern.

#### Scenario: Calculate next daily due date
- **WHEN** calculating next due for daily pattern with interval=2 after Dec 15
- **THEN** next due date is Dec 17

#### Scenario: Calculate next weekly due date
- **WHEN** calculating next due for weekly pattern with days=["monday", "friday"] after Wednesday Dec 18
- **THEN** next due date is Friday Dec 20

#### Scenario: Calculate next monthly due date by day
- **WHEN** calculating next due for monthly pattern with day_of_month=15 after Dec 20
- **THEN** next due date is Jan 15

#### Scenario: Calculate next monthly due date by week
- **WHEN** calculating next due for monthly pattern with week=2, day="friday" after Dec 15
- **THEN** next due date is the 2nd Friday of January

#### Scenario: Handle last day of month
- **WHEN** calculating next due for monthly pattern with day_of_month=31 in February
- **THEN** next due date is Feb 28 (or 29 in leap year)

### Requirement: Recurring Commitment Management Commands

The system SHALL provide commands for managing recurring commitments in the conversational TUI. Recurring commitments use their own `/recurring` namespace (not `/show recurring`) because they are templates that generate commitments, not commitments themselves.

#### Scenario: List recurring commitments
- **WHEN** user types `/recurring`
- **THEN** data panel shows list of all recurring commitment templates with pattern summary and status

#### Scenario: Create recurring commitment
- **WHEN** user types `/recurring new` and describes a recurring commitment
- **THEN** AI guides creation of RecurringCommitment with pattern selection

#### Scenario: Edit recurring commitment pattern
- **WHEN** user types `/recurring edit <id>`
- **THEN** user can modify recurrence pattern, end conditions, and task templates

#### Scenario: Pause recurring commitment
- **WHEN** user types `/recurring pause <id>`
- **THEN** RecurringCommitment.is_active is set to false

#### Scenario: Resume recurring commitment
- **WHEN** user types `/recurring resume <id>`
- **THEN** RecurringCommitment.is_active is set to true

#### Scenario: Delete recurring commitment
- **WHEN** user types `/recurring delete <id>` and confirms
- **THEN** RecurringCommitment is deleted, existing instances remain

### Requirement: Recurring Commitment Display

The system SHALL display recurring commitment information clearly in the TUI.

#### Scenario: Show recurring indicator on instances
- **WHEN** displaying a Commitment that has a recurring_commitment_id
- **THEN** a recurring indicator (↻) is shown with pattern summary

#### Scenario: Show next due date in recurring list
- **WHEN** displaying a RecurringCommitment in the list
- **THEN** the calculated next due date is shown

#### Scenario: Show instance count
- **WHEN** displaying a RecurringCommitment
- **THEN** instances_generated count is visible

#### Scenario: Show active/paused status
- **WHEN** displaying a RecurringCommitment
- **THEN** active or paused status is clearly indicated

