# tui-core Specification

## Purpose
Define the foundational TUI architecture patterns for JDO, establishing the distinction between Screens (full-screen navigation targets) and Widgets (composable UI components), along with navigation, messaging, and styling conventions.
## Requirements
### Requirement: Screen Architecture

The system SHALL implement full-screen views as Textual `Screen` subclasses that participate in the navigation stack.

#### Scenario: MainScreen is a Screen subclass
- **GIVEN** the user opens the application
- **WHEN** the MainScreen is displayed
- **THEN** it is an instance of `textual.screen.Screen` that integrates NavSidebar and content area

#### Scenario: MainScreen embeds chat widgets
- **GIVEN** the MainScreen is displayed
- **WHEN** the content area is rendered
- **THEN** it contains ChatContainer, PromptInput, and DataPanel widgets directly (not via ChatScreen)
- **AND** ChatScreen is no longer used as a separate pushable screen

#### Scenario: SettingsScreen is a Screen subclass
- **GIVEN** the user navigates to the settings view
- **WHEN** the SettingsScreen is displayed
- **THEN** it is an instance of `textual.screen.Screen` that can be pushed/popped from the screen stack

#### Scenario: Screens registered in SCREENS dict
- **GIVEN** the JdoApp is defined
- **WHEN** screens are accessed
- **THEN** MainScreen and SettingsScreen are registered in the `SCREENS` class variable for name-based navigation
- **AND** HomeScreen and ChatScreen are NOT registered (deprecated)

### Requirement: Widget Architecture

The system SHALL implement reusable UI components as Textual `Widget` subclasses that compose within Screens.

#### Scenario: NavSidebar is a Widget
- **GIVEN** the MainScreen is displayed
- **WHEN** the sidebar is rendered
- **THEN** NavSidebar is a `Widget` subclass composed within the MainScreen

#### Scenario: ChatContainer is a Widget
- **GIVEN** the MainScreen is displayed
- **WHEN** the message area is rendered
- **THEN** ChatContainer is a `Widget` subclass composed within the MainScreen

#### Scenario: DataPanel is a Widget
- **GIVEN** the MainScreen is displayed
- **WHEN** the side panel is rendered
- **THEN** DataPanel is a `Widget` subclass composed within the MainScreen

#### Scenario: PromptInput is a Widget
- **GIVEN** the MainScreen is displayed
- **WHEN** the input area is rendered
- **THEN** PromptInput is a `Widget` subclass composed within the MainScreen

#### Scenario: ChatMessage is a Widget
- **GIVEN** messages are displayed in the chat
- **WHEN** a message bubble is rendered
- **THEN** ChatMessage is a `Widget` subclass composed within ChatContainer

#### Scenario: HierarchyView is a Widget
- **GIVEN** the hierarchy tree is displayed
- **WHEN** the tree view is rendered
- **THEN** HierarchyView is a `Widget` subclass that can be composed within any Screen

### Requirement: Screen Stack Navigation

The system SHALL use Textual's screen stack for modal screens using `push_screen()` and `pop_screen()`.

#### Scenario: Navigate to Settings with push_screen
- **GIVEN** the user is on the main layout
- **WHEN** the user triggers navigation to Settings
- **THEN** `push_screen("settings")` is called and SettingsScreen becomes the active screen

#### Scenario: Navigate back with pop_screen
- **GIVEN** the user is on the Settings screen (pushed from main)
- **WHEN** the user triggers back navigation
- **THEN** `pop_screen()` is called and main layout becomes active again

#### Scenario: Screen stack for modals only
- **GIVEN** navigation items (Goals, Commitments, etc.) are selected
- **WHEN** the content updates
- **THEN** no screen push/pop occurs; only DataPanel content changes

### Requirement: Context-Aware Escape Behavior

The system SHALL implement context-aware Escape key behavior that varies based on current focus and input state.

#### Scenario: Escape on MainScreen with focused widget
- **GIVEN** the user is on the MainScreen
- **WHEN** a widget has focus and the user presses Escape
- **THEN** focus moves to PromptInput

#### Scenario: Escape on MainScreen with empty PromptInput
- **GIVEN** the user is on the MainScreen
- **WHEN** PromptInput is focused, empty, and the user presses Escape
- **THEN** a quit confirmation dialog is shown

#### Scenario: Escape on MainScreen with unsent input
- **GIVEN** the user is on the MainScreen
- **WHEN** the PromptInput contains unsent text and the user presses Escape
- **THEN** the PromptInput is cleared (with confirmation if significant text)

#### Scenario: Escape on SettingsScreen navigates back
- **GIVEN** the user is on the SettingsScreen
- **WHEN** the user presses Escape
- **THEN** the screen is popped and MainScreen becomes active

### Requirement: Screen Compose Structure

The system SHALL ensure MainScreen's compose method yields the expected child widgets.

#### Scenario: MainScreen compose yields expected widgets
- **GIVEN** the MainScreen is instantiated
- **WHEN** compose() is called
- **THEN** it yields Header, NavSidebar, ChatContainer, PromptInput, DataPanel, and Footer widgets

#### Scenario: SettingsScreen compose yields expected widgets
- **GIVEN** the SettingsScreen is instantiated
- **WHEN** compose() is called
- **THEN** it yields the expected widgets for settings configuration

### Requirement: Message-Based Communication

The system SHALL use Textual's message system for communication between child components and parent screens/app.

#### Scenario: Widget posts message to parent
- **GIVEN** a Widget needs to communicate an action to its parent
- **WHEN** the action is triggered
- **THEN** the Widget calls `self.post_message(MessageClass())` to bubble the message up

#### Scenario: Screen handles child widget messages
- **GIVEN** a Widget posts a message
- **WHEN** the message bubbles to the parent Screen
- **THEN** the Screen can handle it via `on_<widget>_<message>()` method naming convention

#### Scenario: App handles screen messages
- **GIVEN** a Screen posts a message
- **WHEN** the message bubbles to the App
- **THEN** the App can handle it via `on_<screen>_<message>()` method naming convention

#### Scenario: Message class defined as nested class
- **GIVEN** a component needs to define a custom message
- **WHEN** the message class is created
- **THEN** it is defined as a nested class within the component (e.g., `HomeScreen.NewChat`)

### Requirement: Modal Dialog Pattern

The system SHALL implement modal dialogs as `ModalScreen` subclasses with centered layout.

#### Scenario: ModalScreen blocks parent interaction
- **GIVEN** a modal dialog is pushed
- **WHEN** the user interacts with the UI
- **THEN** key bindings from the parent screen are not processed

#### Scenario: ModalScreen uses centered layout
- **GIVEN** a modal dialog is displayed
- **WHEN** the dialog is rendered
- **THEN** it uses CSS `align: center middle` to center the dialog container

#### Scenario: ModalScreen returns result via dismiss
- **GIVEN** the user completes a modal dialog action
- **WHEN** the dialog closes
- **THEN** `self.dismiss(result)` is called to return a value to the caller

#### Scenario: ModalScreen dismisses on Escape
- **GIVEN** a modal dialog is displayed
- **WHEN** the user presses Escape
- **THEN** the dialog dismisses with a None or cancel result

### Requirement: CSS Styling Conventions

The system SHALL follow consistent CSS styling patterns for Screens and Widgets.

#### Scenario: Screen CSS scoped to screen class
- **GIVEN** a Screen has custom styles
- **WHEN** CSS is defined
- **THEN** styles are scoped using the Screen class name as selector (e.g., `HomeScreen { ... }`)

#### Scenario: Widget CSS scoped to widget class
- **GIVEN** a Widget has custom styles
- **WHEN** CSS is defined
- **THEN** styles are scoped using the Widget class name as selector (e.g., `DataPanel { ... }`)

#### Scenario: DEFAULT_CSS defined in class
- **GIVEN** a Screen or Widget needs custom styles
- **WHEN** the class is defined
- **THEN** styles are provided via the `DEFAULT_CSS` class variable

#### Scenario: Child widget styles use descendant selectors
- **GIVEN** a Screen needs to style child widgets
- **WHEN** CSS rules are written
- **THEN** descendant selectors are used (e.g., `ChatScreen DataPanel { ... }`)

### Requirement: Key Binding Conventions

The system SHALL define key bindings using Textual's `BINDINGS` class variable with consistent patterns.

#### Scenario: BINDINGS defined as ClassVar
- **GIVEN** a Screen or Widget has key bindings
- **WHEN** bindings are defined
- **THEN** they are specified in a `BINDINGS: ClassVar[list[Binding]]` class variable

#### Scenario: Binding format includes key, action, description
- **GIVEN** a key binding is defined
- **WHEN** the binding tuple is created
- **THEN** it includes (key, action_name, description) for footer display

#### Scenario: Actions implemented as action_ methods
- **GIVEN** a binding references action "new_chat"
- **WHEN** the key is pressed
- **THEN** the method `action_new_chat()` is invoked

#### Scenario: Bindings show in footer
- **GIVEN** a Screen has bindings defined
- **WHEN** the Footer widget is displayed
- **THEN** bindings with `show=True` (default) appear in the footer

### Requirement: Test Patterns for Screens

The system SHALL support testing Screens using Textual's `run_test()` and `Pilot` patterns.

#### Scenario: Screen tested via App.run_test
- **GIVEN** a test needs to verify Screen behavior
- **WHEN** the test runs
- **THEN** it uses `async with app.run_test() as pilot:` pattern

#### Scenario: Pilot simulates key presses
- **GIVEN** a test needs to simulate user input
- **WHEN** key simulation is needed
- **THEN** `await pilot.press("key")` is used

#### Scenario: Pilot simulates clicks
- **GIVEN** a test needs to simulate mouse input
- **WHEN** click simulation is needed
- **THEN** `await pilot.click(selector)` is used

#### Scenario: Screen queries use query_one and query
- **GIVEN** a test needs to find widgets
- **WHEN** widget lookup is needed
- **THEN** `app.query_one(Selector)` or `app.query(Selector)` is used

### Requirement: Worker Context Documentation

The system SHALL document all Textual worker context requirements and patterns used in the codebase.

#### Scenario: Document push_screen_wait requirement
- **WHEN** developer reviews Textual patterns documentation
- **THEN** documentation explains push_screen_wait MUST run in worker context
- **AND** provides example of correct usage with run_worker()

#### Scenario: Document NoActiveWorker error
- **WHEN** developer encounters NoActiveWorker exception
- **THEN** documentation explains root cause (push_screen_wait outside worker)
- **AND** provides solution pattern with code example

#### Scenario: Worker context checklist
- **WHEN** developer implements blocking operations in Textual app
- **THEN** documentation provides checklist of operations requiring workers:
  - push_screen_wait (waiting for screen dismissal)
  - Long-running I/O operations
  - Database queries in lifecycle methods
  - AI agent calls

### Requirement: Async Lifecycle Patterns

The system SHALL document async lifecycle method patterns and constraints for Textual screens and widgets.

#### Scenario: on_mount patterns
- **WHEN** developer implements on_mount method
- **THEN** documentation shows correct patterns:
  - Lightweight async operations allowed
  - Blocking operations must use run_worker()
  - push_screen() allowed, push_screen_wait() requires worker

#### Scenario: on_show and on_resume patterns
- **WHEN** developer implements screen lifecycle methods
- **THEN** documentation covers on_show vs on_resume differences
- **AND** provides examples of when to use each

#### Scenario: Lifecycle method constraints
- **WHEN** developer reviews lifecycle documentation
- **THEN** clear guidance on what NOT to do:
  - No blocking I/O without workers
  - No time.sleep() calls
  - No input() or stdin reads

### Requirement: Message Handling Conventions

The system SHALL document message handling patterns and conventions used in the application.

#### Scenario: Message class naming
- **WHEN** developer creates new message class
- **THEN** documentation provides naming convention (PascalCase, noun/verb clarity)
- **AND** shows message bubbling behavior

#### Scenario: Handler method naming
- **WHEN** developer implements message handler
- **THEN** documentation shows convention: `on_<screen>_<message>`
- **AND** explains when handlers are called (automatic registration)

#### Scenario: Message vs action patterns
- **WHEN** developer chooses between message and action
- **THEN** documentation clarifies:
  - Actions: widget-local behavior
  - Messages: cross-widget/screen communication

### Requirement: Screen Navigation Patterns

The system SHALL document screen navigation patterns, stack management, and data passing conventions.

#### Scenario: push_screen vs push_screen_wait
- **WHEN** developer navigates between screens
- **THEN** documentation explains:
  - push_screen: Fire-and-forget navigation
  - push_screen_wait: Wait for screen result (requires worker)

#### Scenario: Passing data to screens
- **WHEN** developer needs to pass data to new screen
- **THEN** documentation shows constructor parameter pattern
- **AND** shows DataPanel pre-loading example

#### Scenario: Screen stack management
- **WHEN** developer implements navigation flow
- **THEN** documentation shows proper stack management
- **AND** explains when to pop_screen vs dismiss vs replace

### Requirement: Focus Management Patterns

The system SHALL document focus management patterns and best practices for keyboard navigation.

#### Scenario: Focus after screen transition
- **WHEN** screen is pushed or popped
- **THEN** documentation shows how to restore focus correctly
- **AND** provides examples of focus() calls in on_show

#### Scenario: Widget focus order
- **WHEN** developer implements composite widgets
- **THEN** documentation explains focus chain
- **AND** shows how to control tab order

### Requirement: Common Pitfalls Documentation

The system SHALL document common Textual pitfalls discovered during implementation and their solutions.

#### Scenario: Pitfall - Yielding screens in compose
- **WHEN** developer reviews pitfalls documentation
- **THEN** explains screens must be pushed, not yielded
- **AND** shows incorrect vs correct pattern

#### Scenario: Pitfall - Mutable class variables
- **WHEN** developer creates widget with class-level data
- **THEN** documentation warns about shared state across instances
- **AND** shows ClassVar pattern for intentional sharing

#### Scenario: Pitfall - Session management with SQLModel
- **WHEN** developer queries database in Textual app
- **THEN** documentation shows context manager pattern
- **AND** warns about session expunge for cross-screen data

### Requirement: Testing Patterns for Textual

The system SHALL document testing patterns specific to Textual applications.

#### Scenario: Pilot testing pattern
- **WHEN** developer writes Textual widget test
- **THEN** documentation shows app.run_test() pattern
- **AND** provides example of pilot interactions

#### Scenario: Message testing
- **WHEN** developer tests message handling
- **THEN** documentation shows how to post messages in tests
- **AND** how to assert on message handling

#### Scenario: Snapshot testing
- **WHEN** developer adds visual regression tests
- **THEN** documentation shows snapshot app pattern
- **AND** explains snapshot update workflow

### Requirement: Settings Screen Auth Status Refresh

The system SHALL update authentication status displays after successful API key authentication.

#### Scenario: Refresh auth status after API key save
- **GIVEN** the Settings screen is displayed
- **WHEN** user saves an API key successfully
- **THEN** the auth status widget for that provider updates to show "Authenticated"
- **AND** the status widget style changes to success color

#### Scenario: Bindings remain active after modal dismiss
- **GIVEN** the Settings screen displayed an API key modal
- **WHEN** the modal is dismissed (success or cancel)
- **THEN** the Escape/Back binding remains responsive
- **AND** user can navigate back to the previous screen

### Requirement: Allocated Hours Calculation

The system SHALL calculate allocated hours from active tasks for AI context.

#### Scenario: Calculate from pending and in-progress tasks
- **WHEN** `_build_ai_context()` is called
- **THEN** `allocated_hours` is calculated as the sum of `estimated_hours` for all tasks with status PENDING or IN_PROGRESS
- **AND** tasks without `estimated_hours` are treated as 0

#### Scenario: Handle database errors gracefully
- **WHEN** the allocated hours query fails
- **THEN** `allocated_hours` returns 0.0
- **AND** a warning is logged with message "Failed to calculate allocated hours: {error}"

### Requirement: Navigation Sidebar Widget

The system SHALL provide a NavSidebar widget for persistent, discoverable navigation.

#### Scenario: NavSidebar is a Widget
- **GIVEN** the application is displayed
- **WHEN** the sidebar is rendered
- **THEN** NavSidebar is a `Widget` subclass that can be composed within any Screen or App

#### Scenario: NavSidebar uses OptionList
- **GIVEN** the NavSidebar is composed
- **WHEN** it renders navigation items
- **THEN** it uses Textual's `OptionList` widget for keyboard-friendly selection

#### Scenario: NavSidebar posts Selected message
- **GIVEN** the user selects a navigation item
- **WHEN** the selection is made (via Enter, click, or number key)
- **THEN** NavSidebar posts a `NavSidebar.Selected` message with `item_id` attribute

#### Scenario: NavSidebar supports collapse mode
- **GIVEN** the sidebar is in expanded mode
- **WHEN** the user presses `[` key
- **THEN** the sidebar collapses to show single-letter shortcuts only

#### Scenario: NavSidebar number key navigation
- **GIVEN** the sidebar has focus
- **WHEN** the user presses a number key (1-9)
- **THEN** the corresponding navigation item is selected directly

#### Scenario: NavSidebar triage badge
- **GIVEN** there are items needing triage
- **WHEN** the sidebar is rendered in expanded mode
- **THEN** the Triage item shows a badge with the count

