# stakeholder Specification

## Purpose
Define the Stakeholder domain model representing people, teams, or organizations to whom commitments are made, with intelligent name matching to avoid duplicates.
## Requirements
### Requirement: Stakeholder Model

The system SHALL provide a `Stakeholder` SQLModel with the following validated fields:
- `id` (UUID): Unique identifier, auto-generated
- `name` (str): Display name, required, non-empty
- `type` (StakeholderType enum): One of `person`, `team`, `organization`, `self`; required
- `contact_info` (str | None): Optional contact details
- `notes` (str | None): Optional additional context
- `created_at` (datetime): Auto-set on creation, timezone-aware (EST default)
- `updated_at` (datetime): Auto-updated on modification, timezone-aware (EST default)

#### Scenario: Create stakeholder with required fields
- **WHEN** user creates a Stakeholder with name="Alice" and type="person"
- **THEN** a valid Stakeholder is created with auto-generated id, created_at, and updated_at

#### Scenario: Reject empty stakeholder name
- **WHEN** user creates a Stakeholder with name="" or name=None
- **THEN** SQLModel validation raises an error

#### Scenario: Reject invalid stakeholder type
- **WHEN** user creates a Stakeholder with type="invalid"
- **THEN** SQLModel validation raises an error

### Requirement: Stakeholder Persistence

The system SHALL persist Stakeholder entities to SQLite with full CRUD operations via SQLModel sessions.

#### Scenario: Save and retrieve stakeholder
- **WHEN** user saves a new Stakeholder via a database session
- **THEN** the stakeholder is persisted to SQLite and can be retrieved by id

#### Scenario: Update stakeholder
- **WHEN** user modifies a stakeholder's name and commits the session
- **THEN** the updated_at timestamp is refreshed and changes are persisted

#### Scenario: Delete stakeholder without commitments
- **WHEN** user deletes a stakeholder that has no associated commitments
- **THEN** the stakeholder is removed from the database

#### Scenario: Prevent deletion of stakeholder with commitments
- **WHEN** user attempts to delete a stakeholder that has associated commitments
- **THEN** the system raises an error indicating the stakeholder cannot be deleted

#### Scenario: Prevent deletion of stakeholder with recurring commitments
- **WHEN** user attempts to delete a stakeholder that has associated RecurringCommitments
- **THEN** the system raises an error indicating the stakeholder cannot be deleted

### Requirement: Self Stakeholder Default

The system SHALL create a default "Self" stakeholder (type=self) on first run if no stakeholders exist.

#### Scenario: Auto-create self stakeholder
- **WHEN** the application starts with an empty stakeholder table
- **THEN** a stakeholder with name="Self" and type="self" is automatically created

### Requirement: Stakeholder Name Matching

The system SHALL intelligently match stakeholder references using fuzzy matching to avoid duplicates.

#### Scenario: Single match auto-resolves
- **WHEN** user mentions "Bob" and only one stakeholder exists with "Bob" in the name (e.g., "Bob Smith")
- **THEN** the AI automatically resolves to "Bob Smith" without asking

#### Scenario: Multiple matches requires clarification
- **WHEN** user mentions "Bob" and multiple stakeholders match (e.g., "Bob Smith", "Bob Jones")
- **THEN** the AI asks "Which Bob? Bob Smith or Bob Jones?"

#### Scenario: No match creates new stakeholder
- **WHEN** user mentions a name that doesn't match any existing stakeholder
- **THEN** the AI asks to confirm creating a new stakeholder with that name

#### Scenario: Exact match preferred
- **WHEN** user mentions "Bob Smith" and a stakeholder named "Bob Smith" exists
- **THEN** the AI uses the exact match without confirmation

