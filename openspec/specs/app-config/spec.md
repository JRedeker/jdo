# app-config Specification

## Purpose
Define the application configuration system using pydantic-settings, supporting environment variables, .env files, and sensible defaults for database path, AI provider, timezone, and logging.
## Requirements
### Requirement: Settings Model

The system SHALL provide a `JDOSettings` pydantic-settings model with the following configuration options:

- `database_path` (Path | None): Override path to SQLite database, defaults to platformdirs location
- `ai_provider` (str): AI provider identifier, defaults to "openai"
- `ai_model` (str): Model identifier, defaults to "gpt-4o"
- `timezone` (str): Default timezone for datetime fields, defaults to "America/New_York"
- `log_level` (str): Logging level, defaults to "INFO"

#### Scenario: Load settings with defaults
- **WHEN** application starts without environment variables set
- **THEN** JDOSettings loads with all default values

#### Scenario: Load settings from environment variables
- **WHEN** environment variable `JDO_AI_MODEL` is set to "gpt-4o-mini"
- **THEN** JDOSettings.ai_model equals "gpt-4o-mini"

#### Scenario: Load settings from .env file
- **WHEN** a `.env` file exists with `JDO_TIMEZONE=Europe/London`
- **THEN** JDOSettings.timezone equals "Europe/London"

#### Scenario: Environment variables override .env file
- **WHEN** `.env` has `JDO_LOG_LEVEL=DEBUG` and environment has `JDO_LOG_LEVEL=WARNING`
- **THEN** JDOSettings.log_level equals "WARNING"

### Requirement: Settings Singleton

The system SHALL provide a singleton accessor for settings to avoid repeated parsing.

#### Scenario: Get settings returns same instance
- **WHEN** `get_settings()` is called multiple times
- **THEN** the same JDOSettings instance is returned each time

#### Scenario: Settings can be reset for testing
- **WHEN** `reset_settings()` is called
- **THEN** the next `get_settings()` call creates a fresh instance

### Requirement: Database Path Configuration

The system SHALL support configurable database path with sensible defaults.

#### Scenario: Default database path uses platformdirs
- **WHEN** `database_path` is not configured
- **THEN** the database is created at `{platformdirs.user_data_dir("jdo")}/jdo.db`

#### Scenario: Custom database path is respected
- **WHEN** `JDO_DATABASE_PATH=/tmp/test.db` is set
- **THEN** the database is created at `/tmp/test.db`

#### Scenario: Database directory is created if missing
- **WHEN** database path points to a non-existent directory
- **THEN** the parent directory is created automatically

### Requirement: AI Provider Configuration

The system SHALL support configuration of AI provider and model selection.

#### Scenario: Configure OpenAI provider
- **WHEN** `JDO_AI_PROVIDER=openai` and `JDO_AI_MODEL=gpt-4o`
- **THEN** AI agent is configured to use OpenAI with the specified model

#### Scenario: Configure OpenRouter provider
- **WHEN** `JDO_AI_PROVIDER=openrouter` and `JDO_AI_MODEL=anthropic/claude-3.5-sonnet`
- **THEN** AI agent is configured to use OpenRouter with the specified model

#### Scenario: Invalid provider raises error
- **WHEN** `JDO_AI_PROVIDER=invalid_provider` is set
- **THEN** settings validation raises a descriptive error

### Requirement: Tenacity Dependency

The system SHALL include `tenacity` as a dependency for retry logic with exponential backoff.

#### Scenario: Tenacity available for import
- **GIVEN** the project dependencies are installed
- **WHEN** code imports from tenacity
- **THEN** `retry`, `stop_after_attempt`, `wait_exponential`, and `retry_if_exception_type` are available

#### Scenario: Minimum version requirement
- **GIVEN** pyproject.toml specifies dependencies
- **THEN** tenacity version SHALL be `>=8.0.0`

#### Scenario: Missing tenacity raises clear error
- **GIVEN** tenacity is not installed in the environment
- **WHEN** the retry module (`jdo.retry`) is imported
- **THEN** an ImportError is raised
- **AND** the error message indicates tenacity is required

