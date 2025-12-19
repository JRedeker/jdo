# provider-auth Specification

## Purpose
Define the authentication system for AI providers, supporting API key authentication for OpenAI and OpenRouter, with secure credential storage and TUI modal screens.
## Requirements
### Requirement: Credential Storage

The system SHALL store provider credentials in a JSON file at the platform-specific data directory (via `platformdirs`) with file permissions set to `0600` on Unix systems.

#### Scenario: First credential storage

- **GIVEN** no auth.json file exists
- **WHEN** credentials are saved for a provider
- **THEN** the system uses `get_auth_path()` from `jdo.paths` to determine the file location
- **AND** creates the data directory if needed
- **AND** creates auth.json with `0600` permissions on Unix (default permissions on Windows)
- **AND** stores the credentials under the provider ID key

#### Scenario: Update existing credentials

- **GIVEN** auth.json exists with credentials for provider "openai"
- **WHEN** new credentials are saved for "openai"
- **THEN** the existing credentials are replaced
- **AND** other provider credentials remain unchanged

#### Scenario: Multiple providers

- **GIVEN** auth.json exists with credentials for "openai"
- **WHEN** credentials are saved for "openrouter"
- **THEN** both provider credentials exist in auth.json

---

### Requirement: API Key Credentials Model

The system SHALL support API key credentials as a Pydantic model.

#### Scenario: Valid API key credentials

- **GIVEN** API key credentials
- **WHEN** the credentials are validated by Pydantic
- **THEN** they must contain a key (non-empty string)

---

### Requirement: Authentication Headers

The system SHALL provide appropriate HTTP headers for authenticated API requests based on credential type.

#### Scenario: API key credentials for OpenAI

- **GIVEN** API key credentials for "openai"
- **WHEN** auth headers are requested
- **THEN** the system returns `Authorization: Bearer {key}` header

#### Scenario: API key credentials for OpenRouter

- **GIVEN** API key credentials for "openrouter"
- **WHEN** auth headers are requested
- **THEN** the system returns `Authorization: Bearer {key}` header

---

### Requirement: Environment Variable Fallback

The system SHALL check environment variables for API keys before requiring manual authentication.

#### Scenario: OpenAI API key from environment

- **GIVEN** no stored credentials for "openai"
- **AND** environment variable `OPENAI_API_KEY` is set
- **WHEN** credentials are requested
- **THEN** the system uses the environment variable value
- **AND** does not prompt for authentication

#### Scenario: OpenRouter API key from environment

- **GIVEN** no stored credentials for "openrouter"
- **AND** environment variable `OPENROUTER_API_KEY` is set
- **WHEN** credentials are requested
- **THEN** the system uses the environment variable value

---

### Requirement: API Key TUI Screen

The system SHALL provide a Textual ModalScreen for entering API keys manually, using dismiss() to return success/failure status.

#### Scenario: Display API key input

- **GIVEN** the API key ModalScreen is pushed for a provider
- **WHEN** the screen is displayed
- **THEN** it shows the provider name
- **AND** provides a masked Input widget (password=True) for the API key
- **AND** displays a link to obtain an API key

#### Scenario: Submit valid API key

- **GIVEN** the API key screen is displayed
- **WHEN** the user enters a non-empty API key and submits
- **THEN** the system stores the credentials
- **AND** displays success notification
- **AND** calls dismiss(True) to return to the caller

#### Scenario: Submit empty API key

- **GIVEN** the API key screen is displayed
- **WHEN** the user submits without entering a key
- **THEN** the Input widget displays a validation error
- **AND** does not store credentials
- **AND** does not dismiss the screen

---

### Requirement: Credential Management

The system SHALL provide functions to check authentication status and clear credentials.

#### Scenario: Check authenticated status

- **GIVEN** valid credentials exist for "openai"
- **WHEN** authentication status is checked
- **THEN** the system returns true

#### Scenario: Check unauthenticated status

- **GIVEN** no credentials exist for "openai"
- **AND** no environment variable is set
- **WHEN** authentication status is checked
- **THEN** the system returns false

#### Scenario: Clear credentials

- **GIVEN** credentials exist for "openai"
- **WHEN** credentials are cleared for "openai"
- **THEN** the credentials are removed from auth.json
- **AND** subsequent auth checks return false

---

### Requirement: Provider Auth Methods Registry

The system SHALL maintain a registry mapping provider IDs to their supported authentication methods.

#### Scenario: OpenAI provider methods

- **GIVEN** the provider registry
- **WHEN** auth methods for "openai" are queried
- **THEN** the system returns API key as the only option

#### Scenario: OpenRouter provider methods

- **GIVEN** the provider registry
- **WHEN** auth methods for "openrouter" are queried
- **THEN** the system returns API key as the only option

### Requirement: Provider Selection Settings

The system SHALL provide a settings menu for switching between configured AI providers. Active provider selection is stored via the JDOSettings model defined in the `app-config` spec (using environment variables or `.env` file with `JDO_` prefix).

#### Scenario: Access settings from home
- **WHEN** user presses 's' on home screen
- **THEN** the settings menu opens showing current provider and available options

#### Scenario: Switch active provider
- **WHEN** user selects a different provider in settings
- **THEN** the active provider is changed and persisted to the `.env` file

#### Scenario: Show only configured providers
- **WHEN** settings menu displays provider options
- **THEN** only providers with valid credentials (stored or from environment) are selectable

#### Scenario: Add new provider from settings
- **WHEN** user selects "Add provider" in settings
- **THEN** the API key auth flow is initiated

### Requirement: Atomic Credential Storage

The system SHALL write credentials atomically to prevent corruption on interrupted writes.

#### Scenario: Atomic file write
- **WHEN** credentials are saved via `_write_store()`
- **THEN** data is written to a temporary file first
- **AND** the temp file is atomically renamed to the target path
- **AND** no partial writes can corrupt the credentials file

#### Scenario: Cleanup on write failure
- **WHEN** credential write fails (e.g., disk full)
- **THEN** the temporary file is cleaned up
- **AND** the original credentials file is unchanged

