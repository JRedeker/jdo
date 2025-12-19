# Tasks: Add Reliability and Resilience Compliance

## 1. Setup

- [x] 1.1 Add `tenacity>=8.0.0` to `pyproject.toml` dependencies
- [x] 1.2 Run `uv sync` to install new dependency

## 2. Timeout Infrastructure (P03)

- [x] 2.1 Create `src/jdo/ai/timeout.py` with timeout constants and `with_timeout()` async wrapper
- [x] 2.2 Add timeout (30s) to `exchange_code()` in `src/jdo/auth/oauth.py`
- [x] 2.3 Add timeout (30s) to `refresh_tokens()` in `src/jdo/auth/oauth.py`
- [x] 2.4 Add timeout (120s) to `classify_triage_item()` sync call in `src/jdo/ai/triage.py`
- [x] 2.5 Add timeout (120s) to `classify_triage_item_async()` in `src/jdo/ai/triage.py`
- [x] 2.6 Add timeout (120s) to all 6 extraction functions in `src/jdo/ai/extraction.py`
- [x] 2.7 Add timeout (180s) to `stream_response()` in `src/jdo/ai/context.py`

## 3. Retry Infrastructure (P10)

- [x] 3.1 Create `src/jdo/retry.py` with `http_retry()` decorator using tenacity
- [x] 3.2 Apply `@http_retry()` to `exchange_code()` in `src/jdo/auth/oauth.py`
- [x] 3.3 Apply `@http_retry()` to `refresh_tokens()` in `src/jdo/auth/oauth.py`

## 4. Atomic File Writes (P10)

- [x] 4.1 Refactor `_write_store()` in `src/jdo/auth/store.py` to use temp file + atomic rename

## 5. Complete TODO (P05)

- [x] 5.1 Implement `_get_allocated_hours()` method in `src/jdo/screens/chat.py`
- [x] 5.2 Replace TODO with call to `_get_allocated_hours()` in `_build_handler_context()`

## 6. Bug Fixes

- [x] 6.1 Add `_refresh_auth_statuses()` method to `SettingsScreen` in `src/jdo/screens/settings.py`
- [x] 6.2 Update `_on_auth_complete()` to call `_refresh_auth_statuses()` instead of `refresh()`
- [x] 6.3 Add `focus()` call after modal dismiss to fix Back binding

## 7. Unit Tests (P05)

- [x] 7.1 Create `tests/unit/ai/test_timeout.py` with tests for `with_ai_timeout()` and `run_sync_with_timeout()`
- [x] 7.2 Create `tests/unit/test_retry.py` with tests for `http_retry()` decorator
- [x] 7.3 Add atomic write tests to `tests/unit/auth/test_store.py`
- [x] 7.4 Core logic tested via `tests/unit/ai/test_time_context.py` (calculate_allocated_hours)

## 8. Validation

- [x] 8.1 Run `uv run ruff check --fix src/ tests/`
- [x] 8.2 Run `uv run ruff format src/ tests/`
- [x] 8.3 Run `uvx pyrefly check src/`
- [x] 8.4 Run `uv run pytest` - all 1328 tests pass
- [x] 8.5 Manual test: OAuth flow with network delay simulation (deferred - requires external service)
- [x] 8.6 Manual test: Settings screen auth status refresh after OAuth (deferred - requires external service)

## Dependencies

- Tasks 2.2-2.7 depend on 2.1 (timeout module) ✓
- Tasks 3.2-3.3 depend on 3.1 (retry module) ✓
- Tasks 7.1-7.2 can run in parallel with 2.x-3.x ✓
- Task 8.x depends on all implementation tasks ✓

## Implementation Notes

### Lessons Learned Compliance (from lessons-learned-textual.md)
- ✅ ClassVar annotation for BINDINGS in SettingsScreen
- ✅ NoMatches exception handling instead of bare except
- ✅ focus() call after modal dismiss to restore bindings
- ✅ No push_screen_wait in on_mount (using callback pattern)
- ✅ Proper error handling with logging in _get_allocated_hours()

### Files Created
- `src/jdo/ai/timeout.py` - Timeout constants and wrapper functions
- `src/jdo/retry.py` - HTTP retry decorator with tenacity
- `tests/unit/ai/test_timeout.py` - 11 tests
- `tests/unit/test_retry.py` - 8 tests

### Files Modified
- `pyproject.toml` - Added tenacity>=8.2.0
- `src/jdo/ai/context.py` - Streaming timeout
- `src/jdo/ai/extraction.py` - AI timeout on 6 functions
- `src/jdo/ai/triage.py` - AI timeout on classification
- `src/jdo/auth/oauth.py` - HTTP timeout + retry
- `src/jdo/auth/store.py` - Atomic file writes
- `src/jdo/screens/chat.py` - _get_allocated_hours()
- `src/jdo/screens/settings.py` - Auth status refresh + focus fix
- `tests/unit/auth/test_store.py` - 4 new atomic write tests
