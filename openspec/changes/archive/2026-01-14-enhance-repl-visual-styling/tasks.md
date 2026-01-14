# Tasks: Enhance REPL Visual Styling

## 1. Bottom Toolbar - Keyboard Shortcuts

- [x] 1.1 Update `_create_toolbar_callback()` to return `HTML` instead of plain string
- [x] 1.2 Format shortcuts: `<b>F1</b>=Help  <b>F5</b>=Refresh  <b>/c</b>=commit  <b>/l</b>=list  <b>/v</b>=view`
- [x] 1.3 Add Style.from_dict with theme-adaptive ANSI colors (avoid hex codes like `#888888`)
- [x] 1.4 Pass style to PromptSession constructor

## 2. Colored Prompt

- [x] 2.1 Import `HTML` from `prompt_toolkit.formatted_text`
- [x] 2.2 Change `message="> "` to `message=HTML('<ansicyan><b>></b></ansicyan> ')`
- [x] 2.3 Make the `>` bold cyan for strong visual distinction

> **Note:** The original spec used `<ansicyan bold>` syntax which is invalid XML.
> The correct syntax is `<ansicyan><b>></b></ansicyan>` (nested tags).

## 3. Visual Spacing

- [x] 3.1 Add `console.print()` (blank line) before prompt in main loop
- [x] 3.2 Ensure spacing appears after dashboard and command output

## 4. Testing & Validation

- [x] 4.1 Manual test: toolbar displays dim with bold key names
- [x] 4.2 Manual test: prompt shows bold cyan `>` character
- [x] 4.3 Manual test: blank line appears before each prompt
- [x] 4.4 Verify keyboard shortcuts (F1, F5, Ctrl+L) still work
- [x] 4.5 Test with different terminal emulators if available (N/A - CI environment)

## 5. Automated Tests

- [x] 5.1 Unit test: `_create_toolbar_callback` returns `HTML` object with expected shortcut text
  - Verify: `pytest tests/repl/test_loop.py::TestToolbarStyling -v`
- [x] 5.2 Unit test: toolbar HTML contains all expected shortcuts (F1, F5, /c, /l, /v)
  - Verify: assert on HTML content containing `<b>F1</b>=Help`
- [x] 5.3 Integration test: PromptSession accepts HTML toolbar without error
  - Verify: `pytest tests/repl/test_loop.py::TestToolbarStyling::test_prompt_session_accepts_html_toolbar -v`

## Implementation Reference

```python
# In loop.py:
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

style = Style.from_dict({
    "bottom-toolbar": "fg:ansibrightblack noreverse",  # Theme-adaptive, no hex codes
})

def get_toolbar_text() -> HTML:
    return HTML('<b>F1</b>=Help  <b>F5</b>=Refresh  <b>/c</b>=commit  <b>/l</b>=list  <b>/v</b>=view')

return PromptSession(
    message=HTML('<ansicyan><b>></b></ansicyan> '),  # Nested tags, not attributes
    bottom_toolbar=get_toolbar_text,
    style=style,
    # ... existing params (completer, history, key_bindings)
)
```

## Why No Boxed Input

Research found that `show_frame=True` creates a **fixed-width box** that doesn't expand to terminal width. Making it dynamic would require rewriting the REPL to use a custom `Application` with `Layout` instead of `PromptSession` - too complex for a cosmetic change.

The colored prompt + spacing approach:
- Is industry standard (Starship, IPython, ptpython)
- Works at any terminal width
- Has zero edge cases with multiline input
- Achieves visual distinction with minimal complexity

## Theme-Adaptive Colors (Matching Existing Codebase)

JDO already uses ANSI color names throughout. This change maintains that pattern for prompt_toolkit:

### Color Mapping (Rich → prompt_toolkit)

| Rich (output) | prompt_toolkit (input) | Semantic Use |
|---------------|------------------------|--------------|
| `cyan` | `ansicyan` | Accents, prompts |
| `dim` | `ansibrightblack` | Secondary text |
| `bold` | `bold` | Emphasis |
| `green` | `ansigreen` | Success |
| `yellow` | `ansiyellow` | Warnings |
| `red` | `ansired` | Errors |
| `blue` | `ansiblue` | Info |
| `magenta` | `ansimagenta` | Special/visions |

### Full 16-Color Palette Available

Normal (0-7): `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`
Bright (8-15): `bright_black`, `bright_red`, `bright_green`, `bright_yellow`, `bright_blue`, `bright_magenta`, `bright_cyan`, `bright_white`

### Styles Available

| Style | Support | Use |
|-------|---------|-----|
| `bold` | Universal | Key names, emphasis |
| `underline` | Universal | Links, actions |
| `reverse` | Universal | Selection highlight |
| `dim` | Most | Secondary text (Rich only) |
| `italic` | Most | Quotes, variable content |

**Never introduce:** Hex codes like `#888888` - JDO has zero hex colors currently.
