# Tasks: Refactor Architectural Consistency

## Phase 1: Utility Function Consolidation

### 1.1 Update models/base.py
- [ ] 1.1.1 Add `today_date() -> date` function to `models/base.py`
- [ ] 1.1.2 Update `__all__` export in `models/base.py` if present
- [ ] 1.1.3 Run `uv run ruff check src/jdo/models/base.py`

### 1.2 Migrate Model Imports
- [ ] 1.2.1 Update `models/draft.py`: import `utc_now` from base, remove local definition
- [ ] 1.2.2 Update `models/goal.py`: import `utc_now`, `today_date` from base, remove local definitions
- [ ] 1.2.3 Update `models/milestone.py`: import `utc_now` from base, remove local definition
- [ ] 1.2.4 Update `models/stakeholder.py`: import `utc_now` from base, remove local definition
- [ ] 1.2.5 Update `models/task.py`: import `utc_now` from base, remove local definition
- [ ] 1.2.6 Update `models/task_history.py`: import `utc_now` from base, remove local definition
- [ ] 1.2.7 Update `models/vision.py`: import `utc_now`, `today_date` from base, remove local definitions

### 1.3 Migrate AI Module
- [ ] 1.3.1 Update `ai/dates.py`: import `today_date` from `models.base`, remove local definition

### 1.4 Phase 1 Validation
- [ ] 1.4.1 Run `uv run ruff check --fix src/jdo/models/ src/jdo/ai/`
- [ ] 1.4.2 Run `uv run ruff format src/jdo/models/ src/jdo/ai/`
- [ ] 1.4.3 Run `uvx pyrefly check src/`
- [ ] 1.4.4 Run `uv run pytest tests/unit/models/ -v`
- [ ] 1.4.5 Verify no remaining `def utc_now` outside base.py: `grep -rn "def utc_now" src/jdo/`
- [ ] 1.4.6 Verify no remaining `def today_date` outside base.py: `grep -rn "def today_date" src/jdo/`

## Phase 2: Handler Type Safety

### 2.1 Create HandlerContext
- [ ] 2.1.1 Add `HandlerContext` dataclass to `commands/handlers/base.py`
- [ ] 2.1.2 Update `CommandHandler.execute()` signature to use `HandlerContext`
- [ ] 2.1.3 Add backward-compatible `context_from_dict()` helper for migration

### 2.2 Update ChatScreen Context Building
- [ ] 2.2.1 Update `ChatScreen._route_command()` to build `HandlerContext`
- [ ] 2.2.2 Update `MainScreen` if it also builds handler context
- [ ] 2.2.3 Run `uv run pytest tests/tui/test_chat_screen.py -v`

### 2.3 Migrate Handlers
- [ ] 2.3.1 Update `commitment_handlers.py` to use `HandlerContext`
- [ ] 2.3.2 Update `goal_handlers.py` to use `HandlerContext`
- [ ] 2.3.3 Update `task_handlers.py` to use `HandlerContext`
- [ ] 2.3.4 Update `vision_handlers.py` to use `HandlerContext`
- [ ] 2.3.5 Update `milestone_handlers.py` to use `HandlerContext`
- [ ] 2.3.6 Update `recurring_handlers.py` to use `HandlerContext`
- [ ] 2.3.7 Update `integrity_handlers.py` to use `HandlerContext`
- [ ] 2.3.8 Update `utility_handlers.py` to use `HandlerContext`

### 2.4 Phase 2 Validation
- [ ] 2.4.1 Run `uv run ruff check --fix src/jdo/commands/`
- [ ] 2.4.2 Run `uv run ruff format src/jdo/commands/`
- [ ] 2.4.3 Run `uvx pyrefly check src/`
- [ ] 2.4.4 Run `uv run pytest tests/unit/commands/ -v`
- [ ] 2.4.5 Run `uv run pytest tests/tui/ -v`

## Phase 3: Suppression Cleanup

### 3.1 Audit Suppressions
- [ ] 3.1.1 List all `# noqa` comments: `grep -rn "# noqa" src/jdo/`
- [ ] 3.1.2 List all `# type: ignore` comments: `grep -rn "# type: ignore" src/jdo/`
- [ ] 3.1.3 Categorize each suppression as: justified, fixable, or removable

### 3.2 Configure Per-File Ignores
- [ ] 3.2.1 Add `[tool.ruff.lint.per-file-ignores]` section to `pyproject.toml`
- [ ] 3.2.2 Move `ARG002` ignores for handlers to per-file config
- [ ] 3.2.3 Move `ANN401` ignores for persistence to per-file config
- [ ] 3.2.4 Document rationale in comments above each ignore rule

### 3.3 Remove Inline Suppressions
- [ ] 3.3.1 Remove `# noqa: ARG002` from handler files (now in config)
- [ ] 3.3.2 Remove `# noqa: ANN401` from persistence/screen files (now in config)
- [ ] 3.3.3 Fix or document any remaining suppressions

### 3.4 Phase 3 Validation
- [ ] 3.4.1 Run `uv run ruff check src/jdo/` (verify no new errors)
- [ ] 3.4.2 Run `uvx pyrefly check src/` (verify no new errors)
- [ ] 3.4.3 Count remaining inline suppressions: `grep -c "# noqa\|# type: ignore" src/jdo/**/*.py`

## Phase 4: Cleanup

### 4.1 Remove Unused BaseModel
- [ ] 4.1.1 Remove `BaseModel` class from `models/base.py`
- [ ] 4.1.2 Update `models/base.py` module docstring
- [ ] 4.1.3 Verify no imports of `BaseModel`: `grep -rn "from jdo.models.base import.*BaseModel" src/`

### 4.2 Deprecate HomeScreen
- [ ] 4.2.1 Add deprecation warning to `HomeScreen.__init__()`
- [ ] 4.2.2 Update docstring to note deprecation and recommend NavSidebar
- [ ] 4.2.3 Add `# TODO: Remove in v2.0` comment

### 4.3 Final Validation
- [ ] 4.3.1 Run `uv run ruff check --fix src/ tests/`
- [ ] 4.3.2 Run `uv run ruff format src/ tests/`
- [ ] 4.3.3 Run `uvx pyrefly check src/`
- [ ] 4.3.4 Run `uv run pytest` (full suite)
- [ ] 4.3.5 Verify test count >= 1368

## Phase 5: Documentation

### 5.1 Update AGENTS.md
- [ ] 5.1.1 Document `utc_now`/`today_date` import convention
- [ ] 5.1.2 Document `HandlerContext` usage pattern
- [ ] 5.1.3 Document per-file-ignores location and policy

### 5.2 Spec Updates
- [ ] 5.2.1 Update `command-handlers` spec for HandlerContext
- [ ] 5.2.2 Update `data-persistence` spec if base.py changes affect it
