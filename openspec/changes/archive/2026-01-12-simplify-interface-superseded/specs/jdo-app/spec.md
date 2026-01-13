## MODIFIED Requirements

### Requirement: Application Entry Point
The system SHALL provide a CLI entry point that launches the Typer application.

#### Scenario: Entry point launches Typer app
- **GIVEN** the user runs `jdo`
- **WHEN** the command is executed
- **THEN** it launches the Typer app which defaults to chat mode

#### Scenario: Entry point handles exceptions
- **GIVEN** the user runs any `jdo` command
- **WHEN** an unhandled exception occurs
- **THEN** it is caught, logged, and a user-friendly error is displayed
- **AND** the exit code is non-zero

#### Scenario: Entry point initializes logging
- **GIVEN** the user runs any `jdo` command
- **WHEN** the application starts
- **THEN** logging is initialized according to JDO_LOG_LEVEL
- **AND** logs are written to the configured file or console

#### Scenario: Entry point initializes database
- **GIVEN** the user runs any `jdo` command that requires data
- **WHEN** the application starts
- **THEN** database tables are created if they don't exist
- **AND** pending migrations are applied

#### Scenario: Database migration fails on startup
- **GIVEN** the user runs a `jdo` command
- **WHEN** database migration fails (e.g., incompatible schema, disk full)
- **THEN** a user-friendly error is displayed: "Database migration failed: <reason>. Run 'jdo db status' for details."
- **AND** the error is logged with full traceback
- **AND** the application exits with code 2

### Requirement: Application Configuration
The system SHALL load configuration from environment variables and .env file as before (unchanged).

#### Scenario: Load AI provider from env
- **GIVEN** JDO_AI_PROVIDER is set to "openai"
- **WHEN** the application starts
- **THEN** OpenAI is used as the AI provider

#### Scenario: Load settings with defaults
- **GIVEN** no environment variables are set
- **WHEN** settings are loaded
- **THEN** defaults are used (provider=anthropic, timezone=America/New_York, etc.)

#### Scenario: Database path from env
- **GIVEN** JDO_DATABASE_PATH is set
- **WHEN** the database is initialized
- **THEN** the custom path is used

#### Scenario: .env file is malformed
- **GIVEN** a .env file exists with invalid syntax (e.g., missing =, invalid escapes)
- **WHEN** settings are loaded
- **THEN** a warning is logged: "Malformed .env file detected. Using environment variables and defaults."
- **AND** the application continues with defaults for unparseable values

#### Scenario: JDO_DATABASE_PATH points to invalid location
- **GIVEN** JDO_DATABASE_PATH is set to a directory without write permissions
- **WHEN** the database is initialized
- **THEN** an error is displayed: "Cannot write to database path: <path>. Check permissions or set JDO_DATABASE_PATH."
- **AND** the application exits with code 2

### Requirement: Authentication Check
The system SHALL verify AI credentials before executing commands that require AI.

#### Scenario: Check credentials before chat
- **GIVEN** the user runs `jdo chat`
- **WHEN** no AI credentials are configured
- **THEN** an error message is displayed: "AI not configured. Set ANTHROPIC_API_KEY or run: jdo config set provider openai"
- **AND** the command exits with code 1

#### Scenario: List commands work without AI
- **GIVEN** the user runs `jdo list commitments`
- **WHEN** AI credentials are not configured
- **THEN** the list is displayed normally (no AI required for queries)

#### Scenario: Add commands require AI for extraction
- **GIVEN** the user runs `jdo add commitment <text>`
- **WHEN** AI credentials are not configured
- **THEN** an error is displayed
- **AND** the command fails
