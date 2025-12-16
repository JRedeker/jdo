<!-- OPENSPEC:START -->
# OpenSpec Instructions
These instructions are for AI assistants working in this project.
Always open `@/openspec/AGENTS.md` when the request mentions planning, proposals, or architecture changes.
<!-- OPENSPEC:END -->

# JDO Agent Guide

**Read `pyproject.toml` before writing code** - it contains strict lint/type rules and explains every exception.

## Commands (run after EVERY code change)

```bash
# Quick check (run this after every file edit)
uv run ruff check --fix src/ tests/ && uv run ruff format src/ tests/

# Full validation (run before committing)
uv run ruff check src/ tests/      # Lint (must pass, 0 errors)
uv run ruff format src/ tests/     # Format
uvx pyrefly check src/             # Type check (errors must be fixed or documented)
uv run pytest                      # Tests (must pass)
```

## Strict Rules

### No inline suppressions without justification
- **NO** `# noqa` comments - configure in `pyproject.toml` per-file-ignores instead
- **NO** `# type: ignore` comments - fix the type or document in pyrefly config
- If you must suppress, add explanation to `pyproject.toml` with the rule

### Type annotations required
- All function parameters and returns must have type hints
- Use `ClassVar` for mutable class attributes
- Use `Iterator[Widget]` not bare generators for Textual compose methods

### Exception handling
- Never use bare `except:` - always catch specific exceptions
- Assign exception messages to variables before raising (EM101/EM102 rules)
```python
# Bad
raise ValueError("Something went wrong")

# Good  
msg = "Something went wrong"
raise ValueError(msg)
```

## Code Style

| Rule | Standard |
|------|----------|
| Imports | stdlib, third-party, then `jdo` (isort enforced) |
| Types | All functions annotated; `ClassVar` for mutable class attrs |
| Naming | `snake_case` functions/vars, `PascalCase` classes, `UPPER_CASE` constants |
| Line length | 100 chars max |
| Quotes | Double quotes |
| Docstrings | Google convention |

## Textual Widget Conventions

```python
from typing import ClassVar
from collections.abc import Iterator
from textual.binding import Binding
from textual.widget import Widget

class MyWidget(Widget):
    # ClassVar required for mutable class attributes
    BINDINGS: ClassVar[list[Binding]] = [
        Binding("enter", "submit", "Submit"),
    ]
    
    # Proper return type for compose
    def compose(self) -> Iterator[Widget]:
        yield SomeChild()
```

## Known Tool Limitations

### Pyrefly false positives (safe to ignore at runtime)
- SQLModel/SQLAlchemy column comparisons (`Commitment.status.in_([...])`)
- Rich `Text.append()` with certain argument types
- Textual reactive attributes

When pyrefly reports errors on working code, verify at runtime then document here.

## Context7 Docs (check before coding)

| Tech | ID | Topics |
|------|----|----- ---|
| Textual | `/textualize/textual` | widgets, screens, bindings |
| Pydantic | `/websites/pydantic_dev` | models, validators |
| PydanticAI | `/pydantic/pydantic-ai` | agents, tools |
| pytest | `/pytest-dev/pytest` | fixtures, markers |
| SQLModel | `/fastapi/sqlmodel` | models, queries |

## TDD Workflow

1. **Red**: Write failing test first
2. **Green**: Implement minimal code to pass
3. **Refactor**: Clean up, run lint/format/typecheck
4. **Verify**: `uv run pytest path/to/test.py -v`

## File Locations

```
src/jdo/
├── ai/           # AI agent, tools
├── auth/         # OAuth, API keys, screens
├── commands/     # Command parser
├── config/       # Settings, paths
├── db/           # Engine, session, migrations
├── models/       # SQLModel entities
├── widgets/      # Textual widgets
└── app.py        # Main application

tests/
├── unit/         # Fast isolated tests
├── integration/  # Database tests
└── tui/          # Textual Pilot tests
```
