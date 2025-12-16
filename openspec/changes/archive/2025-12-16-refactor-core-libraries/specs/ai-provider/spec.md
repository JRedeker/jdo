# Capability: AI Provider Integration

AI provider integration uses PydanticAI for agent-based interactions with language models. This capability provides streaming responses, tool calling, and structured output extraction for commitment management assistance.

## ADDED Requirements

### Requirement: Agent Configuration

The system SHALL provide a PydanticAI agent configured for commitment management assistance.

#### Scenario: Create agent with Anthropic provider
- **WHEN** settings specify `ai_provider=anthropic` and `ai_model=claude-sonnet-4-20250514`
- **THEN** agent is created with model identifier "anthropic:claude-sonnet-4-20250514"

#### Scenario: Create agent with OpenAI provider
- **WHEN** settings specify `ai_provider=openai` and `ai_model=gpt-4o`
- **THEN** agent is created with model identifier "openai:gpt-4o"

#### Scenario: Agent has system prompt
- **WHEN** agent is created
- **THEN** it has a system prompt focused on commitment tracking assistance

### Requirement: Agent Dependencies

The system SHALL provide a dependencies class for injecting runtime context into agent tools.

#### Scenario: Dependencies include session
- **WHEN** agent tool accesses `ctx.deps.session`
- **THEN** an active database session is available

#### Scenario: Dependencies include current user context
- **WHEN** agent tool accesses `ctx.deps.timezone`
- **THEN** the configured timezone string is available

### Requirement: Commitment Tools

The system SHALL provide agent tools for accessing commitment data.

#### Scenario: Get current commitments tool
- **WHEN** agent calls `get_current_commitments` tool
- **THEN** a list of pending and in-progress commitments is returned

#### Scenario: Get overdue commitments tool
- **WHEN** agent calls `get_overdue_commitments` tool
- **THEN** a list of commitments past their due date is returned

#### Scenario: Get commitments by goal tool
- **WHEN** agent calls `get_commitments_for_goal` with a goal_id
- **THEN** commitments associated with that goal are returned

### Requirement: Streaming Responses

The system SHALL support streaming text responses from the AI agent.

#### Scenario: Stream text response
- **WHEN** `agent.run_stream(prompt)` is called
- **THEN** text chunks are yielded as they become available

#### Scenario: Handle stream cancellation
- **WHEN** streaming is cancelled mid-response
- **THEN** resources are cleaned up without error

#### Scenario: Stream with tool calls
- **WHEN** agent response includes tool calls during streaming
- **THEN** tool results are incorporated and streaming continues

### Requirement: Structured Output

The system SHALL support extracting structured data from AI responses.

#### Scenario: Extract commitment suggestion
- **WHEN** agent is asked to suggest a commitment with `output_type=CommitmentSuggestion`
- **THEN** response is parsed into a validated Pydantic model

#### Scenario: Extract task breakdown
- **WHEN** agent is asked to break down work with `output_type=TaskBreakdown`
- **THEN** response is parsed into a list of suggested tasks

#### Scenario: Handle parsing failure
- **WHEN** AI response cannot be parsed into the expected output type
- **THEN** a clear error is raised with the raw response available

### Requirement: Error Handling

The system SHALL handle AI provider errors gracefully.

#### Scenario: Handle rate limit error
- **WHEN** AI provider returns rate limit error
- **THEN** error is caught and user-friendly message is provided

#### Scenario: Handle authentication error
- **WHEN** AI provider returns authentication error
- **THEN** user is prompted to check credentials

#### Scenario: Handle network error
- **WHEN** network connection to AI provider fails
- **THEN** error is caught and retry guidance is provided

### Requirement: Token Management

The system SHALL use OAuth tokens or API keys based on provider configuration.

#### Scenario: Use OAuth token for Claude Max
- **WHEN** Anthropic OAuth credentials are stored
- **THEN** agent uses OAuth access token with beta header

#### Scenario: Use API key for standard access
- **WHEN** API key is configured for provider
- **THEN** agent uses API key for authentication

#### Scenario: Refresh expired OAuth token
- **WHEN** OAuth access token is expired
- **THEN** token is refreshed before making API call
