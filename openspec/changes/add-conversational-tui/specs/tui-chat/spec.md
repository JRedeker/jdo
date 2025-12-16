# Capability: Conversational TUI Chat Interface

The TUI provides an AI-driven conversational interface for creating and managing Goals, Commitments, and Tasks. The interface follows Elia's keyboard-centric design with a split-panel layout showing chat on the left and structured data on the right.

**Implementation Notes** (Textual-specific):
- Use `Horizontal` container with `width: 60%` / `width: 40%` for split-panel layout
- Use `Header` (docked top) and `Footer` (docked bottom) widgets
- Footer automatically displays bindings from `BINDINGS` class attribute where `show=True`
- Use `TextArea` for multi-line input with `tab_behavior="focus"` (default) so Tab moves focus
- Use widget-level `BINDINGS` for context-sensitive shortcuts (not just App-level)
- Use `RichLog` or custom widget for chat message display with streaming support
- Use `VerticalScroll` container for scrollable message area

## ADDED Requirements

### Requirement: Split-Panel Layout

The system SHALL display a split-panel interface with conversational chat on the left (60-70% width) and a structured data panel on the right (30-40% width).

**Implementation Note**: Use Textual's `Horizontal` container with CSS `width: 60%` and `width: 40%` (or `width: 2fr` / `width: 1fr` for fractional units). The data panel should have `overflow-y: auto` for scrolling.

#### Scenario: Default layout on chat screen
- **WHEN** user opens a conversation
- **THEN** the screen displays chat messages on the left and data panel on the right
- **Note**: Layout uses `Horizontal(ChatPanel(), DataPanel())` structure

#### Scenario: Panel focus toggle
- **WHEN** user presses Tab
- **THEN** focus alternates between the chat input and the data panel
- **Note**: Textual's default Tab behavior cycles through focusable widgets. Ensure `can_focus=True` on both panels.

#### Scenario: Responsive panel sizing
- **WHEN** terminal width is narrow (< 80 columns)
- **THEN** data panel collapses to icons/minimal view with expand option
- **Note**: Use CSS media query or reactive check on terminal size to toggle `display: none` on data panel content

### Requirement: Chat Message Display

The system SHALL display conversation messages in a scrollable container with clear visual distinction between user and assistant messages.

#### Scenario: Display user message
- **WHEN** user sends a message
- **THEN** the message appears with "USER" label and timestamp

#### Scenario: Display assistant message
- **WHEN** AI responds
- **THEN** the message appears with "ASSISTANT" label and timestamp

#### Scenario: Streaming response display
- **WHEN** AI is generating a response
- **THEN** text appears incrementally as tokens arrive with "AI is typing..." indicator

#### Scenario: Scroll to latest message
- **WHEN** new message is added
- **THEN** chat container scrolls to show the latest message

#### Scenario: Navigate message history
- **WHEN** user presses Shift+Up or Shift+Down
- **THEN** chat container scrolls through message history

### Requirement: Prompt Input

The system SHALL provide a multi-line text input area for composing messages with command support. Uses Textual's `TextArea` widget with custom key bindings.

#### Scenario: Multi-line input
- **WHEN** user presses Enter in the prompt
- **THEN** a new line is created (not submitted)

#### Scenario: Submit message
- **WHEN** user presses Ctrl+Enter (or Ctrl+J as alias)
- **THEN** the message is sent to the AI
- **Note**: Implemented via custom action binding on TextArea, not default Input behavior

#### Scenario: Command recognition
- **WHEN** user types a message starting with "/"
- **THEN** the system recognizes it as a command

#### Scenario: Empty submit prevention
- **WHEN** user attempts to submit an empty message
- **THEN** the message is not sent

### Requirement: Data Panel - Draft Mode

The system SHALL display a structured template in the data panel when drafting a new Goal, Commitment, or Task.

#### Scenario: Commitment draft template
- **WHEN** AI proposes a commitment from conversation
- **THEN** the data panel shows: Deliverable, Stakeholder, Due, Status (Draft), Goal, and Tasks sections

#### Scenario: Goal draft template
- **WHEN** AI proposes a goal from conversation
- **THEN** the data panel shows: Title, Problem Statement, Solution Vision, Parent Goal, Status (Draft), and Target Date

#### Scenario: Task draft template
- **WHEN** AI proposes a task from conversation
- **THEN** the data panel shows: Title, Scope, Sub-tasks, Status (Draft), and parent Commitment

#### Scenario: Real-time field updates
- **WHEN** user provides additional details in chat that modify the draft
- **THEN** the data panel updates the relevant fields immediately

#### Scenario: Draft indicator
- **WHEN** viewing a draft object
- **THEN** the panel clearly shows "Draft" status with visual distinction

### Requirement: Data Panel - View Mode

The system SHALL display full details of an existing domain object in the data panel.

#### Scenario: View commitment
- **WHEN** user views a commitment via command or selection
- **THEN** the panel shows all commitment fields with current values and associated tasks

#### Scenario: View goal
- **WHEN** user views a goal via command or selection
- **THEN** the panel shows all goal fields with current values and child commitments count

#### Scenario: View task
- **WHEN** user views a task via command or selection
- **THEN** the panel shows task fields including scope and sub-task completion status

### Requirement: Data Panel - List Mode

The system SHALL display a scrollable list of domain objects in the data panel.

#### Scenario: List commitments
- **WHEN** user executes `/show commitments`
- **THEN** the panel shows a list of commitments sorted by due date ascending (soonest first) with deliverable, stakeholder, due date, and status

#### Scenario: List goals
- **WHEN** user executes `/show goals`
- **THEN** the panel shows a hierarchical list of goals with title and status

#### Scenario: List tasks
- **WHEN** user executes `/show tasks`
- **THEN** the panel shows tasks for the current commitment with title and status

#### Scenario: List stakeholders
- **WHEN** user executes `/show stakeholders`
- **THEN** the panel shows a list of stakeholders with name and type

#### Scenario: Navigate list
- **WHEN** panel is focused and user presses j/k
- **THEN** selection moves down/up through the list

#### Scenario: Select list item
- **WHEN** user presses Enter on a list item
- **THEN** the panel switches to view mode for that item

### Requirement: Command - Create Commitment

The system SHALL support the `/commit` command to create a commitment from conversation context.

#### Scenario: Create commitment from context
- **WHEN** user types `/commit` after discussing a commitment
- **THEN** AI extracts deliverable, stakeholder, and due date from conversation and updates draft panel

#### Scenario: Prompt for goal linkage
- **WHEN** AI creates a commitment draft without a goal_id
- **THEN** AI asks: "Would you like to link this commitment to a goal? Linking helps maintain alignment with your vision." and shows available goals

#### Scenario: Allow unlinked commitment
- **WHEN** user declines to link commitment to a goal
- **THEN** the commitment is created with goal_id=NULL (allowed but noted)

#### Scenario: Confirm commitment creation
- **WHEN** user confirms the proposed commitment (types `/commit` again or "yes")
- **THEN** the commitment is saved to the database and panel shows confirmed status

#### Scenario: Modify before confirming
- **WHEN** user provides corrections in chat after `/commit`
- **THEN** AI updates the draft in the panel before final confirmation

#### Scenario: Cancel commitment creation
- **WHEN** user types "cancel" or `/cancel` during draft
- **THEN** the draft is discarded and panel returns to default state

### Requirement: Command - Create Goal

The system SHALL support the `/goal` command to create a goal from conversation context.

#### Scenario: Create goal from context
- **WHEN** user types `/goal` after discussing a goal
- **THEN** AI extracts title, problem statement, and solution vision and updates draft panel

#### Scenario: Confirm goal creation
- **WHEN** user confirms the proposed goal
- **THEN** the goal is saved to the database

#### Scenario: Associate goal with parent
- **WHEN** user specifies a parent goal during creation
- **THEN** the new goal is linked to the parent goal

### Requirement: Command - Create Task

The system SHALL support the `/task` command to add a task to the current commitment context.

#### Scenario: Create task from context
- **WHEN** user types `/task` while viewing or drafting a commitment
- **THEN** AI extracts task title and scope from conversation and updates draft panel

#### Scenario: Add sub-tasks
- **WHEN** user describes sub-tasks in conversation before `/task`
- **THEN** AI includes sub-tasks in the task draft

#### Scenario: Require commitment context
- **WHEN** user types `/task` without an active commitment
- **THEN** AI prompts user to select or create a commitment first

### Requirement: Task Suggestions

The system SHALL suggest task breakdown for commitments but not require them.

#### Scenario: Suggest tasks on commitment creation
- **WHEN** user confirms a new commitment
- **THEN** AI offers: "Would you like to break this down into tasks?" but allows user to skip

#### Scenario: Accept commitment without tasks
- **WHEN** user declines task breakdown or says "no"
- **THEN** the commitment is saved without tasks

#### Scenario: Complex commitment task prompt
- **WHEN** AI detects a commitment with multiple implied steps (e.g., "prepare and deliver presentation")
- **THEN** AI more strongly suggests task breakdown but still allows skipping

### Requirement: Command - View and Navigate

The system SHALL support commands for viewing and navigating domain objects.

#### Scenario: Show command with type
- **WHEN** user types `/show goals`, `/show commitments`, or `/show tasks`
- **THEN** the data panel displays a list of the specified type

#### Scenario: View specific object
- **WHEN** user types `/view <id>` or selects from list
- **THEN** the data panel shows full details of that object

#### Scenario: Edit current object
- **WHEN** user types `/edit` while viewing an object
- **THEN** user can modify the object through conversation

### Requirement: Command - Status Changes

The system SHALL support commands for changing object status.

#### Scenario: Complete commitment
- **WHEN** user types `/complete` while viewing a commitment
- **THEN** AI confirms and marks the commitment as completed with timestamp

#### Scenario: Complete task
- **WHEN** user types `/complete` while viewing a task
- **THEN** the task status changes to completed

#### Scenario: Explicit completion required
- **WHEN** all tasks for a commitment are completed
- **THEN** the commitment remains in its current status until user explicitly completes it

### Requirement: Command - Help

The system SHALL provide a `/help` command listing available commands.

#### Scenario: Display help
- **WHEN** user types `/help`
- **THEN** AI responds with a formatted list of available commands and their descriptions

#### Scenario: Command-specific help
- **WHEN** user types `/help <command>`
- **THEN** AI responds with detailed help for that specific command

### Requirement: Home Screen

The system SHALL provide a home screen showing quick actions and pending draft restoration.

#### Scenario: Fresh start on open
- **WHEN** user opens the app with no pending drafts
- **THEN** a new conversation is started automatically

#### Scenario: Restore pending draft
- **WHEN** user opens the app with a partially created object saved
- **THEN** a fresh conversation opens with AI asking "You have an unfinished [commitment/goal/task]. Would you like to continue creating it?"

#### Scenario: Quick access to objects
- **WHEN** user presses 'g' for goals or 'c' for commitments
- **THEN** the data panel shows that object type list

#### Scenario: Access settings
- **WHEN** user presses 's' on home screen
- **THEN** the settings menu opens

#### Scenario: Access orphan commitments
- **WHEN** user presses 'o' on home screen
- **THEN** the data panel shows all open commitments not linked to any goal (orphan commitments)

### Requirement: Orphan Commitments View

The system SHALL provide a dedicated view for commitments not linked to goals.

#### Scenario: List orphan commitments
- **WHEN** user executes `/show orphans` or presses 'o' from home
- **THEN** the data panel shows all commitments where goal_id is NULL and status is not completed/abandoned

#### Scenario: Orphan commitment indicator
- **WHEN** displaying an orphan commitment
- **THEN** a visual indicator (e.g., ⚠ or "unlinked") shows it has no goal association

#### Scenario: Suggest linking orphans
- **WHEN** user views an orphan commitment
- **THEN** AI suggests: "This commitment isn't linked to a goal. Would you like to connect it to one?"

#### Scenario: Empty orphans view
- **WHEN** user views orphans and all commitments are linked to goals
- **THEN** the data panel shows: "All commitments are linked to goals. Great alignment!"

### Requirement: Conversation Model

The system SHALL maintain an ephemeral Conversation and Message model for runtime chat state. These are NOT persisted to the database.

#### Scenario: Conversation structure
- **WHEN** a conversation is active
- **THEN** it contains a list of Message objects with role (user/assistant/system), content, and timestamp

#### Scenario: Messages in memory only
- **WHEN** messages are exchanged
- **THEN** they exist only in application memory, not in SQLite

#### Scenario: Conversation cleared on quit
- **WHEN** user quits the application
- **THEN** all conversation state is discarded (no persistence)

### Requirement: Draft Model

The system SHALL persist partially created domain objects as Draft entities in SQLite.

#### Scenario: Draft structure
- **WHEN** a draft is saved
- **THEN** it contains: id (UUID), entity_type (commitment/goal/task), partial_data (JSON), created_at, updated_at

#### Scenario: Single active draft
- **WHEN** user starts creating a new entity while a draft exists
- **THEN** the system asks if they want to discard the existing draft or continue it

#### Scenario: Draft to entity conversion
- **WHEN** user confirms a draft
- **THEN** the draft data is validated, converted to the target entity, saved, and the draft is deleted

#### Scenario: Draft expiration
- **WHEN** a draft is older than 7 days
- **THEN** the system prompts user to continue or discard on next app launch

### Requirement: Conversation Lifecycle

The system SHALL treat conversations as ephemeral working sessions.

#### Scenario: Fresh conversation on launch
- **WHEN** user starts the application with no pending draft
- **THEN** a new empty conversation begins

#### Scenario: Restore draft on launch
- **WHEN** user starts the application with a pending draft
- **THEN** AI asks "You have an unfinished [type]. Would you like to continue?"

#### Scenario: Domain objects persist independently
- **WHEN** a domain object is created from a conversation
- **THEN** the object persists in the database; conversation remains ephemeral

### Requirement: AI Context Integration

The system SHALL copy relevant conversational context into domain objects when created.

#### Scenario: Copy context to notes
- **WHEN** AI creates a commitment from conversation
- **THEN** relevant discussion points are copied to the commitment's notes field

#### Scenario: Preserve source reference
- **WHEN** a domain object is created from conversation
- **THEN** the object can be traced back to the source conversation

### Requirement: Keyboard Navigation

The system SHALL support comprehensive keyboard navigation following Elia conventions. Keybindings are context-sensitive based on current screen/focus state.

**Implementation Note**: Context-sensitive bindings are achieved by defining `BINDINGS` on individual widgets/screens, not just the App. Textual resolves bindings from the focused widget up through the DOM. Use `Binding(..., show=True)` for footer-visible shortcuts and `Binding(..., show=False)` for hidden shortcuts.

#### Scenario: Global escape behavior
- **WHEN** user presses Escape
- **THEN** focus returns to prompt input or navigates back to home
- **Note**: Escape binding defined at Screen level with priority=True

#### Scenario: Message navigation (message area focused)
- **WHEN** user presses 'g' while message area widget is focused
- **THEN** scroll moves to first message
- **Note**: 'g' binding defined on MessageArea widget only, not global

#### Scenario: Latest message navigation (message area focused)
- **WHEN** user presses 'G' while message area widget is focused
- **THEN** scroll moves to latest message
- **Note**: 'G' binding defined on MessageArea widget only

#### Scenario: Quick access goals (prompt focused or home)
- **WHEN** user presses 'g' while prompt input is focused or on home screen
- **THEN** the data panel shows goals list
- **Note**: 'g' binding defined on PromptInput widget and HomeScreen, distinct from MessageArea's 'g'

#### Scenario: Quick access commitments (prompt focused or home)
- **WHEN** user presses 'c' while prompt input is focused or on home screen
- **THEN** the data panel shows commitments list

#### Scenario: Open settings (home screen)
- **WHEN** user presses 's' on home screen
- **THEN** the settings menu opens (ModalScreen pushed onto stack)

#### Scenario: Quit application (home screen only)
- **WHEN** user presses 'q' on home screen
- **THEN** the application exits
- **Note**: 'q' binding only on HomeScreen, not global, to prevent accidental quit

### Requirement: AI Field Extraction

The system SHALL handle incomplete information during commitment/goal/task creation by asking follow-up questions.

#### Scenario: Missing required fields
- **WHEN** user types `/commit` and conversation lacks required fields (deliverable, stakeholder, due date)
- **THEN** AI asks specific follow-up questions to gather missing information

#### Scenario: Ambiguous stakeholder
- **WHEN** AI cannot determine the stakeholder from conversation context
- **THEN** AI asks "Who is this commitment to?" with suggestions from existing stakeholders

#### Scenario: Missing due date
- **WHEN** AI cannot determine due date from conversation
- **THEN** AI asks "When do you need to deliver this?" with natural language date suggestions

#### Scenario: Iterative clarification
- **WHEN** user provides partial answer to follow-up question
- **THEN** AI continues asking until all required fields are gathered

### Requirement: Draft Auto-Save

The system SHALL automatically save and restore draft state when navigating away from a conversation.

#### Scenario: Auto-save on navigation
- **WHEN** user has an active draft and navigates to home screen or another conversation
- **THEN** the draft state is automatically persisted

#### Scenario: Restore draft on return
- **WHEN** user returns to a conversation with a saved draft
- **THEN** the data panel restores the draft state and AI acknowledges the in-progress draft

#### Scenario: Clear draft on completion
- **WHEN** user confirms or cancels a draft
- **THEN** the persisted draft state is cleared

### Requirement: Confirmation Flexibility

The system SHALL accept flexible confirmation phrases using fuzzy string matching.

#### Scenario: Accept confirmation variants
- **WHEN** user responds to confirmation prompt with "yes", "yeah", "yep", "sure", "ok", "looks good", "confirm", "do it"
- **THEN** the system recognizes it as confirmation

#### Scenario: Accept cancellation variants
- **WHEN** user responds with "no", "nope", "cancel", "stop", "nevermind", "wait"
- **THEN** the system recognizes it as cancellation

#### Scenario: Fuzzy matching threshold
- **WHEN** user response has >80% similarity to known confirmation/cancellation phrases
- **THEN** the system matches the intent using rapidfuzz token_set_ratio

#### Scenario: Ambiguous response
- **WHEN** user response doesn't clearly match confirmation or cancellation
- **THEN** AI asks for explicit confirmation: "Please confirm with 'yes' or 'cancel'"

### Requirement: AI Availability

The system SHALL require AI connectivity to function and block operations when unavailable.

#### Scenario: AI unavailable on startup
- **WHEN** user starts the application and AI provider is not configured or unreachable
- **THEN** the system displays an error message explaining AI is required and how to configure it

#### Scenario: AI becomes unavailable mid-session
- **WHEN** AI provider becomes unreachable during a session
- **THEN** the system displays an error in the chat and disables the input until reconnection

#### Scenario: Connection retry
- **WHEN** AI is unavailable
- **THEN** the system periodically attempts to reconnect (every 30 seconds)

### Requirement: Due Date Specificity

The system SHALL require a specific day for due dates and store date and time separately.

#### Scenario: Date without time
- **WHEN** user specifies "due Friday" or "due December 20" without a time
- **THEN** the commitment due_date is set to that date and due_time defaults to 09:00 (start of business)

#### Scenario: Date with specific time
- **WHEN** user specifies "due Friday at 3pm"
- **THEN** the commitment due_date is set to Friday and due_time is set to 15:00

#### Scenario: End of day interpretation
- **WHEN** user specifies "due by end of day"
- **THEN** the due_time is set to 17:00 (5 PM)

#### Scenario: Vague date rejected
- **WHEN** user specifies "due next week" or "due soon" without a specific day
- **THEN** AI asks for clarification: "Which day next week?" or "What specific date?"

#### Scenario: Relative dates with specific day
- **WHEN** user specifies "due tomorrow" or "due this Friday"
- **THEN** the system calculates the specific date and applies 09:00 default due_time

### Requirement: Empty State Onboarding

The system SHALL provide guidance when the user has no commitments, goals, or conversations.

#### Scenario: First-time user empty state
- **WHEN** user opens the app with no existing data
- **THEN** the home screen displays onboarding guidance explaining what JDO does and how to start

#### Scenario: Empty commitments list
- **WHEN** user views commitments and none exist
- **THEN** the data panel shows guidance: "No commitments yet. Type 'I need to...' to create your first commitment."

#### Scenario: Empty goals list
- **WHEN** user views goals and none exist
- **THEN** the data panel shows guidance: "No goals yet. Goals give your commitments meaning. Type '/goal' to create one."

### Requirement: Error Display

The system SHALL display errors as inline chat messages from the system.

#### Scenario: Display error in chat
- **WHEN** an error occurs during AI interaction or data operation
- **THEN** a system message appears in the chat with the error description

#### Scenario: Error message styling
- **WHEN** displaying an error message
- **THEN** the message has "SYSTEM" label and distinct visual styling (e.g., red/warning color)

#### Scenario: Actionable error guidance
- **WHEN** displaying an error
- **THEN** the message includes guidance on how to resolve the issue when possible

### Requirement: Visual Design Principles

The system SHALL implement text-focused design with impeccable formatting.

#### Scenario: Consistent alignment
- **WHEN** any screen is displayed
- **THEN** all labels and values are aligned on consistent column boundaries

#### Scenario: Monospace-friendly layout
- **WHEN** content is displayed
- **THEN** spacing and alignment work correctly in monospace fonts

#### Scenario: Status indicators
- **WHEN** status is displayed
- **THEN** Unicode symbols indicate state (e.g., ● active, ✓ complete, ○ pending, ◐ in progress)

#### Scenario: Minimal chrome
- **WHEN** UI elements are rendered
- **THEN** borders and decorations are minimal, prioritizing content

#### Scenario: Footer with shortcuts
- **WHEN** any screen is displayed
- **THEN** a footer shows context-sensitive keyboard shortcuts
- **Note**: Use Textual's `Footer` widget which auto-renders bindings from `BINDINGS` where `show=True`. Bindings from the focused widget and its ancestors are displayed.

### Requirement: Textual Widget Architecture

The system SHALL use the following Textual widget hierarchy for the chat interface.

#### Scenario: App structure
- **WHEN** the application starts
- **THEN** it uses `App[None]` with `SCREENS` dict mapping screen names to Screen classes

#### Scenario: Main chat screen structure
- **WHEN** the chat screen is composed
- **THEN** it yields: `Header()`, `Horizontal(ChatPanel(), DataPanel())`, `Footer()`

#### Scenario: Chat panel structure
- **WHEN** the chat panel is composed
- **THEN** it yields: `VerticalScroll(id="messages")` for message history, `TextArea(id="prompt")` for input

#### Scenario: Data panel structure
- **WHEN** the data panel is composed
- **THEN** it yields a container that switches between List, View, and Draft modes via reactive state

#### Scenario: Settings as modal
- **WHEN** user opens settings
- **THEN** a `ModalScreen` is pushed onto the screen stack, dimming the main screen

#### Scenario: Streaming response widget
- **WHEN** AI generates a streaming response
- **THEN** a Response widget (custom Static subclass) is mounted and updated via `update()` as tokens arrive
