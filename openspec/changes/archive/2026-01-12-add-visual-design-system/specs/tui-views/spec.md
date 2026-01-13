## MODIFIED Requirements

### Requirement: TUI Design Principles

The system SHALL implement a text-focused TUI with minimal panels, impeccable formatting, a cohesive visual design system, and consistent state communication.

#### Scenario: Consistent alignment across screens
- **WHEN** any screen is displayed
- **THEN** all labels and values are aligned on consistent column boundaries

#### Scenario: Monospace-friendly layout
- **WHEN** content is displayed
- **THEN** spacing and alignment work correctly in monospace fonts

#### Scenario: Keyboard-first navigation
- **WHEN** user interacts with the application
- **THEN** all actions are accessible via keyboard shortcuts shown in footer

#### Scenario: Status indicators use symbols and colors
- **WHEN** status is displayed
- **THEN** Unicode symbols indicate state (e.g., circle for active, checkmark for complete)
- **AND** colors follow semantic meaning from the design system

#### Scenario: Visual hierarchy through background depth
- **WHEN** multiple content areas are displayed
- **THEN** background colors create clear visual layers
- **AND** users can distinguish primary content from secondary panels and chrome

#### Scenario: Border styles communicate element importance
- **WHEN** containers and panels are rendered
- **THEN** border styles match element importance per design system
- **AND** users can quickly identify element roles (primary, secondary, modal, focus)

#### Scenario: Focus states are immediately visible
- **WHEN** user navigates with keyboard
- **THEN** the focused element has clear visual indication
- **AND** focus changes are apparent without delay

#### Scenario: Status colors are semantic and consistent
- **WHEN** entity statuses are displayed across any view
- **THEN** colors follow semantic meaning: success=green, warning=yellow, error=red, primary=blue
- **AND** color meanings are consistent across all screens and widgets

#### Scenario: Theme colors create cohesive appearance
- **WHEN** the application is displayed
- **THEN** all colors come from the registered custom theme
- **AND** visual appearance is consistent, branded, and professional

#### Scenario: Scrollbars match theme
- **WHEN** scrollable content is displayed
- **THEN** scrollbar colors match the current theme
- **AND** scrollbar states (hover, active) are visible

#### Scenario: Loading states are styled
- **WHEN** loading indicators are displayed
- **THEN** they use theme-appropriate colors
- **AND** they are visually consistent with other elements

#### Scenario: Modal overlays provide clear separation
- **WHEN** modal dialogs are displayed
- **THEN** overlay dims underlying content
- **AND** dialog container is visually prominent and distinct
