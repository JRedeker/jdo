# test-coverage Specification

## Purpose
Define test organization patterns, coverage requirements, and testing standards to ensure comprehensive test coverage across unit, integration, widget, and snapshot tests.

## ADDED Requirements

### Requirement: Test Organization

The system SHALL organize tests by category with clear separation.

#### Scenario: Unit tests in dedicated directory
- **WHEN** writing tests for a module without external dependencies
- **THEN** tests are placed in `tests/unit/<module>/`

#### Scenario: Integration tests in dedicated directory
- **WHEN** writing tests requiring database or external services
- **THEN** tests are placed in `tests/integration/<area>/`

#### Scenario: TUI tests in dedicated directory
- **WHEN** writing Textual Pilot tests for screens or widgets
- **THEN** tests are placed in `tests/tui/`

#### Scenario: Snapshot tests with organized output
- **WHEN** snapshot tests are created
- **THEN** snapshots are stored in `tests/tui/__snapshots__/<test_module>/`

### Requirement: Coverage Targets

The system SHALL maintain minimum coverage thresholds.

#### Scenario: Overall coverage threshold
- **WHEN** pytest runs with coverage
- **THEN** the build fails if line coverage drops below 80%

#### Scenario: Critical module coverage
- **WHEN** coverage is calculated for `src/jdo/ai/` and `src/jdo/db/`
- **THEN** these modules maintain at least 85% coverage

#### Scenario: New code coverage requirement
- **WHEN** new code is added without tests
- **THEN** coverage diff reports highlight untested lines

### Requirement: Unit Test Standards

The system SHALL require unit tests for all modules.

#### Scenario: Each module has test file
- **WHEN** a new module is added at `src/jdo/foo/bar.py`
- **THEN** a corresponding `tests/unit/foo/test_bar.py` is expected

#### Scenario: External dependencies are mocked
- **WHEN** unit tests run
- **THEN** database, network, and file system calls are mocked

#### Scenario: Tests are isolated
- **WHEN** unit tests run
- **THEN** each test can run independently in any order

### Requirement: Widget Test Standards

The system SHALL require Textual Pilot tests for widgets.

#### Scenario: Widget has pilot test
- **WHEN** a new widget is added at `src/jdo/widgets/foo.py`
- **THEN** a corresponding `tests/tui/test_foo.py` with Pilot tests is expected

#### Scenario: Widget interactions tested
- **WHEN** a widget supports key bindings or mouse events
- **THEN** tests verify these interactions produce expected state changes

#### Scenario: Widget composition tested
- **WHEN** a widget composes child widgets
- **THEN** tests verify child widgets are rendered correctly

### Requirement: Integration Test Standards

The system SHALL require integration tests for database operations.

#### Scenario: Database tests use test fixture
- **WHEN** integration tests run
- **THEN** they use an isolated in-memory or temporary database

#### Scenario: Database state is reset between tests
- **WHEN** a database integration test completes
- **THEN** the database is reset to a clean state

#### Scenario: Full CRUD cycles tested
- **WHEN** a model supports CRUD operations
- **THEN** integration tests verify create, read, update, delete workflows

### Requirement: Snapshot Test Standards

The system SHALL support visual regression testing via snapshots.

#### Scenario: Screen has snapshot test
- **WHEN** a new screen is added
- **THEN** a snapshot test captures its initial rendered state

#### Scenario: Snapshot update workflow
- **WHEN** UI intentionally changes
- **THEN** developer updates snapshots with `pytest --snapshot-update`

#### Scenario: Snapshot diff on failure
- **WHEN** a snapshot test fails
- **THEN** the diff between expected and actual is displayed

### Requirement: Test Markers

The system SHALL use pytest markers for test categorization.

#### Scenario: Unit marker for fast tests
- **WHEN** `pytest -m unit` runs
- **THEN** only tests marked `@pytest.mark.unit` execute

#### Scenario: Integration marker for database tests
- **WHEN** `pytest -m integration` runs
- **THEN** only tests marked `@pytest.mark.integration` execute

#### Scenario: TUI marker for Textual tests
- **WHEN** `pytest -m tui` runs
- **THEN** only tests marked `@pytest.mark.tui` execute
