# AI Agent Credentials Specification

## Purpose

Define how API credentials are passed to PydanticAI providers, ensuring credentials stored in JDO's credential store are used at runtime. Environment variables are NOT used as a fallback per OWASP security best practices.

## ADDED Requirements

### Requirement: Explicit Provider Initialization

The system SHALL pass API credentials explicitly to PydanticAI provider classes instead of relying on environment variables.

#### Scenario: Create agent with stored OpenRouter credentials

- **GIVEN** the configured provider is "openrouter"
- **AND** valid credentials exist in JDO's credential store
- **WHEN** `create_agent()` is called
- **THEN** the agent is created with `OpenRouterProvider(api_key=creds.api_key)`
- **AND** no environment variable lookup is performed

#### Scenario: Create agent with stored OpenAI credentials

- **GIVEN** the configured provider is "openai"
- **AND** valid credentials exist in JDO's credential store
- **WHEN** `create_agent()` is called
- **THEN** the agent is created with `OpenAIProvider(api_key=creds.api_key)`
- **AND** no environment variable lookup is performed

### Requirement: Error on Missing Credentials

The system SHALL raise an appropriate error when no credentials are available from the credential store.

#### Scenario: No credentials available

- **GIVEN** no stored credentials exist for the configured provider
- **WHEN** `create_agent()` is called
- **THEN** a `MissingCredentialsError` is raised
- **AND** the error message includes setup instructions

#### Scenario: Invalid provider configuration

- **GIVEN** the configured provider is not "openai" or "openrouter"
- **WHEN** `create_agent()` is called
- **THEN** an `UnsupportedProviderError` is raised

### Requirement: Provider Implementation

The system SHALL inline provider creation logic in `create_agent()` without a separate factory abstraction.

#### Scenario: OpenRouter provider implementation

- **GIVEN** the configured provider is "openrouter"
- **WHEN** `create_agent()` creates the model
- **THEN** it uses `OpenRouterProvider(api_key=creds.api_key)` directly
- **AND** creates `OpenRouterModel(settings.ai_model, provider=provider)`

#### Scenario: OpenAI provider implementation

- **GIVEN** the configured provider is "openai"
- **WHEN** `create_agent()` creates the model
- **THEN** it uses `OpenAIProvider(api_key=creds.api_key)` directly
- **AND** creates `OpenAIModel(settings.ai_model, provider=provider)`

### Requirement: Credential Validation

The system SHALL validate credentials before passing them to providers.

#### Scenario: Invalid credential format

- **GIVEN** stored credentials exist but the API key format is invalid
- **WHEN** `create_agent()` is called
- **THEN** an `InvalidCredentialsError` is raised
- **AND** the error message indicates the credential format is invalid

#### Scenario: Missing model configuration

- **GIVEN** credentials exist for the configured provider
- **AND** `settings.ai_model` is None or empty
- **WHEN** `create_agent()` is called
- **THEN** a `ConfigError` is raised with setup instructions

### Requirement: Logging and Observability

The system SHALL emit structured logs for credential operations.

#### Scenario: Log credential retrieval

- **GIVEN** credentials exist for the configured provider
- **WHEN** `create_agent()` retrieves credentials
- **THEN** a debug log is emitted with the provider ID (not the key)
- **AND** credential retrieval success/failure is traced

#### Scenario: Log credential errors

- **GIVEN** no credentials exist for the configured provider
- **WHEN** `create_agent()` fails with `MissingCredentialsError`
- **THEN** an error log is emitted with the provider ID
- **AND** the error includes a recovery hint

> **Note**: Logging/Observability is required per JDO core rules (P14).

### Requirement: Supersedes Existing Behavior

This specification SHALL supersede the environment variable fallback and provider auto-selection behaviors defined in `openspec/specs/provider-auth/spec.md` for agent creation.

#### Scenario: Environment variable fallback removed

- **GIVEN** environment variable for the provider is set
- **AND** no stored credentials exist
- **WHEN** `create_agent()` is called
- **THEN** a `MissingCredentialsError` is raised
- **AND** the environment variable is NOT used
- **AND** user is directed to run `jdo auth` to configure credentials

> **Rationale**: OWASP and industry best practices recommend against using environment variables for secrets due to `/proc` filesystem exposure and log leakage risks.

#### Scenario: Provider auto-selection removed

- **GIVEN** `JDO_AI_PROVIDER` is configured to a provider
- **AND** no credentials exist for that provider
- **AND** credentials exist for another provider
- **WHEN** `create_agent()` is called
- **THEN** a `MissingCredentialsError` is raised
- **AND** no auto-selection occurs

> **Rationale**: Explicit provider configuration is preferred over implicit fallback to avoid unexpected provider switches.
