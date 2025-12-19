# tui-chat Spec Delta

## ADDED Requirements

### Requirement: AI Message Handling

The system SHALL invoke the AI agent for non-command chat messages.

#### Scenario: User sends non-command message
- **WHEN** user submits text without a `/` prefix in chat
- **THEN** the message is displayed in the chat container
- **AND** the message is sent to the AI agent for processing

#### Scenario: AI response streams into chat
- **WHEN** AI agent begins responding to a message
- **THEN** an assistant message appears with "Thinking..." indicator
- **AND** the message content updates as text chunks arrive
- **AND** the chat auto-scrolls to show new content

#### Scenario: AI response completes
- **WHEN** AI agent finishes streaming a response
- **THEN** the final message is displayed in full
- **AND** the conversation history is updated with the complete response

#### Scenario: New message cancels previous AI request
- **WHEN** user submits a new message while AI is still responding
- **THEN** the previous AI request is cancelled
- **AND** the new message is processed instead

### Requirement: Conversation History

The system SHALL maintain conversation history within a chat session.

#### Scenario: History accumulates during session
- **WHEN** user and AI exchange multiple messages
- **THEN** conversation history includes all messages with role and content
- **AND** history is available for AI context on subsequent messages

#### Scenario: History truncation
- **WHEN** conversation exceeds 50 messages
- **THEN** oldest messages are removed to maintain context window
- **AND** system prompt is always included

### Requirement: AI Error Display

The system SHALL display user-friendly error messages for AI failures.

#### Scenario: Rate limit error
- **WHEN** AI provider returns rate limit error
- **THEN** chat displays "AI is busy. Please wait a moment and try again."

#### Scenario: Authentication error
- **WHEN** AI provider returns authentication error
- **THEN** chat displays "AI authentication failed. Check your API key in settings."
- **AND** user is guided to settings screen

#### Scenario: Network error
- **WHEN** network connection to AI provider fails
- **THEN** chat displays "Couldn't reach AI provider. Check your connection."

#### Scenario: Unknown error
- **WHEN** an unexpected error occurs during AI processing
- **THEN** chat displays "Something went wrong. Your message was not processed."
- **AND** the error is logged for debugging

### Requirement: AI Credentials Check

The system SHALL verify AI credentials before sending messages.

#### Scenario: No credentials configured
- **WHEN** user sends a message and no API key or OAuth token is configured
- **THEN** chat displays "AI not configured. Set up your API key in settings."
- **AND** user is guided to settings screen

#### Scenario: Credentials available
- **WHEN** user sends a message and credentials are configured
- **THEN** the message is sent to the AI agent

### Requirement: Input State During AI Processing

The system SHALL manage input state while AI is processing.

#### Scenario: Input disabled during streaming
- **WHEN** AI agent is processing a response
- **THEN** the prompt input is disabled to prevent duplicate submissions

#### Scenario: Input re-enabled after completion
- **WHEN** AI response completes or errors
- **THEN** the prompt input is re-enabled for new input

## MODIFIED Requirements

### Requirement: Chat Message Handling

The system SHALL handle non-command messages in the chat.

#### Scenario: Message submitted in chat
- **WHEN** user submits text without a `/` prefix in chat
- **THEN** the message is displayed in chat and sent to AI for processing

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
