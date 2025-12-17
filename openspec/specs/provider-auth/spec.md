# provider-auth Specification

## Purpose
Define the authentication system for AI providers, supporting OAuth 2.0 with PKCE for Claude Max/Pro and API key authentication for OpenAI and OpenRouter, with secure credential storage and TUI modal screens.
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

- **GIVEN** auth.json exists with credentials for provider "anthropic"
- **WHEN** new credentials are saved for "anthropic"
- **THEN** the existing credentials are replaced
- **AND** other provider credentials remain unchanged

#### Scenario: Multiple providers

- **GIVEN** auth.json exists with credentials for "openai"
- **WHEN** credentials are saved for "anthropic"
- **THEN** both provider credentials exist in auth.json

---

### Requirement: OAuth Credentials Model

The system SHALL support OAuth credentials as a Pydantic model with a `type` field using `Literal["oauth"]` for discriminated union support.

#### Scenario: Valid OAuth credentials

- **GIVEN** OAuth credentials with type field set to literal "oauth"
- **WHEN** the credentials are validated by Pydantic
- **THEN** they must contain access token (string)
- **AND** refresh token (string)
- **AND** expires timestamp (integer, milliseconds since epoch)

#### Scenario: Expired OAuth credentials detection

- **GIVEN** OAuth credentials with expires timestamp in the past
- **WHEN** checking if credentials are valid
- **THEN** the system reports credentials as expired

---

### Requirement: API Key Credentials Model

The system SHALL support API key credentials as a Pydantic model with a `type` field using `Literal["api"]` for discriminated union support.

#### Scenario: Valid API key credentials

- **GIVEN** API key credentials with type field set to literal "api"
- **WHEN** the credentials are validated by Pydantic
- **THEN** they must contain a key (non-empty string)

---

### Requirement: Claude OAuth PKCE Flow

The system SHALL implement OAuth 2.0 Authorization Code flow with PKCE for Claude Max/Pro authentication, using the same client ID and endpoints as OpenCode.

#### Scenario: Generate authorization URL

- **GIVEN** a request to start Claude OAuth
- **WHEN** the authorization URL is generated
- **THEN** the URL uses `https://claude.ai/oauth/authorize` as base
- **AND** includes client_id `9d1c250a-e61b-44d9-88ed-5944d1962f5e`
- **AND** includes response_type `code`
- **AND** includes redirect_uri `https://console.anthropic.com/oauth/code/callback`
- **AND** includes scope `org:create_api_key user:profile user:inference`
- **AND** includes a PKCE code_challenge (S256 method)
- **AND** includes state parameter set to the PKCE verifier

#### Scenario: Exchange authorization code for tokens

- **GIVEN** a valid authorization code and PKCE verifier
- **WHEN** the code is exchanged at `https://console.anthropic.com/v1/oauth/token`
- **THEN** the system sends grant_type `authorization_code`
- **AND** includes the code, state, client_id, redirect_uri, and code_verifier
- **AND** stores the returned access_token, refresh_token, and calculated expiry

#### Scenario: Invalid authorization code

- **GIVEN** an invalid or expired authorization code
- **WHEN** the code exchange is attempted
- **THEN** the system returns an authentication error
- **AND** does not store any credentials

---

### Requirement: OAuth Token Refresh

The system SHALL refresh OAuth tokens only when an API request fails with 401 Unauthorized.

#### Scenario: Refresh on 401 response

- **GIVEN** stored OAuth credentials
- **WHEN** an API request fails with 401 Unauthorized
- **THEN** the system calls the token endpoint with grant_type `refresh_token`
- **AND** updates stored credentials with new access_token and expiry
- **AND** retries the original request with the new token

#### Scenario: Refresh token invalid

- **GIVEN** stored OAuth credentials with invalid refresh token
- **WHEN** token refresh is attempted after 401
- **THEN** the system clears the stored credentials
- **AND** returns an error indicating re-authentication is required

#### Scenario: No proactive refresh

- **GIVEN** stored OAuth credentials with access token expiring soon
- **WHEN** credentials are requested for use
- **THEN** the system uses the current token without proactive refresh

---

### Requirement: Authentication Headers

The system SHALL provide appropriate HTTP headers for authenticated API requests based on credential type.

#### Scenario: OAuth credentials headers

- **GIVEN** valid OAuth credentials for "anthropic"
- **WHEN** auth headers are requested
- **THEN** the system returns `Authorization: Bearer {access_token}`
- **AND** includes `anthropic-beta: oauth-2025-04-20` header

#### Scenario: API key credentials headers

- **GIVEN** API key credentials for "anthropic"
- **WHEN** auth headers are requested
- **THEN** the system returns `x-api-key: {key}` header

#### Scenario: API key credentials for OpenAI

- **GIVEN** API key credentials for "openai"
- **WHEN** auth headers are requested
- **THEN** the system returns `Authorization: Bearer {key}` header

---

### Requirement: Environment Variable Fallback

The system SHALL check environment variables for API keys before requiring manual authentication.

#### Scenario: Anthropic API key from environment

- **GIVEN** no stored credentials for "anthropic"
- **AND** environment variable `ANTHROPIC_API_KEY` is set
- **WHEN** credentials are requested
- **THEN** the system uses the environment variable value
- **AND** does not prompt for authentication

#### Scenario: OpenAI API key from environment

- **GIVEN** no stored credentials for "openai"
- **AND** environment variable `OPENAI_API_KEY` is set
- **WHEN** credentials are requested
- **THEN** the system uses the environment variable value

#### Scenario: OpenRouter API key from environment

- **GIVEN** no stored credentials for "openrouter"
- **AND** environment variable `OPENROUTER_API_KEY` is set
- **WHEN** credentials are requested
- **THEN** the system uses the environment variable value

---

### Requirement: OAuth TUI Screen

The system SHALL provide a Textual ModalScreen for completing OAuth authentication within the terminal interface, using dismiss() to return success/failure status.

#### Scenario: Display authorization URL

- **GIVEN** the OAuth ModalScreen is pushed for Claude
- **WHEN** the screen is displayed
- **THEN** it shows the authorization URL
- **AND** offers to open the URL in the default browser via webbrowser module
- **AND** displays instructions to paste the authorization code
- **AND** provides an Input widget for code entry

#### Scenario: Submit authorization code

- **GIVEN** the OAuth screen is displayed
- **WHEN** the user pastes an authorization code and submits
- **THEN** the system exchanges the code for tokens asynchronously
- **AND** displays success notification on success
- **AND** calls dismiss(True) to return to the caller

#### Scenario: Invalid code submission

- **GIVEN** the OAuth screen is displayed
- **WHEN** the user submits an invalid code
- **THEN** the system displays an error notification
- **AND** allows the user to retry or cancel via dismiss(False)

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

- **GIVEN** valid credentials exist for "anthropic"
- **WHEN** authentication status is checked
- **THEN** the system returns true

#### Scenario: Check unauthenticated status

- **GIVEN** no credentials exist for "openai"
- **AND** no environment variable is set
- **WHEN** authentication status is checked
- **THEN** the system returns false

#### Scenario: Clear credentials

- **GIVEN** credentials exist for "anthropic"
- **WHEN** credentials are cleared for "anthropic"
- **THEN** the credentials are removed from auth.json
- **AND** subsequent auth checks return false

---

### Requirement: Provider Auth Methods Registry

The system SHALL maintain a registry mapping provider IDs to their supported authentication methods.

#### Scenario: Anthropic provider methods

- **GIVEN** the provider registry
- **WHEN** auth methods for "anthropic" are queried
- **THEN** the system returns OAuth (Claude Max/Pro) and API key as options

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
- **THEN** the appropriate auth flow (OAuth or API key) is initiated

