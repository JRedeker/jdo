# Change: Enhance Visual Output with Rich and prompt_toolkit Features

## Why

The CLI currently uses only ~30-40% of the Rich and prompt_toolkit libraries' visual capabilities. Users would benefit from animated spinners, command auto-completion, real-time status bars, and markdown rendering that these libraries provide out-of-the-box.

## Research Validation

Architectural research completed. Key findings:

| Feature | Status | Notes |
|---------|--------|-------|
| Spinner | ✅ Proceed | Must stop before Live streaming |
| Auto-completion | ✅ Simplify | Use WordCompleter (not Fuzzy) |
| Bottom toolbar | ✅ Proceed | Add count caching |
| Markdown rendering | ✅ Revise | Render during streaming |
| Rounded tables | ✅ Proceed | Trivial change |
| Tree view | 🔄 Defer | Over-engineered for current needs |
| Progress bar | 🔄 Defer | Existing text progress sufficient |

## What Changes

**Implementing (5 features):**
- **Spinner for AI thinking**: Replace static "Thinking..." text with animated `console.status()` spinner
- **Command auto-completion**: Add `WordCompleter` for slash commands using prompt_toolkit
- **Bottom toolbar**: Show cached stats (commitment count, triage queue size, pending draft indicator)
- **Markdown AI responses**: Render AI responses using `rich.markdown.Markdown` during streaming
- **Rounded table borders**: Use `box.ROUNDED` style for all Rich Tables

**Deferred (2 features):**
- **Tree view for hierarchy**: Current `/list` commands are sufficient; defer to future change
- **Progress bars for triage**: Existing text-based "Item X of Y" is sufficient

## Impact

- Affected specs:
  - `cli-interface` - Input features (auto-complete, toolbar, markdown streaming)
  - `output-formatting` - Visual components (spinner, rounded tables)
- Affected code:
  - `src/jdo/repl/loop.py` - Spinner, auto-complete, toolbar, markdown streaming
  - `src/jdo/repl/session.py` - Add cached count fields
  - `src/jdo/output/formatters.py` - Rounded tables (commitment list)
  - `src/jdo/output/goal.py` - Rounded tables (goal list)
  - `src/jdo/output/vision.py` - Rounded tables (vision list)
  - `src/jdo/output/milestone.py` - Rounded tables (milestone list)
  - `src/jdo/output/task.py` - Rounded tables (task list)
  - `src/jdo/output/integrity.py` - N/A (uses box=None intentionally for metrics)

## Research Sources

- Rich Status: https://rich.readthedocs.io/en/latest/reference/status.html
- prompt_toolkit completion: https://python-prompt-toolkit.readthedocs.io/en/master/pages/asking_for_input.html
- PydanticAI stream_markdown.py: https://github.com/pydantic/pydantic-ai/blob/main/examples/pydantic_ai_examples/stream_markdown.py
