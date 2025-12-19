# data-persistence Spec Delta

## ADDED Requirements

### Requirement: Entity Persistence Service

The system SHALL provide a persistence service for saving entities from draft data.

#### Scenario: Save commitment from draft
- **WHEN** `PersistenceService.save_commitment(draft_data)` is called with valid data
- **THEN** a new Commitment is created in the database
- **AND** the Commitment object is returned with its generated id

#### Scenario: Save goal from draft
- **WHEN** `PersistenceService.save_goal(draft_data)` is called with valid data
- **THEN** a new Goal is created in the database
- **AND** the Goal object is returned with its generated id

#### Scenario: Save task from draft
- **WHEN** `PersistenceService.save_task(draft_data)` is called with valid data
- **THEN** a new Task is created in the database
- **AND** the Task is linked to the specified commitment

#### Scenario: Save milestone from draft
- **WHEN** `PersistenceService.save_milestone(draft_data)` is called with valid data
- **THEN** a new Milestone is created in the database
- **AND** the Milestone is linked to the specified goal

#### Scenario: Save vision from draft
- **WHEN** `PersistenceService.save_vision(draft_data)` is called with valid data
- **THEN** a new Vision is created in the database
- **AND** next_review_date is set to 90 days from creation

#### Scenario: Save recurring commitment from draft
- **WHEN** `PersistenceService.save_recurring_commitment(draft_data)` is called with valid data
- **THEN** a new RecurringCommitment is created in the database
- **AND** the first commitment instance is generated based on recurrence pattern

#### Scenario: Save with missing required fields
- **WHEN** `PersistenceService.save_*()` is called with missing required fields
- **THEN** a `ValidationError` is raised with field names

### Requirement: Stakeholder Resolution

The system SHALL automatically resolve stakeholders by name during entity creation.

#### Scenario: Get existing stakeholder
- **WHEN** `get_or_create_stakeholder(name)` is called with an existing name
- **THEN** the existing Stakeholder is returned

#### Scenario: Create new stakeholder
- **WHEN** `get_or_create_stakeholder(name)` is called with a new name
- **THEN** a new Stakeholder is created and returned

#### Scenario: Case-insensitive matching
- **WHEN** `get_or_create_stakeholder("sarah")` is called and "Sarah" exists
- **THEN** the existing "Sarah" Stakeholder is returned
