# Tasks: Refactor Core Libraries (TDD)

This task list follows Test-Driven Development: write failing tests first, then implement to pass.

**Note**: This is foundational infrastructure. Many tests verify library integration rather than business logic.

**Status**: ✅ Complete (core infrastructure implemented, some tasks deferred to dependent changes)

## Phase 1: Dependencies

### 1.1 Add Dependencies
- [x] Add `sqlmodel>=0.0.24` to pyproject.toml
- [x] Add `pydantic-settings>=2.0.0` to pyproject.toml
- [x] Add `platformdirs>=4.0.0` to pyproject.toml
- [x] Add `pydantic-ai>=0.1.0` to pyproject.toml
- [x] Add `rapidfuzz>=3.0.0` to pyproject.toml
- [x] Run `uv sync` to install dependencies

## Phase 2: Paths Module

### 2.1 Path Function Tests (Red)
- [x] Test: get_data_dir returns platformdirs user_data_dir for "jdo"
- [x] Test: get_config_dir returns platformdirs user_config_dir for "jdo"
- [x] Test: get_database_path returns data_dir / "jdo.db"
- [x] Test: get_auth_path returns data_dir / "auth.json"
- [x] Test: Directories are created if they don't exist

### 2.2 Implement Paths Module (Green)
- [x] Create `src/jdo/paths.py`
- [x] Implement path functions with platformdirs
- [x] Run tests - all should pass

## Phase 3: Settings Module

### 3.1 Settings Tests (Red)
- [x] Test: JDOSettings loads from environment variables with JDO_ prefix
- [x] Test: JDO_AI_PROVIDER env var sets ai_provider field
- [x] Test: JDO_AI_MODEL env var sets ai_model field
- [x] Test: JDO_DATABASE_PATH env var overrides default database path
- [x] Test: Settings loads from .env file
- [x] Test: Env vars override .env file values
- [x] Test: Missing required settings raise validation error

### 3.2 Implement Settings Module (Green)
- [x] Create `src/jdo/config/__init__.py`
- [x] Create `src/jdo/config/settings.py` with `JDOSettings(BaseSettings)`
- [x] Configure env_prefix and env_file
- [x] Run tests - all should pass

### 3.3 Settings Singleton Tests (Red)
- [x] Test: get_settings returns same instance
- [x] Test: reset_settings clears cached instance
- [x] Test: After reset, get_settings returns fresh instance

### 3.4 Implement Settings Singleton (Green)
- [x] Add get_settings and reset_settings functions
- [x] Run tests - all should pass

## Phase 4: Database Module

### 4.1 Engine Tests (Red)
- [x] Test: get_engine returns SQLAlchemy engine
- [x] Test: Engine uses sqlite:/// URL with database_path
- [x] Test: Engine has check_same_thread=False for SQLite

### 4.2 Implement Engine (Green)
- [x] Create `src/jdo/db/__init__.py`
- [x] Create `src/jdo/db/engine.py`
- [x] Implement get_engine function
- [x] Run tests - all should pass

### 4.3 Session Tests (Red)
- [x] Test: get_session yields Session from engine
- [x] Test: Session is committed on success
- [x] Test: Session is rolled back on exception
- [x] Test: Session is closed after use

### 4.4 Implement Session (Green)
- [x] Implement get_session context manager
- [x] Run tests - all should pass

### 4.5 Schema Tests (Red)
- [x] Test: create_db_and_tables creates all SQLModel tables
- [x] Test: Tables include stakeholders, goals, commitments, tasks
- [x] Test: Foreign key constraints are created

### 4.6 Implement Schema (Green)
- [x] Create `src/jdo/db/migrations.py`
- [x] Implement create_db_and_tables
- [x] Run tests - all should pass

## Phase 5: Model Conversion

### 5.1 Stakeholder SQLModel Tests (Red)
- [x] Test: Stakeholder inherits from SQLModel with table=True
- [x] Test: Stakeholder has tablename "stakeholders"
- [x] Test: Stakeholder validates name non-empty
- [x] Test: Stakeholder validates type is StakeholderType

### 5.2 Implement Stakeholder SQLModel (Green)
- [x] Update `src/jdo/models/stakeholder.py` to use SQLModel
- [x] Run tests - all should pass

### 5.3 Goal SQLModel Tests (Red)
- [x] Test: Goal inherits from SQLModel with table=True
- [x] Test: Goal has self-referential parent_goal_id FK
- [x] Test: Goal validates required fields

### 5.4 Implement Goal SQLModel (Green)
- [x] Update `src/jdo/models/goal.py` to use SQLModel
- [x] Run tests - all should pass

### 5.5 Commitment SQLModel Tests (Red)
- [x] Test: Commitment inherits from SQLModel with table=True
- [x] Test: Commitment has stakeholder_id FK to stakeholders
- [x] Test: Commitment has goal_id FK to goals (optional)
- [x] Test: Commitment validates required fields

### 5.6 Implement Commitment SQLModel (Green)
- [x] Update `src/jdo/models/commitment.py` to use SQLModel
- [x] Run tests - all should pass

### 5.7 Task SQLModel Tests (Red)
- [x] Test: Task inherits from SQLModel with table=True
- [x] Test: Task has commitment_id FK to commitments
- [x] Test: Task stores sub_tasks as JSON column
- [x] Test: Task sub_tasks deserializes to list[SubTask]

### 5.8 Implement Task SQLModel (Green)
- [x] Update `src/jdo/models/task.py` to use SQLModel
- [x] Run tests - all should pass

## Phase 6: AI Agent Module

### 6.1 Agent Config Tests (Red)
- [x] Test: Agent uses configured model from settings
- [x] Test: Agent has system prompt
- [x] Test: JDODependencies provides db_session access

### 6.2 Implement Agent Config (Green)
- [x] Create `src/jdo/ai/__init__.py`
- [x] Create `src/jdo/ai/agent.py` with PydanticAI setup
- [x] Create `JDODependencies` dataclass
- [x] Run tests - all should pass

### 6.3-6.6: Agent Tools & Streaming
**Moved to `add-conversational-tui`** - Tools are only meaningful with a consumer (the TUI). Streaming is provided by PydanticAI out of the box via `agent.run_stream()`.

## Phase 7: Auth Module Update

**Moved to `add-provider-auth`** - Auth module does not exist yet.

## Phase 8: Integration Validation

### 8.1 Full Stack Tests
- [x] Test: Settings → Engine → Session → CRUD cycle works
- [x] Test: All models can be created and queried
- [x] Test: Foreign key relationships work end-to-end
- ~~Test: Agent can query via tools~~ (moved to `add-conversational-tui`)

### 8.2 Type Checking
- [x] Run `uvx pyrefly check` and fix any errors

### 8.3 Linting
- [x] Run `uv run ruff check src/ tests/` and fix any issues
- [x] Run `uv run ruff format src/ tests/`

## Deferred Tasks Summary

| Task | Moved To | Rationale |
|------|----------|-----------|
| Agent Tools (6.3-6.4) | `add-conversational-tui` | Tools need a consumer; TUI will define exact interface |
| Streaming (6.5-6.6) | N/A (skip) | PydanticAI provides streaming out of the box |
| Auth Path Update (7.x) | `add-provider-auth` | Auth module doesn't exist yet |
| Agent query via tools test | `add-conversational-tui` | Depends on tools implementation |

## Running Tests

```bash
# Run all tests
uv run pytest

# Run config tests
uv run pytest tests/unit/config/ -v

# Run database tests
uv run pytest tests/unit/db/ -v

# Run with coverage
uv run pytest --cov=src/jdo --cov-report=term-missing

# Type check
uvx pyrefly check

# Lint
uv run ruff check src/ tests/
```
