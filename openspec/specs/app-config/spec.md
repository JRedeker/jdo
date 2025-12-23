# app-config Specification

## Purpose
Define the application configuration system using pydantic-settings, supporting environment variables, .env files, and sensible defaults for database path, AI provider, timezone, and logging.
## Requirements
### Requirement: Settings Model

The system SHALL provide a `JDOSettings` pydantic-settings model with the following configuration options:

- `database_path` (Path | None): Override path to SQLite database, defaults to platformdirs location
- `ai_provider` (str): AI provider identifier, defaults to "openai"
- `ai_model` (str): Model identifier, defaults to "gpt-4.1"
- `timezone` (str): Default timezone for datetime fields, defaults to "America/New_York"
- `log_level` (str): Logging level, defaults to "INFO"

#### Scenario: Load settings with defaults
- **WHEN** application starts without environment variables set
- **THEN** JDOSettings loads with all default values
- **AND** `ai_model` defaults to "gpt-4.1"

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

### Requirement: Provider Selection Persistence

The system SHALL provide a `set_ai_provider()` function that updates the active provider in both the settings singleton and the `.env` file.

#### Scenario: Update singleton and persist to .env
- **WHEN** `set_ai_provider("openrouter")` is called
- **THEN** the settings singleton's `ai_provider` is updated to "openrouter"
- **AND** the `.env` file contains `JDO_AI_PROVIDER=openrouter`
- **AND** other `.env` values are preserved

#### Scenario: Coerce invalid provider to default
- **WHEN** `set_ai_provider("invalid_provider")` is called
- **THEN** the function returns the default provider "openai"
- **AND** the settings singleton is updated to "openai"

#### Scenario: Create .env file if missing
- **WHEN** `set_ai_provider()` is called and no `.env` file exists
- **THEN** a new `.env` file is created with `JDO_AI_PROVIDER=<provider>`

#### Scenario: Respect JDO_ENV_FILE override
- **WHEN** environment variable `JDO_ENV_FILE` is set to `/custom/path/.env`
- **THEN** `set_ai_provider()` writes to that path instead of `./.env`

### Requirement: Env File Helpers

The system SHALL provide internal helper functions for reading and writing `.env` files.

#### Scenario: Parse env file with comments
- **GIVEN** an `.env` file containing:
  ```
  # Comment line
  KEY1=value1
  
  KEY2=value2
  ```
- **WHEN** the file is parsed
- **THEN** `{"KEY1": "value1", "KEY2": "value2"}` is returned
- **AND** comments and blank lines are ignored

#### Scenario: Write env file atomically
- **WHEN** values are written to `.env`
- **THEN** keys are sorted alphabetically
- **AND** each line follows `KEY=value` format
- **AND** file ends with newline

### Requirement: Supported Providers Constant

The system SHALL define a `SUPPORTED_PROVIDERS` constant tuple listing valid provider identifiers.

#### Scenario: Validate provider against constant
- **WHEN** provider validation occurs
- **THEN** the provider is checked against `SUPPORTED_PROVIDERS = ("openai", "openrouter")`

