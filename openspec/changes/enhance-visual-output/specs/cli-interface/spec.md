## ADDED Requirements

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

## MODIFIED Requirements

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
