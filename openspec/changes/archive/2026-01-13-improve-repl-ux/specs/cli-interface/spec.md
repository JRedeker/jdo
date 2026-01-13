## ADDED Requirements

### Requirement: Onboarding Splash Screen

The system SHALL display an onboarding splash screen on first run and when new features are available. This helps users understand the purpose and key capabilities of the app.

#### Scenario: First run onboarding
- **GIVEN** user starts JDO for the first time (no config file exists)
- **WHEN** REPL initializes
- **THEN** splash screen displays before the main prompt:
  - App name and version
  - Brief "what" (commitment tracking) and "why" (accountability)
  - Key commands to get started: `/commit`, `/list`, `/help`
  - "Press Enter to continue"
- **AND** config records that onboarding was shown

#### Scenario: New version onboarding
- **GIVEN** user has used JDO before but a new version introduced features
- **WHEN** REPL initializes and version differs from last seen
- **THEN** "What's New" splash displays:
  - Version number
  - Bullet list of new features
  - "Press Enter to continue"
- **AND** config records new version as seen

#### Scenario: Skip onboarding
- **GIVEN** onboarding screen is displayed
- **WHEN** user presses Escape or Ctrl+C
- **THEN** onboarding is dismissed
- **AND** REPL continues to main prompt
- **AND** onboarding will not show again for this version

#### Scenario: Onboarding is skippable in scripts
- **GIVEN** JDO is run with `--quiet` or `--no-input` flag
- **WHEN** REPL initializes
- **THEN** onboarding is skipped entirely

#### Scenario: Onboarding config write failure
- **GIVEN** onboarding screen is displayed and user presses Enter
- **WHEN** config file write fails (permissions, disk full)
- **THEN** onboarding continues to main prompt anyway
- **AND** warning is logged at WARNING level
- **AND** onboarding may show again on next run (acceptable degradation)

### Requirement: Slash Prefix Command Detection

The system SHALL treat all input starting with `/` as a command, never as natural language. This provides unambiguous command detection.

#### Scenario: Slash input is always a command
- **GIVEN** REPL is awaiting input
- **WHEN** user types any input starting with `/`
- **THEN** input is parsed as a command (not sent to AI)
- **AND** command handler is invoked

#### Scenario: Invalid slash command
- **GIVEN** REPL is awaiting input
- **WHEN** user types `/unknowncommand`
- **THEN** error message shows "Unknown command: /unknowncommand"
- **AND** fuzzy suggestions offered if similar commands exist
- **AND** input is NOT sent to AI

#### Scenario: Natural language with slash
- **GIVEN** user wants to ask about a path like "/home/user"
- **WHEN** user types "what is /home/user"
- **THEN** input is sent to AI (because it doesn't start with `/`)
- **AND** command parser is not invoked

### Requirement: Entity Context Tracking

The system SHALL track the current entity context in session state for navigation and reference resolution.

#### Scenario: Track current entity after view
- **GIVEN** user has viewed an entity with `/view abc123`
- **WHEN** session context is updated
- **THEN** `session.current_entity` contains entity type, ID, short_id, and display_name
- **AND** toolbar displays context breadcrumb

#### Scenario: Clear context on list
- **GIVEN** user has a current entity context
- **WHEN** user runs `/list`
- **THEN** `session.current_entity` is cleared
- **AND** `session.last_list_items` is populated with displayed items

#### Scenario: Resolve "it" and "this" references
- **GIVEN** user has a current entity context
- **WHEN** user says "complete it" or "show this"
- **THEN** reference resolves to `session.current_entity.entity_id`
- **AND** action is applied to the correct entity

#### Scenario: EntityContext data structure
- **GIVEN** `EntityContext` dataclass in `session.py`
- **WHEN** entity context is stored
- **THEN** dataclass contains fields: `entity_type`, `entity_id`, `short_id`, `display_name`
- **AND** `short_id` is first 6 characters of UUID for display
- **AND** `display_name` is truncated deliverable/title for toolbar display

### Requirement: Explicit Number Selection from Lists

The system SHALL support selecting items by explicit numbered shortcuts from the most recent list display. This uses `/1`, `/2` syntax to avoid hidden state and ambiguity per POLA (Principle of Least Astonishment).

#### Scenario: Display numbered list items with shortcuts
- **GIVEN** user runs `/list commitments`
- **WHEN** list is displayed
- **THEN** each item shows shortcut and number: `[/1]`, `[/2]`, etc.
- **AND** items are stored in `session.last_list_items`

#### Scenario: Select item by explicit shortcut
- **GIVEN** user has just viewed a list
- **WHEN** user types `/1` or `/2`
- **THEN** system interprets as `/view` for that item from the list
- **AND** entity details are displayed

#### Scenario: Invalid number shortcut
- **GIVEN** user has just viewed a list with 5 items
- **WHEN** user types `/7` (out of range)
- **THEN** error message explains valid range: "No item 7. Use /1 through /5, or /list to see items."

#### Scenario: Number shortcut without prior list
- **GIVEN** user has not recently viewed a list
- **WHEN** user types `/1`
- **THEN** error message: "No list to select from. Use /list first."

#### Scenario: Last list items data structure
- **GIVEN** `Session` class in `session.py`
- **WHEN** list is displayed
- **THEN** `session.last_list_items` is populated with list of `(entity_type, entity_id)` tuples
- **AND** list is ordered by display position (index 0 = item 1)
- **AND** list is cleared when user runs a non-list command that changes context

### Requirement: Keyboard Shortcuts

The system SHALL provide keyboard shortcuts for common actions using prompt_toolkit key bindings. Uses F5 for refresh instead of Ctrl+R to avoid readline reverse-i-search conflict.

#### Scenario: Clear and refresh with Ctrl+L
- **GIVEN** REPL is running with content on screen
- **WHEN** user presses Ctrl+L
- **THEN** screen is cleared
- **AND** dashboard is redisplayed
- **AND** prompt reappears

#### Scenario: Refresh data with F5
- **GIVEN** REPL is running
- **WHEN** user presses F5
- **THEN** dashboard cache is refreshed from database
- **AND** dashboard is redisplayed with updated data

#### Scenario: Show help with F1
- **GIVEN** REPL is running
- **WHEN** user presses F1
- **THEN** help text is displayed (equivalent to `/help`)

#### Scenario: Keyboard shortcut during AI processing
- **GIVEN** AI is currently processing a request (streaming response)
- **WHEN** user presses Ctrl+L, F5, or F1
- **THEN** keyboard shortcut is ignored until current operation completes
- **AND** no error is displayed

#### Scenario: Keyboard shortcut error handling
- **GIVEN** user presses F5 to refresh dashboard
- **WHEN** database connection fails or query errors
- **THEN** error message displays: "Refresh failed: [reason]"
- **AND** REPL continues functioning normally
- **AND** previous dashboard data remains visible
- **AND** error is logged at INFO level

#### Scenario: Keyboard shortcuts are testable
- **GIVEN** test suite needs to verify keyboard shortcuts
- **WHEN** tests use prompt_toolkit's `create_pipe_input()` and `DummyOutput()`
- **THEN** shortcuts can be triggered programmatically
- **AND** responses can be captured and asserted

### Requirement: Command Abbreviations

The system SHALL support short aliases for commonly used commands.

#### Scenario: Use abbreviation for commit
- **GIVEN** REPL is awaiting input
- **WHEN** user types `/c "send report to Sarah"`
- **THEN** command is interpreted as `/commit "send report to Sarah"`

#### Scenario: Use abbreviation for list
- **GIVEN** REPL is awaiting input
- **WHEN** user types `/l`
- **THEN** command is interpreted as `/list`

#### Scenario: Use abbreviation for view
- **GIVEN** REPL is awaiting input
- **WHEN** user types `/v abc123`
- **THEN** command is interpreted as `/view abc123`

#### Scenario: Abbreviations shown in help
- **GIVEN** user runs `/help`
- **WHEN** help text is displayed
- **THEN** abbreviations are listed: `/c` (commit), `/l` (list), `/v` (view), `/h` (help)
- **AND** keyboard shortcuts are listed: Ctrl+L (clear), F5 (refresh), F1 (help)

## MODIFIED Requirements

### Requirement: Slash Command Auto-completion

The system SHALL provide auto-completion for slash commands using prompt_toolkit WordCompleter. Dynamic entity ID completion is deferred per P20 (prefer simple solutions) since existing partial-ID matching in handlers provides good UX.

> **Supersedes deployed spec**: This expands the completion list from the original 7 commands to all 18+ registered commands. The deployed cli-interface spec's "Show completion options" scenario is updated by this change.

#### Scenario: Tab-complete slash commands
- **GIVEN** the REPL is awaiting user input
- **WHEN** user types `/li` and presses Tab
- **THEN** the input is completed to `/list` (or shows matching options)
- **AND** matching is case-insensitive

#### Scenario: Show completion options
- **GIVEN** the REPL is awaiting user input
- **WHEN** user types `/` and presses Tab
- **THEN** a dropdown shows available commands:
  - Entity creation: `/commit`, `/goal`, `/task`, `/vision`, `/milestone`
  - Navigation: `/list`, `/view`, `/help`
  - Actions: `/complete`, `/atrisk`, `/abandon`, `/recover`
  - Status: `/integrity`, `/triage`, `/hours`

#### Scenario: Graceful handling when no completions match
- **GIVEN** the REPL is awaiting user input
- **WHEN** user types `/xyz` (no matching command) and presses Tab
- **THEN** no completion dropdown is shown
- **AND** the input remains unchanged
- **AND** no error is displayed

### Requirement: Bottom Toolbar Status Bar

The system SHALL display an always-visible status bar at the bottom of the terminal using cached values, including current entity context.

> **Extends deployed spec**: This adds entity context display to the existing toolbar. The deployed cli-interface spec's toolbar scenarios remain valid; this change adds a new scenario for entity context.

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

#### Scenario: Show current entity context
- **GIVEN** user has viewed or is editing an entity
- **WHEN** the prompt is displayed
- **THEN** the bottom toolbar shows entity context: `[commitment:abc123]`
- **AND** context is cleared when user runs `/list` or creates new entity

#### Scenario: Cached values update on data changes
- **GIVEN** user creates, updates, or deletes an entity
- **WHEN** the operation completes
- **THEN** session cache is updated
- **AND** toolbar reflects new values on next render

## Cross-Cutting Concerns

### Error Handling

> **Note**: Error handling for keyboard shortcuts and command dispatch uses existing REPL error patterns. All exceptions are caught at the REPL loop level and displayed as user-friendly messages.

### Logging

> **Note**: Keyboard shortcut usage and command dispatch are logged at DEBUG level using existing `jdo.config.logging` setup. No new logging infrastructure needed.

### Configuration

> **Note**: No new configuration options required. Keyboard shortcuts use standard prompt_toolkit bindings. Command aliases are hardcoded per simplicity principle (P20).

### Security

> **Note**: Security is N/A for this change. Entity navigation uses existing ID-based access patterns. No new authentication or authorization behavior introduced.
