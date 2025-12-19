## 1. Core Infrastructure

- [x] 1.1 Create `tests/uat/` directory structure
- [x] 1.2 Create `tests/uat/__init__.py`
- [x] 1.3 Create `tests/uat/conftest.py` with base fixtures
- [x] 1.4 Create `tests/uat/scenarios/` directory for YAML scenarios

## 2. UI State Observer

- [x] 2.1 Create `tests/uat/observer.py` with UIStateObserver class
- [x] 2.2 Implement `capture()` method returning UIState model
- [x] 2.3 Add screen-specific capture logic (ChatScreen, HomeScreen, etc.)
- [x] 2.4 Add data panel content extraction
- [x] 2.5 Write unit tests for observer in `tests/uat/test_observer.py`

## 3. Action Model

- [x] 3.1 Create `tests/uat/models.py` with Pydantic models
- [x] 3.2 Define UATAction model with all action types
- [x] 3.3 Define UATScenario model for scenario definitions
- [x] 3.4 Define UATResult model for execution results
- [x] 3.5 Define UIState model for state capture
- [x] 3.6 Write unit tests for models

## 4. AI UAT Driver

- [x] 4.1 Create `tests/uat/driver.py` with AIUATDriver class
- [x] 4.2 Implement observation -> action -> execution loop
- [x] 4.3 Add action execution methods (press, click, type, wait, assert)
- [x] 4.4 Add step limit and timeout handling
- [x] 4.5 Add execution logging
- [x] 4.6 Write unit tests for driver with mocked agent

## 5. Scenario Loading

- [x] 5.1 Create `tests/uat/loader.py` for YAML scenario loading
- [x] 5.2 Implement scenario validation
- [x] 5.3 Add precondition execution support
- [x] 5.4 Write unit tests for loader

## 6. Test Fixtures

- [x] 6.1 Create `uat_app` fixture in conftest.py
- [x] 6.2 Create `uat_driver` fixture with TestModel agent
- [x] 6.3 Create `live_uat_driver` fixture for live AI tests
- [x] 6.4 Add `@pytest.mark.live_ai` marker registration

## 7. Scenario Definitions (YAML)

- [x] 7.1 Create `scenarios/navigation.yaml` - screen navigation scenario
- [x] 7.2 Create `scenarios/commitment_creation.yaml` - commitment flow
- [x] 7.3 Create `scenarios/triage_workflow.yaml` - triage processing
- [x] 7.4 Create `scenarios/integrity_dashboard.yaml` - integrity viewing
- [x] 7.5 Create `scenarios/planning_hierarchy.yaml` - full hierarchy creation

## 8. Mock Agent Responses

- [x] 8.1 Create `tests/uat/mocks.py` with FunctionModel implementations
- [x] 8.2 Define deterministic action sequences for each scenario
- [x] 8.3 Write tests verifying mock responses produce valid actions

## 9. Live UAT Tests

- [x] 9.1 Create `tests/uat/test_live_scenarios.py` with live AI tests
- [x] 9.2 Add skip conditions for missing credentials
- [x] 9.3 Add budget/timeout controls for live tests
- [x] 9.4 Integrate with existing e2e test patterns

## 10. Integration Tests

- [x] 10.1 Create `tests/uat/test_scenarios.py` with mock-based tests
- [x] 10.2 Test each scenario with deterministic mocks
- [x] 10.3 Verify all scenarios pass in CI

## 11. CI Configuration

- [x] 11.1 Add UAT tests to CI workflow (mock mode only)
- [x] 11.2 Add nightly job for live AI UAT (optional)
- [x] 11.3 Add test result reporting

## 12. Documentation

- [x] 12.1 Add UAT section to AGENTS.md
- [x] 12.2 Document scenario authoring format
- [x] 12.3 Document running live vs mock UAT tests
