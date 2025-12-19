# Design: AI-Driven User Acceptance Testing

## Context

JDO is a Textual-based TUI app with an existing test suite using:
- **Unit tests**: Fast, isolated tests for models and services
- **TUI tests**: Pilot-based tests for widget and screen behavior
- **E2E tests**: `tests/e2e/test_live_ai.py` with real AI interactions

The gap is systematic UAT that simulates realistic multi-step user journeys with AI-driven decision making, allowing the system to be "dog-fooded" by an AI agent acting as a user.

## Goals

1. Enable AI agent to drive the Textual app through complete user journeys
2. Validate complex flows that span multiple screens and interactions
3. Support both mocked AI (for fast CI) and live AI (for realistic testing)
4. Keep test scenarios declarative and maintainable

## Non-Goals

- Full visual testing (covered by existing snapshots)
- Performance/load testing
- Replacing existing unit/integration tests

## Architecture

### Component Overview

```
+------------------+     +-----------------+     +------------------+
|  Scenario YAML   | --> |  AIUATDriver    | --> |  Textual App     |
|  (declarative)   |     |  (orchestrator) |     |  (via Pilot)     |
+------------------+     +-----------------+     +------------------+
                               |
                               v
                         +-----------------+
                         |  PydanticAI     |
                         |  TestModel or   |
                         |  Live Model     |
                         +-----------------+
```

### Key Classes

#### `UIStateObserver`
Captures current UI state for AI consumption:
- Current screen class and title
- Visible widgets with IDs and content
- Active focus element
- Available keybindings
- Data panel content (if present)
- Chat messages (if on chat screen)

#### `UATAction` (Pydantic model)
Structured output from AI for deterministic action execution:
```python
class UATAction(BaseModel):
    action_type: Literal["press", "click", "type", "wait", "assert", "done"]
    target: str | None = None  # widget ID or key sequence
    value: str | None = None   # text to type or assertion value
    reason: str  # AI's explanation for the action
```

#### `AIUATDriver`
Orchestrates the test execution:
1. Observes current UI state
2. Sends state + scenario goal to AI agent
3. Receives structured `UATAction`
4. Executes action via Pilot
5. Repeats until "done" or max steps reached

#### `UATScenario`
Declarative scenario definition:
```python
class UATScenario(BaseModel):
    name: str
    description: str
    goal: str  # Natural language goal for AI
    preconditions: list[str] = []  # Setup steps
    success_criteria: list[str]  # How to know we're done
    max_steps: int = 50
    timeout_seconds: int = 120
```

### Test Scenarios

Initial live test scenarios (in `tests/uat/scenarios/`):

1. **New User Onboarding**
   - Start app fresh
   - Navigate to settings if needed
   - Return to home and explore

2. **Create Commitment Flow**
   - Navigate to chat
   - Describe a commitment naturally
   - Confirm creation
   - Verify appears in lists

3. **Triage Workflow**
   - Create ambiguous inbox item
   - Enter triage mode
   - Complete triage decision
   - Verify item processed

4. **Integrity Check Journey**
   - View integrity dashboard
   - Navigate to at-risk commitments
   - Update commitment status
   - Verify grade updates

5. **Full Planning Hierarchy**
   - Create vision
   - Create goal under vision
   - Create milestone under goal
   - Create commitment under milestone
   - View hierarchy tree

## Decisions

### Decision: Use PydanticAI TestModel as Default
- **What**: Most UAT runs use `TestModel` with `FunctionModel` fallback for deterministic responses
- **Why**: Eliminates API costs for CI, ensures reproducible tests
- **Alternative**: Always use live AI - rejected due to cost and flakiness
- **Live AI option**: Available via `--live-ai` pytest marker for nightly/manual runs

### Decision: Structured Output for Actions
- **What**: AI returns `UATAction` Pydantic model, not free-form text
- **Why**: Deterministic action execution, no parsing ambiguity
- **Alternative**: Parse natural language commands - rejected due to fragility

### Decision: YAML Scenario Definitions
- **What**: Scenarios defined in YAML files, not Python code
- **Why**: Non-programmers can author scenarios; clear separation of test logic
- **Alternative**: Python dataclasses - viable but less accessible

### Decision: Test-Only Code Location
- **What**: UAT infrastructure lives in `tests/uat/` not `src/jdo/testing/`
- **Why**: No production dependency on test code; simpler packaging
- **Alternative**: Shared module - rejected to keep production lean

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| AI actions vary between runs | Use structured output; deterministic scenarios |
| Live AI tests are slow | Default to TestModel; live tests marked separately |
| UI changes break scenarios | Scenarios reference intent, not specific widget IDs |
| Cost overruns with live AI | Budget limits in CI; most tests use mocks |

## Migration Plan

1. Add test infrastructure (no production changes)
2. Create initial scenarios for existing happy paths
3. Run in CI with TestModel only initially
4. Add live AI runs as nightly job with budget cap

## Open Questions

- Should scenarios support branching (if/else paths)? *Initial answer: No, keep simple*
- How to handle AI timeout during action decision? *Proposal: Fail test with clear error*
- Should we capture video/screenshots for debugging? *Proposal: Use existing snapshot infra*
