# Tasks: Add Testing Infrastructure

## 1. Add Dev Dependencies

- [ ] 1.1 Add `pytest-textual-snapshot>=1.0.0` to dev dependencies in pyproject.toml
- [ ] 1.2 Add `pytest-httpx>=0.30.0` to dev dependencies in pyproject.toml
- [ ] 1.3 Add `pytest-cov>=4.0.0` to dev dependencies in pyproject.toml
- [ ] 1.4 Run `uv sync` to install dependencies

## 2. Configure pytest

- [ ] 2.1 Verify `asyncio_mode = "auto"` is set in pyproject.toml (already present)
- [ ] 2.2 Add coverage configuration to pyproject.toml `[tool.coverage.run]`
- [ ] 2.3 Add coverage report configuration to pyproject.toml `[tool.coverage.report]`
- [ ] 2.4 Add test markers for `unit`, `integration`, `tui` in pytest configuration

## 3. Create Test Directory Structure

- [ ] 3.1 Create `tests/unit/` directory
- [ ] 3.2 Create `tests/unit/models/` directory
- [ ] 3.3 Create `tests/unit/config/` directory
- [ ] 3.4 Create `tests/unit/paths/` directory
- [ ] 3.5 Create `tests/integration/` directory
- [ ] 3.6 Create `tests/integration/db/` directory
- [ ] 3.7 Create `tests/integration/auth/` directory
- [ ] 3.8 Create `tests/tui/` directory
- [ ] 3.9 Create `tests/tui/snapshots/` directory
- [ ] 3.10 Add `__init__.py` to each test subdirectory

## 4. Create Shared Fixtures (tests/conftest.py)

- [ ] 4.1 Create `db_engine` fixture with in-memory SQLite and StaticPool
- [ ] 4.2 Create `db_session` fixture that yields Session from db_engine
- [ ] 4.3 Create `temp_data_dir` fixture using pytest's tmp_path
- [ ] 4.4 Create `test_settings` fixture with environment variable overrides
- [ ] 4.5 Add docstrings explaining each fixture's purpose

## 5. Create Unit Test Fixtures (tests/unit/conftest.py)

- [ ] 5.1 Create fixture for sample Stakeholder instances
- [ ] 5.2 Create fixture for sample Goal instances
- [ ] 5.3 Create fixture for sample Commitment instances
- [ ] 5.4 Create fixture for sample Task instances with sub_tasks

## 6. Create Integration Test Fixtures (tests/integration/conftest.py)

- [ ] 6.1 Create `populated_db` fixture with pre-seeded test data
- [ ] 6.2 Create `auth_store` fixture with temporary auth.json path

## 7. Create TUI Test Fixtures (tests/tui/conftest.py)

- [ ] 7.1 Create `app` fixture that yields JDOApp instance
- [ ] 7.2 Create `pilot` fixture that yields Pilot from app.run_test()

## 8. Write Sample Unit Tests

- [ ] 8.1 Write `tests/unit/models/test_commitment.py` with validation tests
- [ ] 8.2 Write `tests/unit/models/test_goal.py` with nesting validation tests
- [ ] 8.3 Write `tests/unit/models/test_task.py` with sub_task JSON tests
- [ ] 8.4 Write `tests/unit/config/test_settings.py` with env var tests
- [ ] 8.5 Write `tests/unit/paths/test_paths.py` with platform path tests

## 9. Write Sample Integration Tests

- [ ] 9.1 Write `tests/integration/db/test_crud.py` with basic CRUD operations
- [ ] 9.2 Write `tests/integration/db/test_relationships.py` with FK relationship tests
- [ ] 9.3 Write `tests/integration/auth/test_oauth.py` with httpx_mock OAuth flow tests

## 10. Write Sample TUI Tests

- [ ] 10.1 Write `tests/tui/test_app.py` with app startup tests
- [ ] 10.2 Write `tests/tui/test_bindings.py` with key binding tests
- [ ] 10.3 Create initial snapshot for main app screen

## 11. Validation and CI

- [ ] 11.1 Run `uv run pytest` to verify all tests pass
- [ ] 11.2 Run `uv run pytest --cov=src/jdo --cov-report=term-missing` for coverage
- [ ] 11.3 Verify coverage meets 80% threshold (or adjust if infrastructure-only)
- [ ] 11.4 Update CI workflow to run tests with coverage

## Dependencies

- Tasks 4-7 depend on Task 1 (dependencies installed)
- Tasks 8-10 depend on Tasks 4-7 (fixtures available)
- Task 11 depends on Tasks 8-10 (tests written)

## Parallelizable Work

- Tasks 8.1-8.5 can be done in parallel (unit tests are independent)
- Tasks 9.1-9.3 can be done in parallel (integration tests are independent)
- Tasks 10.1-10.3 can be done in parallel (TUI tests are independent)
