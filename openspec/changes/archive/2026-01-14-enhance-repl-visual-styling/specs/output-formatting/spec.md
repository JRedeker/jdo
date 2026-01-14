## ADDED Requirements

### Requirement: Keyboard Shortcut Toolbar

The system SHALL display keyboard shortcuts in the bottom toolbar instead of statistics.

<!-- Research: prompt_toolkit supports HTML, FormattedText for styled toolbars -->
<!-- Source: https://python-prompt-toolkit.readthedocs.io/en/stable/pages/asking_for_input.html#adding-a-bottom-toolbar -->

#### Scenario: Display keyboard shortcuts in toolbar
- **GIVEN** the REPL is running
- **WHEN** the bottom toolbar is displayed
- **THEN** toolbar shows: `F1=Help  F5=Refresh  /c=commit  /l=list  /v=view`
- **AND** shortcuts are separated by double spaces for readability
- **AND** toolbar uses dim styling (`fg:ansibrightblack noreverse`) to not distract from main content
- **AND** colors adapt to user's terminal theme (uses ANSI color names, not hex codes)
- **AND** key names are bold for scannability

#### Scenario: Toolbar remains static
- **GIVEN** the REPL is running
- **WHEN** user navigates or views entities
- **THEN** toolbar content remains constant (shows shortcuts, not dynamic stats)

#### Scenario: Toolbar graceful degradation on non-color terminal
- **GIVEN** terminal does not support ANSI colors (e.g., dumb terminal, CI environment)
- **WHEN** bottom toolbar is displayed
- **THEN** toolbar shows plain text shortcuts without styling
- **AND** bold tags are stripped or ignored gracefully
- **AND** no error or exception is raised

> **Note**: Terminal compatibility is handled by prompt_toolkit's built-in detection.
> No explicit fallback code is needed; prompt_toolkit degrades automatically.

### Requirement: Visual Prompt Styling

The system SHALL provide a visually distinct input prompt area with spacing and color accent.

<!-- Research: prompt_toolkit show_frame=True creates fixed-width box, not suitable -->
<!-- Full-width frame requires custom Application - too complex for cosmetic change -->
<!-- Industry standard (Starship, IPython, ptpython): colored prompt + spacing -->

#### Scenario: Spacing before prompt
- **GIVEN** the REPL is ready for input
- **WHEN** prompt is displayed after dashboard or command output
- **THEN** one blank line appears above the prompt for visual separation

#### Scenario: Colored prompt indicator
- **GIVEN** the REPL is ready for input
- **WHEN** prompt is displayed
- **THEN** prompt uses cyan color via prompt_toolkit HTML: `HTML('<ansicyan><b>></b></ansicyan> ')`
- **AND** the `>` character is bold cyan for strong visual distinction
- **AND** the prompt indicator stands out from surrounding text

<!-- Note: prompt_toolkit HTML uses nested tags, not attributes like `<ansicyan bold>` -->
<!-- Correct: <ansicyan><b>text</b></ansicyan>, Wrong: <ansicyan bold>text</ansicyan> -->

<!-- Note: Rich markup [cyan]...[/cyan] does NOT work in prompt_toolkit -->
<!-- prompt_toolkit uses its own HTML syntax: <ansicyan>, <ansired>, etc. -->
<!-- Source: https://python-prompt-toolkit.readthedocs.io/en/stable/pages/printing_text.html -->

### Requirement: prompt_toolkit Styling Implementation

The system SHALL use prompt_toolkit's native styling system for all input-related formatting.

<!-- Research: Rich and prompt_toolkit are separate rendering systems -->
<!-- Rich for output (tables, panels), prompt_toolkit for input (prompts, toolbars) -->

#### Scenario: Correct styling syntax
- **GIVEN** prompt or toolbar needs color styling
- **WHEN** style is applied
- **THEN** uses prompt_toolkit HTML format: `HTML('<ansicyan>text</ansicyan>')`
- **AND** NOT Rich markup format: `[cyan]text[/cyan]` (which would display as literal text)

#### Scenario: Style via Style.from_dict with theme-adaptive colors
- **GIVEN** consistent styling is needed across prompt and toolbar
- **WHEN** PromptSession is created
- **THEN** a Style object is passed using ANSI color names (NOT hex codes):
  ```python
  Style.from_dict({
      "bottom-toolbar": "fg:ansibrightblack noreverse",
  })
  ```
- **AND** toolbar uses `noreverse` to disable default bright/inverted styling
- **AND** colors use ANSI names (`ansicyan`, `ansibrightblack`) that adapt to terminal theme
- **AND** hex codes (`#888888`) are avoided to ensure light/dark theme compatibility

### Requirement: Consistent Theme-Adaptive Colors

The system SHALL use ANSI color names consistently, matching the existing JDO codebase pattern.

<!-- Research: JDO already uses theme-adaptive colors throughout (green, yellow, red, cyan, dim, bold) -->
<!-- No hex codes exist in the current codebase - this change should maintain that pattern -->

#### Scenario: Match existing color conventions
- **GIVEN** new styling is being added to prompt_toolkit components
- **WHEN** colors are specified
- **THEN** uses the same ANSI color names as existing Rich output (`cyan`, `green`, `yellow`, `red`, `dim`, `bold`)
- **AND** prompt_toolkit equivalents are used (`ansicyan`, `ansigreen`, `ansiyellow`, `ansired`)
- **AND** no hex codes (`#rrggbb`) are introduced
- **AND** colors adapt automatically to user's terminal theme (light/dark mode)

#### Scenario: Color mapping between Rich and prompt_toolkit
- **GIVEN** JDO uses Rich for output and prompt_toolkit for input
- **WHEN** similar styling is needed in both systems
- **THEN** equivalent colors are used:
  | Rich (output) | prompt_toolkit (input) |
  |---------------|------------------------|
  | `cyan` | `ansicyan` |
  | `dim` | `ansibrightblack` or `noreverse` |
  | `bold` | `bold` |
  | `green` | `ansigreen` |

## Cross-Cutting Concerns

> **Note**: Terminal compatibility is N/A for explicit handling. prompt_toolkit automatically
> detects terminal capabilities and degrades styling gracefully. No additional fallback code needed.

> **Note**: Logging/Observability is N/A for this change. Styling is purely cosmetic with no
> failure modes that require logging. prompt_toolkit handles terminal detection internally.

> **Note**: Configuration is N/A for this change. No user-configurable styling options are
> introduced. Future enhancement could add a `--no-color` flag if needed.

## Reference: Available ANSI Colors and Styles

### 16 ANSI Colors (Theme-Adaptive)

| Color | Rich | prompt_toolkit | Use For |
|-------|------|----------------|---------|
| Black | `black` | `ansiblack` | - |
| Red | `red` | `ansired` | Errors, overdue, warnings |
| Green | `green` | `ansigreen` | Success, completed |
| Yellow | `yellow` | `ansiyellow` | At-risk, caution |
| Blue | `blue` | `ansiblue` | Info, in-progress |
| Magenta | `magenta` | `ansimagenta` | Visions, special |
| Cyan | `cyan` | `ansicyan` | Highlights, prompts |
| White | `white` | `ansigray` | - |
| Bright Black | `bright_black` | `ansibrightblack` | Dim/secondary text |
| Bright Red | `bright_red` | `ansibrightred` | Emphasis errors |
| Bright Green | `bright_green` | `ansibrightgreen` | Emphasis success |
| Bright Yellow | `bright_yellow` | `ansibrightyellow` | Emphasis warnings |
| Bright Blue | `bright_blue` | `ansibrightblue` | Emphasis info |
| Bright Magenta | `bright_magenta` | `ansibrightmagenta` | - |
| Bright Cyan | `bright_cyan` | `ansibrightcyan` | Emphasis highlights |
| Bright White | `bright_white` | `ansiwhite` | - |

### Text Styles

| Style | Rich | prompt_toolkit | Terminal Support |
|-------|------|----------------|------------------|
| Bold | `bold` | `bold` | Universal |
| Dim | `dim` | - | Most terminals |
| Italic | `italic` | `italic` | Most (not Windows cmd) |
| Underline | `underline` | `underline` | Universal |
| Reverse | `reverse` | `reverse` | Universal |
| Strikethrough | `strike` | - | Most terminals |
| Blink | `blink` | `blink` | Limited |

### Safe Cross-Terminal Subset

For maximum compatibility, prefer:
- **Colors**: All 16 ANSI colors
- **Styles**: `bold`, `underline`, `reverse`
- **Caution**: `dim`, `italic`, `strike` (most terminals)
- **Avoid**: `blink`, `overline`, `frame` (limited support)

### Current JDO Color Conventions

| Semantic | Color | Used For |
|----------|-------|----------|
| Error | `red` | Errors, overdue items |
| Warning | `yellow` | At-risk, caution messages |
| Success | `green` | Completed, confirmations |
| Info | `blue` | In-progress status |
| Accent | `cyan` | Highlights, prompts, borders |
| Special | `magenta` | Visions, review notices |
| Secondary | `dim` / `bright_black` | Hints, labels, less important text |
| Emphasis | `bold` | Key names, important values |
