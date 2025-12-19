# Change: Add Reliability and Resilience Compliance

## Why

An audit against our core-rules.md identified violations of critical principles:
- **P03 (Timeouts, prio 10)**: 13 network/AI operations lack timeouts, risking indefinite hangs
- **P10 (Idempotence, prio 8)**: HTTP calls lack retry logic; file writes are non-atomic
- **P05 (No Half, prio 9)**: 8 modules lack unit tests; 1 TODO incomplete in production

Additionally, two UI bugs were discovered:
- Settings screen shows stale auth status after successful OAuth authentication
- Escape/Back binding becomes unresponsive after OAuth modal dismissal

## What Changes

### Reliability Infrastructure
- Add `tenacity` dependency for retry logic with exponential backoff
- Create `src/jdo/ai/timeout.py` with timeout constants and async wrapper utilities
- Create `src/jdo/retry.py` with HTTP retry decorators

### P03 Timeout Compliance
- Add 30-second timeout to OAuth HTTP calls in `oauth.py`
- Add 120-second timeout to all PydanticAI agent calls in `triage.py`, `extraction.py`
- Add 180-second timeout to AI streaming in `context.py`

### P10 Idempotence Compliance
- Add retry decorator (3 attempts, exponential backoff) to OAuth token operations
- Convert `AuthStore._write_store()` to atomic file write (temp file + rename)

### P05 Test Coverage
- Complete `allocated_hours` TODO in `chat.py` with actual database query
- Add unit tests for new timeout and retry modules
- Add tests for atomic file write behavior

### Bug Fixes
- Fix Settings screen to update auth status widgets after OAuth success
- Fix Back binding responsiveness after modal dismissal

## Impact

- Affected specs: `ai-provider`, `provider-auth`, `tui-core`, `app-config`
- Affected code:
  - `src/jdo/auth/oauth.py` - timeouts + retry
  - `src/jdo/auth/store.py` - atomic writes
  - `src/jdo/ai/triage.py` - timeouts
  - `src/jdo/ai/extraction.py` - timeouts (6 functions)
  - `src/jdo/ai/context.py` - streaming timeout
  - `src/jdo/screens/settings.py` - bug fixes
  - `src/jdo/screens/chat.py` - complete TODO
- New files:
  - `src/jdo/ai/timeout.py`
  - `src/jdo/retry.py`
  - `tests/unit/ai/test_timeout.py`
  - `tests/unit/test_retry.py`
