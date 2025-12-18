# Change: Add Developer Infrastructure

## Why

The JDO application lacks essential infrastructure for production-quality development:
1. **No structured logging** - Debugging issues in production is difficult without consistent, queryable logs
2. **No custom exception hierarchy** - Error handling is ad-hoc without clear categorization for recovery vs fatal errors
3. **No pre-commit hooks** - Despite strict linting rules, nothing enforces them before commits
4. **Incomplete test coverage** - Missing tests for widgets, config edge cases, and no performance tests
5. **No observability/telemetry** - AI calls, errors, and performance cannot be monitored in production
6. **No database migration tool** - Schema changes require manual intervention; no versioned migrations

## What Changes

### New Capabilities

- **logging**: Structured logging using Loguru with file rotation, JSON output for production, and stdlib interception
- **error-handling**: Custom exception hierarchy with recovery hints, organized by domain (AI, database, TUI, config)
- **dev-tooling**: Pre-commit hooks configuration for ruff, pyrefly, and commit message validation
- **test-coverage**: Test organization patterns, coverage targets, and widget/integration test requirements
- **observability**: Sentry integration for error tracking, performance monitoring, and AI call tracing
- **database-migrations**: Alembic integration with SQLModel for versioned schema migrations

### Modified Capabilities

- **app-config**: Add Sentry DSN and logging configuration settings
- **data-persistence**: Reference migration system for schema changes

## Impact

- Affected specs: `app-config`, `data-persistence` (modified); 6 new capability specs
- Affected code: New modules in `src/jdo/`, config changes in `pyproject.toml`, new `.pre-commit-config.yaml`
- Dependencies: `loguru`, `sentry-sdk`, `alembic`, `pre-commit` (dev)
- Breaking changes: None - all additions are backwards compatible
