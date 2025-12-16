# tui-core Specification

## Purpose

The TUI Core specification defines foundational architecture patterns for the JDO terminal user interface built with Textual. It establishes the distinction between Screens and Widgets, navigation patterns, message-based communication, and modal dialog conventions.

## ADDED Requirements

### Requirement: Screen Architecture

The system SHALL implement full-screen views as Textual `Screen` subclasses that participate in the navigation stack.

#### Scenario: HomeScreen is a Screen subclass
- **GIVEN** the user navigates to the home view
- **WHEN** the HomeScreen is displayed
- **THEN** it is an instance of `textual.screen.Screen` that can be pushed/popped from the screen stack

#### Scenario: ChatScreen is a Screen subclass
- **GIVEN** the user navigates to the chat view
- **WHEN** the ChatScreen is displayed
- **THEN** it is an instance of `textual.screen.Screen` that can be pushed/popped from the screen stack

#### Scenario: SettingsScreen is a Screen subclass
- **GIVEN** the user navigates to the settings view
- **WHEN** the SettingsScreen is displayed
- **THEN** it is an instance of `textual.screen.Screen` that can be pushed/popped from the screen stack

#### Scenario: Screens registered in SCREENS dict
- **GIVEN** the JdoApp is defined
- **WHEN** screens are accessed
- **THEN** HomeScreen, ChatScreen, and SettingsScreen are registered in the `SCREENS` class variable for name-based navigation

### Requirement: Widget Architecture

The system SHALL implement reusable UI components as Textual `Widget` subclasses that compose within Screens.

#### Scenario: ChatContainer is a Widget
- **GIVEN** the ChatScreen is displayed
- **WHEN** the message area is rendered
- **THEN** ChatContainer is a `Widget` subclass composed within the ChatScreen

#### Scenario: DataPanel is a Widget
- **GIVEN** the ChatScreen is displayed
- **WHEN** the side panel is rendered
- **THEN** DataPanel is a `Widget` subclass composed within the ChatScreen

#### Scenario: PromptInput is a Widget
- **GIVEN** the ChatScreen is displayed
- **WHEN** the input area is rendered
- **THEN** PromptInput is a `Widget` subclass composed within the ChatScreen

#### Scenario: ChatMessage is a Widget
- **GIVEN** messages are displayed in the chat
- **WHEN** a message bubble is rendered
- **THEN** ChatMessage is a `Widget` subclass composed within ChatContainer

#### Scenario: HierarchyView is a Widget
- **GIVEN** the hierarchy tree is displayed
- **WHEN** the tree view is rendered
- **THEN** HierarchyView is a `Widget` subclass that can be composed within any Screen

### Requirement: Screen Stack Navigation

The system SHALL use Textual's screen stack for navigation between views using `push_screen()` and `pop_screen()`.

#### Scenario: Navigate forward with push_screen
- **GIVEN** the user is on the Home screen
- **WHEN** the user triggers navigation to Chat
- **THEN** `push_screen("chat")` is called and ChatScreen becomes the active screen

#### Scenario: Navigate back with pop_screen
- **GIVEN** the user is on the Chat screen (pushed from Home)
- **WHEN** the user triggers back navigation
- **THEN** `pop_screen()` is called and Home screen becomes active again

#### Scenario: Screen stack maintains history
- **GIVEN** the user navigates Home -> Chat -> Settings (via push)
- **WHEN** the user presses back twice
- **THEN** the stack unwinds: Settings -> Chat -> Home

#### Scenario: Cannot pop last screen
- **GIVEN** only the Home screen is on the stack
- **WHEN** back navigation is attempted
- **THEN** no action is taken (Home remains displayed)

### Requirement: Context-Aware Escape Behavior

The system SHALL implement context-aware Escape key behavior that varies based on current screen and input state.

#### Scenario: Escape on HomeScreen unfocuses widget
- **GIVEN** the user is on the HomeScreen
- **WHEN** a widget has focus and the user presses Escape
- **THEN** the focused widget loses focus

#### Scenario: Escape on HomeScreen with no focus does nothing
- **GIVEN** the user is on the HomeScreen
- **WHEN** no widget has focus and the user presses Escape
- **THEN** no action is taken

#### Scenario: Escape on ChatScreen with unsent input shows confirmation
- **GIVEN** the user is on the ChatScreen
- **WHEN** the PromptInput contains unsent text and the user presses Escape
- **THEN** a confirmation modal is displayed asking to discard input

#### Scenario: Escape on ChatScreen with empty input navigates back
- **GIVEN** the user is on the ChatScreen
- **WHEN** the PromptInput is empty and the user presses Escape
- **THEN** the screen is popped and HomeScreen becomes active

#### Scenario: Escape on SettingsScreen navigates back
- **GIVEN** the user is on the SettingsScreen
- **WHEN** the user presses Escape
- **THEN** the screen is popped and HomeScreen becomes active

### Requirement: Screen Compose Structure

The system SHALL ensure each Screen's compose method yields the expected child widgets.

#### Scenario: HomeScreen compose yields expected widgets
- **GIVEN** the HomeScreen is instantiated
- **WHEN** compose() is called
- **THEN** it yields the expected widgets for the home view

#### Scenario: ChatScreen compose yields expected widgets
- **GIVEN** the ChatScreen is instantiated
- **WHEN** compose() is called
- **THEN** it yields ChatContainer, PromptInput, and DataPanel widgets

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
