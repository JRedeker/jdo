## MODIFIED Requirements

### Requirement: Provider Selection Settings

The system SHALL provide a settings menu for switching between configured AI providers. Active provider selection is stored via the JDOSettings model defined in the `app-config` spec (using environment variables or `.env` file with `JDO_` prefix).

#### Scenario: Access settings from sidebar
- **WHEN** user selects "Settings" from NavSidebar or presses '9'
- **THEN** the settings menu opens showing current provider and available options

#### Scenario: Switch active provider via RadioSet
- **GIVEN** multiple providers have valid credentials
- **WHEN** user selects a different provider in the RadioSet widget
- **THEN** the active provider is changed via `set_ai_provider()`
- **AND** the change is persisted to the `.env` file
- **AND** the "Current AI Configuration" display updates immediately

#### Scenario: Show only authenticated providers in RadioSet
- **WHEN** settings menu displays the provider RadioSet
- **THEN** only providers with valid credentials (stored or from environment) appear as options
- **AND** providers without credentials are not shown

#### Scenario: Hide RadioSet when only one provider authenticated
- **WHEN** exactly one provider has valid credentials
- **THEN** the RadioSet is hidden (no selection needed)
- **AND** the single authenticated provider is shown as static text

#### Scenario: Pre-select current provider
- **GIVEN** the settings screen is displayed
- **WHEN** the RadioSet renders
- **THEN** the RadioButton for `settings.ai_provider` is selected

#### Scenario: Add new provider from settings
- **WHEN** user selects "Add provider" or "Configure" button for an unauthenticated provider
- **THEN** the API key auth flow is initiated

## ADDED Requirements

### Requirement: Provider Auto-Selection on Startup

The system SHALL automatically select an authenticated provider when the configured provider lacks credentials.

#### Scenario: Auto-select when default lacks credentials
- **GIVEN** `JDO_AI_PROVIDER=openai` is configured
- **AND** no OpenAI credentials exist
- **AND** OpenRouter credentials exist
- **WHEN** the app starts
- **THEN** the app auto-selects "openrouter" as the active provider
- **AND** the choice is persisted to `.env`
- **AND** no "AI not configured" modal is shown

#### Scenario: Prefer openai when multiple providers authenticated
- **GIVEN** both OpenAI and OpenRouter have valid credentials
- **AND** `JDO_AI_PROVIDER=openrouter` is configured (but fallback logic triggered)
- **WHEN** auto-selection occurs
- **THEN** "openai" is preferred if authenticated
- **AND** the choice is persisted

#### Scenario: Show modal when no providers authenticated
- **GIVEN** no provider has valid credentials
- **WHEN** the app starts
- **THEN** the "AI not configured" modal is shown
- **AND** user must configure credentials or quit

#### Scenario: No auto-selection when configured provider works
- **GIVEN** `JDO_AI_PROVIDER=openrouter` is configured
- **AND** OpenRouter credentials exist
- **WHEN** the app starts
- **THEN** no auto-selection occurs
- **AND** "openrouter" remains the active provider
