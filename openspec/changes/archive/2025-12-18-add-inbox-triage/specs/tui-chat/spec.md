## ADDED Requirements

### Requirement: Command - Triage

The system SHALL support the `/triage` command to process inbox items.

#### Scenario: Triage command recognized
- **WHEN** user types `/triage`
- **THEN** the command is parsed as CommandType.TRIAGE

#### Scenario: Triage with items starts workflow
- **WHEN** user types `/triage` and triage items exist
- **THEN** the triage workflow begins with the first item displayed

#### Scenario: Triage without items shows message
- **WHEN** user types `/triage` and no triage items exist
- **THEN** the system responds "No items to triage. Your inbox is empty."

#### Scenario: Triage in help output
- **WHEN** user types `/help`
- **THEN** the help text includes "/triage - Process items in your inbox"

### Requirement: Chat Message Handling

The system SHALL handle non-command messages in the chat.

#### Scenario: Message submitted in chat
- **WHEN** user submits text without a `/` prefix in chat
- **THEN** the message is processed by the AI for intent detection

#### Scenario: Clear intent proceeds to creation
- **WHEN** user submits "I need to send the report to Sarah by Friday"
- **AND** AI detects clear commitment intent
- **THEN** AI responds with creation guidance or suggests `/commit`

#### Scenario: Vague intent creates triage item
- **WHEN** user submits "remember to call mom"
- **AND** AI cannot determine object type with confidence
- **THEN** a triage item is created and AI offers immediate triage

#### Scenario: User accepts immediate triage
- **WHEN** AI offers triage and user responds affirmatively
- **THEN** triage mode starts with the new item

#### Scenario: User declines immediate triage
- **WHEN** AI offers triage and user declines or continues chatting
- **THEN** the item remains in triage queue and conversation continues

### Requirement: Triage Workflow Display

The system SHALL display triage items with AI analysis in the chat.

#### Scenario: Triage item display format
- **WHEN** a triage item is shown in the workflow
- **THEN** the display includes: item number, total count, raw text, AI analysis, and action options

#### Scenario: AI analysis display
- **WHEN** AI analyzes a triage item
- **THEN** the analysis shows: suggested type, confidence indicator, detected entities, and potential links

#### Scenario: Action options display
- **WHEN** triage item is displayed
- **THEN** options show: "[1] Accept [2] Change type [3] Delete [4] Skip"

#### Scenario: Low confidence clarification
- **WHEN** AI confidence is low
- **THEN** a simple clarifying question is shown instead of a type suggestion
