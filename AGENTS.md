<!-- OPENSPEC:START -->
# OpenSpec Instructions
These instructions are for AI assistants working in this project.
Always open `@/openspec/AGENTS.md` when the request mentions planning, proposals, or architecture changes.
<!-- OPENSPEC:END -->

# JDO Agent Guide

## Commands
```bash
uv run ruff check src/ tests/      # Lint
uv run ruff format src/ tests/     # Format
uvx pyrefly check                  # Type check (strict)
uv run pytest                      # Run all tests
uv run pytest tests/test_foo.py::test_bar -v  # Single test
```

## Code Style
- **Imports**: stdlib, third-party, then `jdo` (enforced by isort)
- **Types**: All functions must have type annotations; use `ClassVar` for mutable class attrs
- **Naming**: `snake_case` functions/vars, `PascalCase` classes, `UPPER_CASE` constants
- **Line length**: 100 chars; double quotes; Google docstring convention
- **Errors**: Prefer explicit exceptions; no bare `except:`; use Pydantic for validation
- **Textual**: Inherit from `App[ReturnType]`; use `Binding` for key bindings

## Context7 Docs (check before coding)
| Tech | ID | Topics |
|------|----|--------|
| Textual | `/textualize/textual` | widgets, screens, bindings |
| Pydantic | `/websites/pydantic_dev` | models, validators |
| pytest | `/pytest-dev/pytest` | fixtures, markers |
