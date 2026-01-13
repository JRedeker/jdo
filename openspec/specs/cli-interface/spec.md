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

The system SHALL display AI responses as they stream from the provider using Rich's `Live` display with Markdown rendering.

<!-- Research: PydanticAI stream_markdown.py example renders Markdown on each chunk -->
<!-- Source: https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/stream_markdown.py -->

#### Scenario: Display streaming text with Markdown
- **GIVEN** user has submitted input to the AI
- **WHEN** AI begins responding to user input
- **THEN** text appears incrementally as tokens arrive using Rich `Live` display
- **AND** content is rendered as Markdown on each chunk update
- **AND** headers, lists, code blocks, and emphasis are properly formatted

#### Scenario: Animated thinking indicator
- **GIVEN** user has submitted input to the AI
- **WHEN** AI is processing but no tokens have arrived yet
- **THEN** an animated spinner is shown with "Thinking..." text using `console.status()`
- **AND** spinner uses "dots" animation style
- **AND** `status.stop()` is called BEFORE `Live` display starts (no nesting)

<!-- Research: Must stop Status before starting Live to avoid display conflicts -->
<!-- Source: https://rich.readthedocs.io/en/latest/reference/status.html -->

#### Scenario: Markdown rendering fallback
- **GIVEN** AI response contains content that fails markdown parsing
- **WHEN** markdown rendering fails
- **THEN** the response is displayed as plain text
- **AND** no error is shown to the user

#### Scenario: Streaming timeout
- **GIVEN** AI is streaming a response
- **WHEN** no tokens arrive for more than 30 seconds
- **THEN** the streaming is cancelled
- **AND** spinner is stopped (if still running)
- **AND** user sees a timeout message
- **AND** REPL returns to prompt

#### Scenario: Network failure during streaming
- **GIVEN** AI is streaming a response
- **WHEN** network connection is lost
- **THEN** partial response is displayed (if any)
- **AND** spinner is stopped (if still running)
- **AND** user sees a connection error message
- **AND** REPL returns to prompt

#### Implementation Reference
```python
# Correct pattern: Stop status BEFORE starting Live
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text

status = console.status("[dim]Thinking...[/dim]", spinner="dots")
status.start()

full_response = ""
first_chunk = True

try:
    async for chunk in stream_response(...):
        if first_chunk:
            status.stop()  # Stop BEFORE starting Live
            live = Live('', console=console, vertical_overflow='visible')
            live.start()
            first_chunk = False
        
        full_response += chunk
        try:
            live.update(Markdown(full_response))
        except Exception:
            live.update(Text(full_response))
    
    if not first_chunk:
        live.stop()
finally:
    if first_chunk:
        status.stop()  # Never got chunks, still stop status
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

### Requirement: Slash Command Auto-completion

The system SHALL provide auto-completion for slash commands using prompt_toolkit.

<!-- Research: WordCompleter is sufficient for ~10 commands; FuzzyCompleter deferred -->
<!-- Source: https://python-prompt-toolkit.readthedocs.io/en/master/pages/asking_for_input.html -->

#### Scenario: Tab-complete slash commands
- **GIVEN** the REPL is awaiting user input
- **WHEN** user types `/li` and presses Tab
- **THEN** the input is completed to `/list` (or shows matching options)
- **AND** matching is case-insensitive

#### Scenario: Show completion options
- **GIVEN** the REPL is awaiting user input
- **WHEN** user types `/` and presses Tab
- **THEN** a dropdown shows available commands: `/help`, `/list`, `/commit`, `/complete`, `/review`

#### Scenario: Graceful handling when no completions match
- **GIVEN** the REPL is awaiting user input
- **WHEN** user types `/xyz` (no matching command) and presses Tab
- **THEN** no completion dropdown is shown
- **AND** the input remains unchanged
- **AND** no error is displayed

### Requirement: Bottom Toolbar Status Bar

The system SHALL display an always-visible status bar at the bottom of the terminal using cached values.

<!-- Research: Toolbar callback runs per keystroke; must use cached values, not live DB queries -->
<!-- Source: https://python-prompt-toolkit.readthedocs.io/en/stable/pages/asking_for_input.html#adding-a-bottom-toolbar -->

#### Scenario: Show commitment count
- **GIVEN** the REPL is running
- **WHEN** the prompt is displayed
- **THEN** the bottom toolbar shows the cached number of active commitments

#### Scenario: Show triage queue count
- **GIVEN** the REPL is running
- **WHEN** items exist in the triage queue
- **THEN** the bottom toolbar shows the cached triage queue count

#### Scenario: Show pending draft indicator
- **GIVEN** the user has a pending draft awaiting confirmation
- **WHEN** the prompt is displayed
- **THEN** the bottom toolbar indicates a draft is pending (e.g., "[draft]")

#### Scenario: Cached values update on data changes
- **GIVEN** user creates, updates, or deletes an entity
- **WHEN** the operation completes
- **THEN** session cache is updated
- **AND** toolbar reflects new values on next render

### Requirement: Dashboard Data Caching

The system SHALL cache dashboard data in session state for efficient display.

#### Scenario: Cache includes commitment list
- **GIVEN** dashboard is being prepared
- **WHEN** session cache is updated
- **THEN** cache includes up to 5 upcoming commitments with display data
- **AND** commitments are ordered by due date ascending

#### Scenario: Cache includes goal progress
- **GIVEN** dashboard is being prepared
- **WHEN** session cache is updated
- **THEN** cache includes active goals with progress percentages
- **AND** goals include review due status

#### Scenario: Cache includes integrity summary
- **GIVEN** dashboard is being prepared
- **WHEN** session cache is updated
- **THEN** cache includes integrity grade, score, and trend
- **AND** cache includes current streak in weeks

#### Scenario: Cache updated on commitment changes
- **GIVEN** user creates or completes a commitment
- **WHEN** commitment is saved to database
- **THEN** dashboard cache is refreshed with new data

#### Scenario: Cache updated on goal changes
- **GIVEN** goal progress changes (via commitment completion)
- **WHEN** change is saved
- **THEN** dashboard cache is refreshed with new goal progress

### Requirement: Display Level Selection

The system SHALL automatically select display level based on data volume.

#### Scenario: Select minimal display
- **GIVEN** user has 0 commitments AND 0 goals
- **WHEN** display level is determined
- **THEN** returns MINIMAL (status bar only)

#### Scenario: Select compact display
- **GIVEN** user has 1-2 commitments
- **WHEN** display level is determined
- **THEN** returns COMPACT (merged panel)

#### Scenario: Select standard display
- **GIVEN** user has 3+ commitments AND 0 goals
- **WHEN** display level is determined
- **THEN** returns STANDARD (commitments + status bar)

#### Scenario: Select full display
- **GIVEN** user has 3+ commitments AND 1+ goals
- **WHEN** display level is determined
- **THEN** returns FULL (all panels)

### Requirement: Commitment Summary Display

The system SHALL display a commitment summary panel before each REPL prompt to keep users informed of their current obligations.

#### Scenario: Summary shown after startup
- **GIVEN** the REPL has started
- **WHEN** startup guidance messages complete
- **THEN** commitment summary panel is displayed (if user has commitments)
- **AND** the prompt appears below the summary

#### Scenario: Summary shown after command completion
- **GIVEN** user has executed a command or received AI response
- **WHEN** command processing completes
- **THEN** commitment summary panel is displayed (if user has commitments)
- **AND** the prompt appears below the summary

#### Scenario: Summary updates after commitment changes
- **GIVEN** user creates or completes a commitment
- **WHEN** the operation succeeds
- **THEN** the next summary panel reflects the updated counts
- **AND** next due item is updated if changed

#### Scenario: Summary hidden when no commitments
- **GIVEN** user has no active commitments
- **WHEN** summary would be displayed
- **THEN** no summary panel is shown
- **AND** prompt appears without preceding panel

#### Scenario: Summary uses cached data for performance
- **GIVEN** summary panel is being rendered
- **WHEN** displaying commitment counts and next due item
- **THEN** data is retrieved from session cache (not live DB query)
- **AND** cache is updated only when commitments change

### Requirement: Summary Panel Session Caching

The system SHALL cache commitment summary data in session state for efficient display.

#### Scenario: Cache includes next due commitment
- **GIVEN** user has active commitments
- **WHEN** session cache is updated
- **THEN** cache includes: active_count, at_risk_count, overdue_count
- **AND** cache includes next_due commitment info (deliverable, due_date)

#### Scenario: Cache updated on commitment creation
- **GIVEN** user confirms a new commitment
- **WHEN** commitment is saved to database
- **THEN** session cache is updated with new summary data

#### Scenario: Cache updated on commitment completion
- **GIVEN** user completes a commitment
- **WHEN** commitment status is updated to completed
- **THEN** session cache is updated with new summary data

