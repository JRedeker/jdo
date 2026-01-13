# TUI Navigation Delta

## MODIFIED Requirements

### Requirement: Navigation Sidebar Visual States

The navigation sidebar SHALL provide clear visual feedback for item states in both expanded and collapsed modes.

#### Scenario: Active item in expanded sidebar
- **WHEN** an item is selected and the sidebar is expanded
- **THEN** the active item displays with accent-colored border-left and lighter background
- **AND** the visual distinction is immediately apparent

#### Scenario: Active item in collapsed sidebar
- **WHEN** an item is selected and the sidebar is collapsed
- **THEN** the active item displays with distinct visual styling different from non-active items
- **AND** the visual distinction remains clear despite the reduced space
- **AND** users can identify which navigation item is currently active

#### Scenario: Sidebar collapse toggle
- **WHEN** user presses `[` to toggle sidebar collapse
- **THEN** the sidebar transitions between expanded and collapsed states
- **AND** the active item indicator remains visible throughout the transition
- **AND** the active item continues to be distinguishable in the new state
