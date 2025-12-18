# error-handling Specification

## Purpose
Define a custom exception hierarchy organized by domain, enabling consistent error categorization, recovery hints, and structured error logging throughout the application.

## ADDED Requirements

### Requirement: Base Exception Class

The system SHALL provide a base exception class for all JDO-specific errors.

#### Scenario: Base exception with message
- **WHEN** `JDOError("Something went wrong")` is raised
- **THEN** the exception has `message` attribute set to "Something went wrong"
- **AND** `str(exception)` returns "Something went wrong"

#### Scenario: Base exception with recovery hint
- **WHEN** `JDOError("Failed", recovery_hint="Try again later")` is raised
- **THEN** `exception.recovery_hint` equals "Try again later"

#### Scenario: Base exception is catchable as Exception
- **WHEN** code catches `Exception`
- **THEN** `JDOError` instances are caught

### Requirement: Configuration Exceptions

The system SHALL provide exceptions for configuration-related errors.

#### Scenario: Missing required setting
- **WHEN** a required setting is not found
- **THEN** `ConfigError` is raised with the setting name in the message

#### Scenario: Invalid setting value
- **WHEN** a setting has an invalid value (e.g., invalid timezone)
- **THEN** `ConfigError` is raised with the invalid value and expected format

### Requirement: Database Exceptions

The system SHALL provide exceptions for database-related errors.

#### Scenario: Connection failure
- **WHEN** database connection cannot be established
- **THEN** `DatabaseError` is raised with connection details (excluding credentials)

#### Scenario: Migration failure
- **WHEN** a database migration fails
- **THEN** `MigrationError` is raised with the migration version and error details

#### Scenario: Integrity constraint violation
- **WHEN** a database operation violates a constraint (unique, foreign key)
- **THEN** `DatabaseError` is raised with the constraint name

### Requirement: AI Exceptions

The system SHALL provide exceptions for AI-related errors.

#### Scenario: Provider API failure
- **WHEN** the AI provider returns an error (rate limit, auth, server error)
- **THEN** `ProviderError` is raised with status code and provider name

#### Scenario: Response extraction failure
- **WHEN** AI response cannot be parsed into expected structure
- **THEN** `ExtractionError` is raised with the expected type and raw response summary

#### Scenario: AI exceptions include retry guidance
- **WHEN** `ProviderError` is raised for a retryable error (rate limit, 5xx)
- **THEN** `recovery_hint` includes "Retry after X seconds" if available

### Requirement: Authentication Exceptions

The system SHALL provide exceptions for authentication-related errors.

#### Scenario: OAuth flow failure
- **WHEN** OAuth authorization fails
- **THEN** `AuthError` is raised with the failure reason

#### Scenario: Token expired
- **WHEN** an API call fails due to expired token
- **THEN** `AuthError` is raised with `recovery_hint` of "Re-authenticate with /auth"

### Requirement: TUI Exceptions

The system SHALL provide exceptions for TUI-related errors.

#### Scenario: Widget initialization failure
- **WHEN** a widget cannot be initialized with provided data
- **THEN** `TUIError` is raised with the widget name and invalid data summary

#### Scenario: Screen navigation failure
- **WHEN** navigation to a screen fails
- **THEN** `TUIError` is raised with the target screen name

### Requirement: Exception Hierarchy Structure

The system SHALL organize exceptions in a hierarchy that enables domain-level catching.

#### Scenario: Catch all database errors
- **WHEN** code catches `DatabaseError`
- **THEN** `MigrationError` instances are also caught

#### Scenario: Catch all AI errors
- **WHEN** code catches `AIError`
- **THEN** both `ProviderError` and `ExtractionError` instances are caught

#### Scenario: Catch all JDO errors
- **WHEN** code catches `JDOError`
- **THEN** all custom exceptions are caught
