# command-handlers Specification

## Purpose

Define the modular command handler architecture for JDO, enabling domain-focused handler modules with a centralized registry.

## ADDED Requirements

### Requirement: Handler Registry

The system SHALL provide a centralized registry for command handlers.

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

### Requirement: Handler Base Classes

The system SHALL provide base classes for command handlers.

#### Scenario: CommandHandler abstract interface
- **WHEN** a developer creates a new handler
- **THEN** they extend `CommandHandler` ABC
- **AND** implement the `execute()` method

#### Scenario: HandlerResult dataclass
- **WHEN** a handler executes a command
- **THEN** it returns a `HandlerResult` with message, panel updates, draft data, and confirmation flag

### Requirement: Domain Handler Modules

The system SHALL organize handlers into domain-focused modules.

#### Scenario: Commitment domain handlers
- **WHEN** commitment-related commands are invoked (/commit, /atrisk, /cleanup, /recover, /abandon)
- **THEN** handlers are loaded from `commitment_handlers.py`

#### Scenario: Goal domain handlers
- **WHEN** goal commands are invoked (/goal)
- **THEN** handlers are loaded from `goal_handlers.py`

#### Scenario: Task domain handlers
- **WHEN** task-related commands are invoked (/task, /complete)
- **THEN** handlers are loaded from `task_handlers.py`

#### Scenario: Vision domain handlers
- **WHEN** vision commands are invoked (/vision)
- **THEN** handlers are loaded from `vision_handlers.py`

#### Scenario: Milestone domain handlers
- **WHEN** milestone commands are invoked (/milestone)
- **THEN** handlers are loaded from `milestone_handlers.py`

#### Scenario: Integrity domain handlers
- **WHEN** integrity commands are invoked (/integrity)
- **THEN** handlers are loaded from `integrity_handlers.py`

#### Scenario: Recurring domain handlers
- **WHEN** recurring commitment commands are invoked (/recurring)
- **THEN** handlers are loaded from `recurring_handlers.py`

#### Scenario: Utility handlers
- **WHEN** utility commands are invoked (/help, /show, /view, /cancel, /edit, /type, /hours, /triage)
- **THEN** handlers are loaded from `utility_handlers.py`

### Requirement: Backward Compatibility

The system SHALL maintain backward compatibility during the refactor.

#### Scenario: Existing import paths work
- **WHEN** code imports `get_handler` from `jdo.commands.handlers`
- **THEN** the import succeeds
- **AND** returns the same handler instances as before

#### Scenario: All existing commands work
- **WHEN** any existing slash command is executed
- **THEN** it behaves identically to before the refactor
