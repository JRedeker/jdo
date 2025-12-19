# tui-chat Spec Delta

## ADDED Requirements

### Requirement: Typed Draft Gate

The system SHALL require a draft to have a true entity type before refinement.

#### Scenario: User assigns type before refinement
- **WHEN** a draft is awaiting confirmation and has no true type
- **THEN** the system prompts the user to assign a type
- **AND** the user must confirm the type (y/n) before edits are applied

#### Scenario: AI suggests type only when user doesn't specify
- **WHEN** the user does not specify a type for an untyped draft
- **THEN** AI suggests a type
- **AND** the user must confirm the suggested type (y/n)

### Requirement: Confirmation Flow

The system SHALL support a confirmation workflow for entity creation.

#### Scenario: Handler requests confirmation
- **WHEN** a command handler returns `needs_confirmation=True`
- **THEN** the chat enters confirmation-awaiting state
- **AND** the draft is displayed in the data panel

#### Scenario: User confirms creation
- **WHEN** user responds with "yes", "y", or "confirm" while awaiting confirmation
- **THEN** the pending entity is saved to the database
- **AND** a success message is displayed in chat
- **AND** the data panel shows the saved entity in view mode

#### Scenario: User cancels creation
- **WHEN** user responds with "no", "n", or "cancel" while awaiting confirmation
- **THEN** the draft is discarded
- **AND** a cancellation message is displayed
- **AND** the confirmation state is cleared

#### Scenario: User sends other message while awaiting
- **WHEN** user sends a message that is neither confirmation nor cancellation
- **THEN** the message is treated as a request to modify the draft
- **AND** the system SHALL re-render the updated draft
- **AND** the confirmation state remains active

### Requirement: AI Required

The system SHALL require AI configuration before app use.

#### Scenario: AI not configured at app start
- **WHEN** the user opens the app with no configured AI provider credentials
- **THEN** the home screen displays a blocking modal
- **AND** the modal offers a button to open Settings
- **AND** the modal offers a Quit option

### Requirement: Entity Save Feedback

The system SHALL provide clear feedback after entity persistence.

#### Scenario: Successful save
- **WHEN** an entity is successfully saved to the database
- **THEN** chat displays "Saved! [entity-specific message]"
- **AND** the data panel switches to view mode showing the entity

#### Scenario: Save failure
- **WHEN** an entity fails to save due to validation error
- **THEN** chat displays the specific validation error
- **AND** the draft remains in the data panel for correction

#### Scenario: Save failure due to database error
- **WHEN** an entity fails to save due to database error
- **THEN** chat displays "Couldn't save. Please try again."
- **AND** the draft remains in the data panel
