## 1. Logging Infrastructure (Loguru)

- [ ] 1.1 Add `loguru` to dependencies in `pyproject.toml`
- [ ] 1.2 Create `src/jdo/logging.py` with `configure_logging()` function
- [ ] 1.3 Add logging configuration settings to `JDOSettings` (`log_level`, `log_file_path`)
- [ ] 1.4 Implement stdlib logging interception via `InterceptHandler`
- [ ] 1.5 Configure logging on app startup in `app.py`
- [ ] 1.6 Add debug logging to AI agent tool calls in `src/jdo/ai/tools.py`
- [ ] 1.7 Add debug logging to database session in `src/jdo/db/session.py`
- [ ] 1.8 Add debug logging to screen transitions in `src/jdo/app.py`
- [ ] 1.9 Write unit tests for logging configuration in `tests/unit/test_logging.py`

## 2. Error Handling (Exception Hierarchy)

- [ ] 2.1 Create `src/jdo/exceptions.py` with base `JDOError` class
- [ ] 2.2 Add `ConfigError` exception class
- [ ] 2.3 Add `DatabaseError` and `MigrationError` exception classes
- [ ] 2.4 Add `AIError`, `ProviderError`, `ExtractionError` exception classes
- [ ] 2.5 Add `AuthError` exception class
- [ ] 2.6 Add `TUIError` exception class
- [ ] 2.7 Replace existing exception raises with custom exceptions (AI module)
- [ ] 2.8 Replace existing exception raises with custom exceptions (auth module)
- [ ] 2.9 Write unit tests for exception hierarchy in `tests/unit/test_exceptions.py`

## 3. Pre-commit Hooks (Dev Tooling)

- [ ] 3.1 Add `pre-commit` to dev dependencies in `pyproject.toml`
- [ ] 3.2 Create `.pre-commit-config.yaml` with ruff hooks
- [ ] 3.3 Add pyrefly type checking hook to pre-commit config
- [ ] 3.4 Add standard hooks (trailing whitespace, end-of-file, yaml check)
- [ ] 3.5 Add large file check hook (500KB limit)
- [ ] 3.6 Document pre-commit setup in `AGENTS.md`
- [ ] 3.7 Run `pre-commit run --all-files` to verify configuration

## 4. Test Coverage Improvements

- [ ] 4.1 Update pytest coverage threshold to 80% in `pyproject.toml`
- [ ] 4.2 Add per-module coverage requirements for critical paths
- [ ] 4.3 Create `tests/tui/test_widgets/` directory structure
- [ ] 4.4 Write Pilot tests for `ChatContainer` widget
- [ ] 4.5 Write Pilot tests for `ChatMessage` widget
- [ ] 4.6 Write Pilot tests for `DataPanel` widget
- [ ] 4.7 Write Pilot tests for `HierarchyView` widget
- [ ] 4.8 Add missing unit tests for `src/jdo/config/settings.py` edge cases
- [ ] 4.9 Add test markers documentation to `tests/conftest.py`

## 5. Observability (Sentry)

- [ ] 5.1 Add `sentry-sdk` to dependencies in `pyproject.toml`
- [ ] 5.2 Add Sentry configuration settings to `JDOSettings` (`sentry_dsn`, `sentry_traces_sample_rate`, `environment`)
- [ ] 5.3 Create `src/jdo/observability.py` with `init_sentry()` function
- [ ] 5.4 Initialize Sentry on app startup in `app.py` (conditional on DSN)
- [ ] 5.5 Add Loguru sink for Sentry error forwarding
- [ ] 5.6 Add Sentry span instrumentation to AI agent calls
- [ ] 5.7 Add JDOError context enrichment for Sentry events
- [ ] 5.8 Write unit tests for Sentry initialization in `tests/unit/test_observability.py`
- [ ] 5.9 Document Sentry setup in README or dedicated docs

## 6. Database Migrations (Alembic)

- [ ] 6.1 Add `alembic` to dependencies in `pyproject.toml`
- [ ] 6.2 Create `migrations/` directory structure
- [ ] 6.3 Create `migrations/alembic.ini` configuration
- [ ] 6.4 Create `migrations/env.py` configured for SQLModel
- [ ] 6.5 Create `migrations/script.py.mako` template
- [ ] 6.6 Enable SQLite batch mode in Alembic configuration
- [ ] 6.7 Generate initial migration from current schema
- [ ] 6.8 Add CLI commands for migration management (`jdo db status/upgrade/revision`)
- [ ] 6.9 Write integration tests for migration operations in `tests/integration/db/test_migrations.py`
- [ ] 6.10 Document migration workflow in `AGENTS.md`

## 7. Integration & Documentation

- [ ] 7.1 Update `AGENTS.md` with new tooling commands
- [ ] 7.2 Update `pyproject.toml` ruff config for new modules
- [ ] 7.3 Add `.env.example` with all new configuration options
- [ ] 7.4 Run full test suite and fix any regressions
- [ ] 7.5 Run linting and type checking on all new code
