## MODIFIED Requirements

### Requirement: Handler Base Classes
The system SHALL provide a `CommandHandler` base class with simplified output type.

#### Scenario: CommandHandler returns CommandOutput
- **WHEN** a handler implements `execute()`
- **THEN** it returns `CommandOutput` (not `HandlerResult`)

#### Scenario: CommandOutput structure
- **GIVEN** a handler executes successfully
- **WHEN** it returns CommandOutput
- **THEN** the output contains: message (str), data (dict|list|None), needs_confirmation (bool), draft (dict|None)

#### Scenario: CommandOutput has no UI-specific fields
- **GIVEN** any CommandOutput instance
- **WHEN** inspected
- **THEN** it does NOT contain panel_update or other UI-specific fields
- **AND** it is reusable across CLI and future interfaces

### Requirement: Handler Registry
The system SHALL provide a centralized registry for command handlers (unchanged).

#### Scenario: Get handler by command type
- **WHEN** `get_handler(command_type)` is called
- **THEN** the correct handler instance is returned for that command type
- **AND** handlers are instantiated lazily (only when first requested)

#### Scenario: Handler instance caching
- **WHEN** the same command type is requested multiple times
- **THEN** the same handler instance is returned (singleton per type)

#### Scenario: Unknown command type
- **WHEN** `get_handler()` is called with an unregistered command type
- **THEN** None is returned

### Requirement: Domain Handler Modules
The system SHALL organize handlers into domain-focused modules (unchanged structure, updated return types).

#### Scenario: Commitment handlers return CommandOutput
- **WHEN** commitment commands execute (/commit, /atrisk, /cleanup)
- **THEN** handlers return `CommandOutput` with structured data for display

#### Scenario: Goal handlers return CommandOutput
- **WHEN** goal commands execute (/goal)
- **THEN** handlers return `CommandOutput` with structured data for display

#### Scenario: List handlers include data for formatting
- **WHEN** a list command executes (e.g., CommitHandler list mode)
- **THEN** CommandOutput.data contains a list of entity dicts
- **AND** each dict has id, title/deliverable, due_date, status fields

#### Scenario: Create handlers include draft for confirmation
- **WHEN** a create command executes (e.g., /commit)
- **THEN** CommandOutput.draft contains the proposed entity
- **AND** CommandOutput.needs_confirmation is True
- **AND** CommandOutput.message asks user to confirm

### Requirement: Handler Context
The system SHALL pass context to handlers via a dict (unchanged pattern).

#### Scenario: Context includes conversation history
- **WHEN** a handler needs AI context
- **THEN** the context dict includes "conversation" key with message history

#### Scenario: Context includes current entity if applicable
- **WHEN** a handler operates on selected entity (e.g., /atrisk)
- **THEN** the context dict includes "current_commitment" or "current_goal" etc.

#### Scenario: Context includes available hours for time coaching
- **WHEN** a handler checks capacity (e.g., /task)
- **THEN** the context dict includes "available_hours_remaining" and "allocated_hours"

### Requirement: Error Handling
The system SHALL handle errors during handler execution gracefully.

#### Scenario: Handler execution raises exception
- **GIVEN** a handler is executing
- **WHEN** an unhandled exception occurs during execute()
- **THEN** the exception is caught by the CLI layer
- **AND** a CommandOutput with error message is returned
- **AND** the error is logged with full traceback

#### Scenario: AI service unavailable during handler execution
- **GIVEN** a handler requires AI service (e.g., /commit with natural language)
- **WHEN** the AI service is unavailable (network error, API down)
- **THEN** CommandOutput.message contains user-friendly error: "AI service unavailable. Please check your connection and try again."
- **AND** CommandOutput.data is None
- **AND** the error is logged with retry guidance

#### Scenario: Database query fails during handler execution
- **GIVEN** a handler queries the database
- **WHEN** the database query fails (connection lost, constraint violation)
- **THEN** CommandOutput.message contains actionable error: "Database error: <brief description>. Please try again."
- **AND** the full error is logged
- **AND** the transaction is rolled back if applicable
