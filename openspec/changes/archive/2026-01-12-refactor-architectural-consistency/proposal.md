# Change: Refactor Architectural Consistency

## Why

A comprehensive architectural audit identified several consistency issues that, while not critical, reduce maintainability and increase cognitive load:

1. **Code duplication**: `utc_now()` defined in 8 files, `today_date()` in 3 files
2. **Unused abstractions**: `BaseModel` class exists but is not used by any entity
3. **Untyped interfaces**: Handler `context` parameter is `dict[str, Any]` instead of typed
4. **Large files**: Several files exceed 800 lines with multiple responsibilities
5. **Inconsistent patterns**: Some models import utilities from `base.py`, others define their own
6. **Suppression debt**: 35 `# noqa` and 36 `# type: ignore` comments, some undocumented

Addressing these issues will:
- Reduce code duplication by ~60 lines
- Improve type safety in command handlers
- Make codebase easier to navigate
- Establish clear patterns for future development

## What Changes

### Phase 1: Utility Consolidation (Low Risk)
- Consolidate `utc_now()` to single definition in `models/base.py`
- Add `today_date()` to `models/base.py`
- Update 5 model files to import from base

### Phase 2: Handler Type Safety (Medium Risk)
- Create `HandlerContext` typed dataclass
- Update `CommandHandler.execute()` signature
- Migrate all handlers to use typed context

### Phase 3: Suppression Documentation (Low Risk)
- Move inline `# noqa` to `pyproject.toml` per-file-ignores with justification
- Document `# type: ignore` patterns in pyrefly config
- Remove any suppressions that can be fixed properly

### Phase 4: Cleanup (Low Risk)
- Remove unused `BaseModel` class (keep `utc_now`, `today_date`)
- Mark `HomeScreen` as deprecated with removal timeline
- Document large file refactoring opportunities (deferred)

## Impact

- Affected specs: `data-persistence`, `command-handlers`, `app-config`
- Affected code:
  - `src/jdo/models/base.py` - Add `today_date()`, update exports
  - `src/jdo/models/*.py` - Remove local `utc_now`/`today_date` definitions
  - `src/jdo/commands/handlers/base.py` - Add `HandlerContext` dataclass
  - `src/jdo/commands/handlers/*.py` - Update to use typed context
  - `pyproject.toml` - Add per-file-ignores with documentation
  - `src/jdo/screens/home.py` - Add deprecation notice

## Out of Scope

- Splitting large files (deferred - monitor growth first)
- Moving `ApiKeyScreen` to `screens/` (low value, breaks imports)
- Removing `HomeScreen` (needs NavSidebar completion first)

## Success Criteria

- Zero new `utc_now()` or `today_date()` definitions outside `base.py`
- `HandlerContext` typed class used in all handlers
- All `# noqa` comments either removed or documented in pyproject.toml
- All tests passing (1,368+)
- Lint/type checks passing
