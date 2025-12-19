# ai-uat Specification

## Purpose
TBD - created by archiving change add-ai-driven-uat. Update Purpose after archive.
## Requirements
### Requirement: UI State Observer

The system SHALL provide a utility to capture current UI state for AI consumption.

#### Scenario: Capture screen state
- **WHEN** UIStateObserver.capture() is called with a Textual app
- **THEN** it returns a structured representation including:
  - Current screen class name
  - Screen title (if set)
  - List of visible widgets with IDs and types
  - Currently focused widget ID
  - Available keybindings from footer

#### Scenario: Capture chat screen state
- **WHEN** UIStateObserver captures state on ChatScreen
- **THEN** the representation includes:
  - Chat message count and recent messages
  - Prompt input content
  - Data panel mode and content summary

#### Scenario: Capture data panel content
- **WHEN** UIStateObserver captures state with DataPanel visible
- **THEN** the representation includes:
  - Panel mode (draft, list, view, empty)
  - Item type being displayed
  - Summary of displayed content

#### Scenario: State is JSON-serializable
- **WHEN** UI state is captured
- **THEN** the result is JSON-serializable for AI consumption

### Requirement: UAT Action Model

The system SHALL define a structured action model for AI-driven test execution.

#### Scenario: Press key action
- **WHEN** AI returns UATAction with action_type="press"
- **THEN** the driver calls pilot.press(target) where target is the key sequence

#### Scenario: Click widget action
- **WHEN** AI returns UATAction with action_type="click"
- **THEN** the driver calls pilot.click(target) where target is a CSS selector

#### Scenario: Type text action
- **WHEN** AI returns UATAction with action_type="type"
- **THEN** the driver loads text into the focused input widget

#### Scenario: Wait action
- **WHEN** AI returns UATAction with action_type="wait"
- **THEN** the driver calls pilot.pause() with optional delay from value field

#### Scenario: Assert action
- **WHEN** AI returns UATAction with action_type="assert"
- **THEN** the driver evaluates the assertion against current UI state

#### Scenario: Done action
- **WHEN** AI returns UATAction with action_type="done"
- **THEN** the driver terminates the scenario and evaluates success criteria

#### Scenario: Action includes reasoning
- **WHEN** AI returns any UATAction
- **THEN** the action includes a reason field explaining the AI's decision

### Requirement: AI UAT Driver

The system SHALL provide a driver class that orchestrates AI-driven test execution.

#### Scenario: Initialize driver with app and agent
- **WHEN** AIUATDriver is created
- **THEN** it accepts a JdoApp instance and a PydanticAI agent

#### Scenario: Run scenario to completion
- **WHEN** driver.run_scenario(scenario) is called
- **THEN** the driver loops: observe state, get AI action, execute action
- **AND** continues until AI returns "done" or max_steps is reached

#### Scenario: Respect max steps limit
- **WHEN** scenario execution reaches max_steps without "done"
- **THEN** the driver raises UATStepLimitExceeded with context

#### Scenario: Respect timeout
- **WHEN** scenario execution exceeds timeout_seconds
- **THEN** the driver raises UATTimeoutError with context

#### Scenario: Log all actions
- **WHEN** scenario executes
- **THEN** all actions and their results are logged for debugging

#### Scenario: Return execution result
- **WHEN** scenario completes
- **THEN** driver returns UATResult with success status, steps taken, and any errors

### Requirement: UAT Scenario Definition

The system SHALL support declarative scenario definitions.

#### Scenario: Load scenario from YAML
- **WHEN** scenario YAML file is parsed
- **THEN** it produces a UATScenario model with name, description, goal, and success criteria

#### Scenario: Scenario includes preconditions
- **WHEN** scenario has preconditions defined
- **THEN** preconditions are executed before AI-driven steps begin

#### Scenario: Scenario defines success criteria
- **WHEN** scenario defines success_criteria
- **THEN** criteria are evaluated when AI returns "done" action

#### Scenario: Scenario has configurable limits
- **WHEN** scenario is defined
- **THEN** it can specify max_steps (default 50) and timeout_seconds (default 120)

### Requirement: TestModel Integration

The system SHALL support using PydanticAI TestModel for cost-free test runs.

#### Scenario: Run with TestModel
- **WHEN** UAT test runs without --live-ai marker
- **THEN** the driver uses TestModel or FunctionModel for deterministic responses

#### Scenario: Run with live AI
- **WHEN** UAT test has @pytest.mark.live_ai marker
- **THEN** the driver uses the configured live AI provider

#### Scenario: TestModel returns valid actions
- **WHEN** TestModel is used for UAT
- **THEN** it returns valid UATAction JSON matching expected scenario flow

### Requirement: UAT Test Fixtures

The system SHALL provide pytest fixtures for UAT test authoring.

#### Scenario: uat_driver fixture
- **WHEN** test requests uat_driver fixture
- **THEN** it receives an AIUATDriver configured with test app and mock agent

#### Scenario: live_uat_driver fixture
- **WHEN** test requests live_uat_driver fixture
- **THEN** it receives an AIUATDriver configured with live AI (requires credentials)

#### Scenario: uat_app fixture
- **WHEN** test requests uat_app fixture
- **THEN** it receives a JdoApp configured for UAT testing with temp database

### Requirement: Commitment Creation Scenario

The system SHALL include a UAT scenario for commitment creation flow.

#### Scenario: Create commitment via natural language
- **GIVEN** user is on home screen
- **WHEN** AI navigates to chat and describes a commitment
- **THEN** a commitment draft appears in data panel
- **AND** after confirmation, commitment is persisted

#### Scenario: Verify commitment in list
- **GIVEN** a commitment was just created
- **WHEN** AI navigates to commitment list
- **THEN** the new commitment appears in the list

### Requirement: Triage Workflow Scenario

The system SHALL include a UAT scenario for triage workflow.

#### Scenario: Complete triage flow
- **GIVEN** triage items exist in the inbox
- **WHEN** AI enters triage mode via /triage or 't' key
- **THEN** triage interface is displayed with first item

#### Scenario: Process triage item
- **GIVEN** triage interface is displayed
- **WHEN** AI selects an action (accept, change type, delete, skip)
- **THEN** the item is processed and next item is shown or triage completes

### Requirement: Integrity Dashboard Scenario

The system SHALL include a UAT scenario for integrity dashboard interaction.

#### Scenario: View integrity metrics
- **GIVEN** user has existing commitments
- **WHEN** AI navigates to integrity view via 'i' key
- **THEN** integrity grade and metrics are displayed

#### Scenario: Navigate from integrity to at-risk items
- **GIVEN** integrity dashboard shows at-risk commitments
- **WHEN** AI requests to view at-risk items
- **THEN** at-risk commitment list is displayed

### Requirement: Navigation Scenario

The system SHALL include a UAT scenario for multi-screen navigation.

#### Scenario: Navigate through all main screens
- **GIVEN** app is running on home screen
- **WHEN** AI navigates: home -> chat -> home -> settings -> home
- **THEN** each transition completes without error

#### Scenario: Escape returns to previous screen
- **GIVEN** user is on a non-home screen
- **WHEN** AI presses escape
- **THEN** app returns to previous screen in stack

### Requirement: Planning Hierarchy Scenario

The system SHALL include a UAT scenario for full planning hierarchy creation.

#### Scenario: Create vision to commitment chain
- **GIVEN** user starts with empty database
- **WHEN** AI creates: vision -> goal -> milestone -> commitment
- **THEN** hierarchy view shows complete chain

#### Scenario: Navigate hierarchy tree
- **GIVEN** hierarchy tree is displayed
- **WHEN** AI expands and navigates nodes
- **THEN** each level displays correctly and is navigable

