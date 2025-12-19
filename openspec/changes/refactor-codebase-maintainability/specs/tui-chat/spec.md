## ADDED Requirements

### Requirement: Conversation History Management

The system SHALL manage conversation history to prevent unbounded memory growth.

#### Scenario: Prune conversation after user message
- **WHEN** a user message is added to conversation history
- **AND** conversation length exceeds MAX_CONVERSATION_HISTORY (default 50)
- **THEN** the oldest messages are removed to maintain the limit
- **AND** only the most recent MAX_CONVERSATION_HISTORY messages are retained

#### Scenario: Prune conversation after AI response
- **WHEN** an AI response is added to conversation history
- **AND** conversation length exceeds MAX_CONVERSATION_HISTORY
- **THEN** the oldest messages are removed to maintain the limit

#### Scenario: Preserve recent context
- **WHEN** conversation is pruned
- **THEN** the most recent messages are preserved
- **AND** AI retains sufficient context for coherent responses

#### Scenario: No pruning when under limit
- **WHEN** conversation length is at or below MAX_CONVERSATION_HISTORY
- **THEN** no messages are removed
