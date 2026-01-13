# Design: Refactor Architectural Consistency

## Context

The JDO codebase has grown to ~8,500 lines of source code with 82 Python files. A comprehensive audit revealed consistency issues that emerged organically during rapid development. This design document captures the technical decisions for addressing these issues systematically.

### Current State Analysis

| Issue | Count | Impact | Risk to Fix |
|-------|-------|--------|-------------|
| Duplicate `utc_now()` | 8 files | Maintenance burden | Low |
| Duplicate `today_date()` | 3 files | Maintenance burden | Low |
| Unused `BaseModel` class | 1 file | Confusion | Low |
| Untyped handler context | 20+ handlers | Type safety gap | Medium |
| Undocumented suppressions | 71 comments | Technical debt | Low |
| Large files (>800 LOC) | 4 files | Readability | High (deferred) |

## Goals / Non-Goals

### Goals
1. Eliminate code duplication in utility functions
2. Improve type safety in command handler interface
3. Document or eliminate lint/type suppressions
4. Establish patterns that prevent future inconsistency

### Non-Goals
1. Splitting large files (premature - monitor growth first)
2. Major architectural changes (scope creep)
3. Performance optimization (not the issue)
4. Changing external interfaces (breaking changes)

## Decisions

### Decision 1: Utility Function Consolidation

**What**: Move all datetime utilities to `models/base.py` and import everywhere.

**Why**: 
- `utc_now()` is identical in all 8 files
- `today_date()` is identical in all 3 files
- `base.py` already exists and is partially used
- Simple find-and-replace refactor

**Alternatives Considered**:
1. Create separate `jdo.utils.datetime` module - Rejected: overkill for 2 functions
2. Use stdlib directly everywhere - Rejected: loses consistency, `UTC` import verbosity

**Implementation**:
```python
# models/base.py (updated)
from datetime import UTC, date, datetime

def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)

def today_date() -> date:
    """Get today's date in UTC."""
    return datetime.now(UTC).date()
```

All model files import: `from jdo.models.base import utc_now, today_date`

---

### Decision 2: Typed Handler Context

**What**: Replace `dict[str, Any]` with `HandlerContext` dataclass.

**Why**:
- Current context has no type safety
- Easy to pass wrong keys or forget required fields
- IDE autocomplete doesn't work
- Documentation is implicit (scattered in handler code)

**Alternatives Considered**:
1. TypedDict - Rejected: still allows missing keys, less IDE support
2. Protocol - Rejected: overkill, we own both sides
3. Keep dict with documentation - Rejected: doesn't prevent bugs

**Implementation**:
```python
# commands/handlers/base.py
@dataclass
class HandlerContext:
    """Context passed to command handlers.
    
    Attributes:
        conversation_history: Recent messages for AI context.
        extracted_fields: Fields extracted from conversation.
        draft_data: Current draft being built (if any).
        timezone: User's timezone setting.
        available_hours: Hours remaining today (if set).
    """
    conversation_history: list[dict[str, str]]
    extracted_fields: dict[str, Any]
    draft_data: dict[str, Any] | None = None
    timezone: str = "America/New_York"
    available_hours: float | None = None
```

**Migration Path**:
1. Add `HandlerContext` class
2. Update `CommandHandler.execute()` signature
3. Update `ChatScreen._route_command()` to build context
4. Update each handler (20 files, mechanical change)
5. Remove old dict construction

---

### Decision 3: Suppression Documentation Strategy

**What**: Move justified suppressions to pyproject.toml, fix or remove unjustified ones.

**Why**:
- AGENTS.md says "NO `# noqa` comments - configure in pyproject.toml per-file-ignores"
- Inline suppressions hide the reason from reviewers
- Centralized config makes audit easier

**Categories Found**:

| Suppression | Count | Action |
|-------------|-------|--------|
| `ARG002` (unused arg) | 15 | Move to per-file-ignores (handler interface) |
| `ANN401` (Any type) | 4 | Move to per-file-ignores (persistence polymorphism) |
| `BLE001` (bare except) | 1 | Fix or justify |
| `type: ignore` | 36 | Document pyrefly false positives |

**Implementation**:
```toml
# pyproject.toml addition
[tool.ruff.lint.per-file-ignores]
# Handler interface requires context param even if unused
"src/jdo/commands/handlers/*.py" = ["ARG002"]
# Persistence service returns multiple entity types
"src/jdo/db/persistence.py" = ["ANN401"]
"src/jdo/screens/chat.py" = ["ANN401"]
"src/jdo/screens/main.py" = ["ANN401"]
```

---

### Decision 4: Cleanup Unused Code

**What**: Remove `BaseModel` class, deprecate `HomeScreen`.

**Why**:
- `BaseModel` is never used (entities inherit directly from `SQLModel`)
- `HomeScreen` is superseded by `NavSidebar` + `MainScreen`

**Implementation**:
1. Remove `BaseModel` class from `models/base.py` (keep utility functions)
2. Add deprecation warning to `HomeScreen.__init__()`
3. Update `__all__` exports

---

## Risks / Trade-offs

### Risk 1: Handler Context Migration
**Risk**: Changing handler signature could break tests.
**Mitigation**: 
- Comprehensive test coverage exists (1,368 tests)
- Mechanical change with search-replace
- Run tests after each handler update

### Risk 2: Import Cycle from Base
**Risk**: Adding `today_date()` to base could cause import cycles.
**Mitigation**:
- `base.py` only imports from stdlib
- No model imports other models via base
- Already works for `utc_now()` in 3 files

### Risk 3: Suppression Removal Breaks Build
**Risk**: Removing suppressions might expose real issues.
**Mitigation**:
- Run lint/type checks after each removal
- Only move justified suppressions to config
- Fix any exposed issues before proceeding

## Migration Plan

### Phase 1: Utility Consolidation (Day 1)
1. Add `today_date()` to `models/base.py`
2. Update model imports (5 files)
3. Remove duplicate definitions
4. Run tests

### Phase 2: Handler Context (Day 1-2)
1. Add `HandlerContext` dataclass
2. Update base class signature
3. Update ChatScreen context building
4. Migrate handlers one module at a time
5. Run tests after each module

### Phase 3: Suppression Cleanup (Day 2)
1. Audit each suppression
2. Move justified ones to pyproject.toml
3. Fix or document remaining
4. Verify lint/type checks pass

### Phase 4: Cleanup (Day 2)
1. Remove `BaseModel` class
2. Add deprecation to `HomeScreen`
3. Update exports
4. Final test run

## Open Questions

1. **Should we create a migration guide for the handler context change?**
   - Decision: No, internal change with no external consumers.

2. **Should `HomeScreen` be removed entirely?**
   - Decision: Deprecate first, remove after NavSidebar is fully validated.

3. **Should large files be split now?**
   - Decision: No, monitor growth. Current sizes are manageable.
