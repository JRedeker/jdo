# Change: Add AI-Driven User Acceptance Testing

## Why

The current test suite includes Pilot-based tests and live AI tests (`tests/e2e/test_live_ai.py`), but lacks a systematic approach to simulate realistic user acceptance testing (UAT) scenarios. Manual UAT is time-consuming and inconsistent. An AI agent driving the Textual app through Pilot can execute complex multi-step user journeys, validate business logic flows, and catch regressions that simple unit tests miss.

## What Changes

- **New capability**: `ai-uat` - AI-driven user acceptance testing infrastructure
- Add `AIUATDriver` class that wraps Textual's Pilot with AI decision-making
- Create scenario definition format for declarative UAT test cases
- Implement state observation utilities to capture UI state for AI consumption
- Add live UAT test suite covering key user journeys:
  - Commitment creation and management flow
  - Triage workflow completion
  - Goal/Vision hierarchy navigation
  - Integrity dashboard interaction
  - Settings and authentication flows

## Impact

- Affected specs: New `ai-uat` capability (no existing spec modifications)
- Affected code:
  - New `tests/uat/` directory for AI-driven tests
  - New `src/jdo/testing/` module for UAT infrastructure (optional, could be test-only)
- Dependencies:
  - Existing: `pydantic-ai`, `textual`, `pytest`
  - Uses existing `TestModel` from pydantic-ai for cost-controlled test runs
  - Uses existing Pilot API from Textual

## Risks

- **Cost**: Live AI tests incur API costs; mitigated by using `TestModel` for most runs and live tests only in CI with budget controls
- **Flakiness**: AI decisions may vary; mitigated by structured outputs and deterministic scenario definitions
- **Maintenance**: Scenarios need updates when UI changes; mitigated by declarative scenario format
