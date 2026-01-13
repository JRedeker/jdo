## MODIFIED Requirements

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

#### Scenario: Exit REPL via plain text
- **GIVEN** the REPL is running
- **WHEN** user types `exit`, `quit`, or presses Ctrl+D
- **THEN** a goodbye message is displayed
- **AND** the REPL terminates gracefully

#### Scenario: Exit REPL via slash command
- **GIVEN** the REPL is running
- **WHEN** user types `/exit` or `/quit`
- **THEN** a goodbye message is displayed
- **AND** the REPL terminates gracefully

#### Scenario: Exit slash command ignores trailing arguments
- **GIVEN** the REPL is running
- **WHEN** user types `/exit foo` or `/quit bar`
- **THEN** a goodbye message is displayed
- **AND** the REPL terminates gracefully
- **AND** trailing arguments are ignored

#### Scenario: Exit slash commands are case-insensitive
- **GIVEN** the REPL is running
- **WHEN** user types `/EXIT`, `/QUIT`, `/Exit`, or `/Quit`
- **THEN** a goodbye message is displayed
- **AND** the REPL terminates gracefully

<!-- Research note: Exit handled as special-case input (before slash command routing) per prompt_toolkit design philosophy. Exit is a signal, not a command. -->

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

## MODIFIED Requirements

### Requirement: Slash Command Auto-completion

The system SHALL provide auto-completion for slash commands using prompt_toolkit.

<!-- Research: WordCompleter is sufficient for ~10 commands; FuzzyCompleter deferred -->
<!-- Source: https://python-prompt-toolkit.readthedocs.io/en/master/pages/asking_for_input.html -->
<!-- Note: NestedCompleter would be better for hierarchical commands but is out of scope -->

#### Scenario: Tab-complete slash commands
- **GIVEN** the REPL is awaiting user input
- **WHEN** user types `/li` and presses Tab
- **THEN** the input is completed to `/list` (or shows matching options)
- **AND** matching is case-insensitive

#### Scenario: Show completion options
- **GIVEN** the REPL is awaiting user input
- **WHEN** user types `/` and presses Tab
- **THEN** a dropdown shows available commands: `/help`, `/list`, `/commit`, `/complete`, `/review`, `/exit`, `/quit`

#### Scenario: Graceful handling when no completions match
- **GIVEN** the REPL is awaiting user input
- **WHEN** user types `/xyz` (no matching command) and presses Tab
- **THEN** no completion dropdown is shown
- **AND** the input remains unchanged
- **AND** no error is displayed

> **Note**: Logging is N/A for exit commands because exit is a signal, not a command that affects state. No structured logging required.
