# Capability: Testing Infrastructure

Testing infrastructure provides pytest-based automated testing for JDO, including fixtures for database isolation, settings override, TUI simulation, and HTTP mocking.

## ADDED Requirements

### Requirement: Database Test Fixture

The system SHALL provide a pytest fixture that creates an isolated in-memory SQLite database for each test.

#### Scenario: Fresh database per test
- **WHEN** a test requests the `db_session` fixture
- **THEN** an in-memory SQLite database is created with all tables
- **AND** the session is yielded to the test
- **AND** the database is discarded after the test completes

#### Scenario: Database isolation between tests
- **WHEN** test A creates a Commitment and completes
- **AND** test B requests the `db_session` fixture
- **THEN** test B sees an empty database with no commitments

#### Scenario: Tables created from SQLModel metadata
- **WHEN** the `db_engine` fixture creates the database
- **THEN** all SQLModel table classes are reflected as database tables
- **AND** foreign key relationships are enforced

### Requirement: Settings Test Fixture

The system SHALL provide a pytest fixture that creates isolated application settings with temporary paths.

#### Scenario: Temporary data directory
- **WHEN** a test requests the `test_settings` fixture
- **THEN** the settings use a temporary directory for database and auth files
- **AND** the temporary directory is cleaned up after the test

#### Scenario: Environment variable override
- **WHEN** a test sets `JDO_AI_MODEL=test-model` via monkeypatch
- **AND** requests the `test_settings` fixture
- **THEN** `settings.ai_model` equals "test-model"

#### Scenario: Settings singleton reset
- **WHEN** test A modifies settings
- **AND** test B requests the `test_settings` fixture
- **THEN** test B gets fresh settings unaffected by test A

### Requirement: TUI Test Support

The system SHALL support Textual Pilot-based testing for TUI components.

#### Scenario: App run_test context manager
- **WHEN** a test uses `async with app.run_test() as pilot`
- **THEN** the app runs in headless mode
- **AND** the pilot object can simulate user input

#### Scenario: Simulate key press
- **WHEN** a test calls `await pilot.press("q")`
- **THEN** the app receives a key press event for "q"
- **AND** any bound action for "q" is triggered

#### Scenario: Simulate button click
- **WHEN** a test calls `await pilot.click("#submit")`
- **THEN** the button with id "submit" receives a click event
- **AND** the button's on_click handler is called

#### Scenario: Wait for async updates
- **WHEN** a test calls `await pilot.pause()`
- **THEN** all pending messages are processed
- **AND** the screen state is fully updated before assertions

### Requirement: HTTP Mock Fixture

The system SHALL provide pytest-httpx integration for mocking HTTP requests.

#### Scenario: Mock successful response
- **WHEN** a test registers `httpx_mock.add_response(url="...", json={...})`
- **AND** application code makes an httpx request to that URL
- **THEN** the mock response is returned
- **AND** no real HTTP request is made

#### Scenario: Mock error response
- **WHEN** a test registers `httpx_mock.add_response(status_code=401)`
- **AND** application code makes an httpx request
- **THEN** the response has status code 401

#### Scenario: Mock exception
- **WHEN** a test registers `httpx_mock.add_exception(httpx.ReadTimeout(...))`
- **AND** application code makes an httpx request
- **THEN** `httpx.ReadTimeout` is raised

#### Scenario: Verify request details
- **WHEN** a test makes an HTTP request through mocked code
- **THEN** `httpx_mock.get_request()` returns the request object
- **AND** the test can assert on method, URL, headers, and body

### Requirement: Snapshot Testing

The system SHALL support visual regression testing for TUI screens using pytest-textual-snapshot.

#### Scenario: Create initial snapshot
- **WHEN** a test calls `snap_compare("path/to/app.py")`
- **AND** no baseline exists
- **THEN** the test fails with instructions to create baseline
- **AND** a new snapshot file is generated

#### Scenario: Compare against baseline
- **WHEN** a test calls `snap_compare("path/to/app.py")`
- **AND** a baseline snapshot exists
- **THEN** the current render is compared to the baseline
- **AND** the test passes if they match

#### Scenario: Update snapshot
- **WHEN** `pytest --snapshot-update` is run
- **THEN** baseline snapshots are updated to match current output
- **AND** future tests compare against the new baseline

### Requirement: Test Organization

The system SHALL organize tests into unit, integration, and TUI categories.

#### Scenario: Run all tests
- **WHEN** `uv run pytest` is executed
- **THEN** all tests in `tests/` are discovered and run

#### Scenario: Run unit tests only
- **WHEN** `uv run pytest tests/unit/` is executed
- **THEN** only tests in the `unit/` directory are run

#### Scenario: Run TUI tests only
- **WHEN** `uv run pytest tests/tui/` is executed
- **THEN** only TUI-related tests are run

#### Scenario: Shared fixtures available
- **WHEN** any test requests `db_session` or `test_settings`
- **THEN** the fixture is available regardless of test location
- **AND** fixtures are defined in `tests/conftest.py`

### Requirement: Code Coverage

The system SHALL track and report test code coverage.

#### Scenario: Generate coverage report
- **WHEN** `uv run pytest --cov=src/jdo` is executed
- **THEN** a coverage report is generated showing line and branch coverage

#### Scenario: Coverage threshold enforcement
- **WHEN** coverage falls below 80%
- **AND** `--cov-fail-under=80` is specified
- **THEN** the test run fails with coverage below threshold message

#### Scenario: Exclude non-testable code
- **WHEN** coverage is calculated
- **THEN** `__init__.py` files are excluded
- **AND** `TYPE_CHECKING` blocks are excluded
- **AND** `raise NotImplementedError` lines are excluded

### Requirement: Async Test Support

The system SHALL support async test functions without explicit markers.

#### Scenario: Auto-detect async tests
- **WHEN** a test function is defined as `async def test_something():`
- **THEN** pytest-asyncio automatically runs it in an event loop
- **AND** no `@pytest.mark.asyncio` decorator is required

#### Scenario: Async fixtures
- **WHEN** a fixture is defined as `async def my_fixture():`
- **THEN** it can be used by async test functions
- **AND** `await` can be used within the fixture

#### Scenario: Function-scoped event loops
- **WHEN** multiple async tests run
- **THEN** each test gets a fresh event loop
- **AND** async state does not leak between tests

### Requirement: Model Validation Testing

The system SHALL enable testing of SQLModel validation rules.

#### Scenario: Test required field validation
- **WHEN** creating a Commitment without a required `deliverable` field
- **THEN** SQLModel validation raises a validation error

#### Scenario: Test field constraints
- **WHEN** creating a Goal with an empty `title` (min_length=1)
- **THEN** SQLModel validation raises a validation error

#### Scenario: Test relationship loading
- **WHEN** a Commitment is created with a `stakeholder_id`
- **AND** the stakeholder is accessed via `commitment.stakeholder`
- **THEN** the related Stakeholder object is loaded

#### Scenario: Test JSON column serialization
- **WHEN** a Task is created with `sub_tasks=[SubTask(description="test")]`
- **AND** the Task is saved and reloaded from the database
- **THEN** `task.sub_tasks` can be parsed back into SubTask objects
