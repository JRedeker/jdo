# tui-core Specification Delta

## MODIFIED Requirements

### Requirement: Screen Architecture

The system SHALL implement full-screen views as Textual `Screen` subclasses that participate in the navigation stack.

#### Scenario: MainScreen is a Screen subclass
- **GIVEN** the user opens the application
- **WHEN** the MainScreen is displayed
- **THEN** it is an instance of `textual.screen.Screen` that integrates NavSidebar and content area

#### Scenario: ChatScreen embedded in MainScreen
- **GIVEN** the MainScreen is displayed
- **WHEN** the content area is rendered
- **THEN** it contains ChatContainer, PromptInput, and DataPanel widgets (not as separate Screen)

#### Scenario: SettingsScreen is a Screen subclass
- **GIVEN** the user navigates to the settings view
- **WHEN** the SettingsScreen is displayed
- **THEN** it is an instance of `textual.screen.Screen` that can be pushed/popped from the screen stack

#### Scenario: Screens registered in SCREENS dict
- **GIVEN** the JdoApp is defined
- **WHEN** screens are accessed
- **THEN** MainScreen and SettingsScreen are registered in the `SCREENS` class variable for name-based navigation

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

### Requirement: MainScreen Compose Structure

The system SHALL ensure MainScreen's compose method yields the expected child widgets.

#### Scenario: MainScreen compose yields expected widgets
- **GIVEN** the MainScreen is instantiated
- **WHEN** compose() is called
- **THEN** it yields Header, NavSidebar, ChatContainer, PromptInput, DataPanel, and Footer widgets

#### Scenario: SettingsScreen compose yields expected widgets
- **GIVEN** the SettingsScreen is instantiated
- **WHEN** compose() is called
- **THEN** it yields the expected widgets for settings configuration

## REMOVED Requirements

### Requirement: HomeScreen Architecture

**Reason**: HomeScreen is being replaced by NavSidebar integrated into MainScreen.

**Migration**: Use MainScreen with NavSidebar for navigation discovery.
