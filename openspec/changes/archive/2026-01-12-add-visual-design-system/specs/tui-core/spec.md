## MODIFIED Requirements

### Requirement: CSS Styling Conventions

The system SHALL follow consistent CSS styling patterns for Screens and Widgets, using a centralized external stylesheet, custom themes, and documented design tokens.

#### Scenario: App defines CSS_PATH for external stylesheet
- **GIVEN** the JdoApp class is defined
- **WHEN** CSS loading occurs
- **THEN** `CSS_PATH = "app.tcss"` points to the centralized stylesheet
- **AND** shared styles and utility classes are loaded from this file

#### Scenario: App registers custom themes in init
- **GIVEN** the JdoApp is instantiated
- **WHEN** `__init__` runs
- **THEN** custom JDO themes (jdo-dark and jdo-light) are registered via `register_theme()`
- **AND** theme colors override Textual defaults

#### Scenario: Theme toggle uses custom themes
- **GIVEN** user presses the dark mode toggle key
- **WHEN** `action_toggle_dark` executes
- **THEN** the app switches between `jdo-dark` and `jdo-light` themes
- **AND** all theme variables update accordingly

#### Scenario: Screen CSS scoped to screen class
- **GIVEN** a Screen has custom styles
- **WHEN** CSS is defined
- **THEN** styles are scoped using the Screen class name as selector (e.g., `MainScreen { ... }`)

#### Scenario: Widget CSS scoped to widget class
- **GIVEN** a Widget has custom styles
- **WHEN** CSS is defined
- **THEN** styles are scoped using the Widget class name as selector (e.g., `DataPanel { ... }`)

#### Scenario: DEFAULT_CSS for widget-specific overrides
- **GIVEN** a Screen or Widget needs styles beyond app.tcss
- **WHEN** the class is defined
- **THEN** widget-specific overrides are provided via `DEFAULT_CSS` class variable
- **AND** these styles have higher specificity than app.tcss

#### Scenario: Child widget styles use descendant selectors
- **GIVEN** a Screen needs to style child widgets
- **WHEN** CSS rules are written
- **THEN** descendant selectors are used (e.g., `MainScreen DataPanel { ... }`)

#### Scenario: Theme variables used for all colors
- **GIVEN** any component needs color styling
- **WHEN** colors are specified
- **THEN** theme variables are used (e.g., `$primary`, `$surface`, `$accent`)
- **AND** hardcoded hex colors are only used in theme definitions

#### Scenario: Border styles follow documented hierarchy
- **GIVEN** a component needs a border
- **WHEN** border is specified
- **THEN** the border style matches the element's importance level per tui-styling spec
- **AND** styles are: `round` for primary containers, `tall` for secondary, `double` for modals, `heavy` for focus

#### Scenario: Focus states use consistent patterns
- **GIVEN** an interactive widget receives focus
- **WHEN** focus styles are applied
- **THEN** border changes to `$accent` color
- **AND** optional `background-tint` provides subtle emphasis
