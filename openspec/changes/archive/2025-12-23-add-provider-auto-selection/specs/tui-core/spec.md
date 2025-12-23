## ADDED Requirements

### Requirement: RadioSet Widget Pattern

The system SHALL use Textual's standard `RadioSet` widget for mutually exclusive option selection in settings screens.

#### Scenario: RadioSet for provider selection
- **GIVEN** the SettingsScreen needs to display provider options
- **WHEN** the RadioSet is composed
- **THEN** it contains `RadioButton` children for each authenticated provider
- **AND** the RadioSet uses standard Textual styling

#### Scenario: Handle RadioSet.Changed message
- **GIVEN** the RadioSet is displayed with multiple options
- **WHEN** the user selects a different RadioButton
- **THEN** the `RadioSet.Changed` message is posted
- **AND** the handler receives the new selected value

#### Scenario: RadioSet keyboard navigation
- **GIVEN** the RadioSet has focus
- **WHEN** the user presses arrow keys
- **THEN** selection moves between RadioButton options
- **AND** Enter confirms the selection

### Requirement: Settings Screen Dynamic Updates

The system SHALL update display elements when provider selection changes without requiring screen refresh.

#### Scenario: Update current provider display
- **GIVEN** the SettingsScreen is displayed with "Provider: openai"
- **WHEN** user selects "openrouter" in the RadioSet
- **THEN** the display updates to "Provider: openrouter"
- **AND** no screen navigation occurs

#### Scenario: Refresh after external credential change
- **GIVEN** the SettingsScreen is displayed
- **WHEN** API key modal completes successfully
- **THEN** the RadioSet options are refreshed to include newly authenticated provider
- **AND** auth status widgets are updated
