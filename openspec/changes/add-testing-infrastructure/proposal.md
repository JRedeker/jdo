# Change: Add Testing Infrastructure

## Why

JDO is a greenfield project with 6 pending proposals that will add significant functionality: domain models, data persistence, AI integration, OAuth authentication, and a conversational TUI. Implementing comprehensive testing infrastructure BEFORE these features ensures:

1. **TDD workflow**: Tests written alongside code from day one
2. **Regression prevention**: Catch bugs as new features are added
3. **Confidence in refactoring**: Safe to improve code without fear
4. **Documentation**: Tests serve as executable specifications

## What Changes

### New Capabilities
- **Testing Infrastructure**: Core pytest configuration, fixtures, and test organization

### Test Coverage Areas
- **Model Testing**: SQLModel validation, relationships, JSON columns
- **Database Testing**: In-memory SQLite fixtures, CRUD operations, transactions
- **Configuration Testing**: pydantic-settings, environment variable handling
- **TUI Testing**: Textual Pilot-based UI testing, key bindings, screen navigation
- **AI Integration Testing**: PydanticAI agent mocking, tool testing
- **HTTP Mocking**: OAuth flow testing with pytest-httpx

### New Dependencies (dev only)
- `pytest-textual-snapshot` - Visual regression testing for TUI
- `pytest-httpx` - HTTP request mocking for OAuth/API tests
- `pytest-cov` - Code coverage reporting

### Test Organization
```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── models/              # SQLModel validation tests
│   ├── config/              # Settings tests
│   └── paths/               # platformdirs tests
├── integration/
│   ├── db/                  # Database CRUD tests
│   └── auth/                # OAuth flow tests
└── tui/
    ├── snapshots/           # Visual regression baselines
    └── test_*.py            # Pilot-based TUI tests
```

## Impact

- **Affected specs**: All pending proposals (provides testing patterns for each)
- **Affected code**: `tests/` directory, `pyproject.toml` (dev dependencies)
- **Dependencies**: Cross-references `refactor-core-libraries` for SQLModel/pydantic-settings patterns

## Alignment with Existing Proposals

| Proposal | Testing Strategy |
|----------|------------------|
| `refactor-core-libraries` | In-memory SQLite fixture, settings fixture with env override |
| `add-core-domain-models` | Model validation tests, relationship tests, JSON column tests |
| `add-provider-auth` | pytest-httpx for OAuth token exchange, credential storage tests |
| `add-conversational-tui` | Textual Pilot for chat UI, snapshot tests for visual regression |
| `add-recurring-commitments` | Date calculation edge cases, recurrence pattern tests |
| `update-goal-vision-focus` | Status transition tests, review command tests |
