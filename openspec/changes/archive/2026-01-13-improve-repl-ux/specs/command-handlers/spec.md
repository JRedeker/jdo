## ADDED Requirements

### Requirement: HandlerResult Contract

The system SHALL define a complete `HandlerResult` dataclass contract for communication between handlers and the REPL loop.

> **Extends deployed spec**: This adds new fields (`error`, `suggestions`, `entity_context`, `clear_context`) to the existing `HandlerResult` dataclass. Existing fields (`message`, `panel_update`, `draft_data`, `needs_confirmation`) remain unchanged.

#### Scenario: HandlerResult data model
- **GIVEN** a handler executes a command
- **WHEN** handler returns result
- **THEN** `HandlerResult` contains:
  - `message: str` - Response text to display (required)
  - `panel_update: dict | None` - Optional Rich panel to render
  - `draft_data: dict | None` - Pending draft for confirmation flow
  - `needs_confirmation: bool` - Whether to prompt user for yes/no
  - `error: bool` - Whether result represents an error (default False)
  - `suggestions: list[str] | None` - Follow-up command suggestions
  - `entity_context: EntityContext | None` - Entity to set as current context
  - `clear_context: bool` - Whether to clear current entity context

#### Scenario: Handler returns success
- **GIVEN** handler completes successfully
- **WHEN** result is returned
- **THEN** `error=False` (default)
- **AND** `message` contains success text
- **AND** `suggestions` may contain follow-up actions

#### Scenario: Handler returns error
- **GIVEN** handler encounters an error (entity not found, invalid input)
- **WHEN** result is returned
- **THEN** `error=True`
- **AND** `message` contains user-friendly error text
- **AND** `suggestions` contains recovery hints

#### Scenario: Handlers are stateless
- **GIVEN** handlers are singletons (cached in registry)
- **WHEN** handler executes
- **THEN** handler MUST NOT store state in instance variables
- **AND** all state flows through `context` parameter
- **AND** all output flows through `HandlerResult`

### Requirement: Wire Existing Handler Registry

The system SHALL wire the existing handler registry to the REPL loop for command dispatch. A new CommandDispatcher class is unnecessary since the codebase already has a module-level registry at commands/handlers/__init__.py with get_handler() function.

#### Scenario: Dispatch via existing registry
- **GIVEN** user enters `/commit "send report"`
- **WHEN** REPL processes the command
- **THEN** `get_handler(command_type)` is called from `commands/handlers`
- **AND** handler's `execute()` method is called
- **AND** `HandlerResult` is returned to REPL

#### Scenario: Unknown command with fuzzy suggestion
- **GIVEN** user enters `/compleet abc123` (typo)
- **WHEN** no handler is found
- **THEN** fuzzy matching suggests similar commands
- **AND** returns message: "Unknown command. Did you mean: /complete?"

#### Scenario: Unknown command without suggestion
- **GIVEN** user enters `/xyzabc` (no similar commands)
- **WHEN** no handler is found and no fuzzy matches
- **THEN** returns message: "Unknown command. Type /help for available commands."

### Requirement: Async Handler Interface

The system SHALL use uniform async interface for all command handlers. Python community consensus recommends uniform async for simplicity since async overhead on simple handlers is negligible.

#### Scenario: Async handler execution
- **GIVEN** `/commit` handler needs AI extraction
- **WHEN** REPL calls `await handler.execute()`
- **THEN** execution completes with AI call
- **AND** REPL loop handles async properly

#### Scenario: Simple handler as async
- **GIVEN** `/help` handler needs no async operations
- **WHEN** REPL calls `await handler.execute()`
- **THEN** handler returns immediately (no actual suspension)
- **AND** overhead is negligible

### Requirement: View Command Handler

The system SHALL provide a handler for viewing entity details.

#### Scenario: View entity by full ID
- **GIVEN** user enters `/view 550e8400-e29b-41d4-a716-446655440000`
- **WHEN** handler executes
- **THEN** entity is fetched by full UUID
- **AND** detailed panel is displayed
- **AND** session context is updated to this entity

#### Scenario: View entity by short ID
- **GIVEN** user enters `/view 550e84`
- **WHEN** handler executes
- **THEN** entity is fetched by ID prefix match
- **AND** if unique match found, detailed panel is displayed

#### Scenario: View with ambiguous ID across types
- **GIVEN** user enters `/view abc123`
- **WHEN** multiple entities match (e.g., commitment abc123... and goal abc123...)
- **THEN** list displays both with type labels:
  - "Multiple matches for 'abc123':"
  - "[1] commitment: Send report to Sarah"
  - "[2] goal: Q1 Revenue Target"
- **AND** prompt: "Which did you mean? Enter 1 or 2, or use a longer ID"
- **AND** user selection completes the view operation

#### Scenario: View with obvious match from context
- **GIVEN** user enters `/view abc123` after `/list commitments`
- **WHEN** one commitment matches and one goal matches
- **THEN** commitment is shown (context suggests user meant commitment)
- **AND** note: "Showing commitment. Also found: goal abc123..."

#### Scenario: View entity not found
- **GIVEN** user enters `/view xyz123`
- **WHEN** no entity matches the ID
- **THEN** error message: "Entity not found: xyz123"
- **AND** suggestion: "Use /list to see available entities"

#### Scenario: View by number shortcut from list
- **GIVEN** user enters `/2` after viewing a list
- **WHEN** handler executes
- **THEN** entity is fetched from `session.last_list_items[1]`
- **AND** detailed panel is displayed

### Requirement: Enhanced Help Handler

The system SHALL provide comprehensive help with categories and detailed command documentation.

#### Scenario: Display categorized help
- **GIVEN** user enters `/help`
- **WHEN** handler executes
- **THEN** commands are grouped by category:
  - **Creating**: `/commit`, `/goal`, `/task`, `/vision`, `/milestone`, `/recurring`
  - **Viewing**: `/list`, `/view`, `/integrity`
  - **Actions**: `/complete`, `/atrisk`, `/abandon`, `/recover`
  - **Utilities**: `/help`, `/triage`, `/hours`, `/review`
- **AND** each command shows brief description
- **AND** shortcuts section shows abbreviations and keyboard shortcuts

#### Scenario: Display command-specific help
- **GIVEN** user enters `/help commit`
- **WHEN** handler executes
- **THEN** detailed help for `/commit` is shown:
  - Usage: `/commit <description>` or `/commit "quoted text"`
  - Examples: `/commit send report to Sarah by Friday`
  - Related commands: `/list commitments`, `/complete`

#### Scenario: Help for unknown command
- **GIVEN** user enters `/help xyz`
- **WHEN** handler executes
- **THEN** message: "Unknown command: /xyz"
- **AND** suggests similar commands if any match

### Requirement: Fuzzy Command Matching

The system SHALL suggest similar commands when user enters unrecognized commands using 75% similarity threshold. The 60% threshold was too permissive for short command names; testing showed false positives. The 75% threshold matches the pattern in confirmation.py.

#### Scenario: Suggest on typo with description
- **GIVEN** user enters `/comit` (missing 'm')
- **WHEN** fuzzy matching processes command
- **THEN** finds `/commit` with >75% similarity
- **AND** message includes command description:
  - "Unknown command: /comit"
  - "Did you mean: /commit (create a commitment)?"

#### Scenario: Multiple suggestions with descriptions
- **GIVEN** user enters `/compl`
- **WHEN** fuzzy matching processes command
- **THEN** multiple matches found with descriptions:
  - "Unknown command: /compl"
  - "Did you mean:"
  - "  /complete (mark commitment done)"
  - "  /commit (create a commitment)"

#### Scenario: No similar commands (below threshold)
- **GIVEN** user enters `/xyz` or `/goat`
- **WHEN** fuzzy matching processes command
- **THEN** no matches above 75% threshold
- **AND** message: "Unknown command. Type /help for available commands."

### Requirement: List Command Handler

The system SHALL provide a handler for listing entities with proper session state management.

#### Scenario: List commitments
- **GIVEN** user enters `/list` or `/list commitments`
- **WHEN** handler executes
- **THEN** commitment list is displayed with shortcuts
- **AND** `session.last_list_items` is populated
- **AND** `session.current_entity` is cleared

#### Scenario: List goals
- **GIVEN** user enters `/list goals`
- **WHEN** handler executes
- **THEN** goal list is displayed with shortcuts
- **AND** `session.last_list_items` is populated

#### Scenario: List with invalid entity type
- **GIVEN** user enters `/list widgets`
- **WHEN** handler executes
- **THEN** error message: "Unknown list type: widgets"
- **AND** hint: "Valid types: commitments, goals, visions, tasks, milestones"

#### Scenario: List with database error
- **GIVEN** user enters `/list commitments`
- **WHEN** database query fails (connection error, timeout)
- **THEN** error message: "Failed to load commitments. Please try again."
- **AND** error is logged at ERROR level with details
- **AND** REPL continues functioning normally

## MODIFIED Requirements

### Requirement: Handler Registry

The system SHALL provide a centralized registry for command handlers with lazy instantiation.

#### Scenario: Get handler by command type
- **WHEN** `get_handler(command_type)` is called
- **THEN** the correct handler instance is returned for that command type
- **AND** handlers are instantiated lazily (only when first requested)

#### Scenario: Handler instance caching
- **WHEN** the same command type is requested multiple times
- **THEN** the same handler instance is returned (singleton per type)

#### Scenario: Unknown command type
- **WHEN** `get_handler()` is called with an unregistered command type
- **THEN** None is returned
- **AND** caller handles with fuzzy suggestion

#### Scenario: All command types registered
- **GIVEN** REPL uses registry
- **WHEN** any `CommandType` from parser is dispatched
- **THEN** a handler is registered for that type
- **AND** handler executes appropriate action

### Requirement: Domain Handler Modules

The system SHALL organize handlers into domain-focused modules with enhanced utility handlers.

#### Scenario: Utility handlers
- **WHEN** utility commands are invoked (`/help`, `/show`, `/view`, `/cancel`, `/edit`, `/type`, `/hours`, `/triage`)
- **THEN** handlers are loaded from `utility_handlers.py`

#### Scenario: View handler available
- **WHEN** `/view` command is invoked
- **THEN** `ViewHandler` is loaded from `utility_handlers.py`
- **AND** handler supports ID lookup and number shortcut selection

#### Scenario: Help handler enhanced
- **WHEN** `/help` or `/help <command>` is invoked
- **THEN** `HelpHandler` provides categorized or detailed help

## Cross-Cutting Concerns

### Error Handling

> **Note**: All handlers return `HandlerResult` with error messages. Handlers never raise exceptions directly; they catch and convert to user-friendly messages. The fuzzy command matching provides helpful suggestions on typos.

### Logging

> **Note**: Handler execution is logged at DEBUG level via existing infrastructure. Failed lookups log at INFO level for observability without noise.

### Performance

> **Note**: Performance is not a concern. Handler dispatch via `get_handler()` is O(1) dictionary lookup. Fuzzy matching only runs for unknown commands (~20 commands, negligible).

### Security

> **Note**: Security is N/A. Handlers operate within existing authorization model. No elevation of privilege or new access patterns introduced.
