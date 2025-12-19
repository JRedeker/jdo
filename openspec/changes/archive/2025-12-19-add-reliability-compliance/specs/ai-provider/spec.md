## ADDED Requirements

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
