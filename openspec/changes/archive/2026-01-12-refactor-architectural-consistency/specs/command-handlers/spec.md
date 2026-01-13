## MODIFIED Requirements

### Requirement: Handler Base Classes

The system SHALL provide base classes for command handlers.

#### Scenario: CommandHandler abstract interface
- **WHEN** a developer creates a new handler
- **THEN** they extend `CommandHandler` ABC
- **AND** implement the `execute()` method

#### Scenario: HandlerResult dataclass
- **WHEN** a handler executes a command
- **THEN** it returns a `HandlerResult` with message, panel updates, draft data, and confirmation flag

#### Scenario: HandlerContext typed dataclass
- **WHEN** a handler's `execute()` method is called
- **THEN** it receives a `HandlerContext` instance (not a raw dict)
- **AND** the context provides typed access to conversation_history, extracted_fields, draft_data, timezone, and available_hours

## ADDED Requirements

### Requirement: Typed Handler Context

The system SHALL provide a typed context dataclass for handler execution.

#### Scenario: HandlerContext fields
- **WHEN** `HandlerContext` is instantiated
- **THEN** it has fields: conversation_history (list), extracted_fields (dict), draft_data (dict|None), timezone (str), available_hours (float|None)
- **AND** default values are provided for optional fields

#### Scenario: Context construction from screen
- **WHEN** `ChatScreen` or `MainScreen` routes a command to a handler
- **THEN** it constructs a `HandlerContext` with current conversation state
- **AND** passes it to `handler.execute()`

#### Scenario: Handler context access
- **WHEN** a handler needs conversation history
- **THEN** it accesses `context.conversation_history` with type hints
- **AND** IDE autocomplete works for all context fields
