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
- All source files must start with `from __future__ import annotations` (after docstring)
- Use `TYPE_CHECKING` blocks only for imports that would cause circular dependencies

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
- SQLModel/SQLAlchemy `.order_by()` with datetime columns (`Entry.created_at`)
- Rich `Text.append()` with certain argument types
- Textual reactive attributes

When pyrefly reports errors on working code, verify at runtime then document here.

## Pre-commit Hooks

Pre-commit hooks are configured to run automatically before each commit:

```bash
# Install hooks (one-time setup)
uv run pre-commit install

# Run manually on all files
uv run pre-commit run --all-files

# Skip hooks if needed (not recommended)
git commit --no-verify
```

Hooks configured:
- `trailing-whitespace` - Remove trailing whitespace
- `end-of-file-fixer` - Ensure files end with newline
- `check-yaml` - Validate YAML syntax
- `check-toml` - Validate TOML syntax
- `check-added-large-files` - Block files > 500KB
- `ruff` - Lint with auto-fix
- `ruff-format` - Format code
- `pyrefly` - Type checking on src/

## Database Migrations

Database migrations are managed with Alembic:

```bash
# Check current migration status
jdo db status

# Apply all pending migrations
jdo db upgrade

# Create a new migration (auto-detects model changes)
jdo db revision -m "Add new field to model"

# Rollback one migration
jdo db downgrade
```

**Workflow for schema changes**:
1. Modify SQLModel model in `src/jdo/models/`
2. Create migration: `jdo db revision -m "Description"`
3. Review generated migration in `migrations/versions/`
4. Apply migration: `jdo db upgrade`
5. Run tests: `uv run pytest`

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
├── auth/         # API key authentication, screens
├── commands/     # Command parser
├── config/       # Settings, paths
├── db/           # Engine, session, migrations
├── models/       # SQLModel entities
├── screens/      # Textual screens (HomeScreen, ChatScreen, etc.)
├── widgets/      # Textual widgets (NavSidebar, DataPanel, etc.)
└── app.py        # Main application

tests/
├── unit/         # Fast isolated tests
├── integration/  # Database tests
├── tui/          # Textual Pilot tests
└── uat/          # AI-driven UAT tests
```

## Navigation Architecture

The app uses a **NavSidebar** widget for navigation:

| Component | Purpose |
|-----------|---------|
| `NavSidebar` | Persistent left sidebar with navigation items |
| `HomeScreen` | Landing screen (being superseded by sidebar) |
| `ChatScreen` | Main chat interface with AI |
| `SettingsScreen` | Configuration and API key management |

### Key Navigation Bindings

| Key | Action |
|-----|--------|
| `[` | Toggle sidebar collapse |
| `1-9` | Quick-nav to sidebar items |
| `Tab` | Cycle focus between widgets |
| `Escape` | Context-aware back/cancel |
| `q` | Quit application |

### Adding Navigation Items

Edit `src/jdo/widgets/nav_sidebar.py`:

```python
NAV_ITEMS: list[NavItem | None] = [
    NavItem(id="chat", label="Chat", shortcut="n"),
    None,  # Separator
    NavItem(id="goals", label="Goals", shortcut="g"),
    # Add new items here...
]
```

Handle selections in `src/jdo/app.py`:

```python
def on_nav_sidebar_selected(self, message: NavSidebar.Selected) -> None:
    handlers = {
        "chat": self._nav_to_chat,
        "goals": self._nav_to_goals,
        # Add handlers here...
    }
    handler = handlers.get(message.item_id)
    if handler:
        handler()
```

## AI-Driven UAT Testing

The `tests/uat/` directory contains AI-driven User Acceptance Testing infrastructure.

### Running UAT Tests

```bash
# Run all UAT tests with mock AI (fast, free)
uv run pytest tests/uat/ -v

# Run only live AI tests (requires credentials)
uv run pytest tests/uat/ -v -m live_ai

# Skip live AI tests
uv run pytest tests/uat/ -v -m "not live_ai"
```

### UAT Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `models.py` | tests/uat/ | Pydantic models for actions, scenarios, results |
| `observer.py` | tests/uat/ | Captures UI state for AI consumption |
| `driver.py` | tests/uat/ | Orchestrates AI-driven test execution |
| `loader.py` | tests/uat/ | Loads scenarios from YAML files |
| `mocks.py` | tests/uat/ | Mock AI responses for deterministic tests |
| `scenarios/` | tests/uat/ | YAML scenario definitions |

### Writing New Scenarios

Create a YAML file in `tests/uat/scenarios/`:

```yaml
name: my_scenario
description: What this scenario tests
goal: |
  Natural language description of what the AI should accomplish.
  Be specific about the expected end state.

preconditions:
  - press:n   # Navigate to chat first

success_criteria:
  - screen:HomeScreen  # Must end on home screen
  - no_errors          # No step failures
  - completed          # AI signaled "done"

max_steps: 30
timeout_seconds: 90

tags:
  - smoke
  - my_feature
```

### Adding Mock Responses

For deterministic CI tests, add a mock in `tests/uat/mocks.py`:

```python
def create_my_scenario_mock() -> FunctionModel:
    step = 0
    def model_fn(messages, info):
        nonlocal step
        step += 1
        actions = [
            UATAction(action_type=ActionType.PRESS, target="n", reason="..."),
            UATAction(action_type=ActionType.DONE, reason="..."),
        ]
        action = actions[min(step - 1, len(actions) - 1)]
        return ModelResponse(parts=[TextPart(content=action.model_dump_json())])
    return FunctionModel(model_fn)

# Add to SCENARIO_MOCKS dict
SCENARIO_MOCKS["my_scenario"] = create_my_scenario_mock
```
