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

## Known Tool Limitations

### Pyrefly false positives (safe to ignore at runtime)
- SQLModel/SQLAlchemy column comparisons (`Commitment.status.in_([...])`)
- SQLModel/SQLAlchemy `.order_by()` with datetime columns (`Entry.created_at`)
- Rich `Text.append()` with certain argument types

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
| Rich | `/textualize/rich` | tables, panels, live display |
| prompt_toolkit | `/prompt-toolkit/python-prompt-toolkit` | REPL, history |
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
├── ai/           # AI agent, tools, extraction
├── auth/         # API key authentication
├── commands/     # Command parser and handlers
├── config/       # Settings, paths
├── db/           # Engine, session, migrations
├── models/       # SQLModel entities
├── output/       # Rich formatters for CLI output
├── repl/         # REPL loop and session management
└── cli.py        # CLI entry point

tests/
├── unit/         # Fast isolated tests
├── integration/  # Database tests
├── repl/         # REPL loop tests
└── output/       # Output formatter tests
```

## REPL Architecture

The app uses a conversational REPL with hybrid input handling:

| Component | Purpose |
|-----------|---------|
| `repl/loop.py` | Main REPL loop with prompt_toolkit |
| `repl/session.py` | Session state (history, context, drafts) |
| `output/formatters.py` | Rich formatters for entities |

### AI Agent Tools

The AI agent has access to tools for both querying and mutating data:

**Query Tools**:
- `query_current_commitments` - List active commitments
- `query_overdue_commitments` - List past-due commitments
- `query_user_time_context` - Check available hours and allocation
- `query_task_history` - Review past task completion patterns
- `query_commitment_time_rollup` - Get time breakdown for a commitment
- `query_integrity_with_context` - Get integrity metrics and coaching areas

**Mutation Tools**:
- `create_commitment` - Create a new commitment
- `add_task_to_commitment` - Add a task to an existing commitment

The AI agent automatically uses these tools when you describe work. For example:
- "I need to send the report to Sarah by Friday" → creates a commitment
- "Add a task to review the spec" → adds a task to an existing commitment

### Key Commands

| Command | Action |
|---------|--------|
| `/help` (`/h`) | Show available commands |
| `/list` (`/l`) | List commitments (default) |
| `/list goals` | List all goals |
| `/list visions` | List all visions |
| `/view <id>` (`/v`) | View entity details |
| `/1` - `/5` | Quick-select from last list |
| `/commit "..."` (`/c`) | Create a new commitment |
| `/complete <id>` | Mark commitment complete |
| `/review` | Review visions due for quarterly review |
| `exit` or `quit` | Exit the REPL |

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| F1 | Show help |
| F5 | Refresh dashboard |
| Ctrl+L | Clear screen, show dashboard |

### Adding Slash Commands

Commands are implemented as handlers in `src/jdo/commands/handlers/`.
Register new handlers in `src/jdo/commands/handlers/__init__.py`:

```python
# In _HANDLERS dict
CommandType.MYCOMMAND: MyCommandHandler,
```

## Testing

```bash
# Run all tests (sequential)
uv run pytest

# Run all tests in parallel (recommended)
uv run pytest -n auto

# Run specific categories
uv run pytest -m unit
uv run pytest -m integration

# Check coverage
uv run pytest --cov=src/jdo

# See full testing guide
# See docs/TESTING.md for best practices
```

## Testing Best Practices

1. **Isolation**: Use `db_session` fixture for database tests. It handles auto-rollback and connection cleanup.
2. **Parallelism**: Ensure tests are independent to support `pytest-xdist`. Avoid shared global state.
3. **Robustness**: Use `hypothesis` for functions with complex input space (dates, recurrence).
4. **Safety**: All tests have a 30s timeout. Use `@pytest.mark.timeout(N)` for slower tests.
5. **No Warnings**: Fix all resource warnings (unclosed DB connections) in fixtures.



