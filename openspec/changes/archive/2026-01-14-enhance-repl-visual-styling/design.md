# Design: Enhance REPL Visual Styling

## Context

Research validated prompt_toolkit capabilities but identified:
1. **Incorrect syntax in original spec**: Used Rich markup (`[cyan]>[/cyan]`) which doesn't work in prompt_toolkit
2. **Boxed input limitation**: `show_frame=True` creates fixed-width box, not suitable for dynamic terminal widths

This design document captures the researched best practices and architectural decisions.

## Goals / Non-Goals

**Goals:**
- Improve visual polish and discoverability
- Bold cyan prompt for strong visual distinction
- Dim keyboard shortcuts in toolbar for discoverability
- Keep implementation simple and maintainable

**Non-Goals:**
- Full-screen TUI-style input blocks (requires custom Application, too complex)
- Boxed input frame (fixed-width limitation makes it unsuitable)

## Decisions

### Decision 1: Use prompt_toolkit's native HTML styling for toolbar

**Why:** prompt_toolkit has comprehensive formatting support via `HTML()`, `FormattedText`, and style dicts.

**Implementation:**
```python
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

style = Style.from_dict({
    "bottom-toolbar": "fg:ansibrightblack noreverse",  # Theme-adaptive
})

def get_toolbar_text() -> HTML:
    return HTML('<b>F1</b>=Help  <b>F5</b>=Refresh  <b>/c</b>=commit  <b>/l</b>=list  <b>/v</b>=view')
```

**Sources:**
- https://python-prompt-toolkit.readthedocs.io/en/stable/pages/asking_for_input.html#adding-a-bottom-toolbar

### Decision 2: Use HTML for colored prompt (NOT Rich markup)

**Why:** Rich and prompt_toolkit are separate rendering systems with incompatible syntax.

**Correct:**
```python
message=HTML('<ansicyan bold>></ansicyan> ')
```

**Wrong (what spec originally said):**
```python
message="[cyan]>[/cyan] "  # This would display literally as text
```

**Sources:**
- https://python-prompt-toolkit.readthedocs.io/en/stable/pages/printing_text.html

### Decision 3: Skip boxed input frame (technical limitation)

**Research findings:** `show_frame=True` creates a fixed-width box that doesn't adapt to terminal width.

To get a dynamic full-width frame would require:
- Switching from `PromptSession` to custom `Application`
- Building a custom `Layout` with `Frame` widget
- Significantly more complex code for a cosmetic feature

**Chosen approach:** Bold cyan prompt + spacing
- Industry standard (Starship, IPython, ptpython)
- Works at any terminal width
- Zero edge cases

**Sources:**
- prompt_toolkit source: `PromptSession._create_layout()` - `show_frame` is simplified wrapper
- Frame widget requires custom Application for full control

## Risks / Trade-offs

| Approach | Pros | Cons |
|----------|------|------|
| Bold cyan prompt + spacing | Simple, industry standard, no edge cases | Less visually distinctive than box |
| Boxed input (`show_frame=True`) | Visually unique | Fixed width, doesn't adapt to terminal |
| Custom Application with Frame | Full control, dynamic width | Major refactor, high complexity |

**Chosen:** Bold cyan prompt + spacing (best balance of polish and simplicity)

### Decision 4: Use theme-adaptive ANSI colors (not hex codes)

**Why:** Hex codes like `#888888` are fixed colors that don't adapt to the user's terminal theme (light/dark mode, custom palettes). ANSI color names let the terminal define the actual RGB values.

**Color tiers:**
| Type | Example | Theme-Adaptive? |
|------|---------|-----------------|
| ANSI 16 names | `ansicyan`, `ansibrightblack` | ✅ Yes |
| Hex codes | `#888888`, `#1a1a1a` | ❌ No |
| 256 palette | `skyblue`, `color(208)` | ❌ No |

**Implementation:**
```python
# Good - adapts to terminal theme
"fg:ansibrightblack"  # User's "bright black" (usually gray)
"fg:ansicyan"         # User's "cyan"

# Bad - fixed color, ignores theme
"fg:#888888"          # Always this exact gray
```

**Sources:**
- ANSI color codes: colors 0-15 are defined by the terminal emulator
- vim/tmux/starship all use ANSI names for theme compatibility

## Open Questions

None - research resolved the key questions about implementation approach.
