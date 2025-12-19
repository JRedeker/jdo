# ai-provider Specification

## Purpose
Define the PydanticAI agent configuration for commitment management assistance, including provider setup, dependency injection, commitment tools, streaming responses, and structured output extraction.
## Requirements
### Requirement: Agent Configuration

The system SHALL provide a PydanticAI agent configured for commitment management assistance.

#### Scenario: Create agent with OpenAI provider
- **WHEN** settings specify `ai_provider=openai` and `ai_model=gpt-4o`
- **THEN** agent is created with model identifier "openai:gpt-4o"

#### Scenario: Create agent with OpenRouter provider
- **WHEN** settings specify `ai_provider=openrouter` and `ai_model=anthropic/claude-3.5-sonnet`
- **THEN** agent is created with model identifier "openrouter:anthropic/claude-3.5-sonnet"

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

The system SHALL use API keys based on provider configuration.

#### Scenario: Use API key for provider access
- **WHEN** API key is configured for provider
- **THEN** agent uses API key for authentication

### Requirement: AI Coaching System Prompt

The system SHALL use an enhanced system prompt that instructs the AI to act as a commitment integrity coach with proactive pushback behaviors.

#### Scenario: Coaching prompt loaded
- **WHEN** agent is created
- **THEN** the system prompt includes coaching behaviors for time management, integrity-based guidance, and estimation coaching

#### Scenario: Time-based pushback behavior
- **WHEN** system prompt is active
- **THEN** AI is instructed to ask "How many hours do you have remaining today?" and compare against task estimates
- **AND** AI understands this means hours remaining right now, not total workday hours

#### Scenario: Integrity-based coaching behavior
- **WHEN** system prompt is active
- **THEN** AI is instructed to reference user's letter grade and history when discussing new commitments

#### Scenario: Estimation coaching behavior
- **WHEN** system prompt is active
- **THEN** AI is instructed to request time estimates for every task and reference historical accuracy patterns

### Requirement: User Time Context Tool

The system SHALL provide an AI tool for querying user's daily time availability and allocation.

#### Scenario: Query time context
- **WHEN** AI calls query_user_time_context tool
- **THEN** it returns: available_hours_today, hours_allocated (sum of today's task estimates), remaining_capacity, and list of scheduled tasks

#### Scenario: No available hours set
- **WHEN** AI queries time context and user hasn't set available_hours_today
- **THEN** response indicates: "Available hours not set. Ask user: 'How many hours do you have available today?'"

#### Scenario: Over-allocated warning
- **WHEN** hours_allocated exceeds available_hours_today
- **THEN** response includes warning: "Over-committed by X hours. User has Y hours available but Z hours of tasks."

### Requirement: AI Pushback on Over-Commitment

The system SHALL enable AI to push back with suggestions (not blocking) when users attempt to take on more work than available time allows.

#### Scenario: Warn on task creation exceeding capacity
- **WHEN** user requests new task creation
- **AND** adding the task would exceed available_hours_today
- **THEN** AI warns: "This would put you at X hours for today but you only have Y hours remaining. Consider deferring something or extending the deadline."
- **AND** AI does NOT block task creation (suggestive, not blocking)

#### Scenario: Warn on commitment creation exceeding capacity
- **WHEN** user requests new commitment
- **AND** AI estimates total effort would exceed available capacity before due date
- **THEN** AI warns: "This commitment would require X hours but you have Y hours available before the due date. Is this realistic?"
- **AND** AI does NOT block commitment creation (suggestive, not blocking)

#### Scenario: Suggest deferral options
- **WHEN** AI detects over-commitment
- **THEN** AI suggests specific items that could be deferred or renegotiated
- **AND** suggestions are helpful, not demanding

#### Scenario: Reference integrity on pushback
- **WHEN** AI pushes back on over-commitment
- **AND** user's integrity grade is below B
- **THEN** AI includes: "Your current integrity grade is X. Taking on more work you can't complete will lower it further."

### Requirement: AI Estimation Coaching

The system SHALL enable AI to help users improve their time estimation skills.

#### Scenario: Request estimate for new task
- **WHEN** user creates a task via AI
- **THEN** AI asks: "How long do you think this will take?" before confirming creation

#### Scenario: Reference historical accuracy
- **WHEN** user provides an estimate
- **AND** task history shows poor estimation accuracy
- **THEN** AI responds: "Your recent estimates have been off by about X%. For similar tasks, you estimated Y hours but they took Z hours. Do you want to adjust?"
- **AND** similarity is inferred by AI from user's own task history only (title keywords, same commitment)
- **AND** AI does NOT compare across different users' data

#### Scenario: Suggest confidence level
- **WHEN** user provides an estimate for unfamiliar task type
- **THEN** AI asks: "How confident are you in that estimate? (high/medium/low)"

#### Scenario: Celebrate accurate estimation
- **WHEN** user completes a task and selects "On Target" for actual hours category
- **THEN** AI acknowledges: "Nice! Your estimate was spot on."

### Requirement: AI Session Initialization

The system SHALL prompt for available hours at the start of each chat session.

#### Scenario: First message prompts for hours
- **WHEN** user starts a new chat session
- **AND** available_hours_remaining is not set
- **THEN** AI's first response includes: "Before we dive in, how many hours do you have remaining for work today?"

#### Scenario: Remember hours within session
- **WHEN** user provides available_hours_remaining
- **THEN** the value is stored for the session and AI references it in subsequent responses

#### Scenario: Allow hours update mid-session
- **WHEN** user says "I now have X hours left" or similar
- **THEN** available_hours_remaining is updated and AI acknowledges the change
- **AND** AI does NOT proactively re-ask (user-initiated updates only)

### Requirement: AI Operation Timeouts

The system SHALL enforce timeouts on all AI operations to prevent indefinite hangs.

#### Scenario: Timeout on AI agent call
- **WHEN** an AI agent call is made (classification, extraction, streaming)
- **THEN** the operation times out after the configured duration (120s for calls, 180s for streaming)
- **AND** a TimeoutError is raised with clear message

#### Scenario: Sync AI call with timeout
- **WHEN** `classify_triage_item()` is called synchronously
- **THEN** the operation is wrapped with a 120-second timeout via ThreadPoolExecutor
- **AND** TimeoutError is raised if exceeded

#### Scenario: Async AI call with timeout
- **WHEN** any async extraction function is called
- **THEN** the operation is wrapped with `asyncio.timeout(120)`
- **AND** TimeoutError is raised if exceeded

#### Scenario: Streaming with timeout
- **WHEN** `stream_response()` is called
- **THEN** the entire streaming operation has a 180-second timeout
- **AND** the stream is cancelled cleanly if timeout is exceeded
- **AND** any partial response received before timeout is discarded

#### Scenario: UI handles timeout gracefully
- **WHEN** TimeoutError is raised during any AI operation
- **THEN** the chat displays an error message indicating the timeout
- **AND** the prompt input is re-enabled for user retry
- **AND** no partial or corrupted state is left in the conversation

### Requirement: Timeout Configuration

The system SHALL define timeout constants for different operation types.

#### Scenario: AI timeout constants
- **GIVEN** the timeout module exists
- **THEN** it defines `AI_TIMEOUT_SECONDS = 120` for standard AI calls
- **AND** it defines `AI_STREAM_TIMEOUT = 180` for streaming operations
- **AND** constants are importable from `jdo.ai.timeout`

