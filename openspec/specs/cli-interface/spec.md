# cli-interface Specification

## Purpose
Define the command-line REPL interface for JDO, including loop entry/exit handling, input history with prompt_toolkit, streaming AI response display, Rich console output, session state management, database initialization, and observability logging.

## Requirements

### Requirement: REPL Loop Entry Point

The system SHALL provide a REPL (Read-Eval-Print Loop) as the primary interactive interface when `jdo` is invoked without subcommands.

#### Scenario: Launch REPL by default
- **GIVEN** the user has a terminal open
- **WHEN** user runs `jdo` with no arguments
- **THEN** the REPL loop starts
- **AND** a welcome message is displayed
- **AND** the prompt awaits user input

#### Scenario: REPL displays prompt
- **GIVEN** the REPL has started successfully
- **WHEN** the REPL is ready for input
- **THEN** a prompt indicator is shown (e.g., `jdo> ` or `> `)
- **AND** the cursor awaits user input

#### Scenario: Exit REPL
- **GIVEN** the REPL is running
- **WHEN** user types `exit`, `quit`, or presses Ctrl+D
- **THEN** a goodbye message is displayed
- **AND** the REPL terminates gracefully

#### Scenario: Ctrl+C handling
- **GIVEN** the REPL is awaiting user input
- **WHEN** user presses Ctrl+C during input
- **THEN** the current input is cancelled
- **AND** the prompt reappears for new input
- **AND** the REPL does not exit

#### Scenario: Empty input handling
- **GIVEN** the REPL is awaiting user input
- **WHEN** user submits empty input (just presses Enter)
- **THEN** the prompt reappears without error
- **AND** no AI call is made

#### Scenario: Whitespace-only input handling
- **GIVEN** the REPL is awaiting user input
- **WHEN** user submits whitespace-only input
- **THEN** the prompt reappears without error
- **AND** no AI call is made

### Requirement: Input History

The system SHALL provide input history navigation using prompt_toolkit.

#### Scenario: Navigate history with arrow keys
- **GIVEN** the user has entered at least one previous input
- **WHEN** user presses Up arrow at prompt
- **THEN** the previous input is recalled
- **AND** user can edit before submitting

#### Scenario: History persists within session
- **GIVEN** the REPL is running
- **WHEN** user enters multiple inputs in a session
- **THEN** all inputs are available via Up/Down arrows
- **AND** history order is most-recent-first

#### Scenario: History does not persist across sessions
- **GIVEN** user has used the REPL previously
- **WHEN** user exits and restarts the REPL
- **THEN** history from previous session is not available

### Requirement: Streaming AI Response Display

The system SHALL display AI responses as they stream from the provider using Rich's `Live` display.

<!-- Research Note: PydanticAI run_stream() returns async context manager. Rich's Live display
     is the documented approach for streaming text, not console.status() + print(end="").
     Source: ai.pydantic.dev/output/#streamed-results, rich.readthedocs.io/live.html -->

#### Scenario: Display streaming text
- **GIVEN** user has submitted input to the AI
- **WHEN** AI begins responding to user input
- **THEN** text appears incrementally as tokens arrive using Rich `Live` display
- **AND** no blank waiting period before first token
- **AND** display updates without terminal flicker

#### Scenario: Thinking indicator
- **GIVEN** user has submitted input to the AI
- **WHEN** AI is processing but no tokens have arrived yet
- **THEN** a "Thinking..." indicator is shown (separate from streaming display)
- **AND** indicator disappears when first token arrives

#### Scenario: Complete response formatting
- **GIVEN** AI is streaming a response
- **WHEN** AI response completes
- **THEN** the full response is properly formatted
- **AND** a newline separates response from next prompt

#### Scenario: Streaming timeout
- **GIVEN** AI is streaming a response
- **WHEN** no tokens arrive for more than 30 seconds
- **THEN** the streaming is cancelled
- **AND** user sees a timeout message
- **AND** REPL returns to prompt

#### Scenario: Network failure during streaming
- **GIVEN** AI is streaming a response
- **WHEN** network connection is lost
- **THEN** partial response is displayed (if any)
- **AND** user sees a connection error message
- **AND** REPL returns to prompt

#### Implementation Reference
```python
# Correct pattern using PydanticAI + Rich Live
from rich.live import Live
from rich.text import Text

async with agent.run_stream(input, deps=deps, message_history=history) as result:
    output = Text()
    with Live(output, console=console, refresh_per_second=10) as live:
        async for chunk in result.stream_text():
            output.append(chunk)
            live.update(output)
```

### Requirement: Rich Console Output

The system SHALL use Rich library for formatted terminal output.

#### Scenario: Table output for lists
- **GIVEN** user has requested a list of entities
- **WHEN** AI shows a list of entities (commitments, goals, etc.)
- **THEN** data is displayed in a Rich Table
- **AND** columns are appropriately sized
- **AND** status values use color coding

#### Scenario: Entity detail output
- **GIVEN** user has requested details of an entity
- **WHEN** AI shows a single entity's details
- **THEN** data is displayed with Rich Panel or formatted text
- **AND** key fields are clearly labeled

#### Scenario: Error output styling
- **GIVEN** user is interacting with the REPL
- **WHEN** an error occurs
- **THEN** error message is displayed with warning/error styling
- **AND** actionable guidance is provided when possible

### Requirement: Session State Management

The system SHALL maintain session state in memory during REPL operation.

<!-- Research Note: Use Pydantic AI's native message_history support.
     Token-based pruning is preferred over message-count limits.
     Source: ai.pydantic.dev/message-history, cookbook.openai.com -->

#### Scenario: Conversation history maintained
- **GIVEN** the REPL session is active
- **WHEN** user and AI exchange messages
- **THEN** previous messages are available as context for AI
- **AND** AI can reference earlier conversation
- **AND** Pydantic AI's `message_history` parameter is used

#### Scenario: History pruning by token limit
- **WHEN** conversation history exceeds token budget (e.g., 8000 tokens)
- **THEN** oldest messages are pruned
- **AND** most recent context is preserved
- **AND** AI behavior remains coherent
- **NOTE**: Token-based limits preferred over message counts (research finding)

#### Scenario: Current context tracking
- **GIVEN** the REPL session is active
- **WHEN** user is viewing or editing a specific entity
- **THEN** session tracks the "current" entity
- **AND** subsequent inputs can reference "it" or "this"

#### Scenario: Pending draft state
- **GIVEN** user has requested to create an entity
- **WHEN** AI proposes creating an entity
- **THEN** the draft is held in session state
- **AND** user can confirm, refine, or cancel

#### Scenario: Session state resets on exit
- **GIVEN** the REPL has accumulated session state
- **WHEN** user exits the REPL
- **THEN** all session state is discarded
- **AND** next session starts fresh

### Requirement: Fire-and-Forget Capture Command

The system SHALL support quick capture via `jdo capture "text"` subcommand.

#### Scenario: Capture creates triage item
- **GIVEN** user has a quick thought to capture
- **WHEN** user runs `jdo capture "remember to call mom"`
- **THEN** a Draft with UNKNOWN type is created in the database
- **AND** confirmation message is printed to stdout
- **AND** command exits immediately

#### Scenario: Capture works without REPL
- **GIVEN** user wants to capture without interactive session
- **WHEN** user runs `jdo capture` from a script or shortcut
- **THEN** no REPL is launched
- **AND** no AI interaction occurs

### Requirement: AI Credentials Verification

The system SHALL verify AI credentials before starting the REPL.

#### Scenario: No credentials configured
- **GIVEN** no AI provider credentials are configured
- **WHEN** user runs `jdo`
- **THEN** an error message explains how to configure credentials
- **AND** the REPL does not start

#### Scenario: Credentials available
- **GIVEN** valid AI provider credentials exist
- **WHEN** user runs `jdo`
- **THEN** the REPL starts normally

#### Scenario: Credentials become invalid during session
- **WHEN** AI returns authentication error mid-session
- **THEN** error is displayed with guidance to check credentials
- **AND** REPL continues (user can retry after fixing)

### Requirement: Database Initialization

The system SHALL ensure database is initialized before REPL starts.

#### Scenario: First run creates database
- **GIVEN** no database file exists
- **WHEN** user runs `jdo` for the first time
- **THEN** database tables are created
- **AND** REPL starts normally

#### Scenario: Subsequent runs use existing database
- **GIVEN** database file exists from previous session
- **WHEN** user runs `jdo` with existing database
- **THEN** existing data is available
- **AND** no data loss occurs

### Requirement: Logging and Observability

The system SHALL provide structured logging for debugging and monitoring.

> **Note**: Production logging inherits from existing jdo.config.logging setup. No new logging infrastructure needed.

#### Scenario: Log AI requests and responses
- **GIVEN** debug logging is enabled
- **WHEN** AI agent processes a request
- **THEN** request and response are logged at DEBUG level
- **AND** no sensitive user data is logged at INFO level or above

#### Scenario: Log errors with context
- **GIVEN** an error occurs during REPL operation
- **WHEN** error is handled
- **THEN** error is logged with stack trace at ERROR level
- **AND** user sees friendly message (not stack trace)

### Requirement: Multi-line Input

The system SHALL support multi-line input for longer messages.

#### Scenario: Multi-line input via Meta+Enter
- **GIVEN** the REPL is awaiting user input
- **WHEN** user presses Meta+Enter (or Alt+Enter)
- **THEN** a new line is added to the input
- **AND** user can continue typing

#### Scenario: Submit multi-line input
- **GIVEN** user has entered multi-line input
- **WHEN** user presses Enter on a complete input
- **THEN** the entire multi-line input is sent to AI
