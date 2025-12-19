# Change: Refactor Codebase Maintainability

## Why

A complexity analysis revealed three high-priority issues:
1. **Memory leak**: `ChatScreen._conversation` grows unbounded, risking crashes in long sessions and hitting API token limits
2. **God class**: `handlers.py` at 2,396 lines with 20 handler classes violates single-responsibility and impedes testing/navigation
3. **Duplicated navigation**: `app.py` has 10 `on_home_screen_*` handlers and 10 `_nav_to_*` methods with heavily duplicated entity-fetching code (~290 lines of duplication)

## What Changes

- **tui-chat**: Add conversation history pruning with configurable limit (default 50 messages)
- **command-handlers**: NEW capability - split handlers.py into domain-focused modules with a registry pattern
- **jdo-app**: Extract navigation data-fetching into a `NavigationService` and consolidate duplicate handler patterns

## Impact

- Affected specs: `tui-chat` (modified), `command-handlers` (new), `jdo-app` (modified)
- Affected code:
  - `src/jdo/screens/chat.py` - add pruning logic
  - `src/jdo/commands/handlers.py` - split into `handlers/` package
  - `src/jdo/commands/handlers/__init__.py` - registry
  - `src/jdo/commands/handlers/commitment_handlers.py`
  - `src/jdo/commands/handlers/goal_handlers.py`
  - `src/jdo/commands/handlers/task_handlers.py`
  - `src/jdo/commands/handlers/vision_handlers.py`
  - `src/jdo/commands/handlers/milestone_handlers.py`
  - `src/jdo/commands/handlers/integrity_handlers.py`
  - `src/jdo/commands/handlers/recurring_handlers.py`
  - `src/jdo/commands/handlers/utility_handlers.py` (help, show, view, cancel, edit, type, hours)
  - `src/jdo/app.py` - consolidate navigation handlers
  - `src/jdo/db/navigation.py` (new) - entity list data fetching

## Non-Goals

- **SQLModel alternatives**: Report incorrectly claimed 4 models; actual count is 10. SQLAlchemy overhead is justified.
- **pydantic-ai dependency issue**: Unactionable without upstream changes (no `[aws]`/`[temporal]` extras exist).
- **data_panel.py split**: At 1,053 lines with 52 methods, worth monitoring but not urgent; methods are focused and file has clear structure.
- **integrity/service.py**: At 670 lines, analyzed and found well-structured with single responsibility. Minor improvements (timezone helper, streak query limit) can be done opportunistically.
