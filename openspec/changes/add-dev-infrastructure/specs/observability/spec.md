# observability Specification

## Purpose
Define production observability using Sentry for error tracking, performance monitoring, and AI call tracing, with optional enablement via configuration.

## ADDED Requirements

### Requirement: Sentry Initialization

The system SHALL optionally initialize Sentry for error tracking.

#### Scenario: Initialize when DSN configured
- **WHEN** application starts with `JDOSettings.sentry_dsn` set
- **THEN** Sentry SDK is initialized with the DSN

#### Scenario: Skip initialization when DSN not set
- **WHEN** application starts without `JDOSettings.sentry_dsn`
- **THEN** Sentry SDK is not initialized
- **AND** no errors are logged about missing configuration

#### Scenario: Environment tag set
- **WHEN** Sentry is initialized
- **THEN** the `environment` tag is set to `JDOSettings.environment` (default: "development")

### Requirement: Automatic Error Capture

The system SHALL automatically capture unhandled exceptions.

#### Scenario: Unhandled exception sent to Sentry
- **WHEN** an unhandled exception propagates to the application root
- **THEN** the exception is captured with full traceback
- **AND** local variables are included (if enabled)

#### Scenario: JDOError includes recovery hint
- **WHEN** a `JDOError` subclass is captured
- **THEN** the `recovery_hint` is included as a tag

#### Scenario: PII is not sent by default
- **WHEN** Sentry captures an event
- **THEN** personally identifiable information is scrubbed unless explicitly enabled

### Requirement: Manual Error Reporting

The system SHALL support explicit error capture.

#### Scenario: Capture handled exception
- **WHEN** `sentry_sdk.capture_exception(exception)` is called
- **THEN** the exception is sent to Sentry even if handled

#### Scenario: Capture message
- **WHEN** `sentry_sdk.capture_message("message", level="warning")` is called
- **THEN** the message appears in Sentry as an issue

### Requirement: Performance Tracing

The system SHALL support performance tracing for key operations.

#### Scenario: AI calls are traced
- **WHEN** an AI agent processes a request
- **THEN** a Sentry span is created with operation "ai.agent"
- **AND** the span includes tool calls as child spans

#### Scenario: Database operations are traced
- **WHEN** a database query executes
- **THEN** it appears as a span in the current transaction

#### Scenario: Sampling rate configured
- **WHEN** Sentry is initialized
- **THEN** `traces_sample_rate` is set to `JDOSettings.sentry_traces_sample_rate` (default: 0.1)

### Requirement: Loguru Integration

The system SHALL send error-level logs to Sentry.

#### Scenario: Error logs captured
- **WHEN** `logger.error("message")` or `logger.exception("message")` is called
- **THEN** the log is sent to Sentry as a breadcrumb or event

#### Scenario: Debug logs not sent
- **WHEN** `logger.debug("message")` is called
- **THEN** the log is NOT sent to Sentry

### Requirement: Context Enrichment

The system SHALL enrich Sentry events with application context.

#### Scenario: Add user context
- **WHEN** a user is authenticated
- **THEN** Sentry scope includes user ID (not email or name for privacy)

#### Scenario: Add AI context
- **WHEN** an error occurs during AI processing
- **THEN** Sentry event includes AI model, provider, and tool context

#### Scenario: Add version context
- **WHEN** Sentry is initialized
- **THEN** the `release` is set to the application version from `pyproject.toml`
