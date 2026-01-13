# TUI Core Delta

## MODIFIED Requirements

### Requirement: Application Bindings

The application SHALL provide accurate and descriptive labels for all keyboard bindings.

#### Scenario: Theme toggle binding display
- **WHEN** user views available bindings
- **THEN** the theme toggle binding displays as "Toggle Theme" (not "Toggle Dark Mode")
- **AND** the description accurately reflects the action performed

#### Scenario: Theme toggle action
- **WHEN** user presses `d` key
- **THEN** the application toggles between jdo-dark and jdo-light themes
- **AND** the binding description accurately describes this behavior

## ADDED Requirements

### Requirement: CSS Architecture Documentation

The TUI application SHALL document CSS file loading and performance considerations for maintainability.

#### Scenario: CSS path resolution documentation
- **WHEN** developer reviews `src/jdo/app.py`
- **THEN** the CSS_PATH constant includes a comment explaining it resolves relative to the module
- **AND** the expected file location is clearly stated

#### Scenario: Performance consideration documentation
- **WHEN** developer reviews `src/jdo/app.tcss`
- **THEN** the universal selector usage includes a comment about potential performance implications
- **AND** the comment suggests alternatives if performance issues arise
