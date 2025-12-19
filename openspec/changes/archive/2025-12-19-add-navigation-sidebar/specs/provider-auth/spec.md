# provider-auth Specification Delta

## ADDED Requirements

### Requirement: Settings Access

The system SHALL provide settings access via NavSidebar.

#### Scenario: Access settings from sidebar
- **WHEN** user selects "Settings" from NavSidebar or presses '9'
- **THEN** the SettingsScreen opens showing current provider and available options

#### Scenario: Switch active provider
- **WHEN** user selects a different provider in settings
- **THEN** the active provider is changed and persisted to the `.env` file

#### Scenario: Show only configured providers
- **WHEN** settings menu displays provider options
- **THEN** only providers with valid credentials (stored or from environment) are selectable
