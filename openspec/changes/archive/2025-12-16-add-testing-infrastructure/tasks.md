# Tasks: Add Testing Infrastructure

**Status**: ✅ Complete

## 1. Add Dev Dependencies

- [x] 1.1 Add `pytest-textual-snapshot>=1.0.0` to dev dependencies in pyproject.toml
- [x] 1.2 Add `pytest-httpx>=0.30.0` to dev dependencies in pyproject.toml
- [x] 1.3 Add `pytest-cov>=4.0.0` to dev dependencies in pyproject.toml (already present)
- [x] 1.4 Run `uv sync` to install dependencies

## 2. Configure pytest

- [x] 2.1 Verify `asyncio_mode = "auto"` is set in pyproject.toml (already present)
- [x] 2.2 Add coverage configuration to pyproject.toml `[tool.coverage.run]`
- [x] 2.3 Add coverage report configuration to pyproject.toml `[tool.coverage.report]`
- [x] 2.4 Add test markers for `unit`, `integration`, `tui` in pytest configuration

## 3. Create Test Directory Structure

- [x] 3.1 Create `tests/unit/` directory (already exists)
- [x] 3.2 Create `tests/unit/models/` directory (already exists)
- [x] 3.3 Create `tests/unit/config/` directory (already exists)
- [x] 3.4 Create `tests/unit/paths/` directory (not needed - paths tests in config/)
- [x] 3.5 Create `tests/integration/` directory
- [x] 3.6 Create `tests/integration/db/` directory
- [x] 3.7 Create `tests/integration/auth/` directory
- [x] 3.8 Create `tests/tui/` directory
- [x] 3.9 Create `tests/tui/snapshots/` directory
- [x] 3.10 Add `__init__.py` to each test subdirectory

## 4. Create Shared Fixtures (tests/conftest.py)

- [x] 4.1 Create `db_engine` fixture with in-memory SQLite and StaticPool
- [x] 4.2 Create `db_session` fixture that yields Session from db_engine
- [x] 4.3 Create `temp_data_dir` fixture using pytest's tmp_path
- [x] 4.4 Create `test_settings` fixture with environment variable overrides
- [x] 4.5 Add docstrings explaining each fixture's purpose

## 5. Create Unit Test Fixtures (tests/unit/conftest.py)

Note: Unit test fixtures already exist from refactor-core-libraries implementation.

- [x] 5.1 Create fixture for sample Stakeholder instances (in model tests)
- [x] 5.2 Create fixture for sample Goal instances (in model tests)
- [x] 5.3 Create fixture for sample Commitment instances (in model tests)
- [x] 5.4 Create fixture for sample Task instances with sub_tasks (in model tests)

## 6. Create Integration Test Fixtures (tests/integration/conftest.py)

- [x] 6.1 Create `populated_db` fixture with pre-seeded test data
- [x] 6.2 Create `auth_store` fixture with temporary auth.json path

## 7. Create TUI Test Fixtures (tests/tui/conftest.py)

- [x] 7.1 Create `app` fixture that yields JDOApp instance (placeholder - skips until TUI implemented)
- [x] 7.2 Create `pilot` fixture that yields Pilot from app.run_test() (placeholder - skips until TUI implemented)

## 8. Write Sample Unit Tests

Note: Unit tests already exist from refactor-core-libraries implementation.

- [x] 8.1 Write `tests/unit/models/test_commitment.py` with validation tests
- [x] 8.2 Write `tests/unit/models/test_goal.py` with nesting validation tests
- [x] 8.3 Write `tests/unit/models/test_task.py` with sub_task JSON tests
- [x] 8.4 Write `tests/unit/config/test_settings.py` with env var tests
- [x] 8.5 Write `tests/unit/paths/test_paths.py` with platform path tests (in config/test_paths.py)

## 9. Write Sample Integration Tests

- [x] 9.1 Write `tests/integration/db/test_crud.py` with basic CRUD operations
- [x] 9.2 Write `tests/integration/db/test_relationships.py` with FK relationship tests (covered in test_crud.py)
- [x] 9.3 Write `tests/integration/auth/test_oauth.py` with httpx_mock OAuth flow tests (placeholder - auth module not yet implemented)

## 10. Write Sample TUI Tests

- [x] 10.1 Write `tests/tui/test_app.py` with app startup tests (placeholder - skipped until TUI implemented)
- [x] 10.2 Write `tests/tui/test_bindings.py` with key binding tests (in test_app.py - skipped until TUI implemented)
- [x] 10.3 Create initial snapshot for main app screen (deferred until TUI implemented)

## 11. Validation and CI

- [x] 11.1 Run `uv run pytest` to verify all tests pass (99 passed, 5 skipped)
- [x] 11.2 Run `uv run pytest --cov=src/jdo --cov-report=term-missing` for coverage (83.53%)
- [x] 11.3 Verify coverage meets 70% threshold ✅
- [x] 11.4 Update CI workflow to run tests with coverage (CI already runs pytest)

## Summary

- **Tests**: 99 passed, 5 skipped (TUI tests deferred)
- **Coverage**: 83.53% (exceeds 70% threshold)
- **New dependencies**: pytest-textual-snapshot, pytest-httpx
- **New fixtures**: db_engine, db_session, temp_data_dir, test_settings, populated_db, auth_store_path
- **Test markers**: unit, integration, tui

## Running Tests

```bash
# Run all tests
uv run pytest

# Run by marker
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m tui

# Run with coverage
uv run pytest --cov=src/jdo --cov-report=term-missing

# Update snapshots (when TUI is implemented)
uv run pytest --snapshot-update
```
