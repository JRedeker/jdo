## ADDED Requirements

### Requirement: Custom Theme Definition

The system SHALL define custom JDO themes with a cohesive color palette for visual consistency.

#### Scenario: Dark theme is registered
- **GIVEN** the application starts
- **WHEN** themes are initialized
- **THEN** a `jdo-dark` theme is registered with custom colors for primary, secondary, accent, success, warning, error, surface, and panel

#### Scenario: Light theme is registered
- **GIVEN** the application starts
- **WHEN** themes are initialized
- **THEN** a `jdo-light` theme is registered with appropriate light-mode colors

#### Scenario: Theme applies to all widgets
- **WHEN** a theme variable like `$primary` is used in CSS
- **THEN** it resolves to the custom theme's color value
- **AND** widgets consistently use the theme colors

#### Scenario: Theme toggle switches custom themes
- **WHEN** user toggles dark/light mode via `d` key
- **THEN** the app switches between `jdo-dark` and `jdo-light` themes
- **AND** all custom colors update accordingly

#### Scenario: Theme variables include scrollbar styling
- **WHEN** a custom theme is applied
- **THEN** the theme's `variables` dict includes scrollbar color definitions
- **AND** scrollbars match the theme's color palette

### Requirement: External Stylesheet

The system SHALL use an external TCSS file for centralized styling with live-reload support.

#### Scenario: App loads external CSS
- **GIVEN** `app.tcss` exists in the application directory
- **WHEN** the application starts
- **THEN** styles from `app.tcss` are applied to all screens and widgets

#### Scenario: Live reload during development
- **GIVEN** the application is running with `--dev` flag
- **WHEN** `app.tcss` is modified and saved
- **THEN** styles update immediately without restarting

#### Scenario: Widget DEFAULT_CSS inherits from app styles
- **WHEN** a widget defines `DEFAULT_CSS`
- **THEN** app-level styles from `app.tcss` are inherited
- **AND** widget styles can override with higher specificity

#### Scenario: CSS file contains utility classes
- **GIVEN** `app.tcss` is loaded
- **WHEN** styles are parsed
- **THEN** utility classes for status, badge, grade, and spacing are available

### Requirement: Border Hierarchy

The system SHALL use distinct border styles to communicate visual hierarchy and element importance.

#### Scenario: Primary containers use round borders
- **WHEN** ChatContainer or main content panels are rendered
- **THEN** they use `border: round $primary` style
- **AND** the rounded corners convey modern, prominent appearance

#### Scenario: Secondary containers use subtle borders
- **WHEN** DataPanel or secondary content areas are rendered
- **THEN** they use `border: tall $surface-lighten-1` style
- **AND** the styling is visually subordinate to primary containers

#### Scenario: Modal dialogs use double borders
- **WHEN** a modal dialog (ApiKeyScreen, DraftRestoreScreen, AiRequiredScreen) is displayed
- **THEN** it uses `border: double $accent` style
- **AND** the border clearly distinguishes it as an overlay

#### Scenario: Focused elements use heavy borders
- **WHEN** an interactive element receives focus
- **THEN** it displays a `border: heavy $accent` or tint change
- **AND** the focus state is immediately visible

#### Scenario: Error states use error-colored borders
- **WHEN** an element is in an error state
- **THEN** it uses `border: round $error` style
- **AND** the error is visually prominent

#### Scenario: Sidebar uses subtle separation border
- **WHEN** NavSidebar is rendered
- **THEN** it uses `border-right: tall $surface-lighten-1` style
- **AND** the border provides subtle visual separation from content

### Requirement: Background Depth System

The system SHALL use layered background colors to create visual depth and grouping.

#### Scenario: Screen uses base background
- **WHEN** the Screen container is rendered
- **THEN** it uses `background: $background` as the base layer

#### Scenario: Primary surfaces use surface color
- **WHEN** main content areas are rendered
- **THEN** they use `background: $surface` for the primary layer

#### Scenario: Raised elements use lighter surface
- **WHEN** elements need to appear elevated (cards, dropdowns)
- **THEN** they use `background: $surface-lighten-1`

#### Scenario: Sunken elements use darker surface
- **WHEN** elements need to appear recessed (sidebar, gutters)
- **THEN** they use `background: $surface-darken-1`

#### Scenario: Focus adds background tint
- **WHEN** an element receives focus
- **THEN** a subtle `background-tint: $accent 5%` is applied
- **AND** the tint indicates focus without overwhelming content

#### Scenario: Panel backgrounds are distinct
- **WHEN** DataPanel or NavSidebar are rendered
- **THEN** they use distinct background colors from main content
- **AND** visual grouping is immediately apparent

### Requirement: Chat Message Visual Differentiation

The system SHALL visually distinguish chat messages by role using borders and backgrounds.

#### Scenario: User messages have accent indicator
- **WHEN** a user message is displayed in ChatContainer
- **THEN** it has `border-left: heavy $accent` as a colored accent bar
- **AND** background uses `$surface`

#### Scenario: Assistant messages have primary indicator
- **WHEN** an assistant message is displayed
- **THEN** it has `border-left: heavy $primary` as a colored accent bar
- **AND** background uses `$panel`

#### Scenario: System messages have warning styling
- **WHEN** a system message is displayed
- **THEN** it has `border: round $warning` to indicate system-level content
- **AND** background uses `$warning 10%` for subtle emphasis

#### Scenario: Thinking state has muted appearance
- **WHEN** an assistant message is in thinking state
- **THEN** it has `text-opacity: 70%` and muted styling
- **AND** the reduced opacity indicates pending content

#### Scenario: Error messages have error styling
- **WHEN** an error message is displayed
- **THEN** it has `border: round $error` styling
- **AND** background uses `$error 10%` for emphasis

### Requirement: NavSidebar Visual Enhancement

The system SHALL provide clear visual hierarchy and state indication in the navigation sidebar.

#### Scenario: Sidebar has depth from main content
- **WHEN** NavSidebar is rendered
- **THEN** it uses `background: $surface-darken-1` to appear recessed
- **AND** `border-right: tall $surface-lighten-1` for subtle separation

#### Scenario: Active item has prominent indicator
- **WHEN** a navigation item is selected/active
- **THEN** it displays `border-left: heavy $accent` indicator
- **AND** the accent color clearly marks the current location

#### Scenario: Highlighted item has subtle background
- **WHEN** a navigation item is keyboard-highlighted but not selected
- **THEN** it displays `background: $primary 20%` for visibility
- **AND** the highlighting is distinct from the active indicator

#### Scenario: Collapsed sidebar maintains hierarchy
- **WHEN** NavSidebar is in collapsed state
- **THEN** visual styling remains consistent but adapts to narrow width
- **AND** active item indicator remains visible

#### Scenario: Sidebar hover state is visible
- **WHEN** mouse hovers over a navigation item
- **THEN** it displays `background: $surface-darken-1` or hover tint
- **AND** the hover state is distinct from highlighted state

### Requirement: Focus State Consistency

The system SHALL provide consistent and visible focus states across all interactive widgets.

#### Scenario: Input fields show focus clearly
- **WHEN** PromptInput or other input receives focus
- **THEN** border changes to `round $accent`
- **AND** background has subtle `background-tint: $accent 5%`

#### Scenario: Option lists show focus on highlighted item
- **WHEN** OptionList (sidebar, selectors) has focus
- **THEN** the highlighted item has visible styling
- **AND** keyboard navigation is immediately apparent

#### Scenario: Buttons show focus state
- **WHEN** a button receives focus
- **THEN** it displays a focus ring or border change
- **AND** the focused button is distinguishable from others

#### Scenario: Focus is visible in all themes
- **WHEN** focus is applied in either dark or light theme
- **THEN** the focus indicator has sufficient contrast
- **AND** accessibility is maintained

### Requirement: Utility CSS Classes

The system SHALL provide reusable utility classes for common styling patterns.

#### Scenario: Status color classes apply semantic colors
- **WHEN** `.status-success` class is applied
- **THEN** the element uses `color: $success`
- **AND** similar classes exist for warning, error, muted, pending, in-progress, at-risk, abandoned

#### Scenario: Badge classes provide background and foreground
- **WHEN** `.badge-warning` class is applied
- **THEN** the element uses `background: $warning 20%` and `color: $warning`
- **AND** similar classes exist for success, error, info

#### Scenario: Spacing classes provide consistent rhythm
- **WHEN** `.p-1` or `.m-2` classes are applied
- **THEN** consistent padding/margin values are applied
- **AND** spacing follows the 1-2 unit rhythm

#### Scenario: Surface classes apply background depths
- **WHEN** `.surface-raised` class is applied
- **THEN** the element uses `background: $surface-lighten-1`
- **AND** similar classes exist for base surface and sunken

### Requirement: Status Indicator Visual System

The system SHALL use consistent visual indicators for entity statuses across all views.

#### Scenario: Pending status uses muted styling
- **WHEN** an entity with status "pending" is displayed
- **THEN** it uses `color: $text-muted` or dim style
- **AND** the visual weight is lower than active items

#### Scenario: In-progress status uses primary color
- **WHEN** an entity with status "in_progress" is displayed
- **THEN** it uses `color: $primary` to indicate activity

#### Scenario: Completed status uses success color
- **WHEN** an entity with status "completed" is displayed
- **THEN** it uses `color: $success` to indicate completion

#### Scenario: At-risk status uses warning styling
- **WHEN** an entity with status "at_risk" is displayed
- **THEN** it uses `color: $warning` with `text-style: bold`
- **AND** the visual urgency is higher than other statuses

#### Scenario: Abandoned status uses error color
- **WHEN** an entity with status "abandoned" is displayed
- **THEN** it uses `color: $error` to indicate abandonment

#### Scenario: Draft status uses secondary styling
- **WHEN** an entity with status "draft" is displayed
- **THEN** it uses `color: $secondary` with `text-style: italic`
- **AND** the styling indicates temporary state

### Requirement: Grade Color Coding

The system SHALL use consistent color coding for integrity grades.

#### Scenario: A-range grades use success color
- **WHEN** integrity grade is A+, A, or A-
- **THEN** it displays with `color: $success` (green)

#### Scenario: B-range grades use primary color
- **WHEN** integrity grade is B+, B, or B-
- **THEN** it displays with `color: $primary` (blue)

#### Scenario: C-range grades use warning color
- **WHEN** integrity grade is C+, C, or C-
- **THEN** it displays with `color: $warning` (yellow/orange)

#### Scenario: D and F grades use error color
- **WHEN** integrity grade is D+, D, D-, or F
- **THEN** it displays with `color: $error` (red)

### Requirement: Scrollbar Theming

The system SHALL customize scrollbar appearance to match the theme.

#### Scenario: Scrollbar colors match theme
- **WHEN** a scrollable widget is rendered
- **THEN** scrollbar uses theme-defined colors from `variables` dict
- **AND** scrollbar background matches surface color

#### Scenario: Scrollbar hover state is visible
- **WHEN** mouse hovers over scrollbar
- **THEN** scrollbar color changes to hover color
- **AND** the change is subtle but noticeable

#### Scenario: Scrollbar active state is visible
- **WHEN** scrollbar is being dragged
- **THEN** scrollbar color changes to accent color
- **AND** the active state is clearly distinct

### Requirement: Loading Indicator Styling

The system SHALL style loading indicators to match the theme.

#### Scenario: Loading indicator uses theme color
- **WHEN** a loading indicator is displayed
- **THEN** it uses `color: $primary` or theme-appropriate color
- **AND** the color is consistent with the overall theme

### Requirement: Modal Overlay Styling

The system SHALL provide consistent styling for modal overlays.

#### Scenario: Modal overlay uses translucent background
- **WHEN** a modal dialog is displayed
- **THEN** the overlay uses `background: $primary 30%` for dimming effect
- **AND** the underlying content is visible but de-emphasized

#### Scenario: Modal dialog is visually distinct
- **WHEN** a modal dialog container is rendered
- **THEN** it uses `background: $surface` for solid background
- **AND** `border: double $accent` for prominent framing

#### Scenario: Modal buttons are prominent
- **WHEN** modal action buttons are displayed
- **THEN** primary action uses `background: $accent`
- **AND** secondary actions use subtle styling
