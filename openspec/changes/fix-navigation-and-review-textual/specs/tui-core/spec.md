# Capability: TUI Core (Textual Patterns and Best Practices)

This spec documents Textual-specific patterns, conventions, and best practices discovered through implementation and review of our TUI application.

**Cross-reference**: See `jdo-app` for main application implementation, `tui-views` for screen implementations.

## ADDED Requirements

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

## MODIFIED Requirements

None - all documentation is new.

## REMOVED Requirements

None.
