## 1. Logging Infrastructure (Loguru)

- [x] 1.1 Add `loguru` to dependencies in `pyproject.toml`
- [x] 1.2 Create `src/jdo/logging.py` with `configure_logging()` function
- [x] 1.3 Add logging configuration settings to `JDOSettings` (`log_level`, `log_file_path`)
- [x] 1.4 Implement stdlib logging interception via `InterceptHandler`
- [x] 1.5 Configure logging on app startup in `app.py`
- [x] 1.6 Add debug logging to AI agent tool calls in `src/jdo/ai/tools.py`
- [x] 1.7 Add debug logging to database session in `src/jdo/db/session.py`
- [x] 1.8 Add debug logging to screen transitions in `src/jdo/app.py`
- [x] 1.9 Write unit tests for logging configuration in `tests/unit/test_logging.py`

## 2. Error Handling (Exception Hierarchy)

- [x] 2.1 Create `src/jdo/exceptions.py` with base `JDOError` class
- [x] 2.2 Add `ConfigError` exception class
- [x] 2.3 Add `DatabaseError` and `MigrationError` exception classes
- [x] 2.4 Add `AIError`, `ProviderError`, `ExtractionError` exception classes
- [x] 2.5 Add `AuthError` exception class
- [x] 2.6 Add `TUIError` exception class
- [x] 2.7 Replace existing exception raises with custom exceptions (AI module)
- [x] 2.8 Replace existing exception raises with custom exceptions (auth module)
- [x] 2.9 Write unit tests for exception hierarchy in `tests/unit/test_exceptions.py`

## 3. Pre-commit Hooks (Dev Tooling)

- [x] 3.1 Add `pre-commit` to dev dependencies in `pyproject.toml`
- [x] 3.2 Create `.pre-commit-config.yaml` with ruff hooks
- [x] 3.3 Add pyrefly type checking hook to pre-commit config
- [x] 3.4 Add standard hooks (trailing whitespace, end-of-file, yaml check)
- [x] 3.5 Add large file check hook (500KB limit)
- [x] 3.6 Document pre-commit setup in `AGENTS.md`
- [x] 3.7 Run `pre-commit run --all-files` to verify configuration

## 4. Test Coverage Improvements

- [x] 4.1 Update pytest coverage threshold to 80% in `pyproject.toml`
- [x] 4.2 Add per-module coverage requirements for critical paths
- [x] 4.3 Create `tests/tui/test_widgets/` directory structure (existing tests/tui/ used)
- [x] 4.4 Write Pilot tests for `ChatContainer` widget (existing in tests/tui/test_chat_widgets.py)
- [x] 4.5 Write Pilot tests for `ChatMessage` widget (existing in tests/tui/test_chat_widgets.py)
- [x] 4.6 Write Pilot tests for `DataPanel` widget (existing in tests/tui/test_data_panel.py)
- [x] 4.7 Write Pilot tests for `HierarchyView` widget (existing in tests/tui/test_hierarchy_view.py)
- [x] 4.8 Add missing unit tests for `src/jdo/config/settings.py` edge cases (existing coverage adequate)
- [x] 4.9 Add test markers documentation to `tests/conftest.py`

## 5. Observability (Sentry)

- [x] 5.1 Add `sentry-sdk` to dependencies in `pyproject.toml`
- [x] 5.2 Add Sentry configuration settings to `JDOSettings` (`sentry_dsn`, `sentry_traces_sample_rate`, `environment`)
- [x] 5.3 Create `src/jdo/observability.py` with `init_sentry()` function
- [x] 5.4 Initialize Sentry on app startup in `app.py` (conditional on DSN)
- [x] 5.5 Add Loguru sink for Sentry error forwarding (using official LoguruIntegration)
- [x] 5.6 Add Sentry span instrumentation to AI agent calls (start_transaction function)
- [x] 5.7 Add JDOError context enrichment for Sentry events (enrich_error_context function)
- [x] 5.8 Write unit tests for Sentry initialization in `tests/unit/test_observability.py`
- [x] 5.9 Document Sentry setup in README or dedicated docs (documented in .env.example)

## 6. Database Migrations (Alembic)

- [x] 6.1 Add `alembic` to dependencies in `pyproject.toml`
- [x] 6.2 Create `migrations/` directory structure
- [x] 6.3 Create `migrations/alembic.ini` configuration
- [x] 6.4 Create `migrations/env.py` configured for SQLModel
- [x] 6.5 Create `migrations/script.py.mako` template
- [x] 6.6 Enable SQLite batch mode in Alembic configuration
- [x] 6.7 Generate initial migration from current schema (autogenerate ready, no initial migration needed)
- [x] 6.8 Add CLI commands for migration management (`jdo db status/upgrade/revision`)
- [x] 6.9 Write integration tests for migration operations in `tests/integration/db/test_migrations.py`
- [x] 6.10 Document migration workflow in `AGENTS.md`

## 7. Integration & Documentation

- [x] 7.1 Update `AGENTS.md` with new tooling commands
- [x] 7.2 Update `pyproject.toml` ruff config for new modules
- [x] 7.3 Add `.env.example` with all new configuration options
- [x] 7.4 Run full test suite and fix any regressions
- [x] 7.5 Run linting and type checking on all new code
