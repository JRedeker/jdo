# logging Specification

## Purpose
Define structured logging using Loguru with configurable output sinks, log rotation, and stdlib interception for consistent logging across the application and third-party libraries.

## ADDED Requirements

### Requirement: Logging Configuration

The system SHALL provide a centralized logging configuration using Loguru.

#### Scenario: Configure logging on startup
- **WHEN** the application starts
- **THEN** logging is configured based on `JDOSettings.log_level`
- **AND** console output uses human-readable format with colors
- **AND** file output (if enabled) uses JSON serialization

#### Scenario: File rotation enabled
- **WHEN** file logging is enabled via `JDOSettings.log_file_path`
- **THEN** logs rotate at 10 MB
- **AND** logs are retained for 7 days
- **AND** old logs are compressed

#### Scenario: Disable file logging
- **WHEN** `JDOSettings.log_file_path` is not set
- **THEN** only console logging is active

### Requirement: Stdlib Logging Interception

The system SHALL intercept Python stdlib logging to route all logs through Loguru.

#### Scenario: Third-party library logs captured
- **WHEN** a library like `httpx` or `sqlalchemy` logs a message via stdlib logging
- **THEN** the message appears in Loguru output with appropriate level mapping

#### Scenario: Preserve log level mapping
- **WHEN** stdlib `logging.WARNING` is used
- **THEN** it maps to Loguru `WARNING` level

### Requirement: Contextual Logging

The system SHALL support adding context to log messages.

#### Scenario: Add request context
- **WHEN** `logger.bind(request_id="abc123")` is called
- **THEN** subsequent logs include `request_id` in structured output

#### Scenario: Exception logging with traceback
- **WHEN** `logger.exception("message")` is called in an except block
- **THEN** the full traceback is included in the log output

### Requirement: Log Access Patterns

The system SHALL log key operations for debugging and audit.

#### Scenario: Log AI agent calls
- **WHEN** an AI agent tool is invoked
- **THEN** the tool name, input summary, and duration are logged at DEBUG level

#### Scenario: Log database operations
- **WHEN** a database session commits or rolls back
- **THEN** the operation is logged at DEBUG level

#### Scenario: Log screen transitions
- **WHEN** a Textual screen is pushed or popped
- **THEN** the screen name is logged at DEBUG level
