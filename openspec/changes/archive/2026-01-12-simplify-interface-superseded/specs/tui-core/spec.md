## REMOVED Requirements

### Requirement: Screen Architecture
**Reason**: Textual Screens architecture replaced with Typer CLI  
**Migration**: N/A - breaking change, new interface

### Requirement: Widget Architecture
**Reason**: Textual Widgets replaced with simple formatters  
**Migration**: N/A - breaking change, new interface

### Requirement: Screen Stack Navigation
**Reason**: No screen stack in CLI  
**Migration**: Settings accessed via `jdo config` command

### Requirement: Context-Aware Escape Behavior
**Reason**: CLI uses standard terminal interrupt (Ctrl+C)  
**Migration**: Users press Ctrl+C to exit

### Requirement: Screen Compose Structure
**Reason**: No Textual compose() in CLI  
**Migration**: N/A

### Requirement: Message-Based Communication
**Reason**: No widget message passing in CLI  
**Migration**: Direct function calls

### Requirement: Modal Dialog Pattern
**Reason**: CLI uses prompts for confirmation  
**Migration**: Replace modals with `Confirm.ask()` prompts

### Requirement: CSS Styling Conventions
**Reason**: No CSS in CLI  
**Migration**: Use Rich markup for formatting

### Requirement: Key Binding Conventions
**Reason**: No custom key bindings in CLI (standard terminal bindings)  
**Migration**: Users use standard readline keys (up/down, Ctrl+C, etc.)

### Requirement: Test Patterns for Screens
**Reason**: No Textual screens to test  
**Migration**: Use pytest with mocked stdin/stdout

### Requirement: Worker Context Documentation
**Reason**: No Textual workers in CLI  
**Migration**: Synchronous command execution (or standard asyncio if needed)

### Requirement: Async Lifecycle Patterns
**Reason**: No Textual lifecycle (on_mount, on_show, etc.)  
**Migration**: Standard Python function calls

### Requirement: Message Handling Conventions
**Reason**: No widget messages  
**Migration**: Direct function returns

### Requirement: Screen Navigation Patterns
**Reason**: No screen navigation  
**Migration**: Subcommands (e.g., `jdo config` instead of push_screen(Settings))

### Requirement: Focus Management Patterns
**Reason**: No widget focus management  
**Migration**: Terminal cursor handled by readline/prompt library

### Requirement: Common Pitfalls Documentation
**Reason**: Textual-specific pitfalls no longer apply  
**Migration**: N/A

### Requirement: Testing Patterns for Textual
**Reason**: No Textual to test  
**Migration**: Standard pytest patterns

### Requirement: Settings Screen Auth Status Refresh
**Reason**: Settings via `jdo config` commands  
**Migration**: Auth status checked on command execution

### Requirement: Allocated Hours Calculation
**Reason**: Moved to backend (unchanged logic, different display)  
**Migration**: Available via `jdo show hours` or in chat

### Requirement: Navigation Sidebar Widget
**Reason**: No sidebar in CLI  
**Migration**: Use subcommands: `jdo list goals`, `jdo list commitments`, etc.

### Requirement: RadioSet Widget Pattern
**Reason**: No RadioSet widget  
**Migration**: Use `Prompt.ask()` with choices or `--provider` flag

### Requirement: Settings Screen Dynamic Updates
**Reason**: No Settings screen  
**Migration**: `jdo config set provider <name>` command

## ADDED Requirements

### Requirement: Typer Application Structure
The system SHALL use Typer to provide a CLI with subcommands for all operations.

#### Scenario: Main app is Typer instance
- **GIVEN** the user runs `jdo --help`
- **WHEN** the help text is displayed
- **THEN** it shows a Typer-generated command list with chat, list, add, show, config subcommands

#### Scenario: Chat command launches REPL
- **GIVEN** the user runs `jdo` or `jdo chat`
- **WHEN** the command executes
- **THEN** an interactive REPL loop starts accepting user input

#### Scenario: List commands execute and exit
- **GIVEN** the user runs `jdo list commitments`
- **WHEN** the command executes
- **THEN** it displays a formatted list and exits immediately

#### Scenario: Add commands execute and exit
- **GIVEN** the user runs `jdo add commitment "Deliver report by Friday"`
- **WHEN** the command executes
- **THEN** it creates the commitment and exits with confirmation message

#### Scenario: Invalid subcommand provided
- **GIVEN** the user runs `jdo invalidcommand`
- **WHEN** Typer processes the command
- **THEN** Typer displays an error: "No such command 'invalidcommand'"
- **AND** suggests valid commands using fuzzy matching if possible
- **AND** exits with code 1

#### Scenario: Invalid arguments provided to command
- **GIVEN** the user runs `jdo list invalidtype`
- **WHEN** the command validates arguments
- **THEN** an error is displayed: "Invalid entity type. Choose from: commitments, goals, tasks, milestones"
- **AND** the command exits with code 1

### Requirement: Interactive Chat REPL
The system SHALL provide an interactive chat mode with conversation history.

#### Scenario: REPL loop accepts input
- **GIVEN** the user is in chat mode
- **WHEN** the user types a message and presses Enter
- **THEN** the message is sent to the AI agent

#### Scenario: AI response streams to console
- **GIVEN** the user sent a message
- **WHEN** the AI generates a response
- **THEN** the response is displayed using Rich formatting
- **AND** the response is added to conversation history

#### Scenario: Exit on quit command
- **GIVEN** the user is in chat mode
- **WHEN** the user types "quit", "exit", or presses Ctrl+C
- **THEN** the REPL exits gracefully

#### Scenario: Conversation history maintained
- **GIVEN** the user has sent multiple messages in chat mode
- **WHEN** a new message is sent
- **THEN** the AI receives conversation history for context

#### Scenario: Chat REPL encounters streaming error from AI
- **GIVEN** the user is in chat mode and sent a message
- **WHEN** the AI streaming fails mid-response (network timeout, rate limit)
- **THEN** the partial response is displayed if any
- **AND** an error message is shown: "AI response interrupted: <reason>. Type your message again to retry."
- **AND** the conversation remains in a valid state (user can continue chatting)

#### Scenario: Conversation history persists within session only
- **GIVEN** the user has an active chat session with history
- **WHEN** the user exits chat mode
- **THEN** conversation history is discarded (no persistence between sessions)
- **AND** the next `jdo chat` starts with empty history

#### Scenario: Network timeout during AI streaming
- **GIVEN** the user is in chat mode waiting for AI response
- **WHEN** the network request times out (e.g., 30 seconds)
- **THEN** a timeout error is displayed: "AI request timed out. Please try again."
- **AND** the user can send a new message immediately

### Requirement: Command Output Formatting
The system SHALL provide formatters to convert handler output to Rich-formatted displays.

#### Scenario: Format commitment list as table
- **GIVEN** a handler returns a list of commitment dicts
- **WHEN** `format_commitment_list()` is called
- **THEN** a Rich Table is returned with columns: ID, Deliverable, Due, Status

#### Scenario: Format goal list as table
- **GIVEN** a handler returns a list of goal dicts
- **WHEN** `format_goal_list()` is called
- **THEN** a Rich Table is returned with columns: ID, Title, Due, Status, Progress

#### Scenario: Format entity view as panel
- **GIVEN** a handler returns a single commitment dict
- **WHEN** `format_commitment()` is called
- **THEN** a Rich Panel is returned with all commitment fields formatted

#### Scenario: Format hierarchy as tree
- **GIVEN** a handler returns hierarchical data
- **WHEN** `format_hierarchy()` is called
- **THEN** a Rich Tree is returned showing Vision → Goal → Milestone → Commitment structure

#### Scenario: Formatter receives malformed data
- **GIVEN** a handler returns data with missing required fields
- **WHEN** `format_commitment_list()` is called
- **THEN** the formatter handles missing fields gracefully (displays "N/A" or empty string)
- **AND** logs a warning about malformed data
- **AND** does not raise an exception

#### Scenario: Formatter receives empty list
- **GIVEN** a handler returns an empty list for commitments
- **WHEN** `format_commitment_list()` is called
- **THEN** a message is returned: "[i]No commitments found[/i]"
- **AND** no table is rendered

#### Scenario: Formatter receives None data
- **GIVEN** a handler returns CommandOutput with data=None
- **WHEN** a formatter is called
- **THEN** it returns a simple message: "[i]No data available[/i]"
- **AND** does not attempt to render a table or panel

### Requirement: Simplified Handler Output
The system SHALL use `CommandOutput` dataclass for all handler returns, replacing `HandlerResult`.

#### Scenario: Handler returns CommandOutput
- **GIVEN** a command handler executes
- **WHEN** the handler completes
- **THEN** it returns a `CommandOutput` with message, data, and optional draft/confirmation flag

#### Scenario: CommandOutput contains structured data
- **GIVEN** a list command executes
- **WHEN** the handler returns CommandOutput
- **THEN** the data field contains a list of dicts suitable for formatting

#### Scenario: No UI-specific fields in output
- **GIVEN** any command handler
- **WHEN** it returns CommandOutput
- **THEN** there is no `panel_update` or other UI-specific field
- **AND** the output is reusable across CLI and future interfaces

### Requirement: Rich Console Output
The system SHALL use Rich library for all formatted output.

#### Scenario: Tables use Rich Table
- **GIVEN** a list command executes
- **WHEN** the output is displayed
- **THEN** it uses `rich.table.Table` with proper styling

#### Scenario: Status indicators use Rich status
- **GIVEN** the AI is processing a request
- **WHEN** the user waits
- **THEN** a Rich `status()` context manager shows a spinner with "Thinking..." message

#### Scenario: Errors use Rich console.print with style
- **GIVEN** an error occurs
- **WHEN** the error is displayed
- **THEN** it uses `console.print()` with "bold red" style

### Requirement: Standard CLI Conventions
The system SHALL follow standard CLI conventions for flags, help, and exit codes.

#### Scenario: Help flag shows usage
- **GIVEN** the user runs `jdo --help` or `jdo list --help`
- **WHEN** the help is displayed
- **THEN** it shows usage, options, and subcommands

#### Scenario: Version flag shows version
- **GIVEN** the user runs `jdo --version`
- **WHEN** the command executes
- **THEN** it displays the version from pyproject.toml and exits

#### Scenario: Success exit code is 0
- **GIVEN** a command executes successfully
- **WHEN** the command completes
- **THEN** the exit code is 0

#### Scenario: Error exit code is non-zero
- **GIVEN** a command fails (invalid input, API error, etc.)
- **WHEN** the command exits
- **THEN** the exit code is non-zero (1 for user error, 2 for system error)

### Requirement: Non-Interactive Execution
The system SHALL handle non-interactive contexts appropriately.

#### Scenario: Confirmation prompts in non-interactive context
- **GIVEN** a command requires confirmation (e.g., `jdo add commitment <text>`)
- **WHEN** the command runs in a non-interactive context (piped input, CI/CD)
- **THEN** the system detects non-interactive mode (no TTY)
- **AND** either auto-confirms with a flag (--yes) or fails with error: "Interactive confirmation required. Use --yes to auto-confirm."

### Requirement: Structured Logging
The system SHALL emit structured logs for all CLI operations.

#### Scenario: Logging levels follow convention
- **GIVEN** any CLI command executes
- **WHEN** logging is performed
- **THEN** logs follow these levels:
  - DEBUG: Parameter values, context details, formatter inputs
  - INFO: Command start/completion, AI requests sent/received
  - WARNING: Recoverable errors (malformed data, missing fields)
  - ERROR: Command failures, unhandled exceptions
  - CRITICAL: System failures (database unavailable, corrupted state)

#### Scenario: Structured log format for CLI operations
- **GIVEN** a CLI command executes
- **WHEN** an operation is logged
- **THEN** the log includes: timestamp, level, command, user_id (if applicable), duration_ms, status (success/error), error_type (if error)
- **AND** logs are JSON-formatted when JDO_LOG_FORMAT=json

#### Scenario: API keys sanitized from logs
- **GIVEN** any operation involves API keys or credentials
- **WHEN** logging occurs
- **THEN** API keys are redacted: "ANTHROPIC_API_KEY=sk-***REDACTED***"
- **AND** full keys are never written to log files or console

### Requirement: Observability
The system SHALL emit performance metrics for key operations.

#### Scenario: AI response time tracked
- **GIVEN** a command invokes the AI service
- **WHEN** the AI responds
- **THEN** the response time is logged: "AI request completed in <duration_ms>ms"
- **AND** slow requests (>5s) log a WARNING

#### Scenario: Database query duration tracked
- **GIVEN** a command queries the database
- **WHEN** the query completes
- **THEN** query duration is logged at DEBUG level
- **AND** slow queries (>1s) log a WARNING with the query summary

### Requirement: Input Validation
The system SHALL validate all command arguments before execution.

#### Scenario: Validate entity IDs
- **GIVEN** a command accepts an entity ID (e.g., `jdo show commitment 123`)
- **WHEN** the ID is non-numeric or negative
- **THEN** an error is displayed: "Invalid ID. Must be a positive integer."
- **AND** the command exits with code 1

#### Scenario: Validate date inputs
- **GIVEN** a command accepts a date (e.g., `jdo add commitment --due 2024-13-45`)
- **WHEN** the date is invalid
- **THEN** an error is displayed: "Invalid date format. Use YYYY-MM-DD."
- **AND** the command exits with code 1

### Requirement: Configuration Security
The system SHALL handle configuration files securely.

#### Scenario: .env file permissions checked
- **GIVEN** a .env file exists
- **WHEN** the application starts
- **THEN** the file permissions are checked
- **AND** if world-readable (permissions 644 or looser), a WARNING is logged: ".env file is world-readable. Consider: chmod 600 .env"

> **Note**: Multiple .env files are NOT supported. Only the project root .env is loaded per python-dotenv convention.

### Requirement: Performance Constraints
The system SHALL meet performance requirements for interactive use.

#### Scenario: List commands respond quickly
- **GIVEN** a user runs `jdo list commitments`
- **WHEN** the database has <1000 records
- **THEN** the command completes in <500ms
- **AND** the table is rendered immediately

#### Scenario: Conversation history limited
- **GIVEN** the user is in chat mode
- **WHEN** conversation history is maintained
- **THEN** only the last 50 messages are kept
- **AND** older messages are trimmed automatically

#### Scenario: AI streaming timeout
- **GIVEN** the user is waiting for an AI response
- **WHEN** 30 seconds elapse without response
- **THEN** the request times out
- **AND** an error is displayed
