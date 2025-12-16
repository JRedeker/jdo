# Tasks: Refactor Core Libraries (TDD)

This task list follows Test-Driven Development: write failing tests first, then implement to pass.

**Note**: This is foundational infrastructure. Many tests verify library integration rather than business logic.

## Phase 1: Dependencies

### 1.1 Add Dependencies
- [ ] Add `sqlmodel>=0.0.24` to pyproject.toml
- [ ] Add `pydantic-settings>=2.0.0` to pyproject.toml
- [ ] Add `platformdirs>=4.0.0` to pyproject.toml
- [ ] Add `pydantic-ai>=0.1.0` to pyproject.toml
- [ ] Add `rapidfuzz>=3.0.0` to pyproject.toml
- [ ] Run `uv sync` to install dependencies

## Phase 2: Paths Module

### 2.1 Path Function Tests (Red)
- [ ] Test: get_data_dir returns platformdirs user_data_dir for "jdo"
- [ ] Test: get_config_dir returns platformdirs user_config_dir for "jdo"
- [ ] Test: get_database_path returns data_dir / "jdo.db"
- [ ] Test: get_auth_path returns data_dir / "auth.json"
- [ ] Test: Directories are created if they don't exist

### 2.2 Implement Paths Module (Green)
- [ ] Create `src/jdo/paths.py`
- [ ] Implement path functions with platformdirs
- [ ] Run tests - all should pass

## Phase 3: Settings Module

### 3.1 Settings Tests (Red)
- [ ] Test: JDOSettings loads from environment variables with JDO_ prefix
- [ ] Test: JDO_AI_PROVIDER env var sets ai_provider field
- [ ] Test: JDO_AI_MODEL env var sets ai_model field
- [ ] Test: JDO_DATABASE_PATH env var overrides default database path
- [ ] Test: Settings loads from .env file
- [ ] Test: Env vars override .env file values
- [ ] Test: Missing required settings raise validation error

### 3.2 Implement Settings Module (Green)
- [ ] Create `src/jdo/config/__init__.py`
- [ ] Create `src/jdo/config/settings.py` with `JDOSettings(BaseSettings)`
- [ ] Configure env_prefix and env_file
- [ ] Run tests - all should pass

### 3.3 Settings Singleton Tests (Red)
- [ ] Test: get_settings returns same instance
- [ ] Test: reset_settings clears cached instance
- [ ] Test: After reset, get_settings returns fresh instance

### 3.4 Implement Settings Singleton (Green)
- [ ] Add get_settings and reset_settings functions
- [ ] Run tests - all should pass

## Phase 4: Database Module

### 4.1 Engine Tests (Red)
- [ ] Test: get_engine returns SQLAlchemy engine
- [ ] Test: Engine uses sqlite:/// URL with database_path
- [ ] Test: Engine has check_same_thread=False for SQLite

### 4.2 Implement Engine (Green)
- [ ] Create `src/jdo/db/__init__.py`
- [ ] Create `src/jdo/db/engine.py`
- [ ] Implement get_engine function
- [ ] Run tests - all should pass

### 4.3 Session Tests (Red)
- [ ] Test: get_session yields Session from engine
- [ ] Test: Session is committed on success
- [ ] Test: Session is rolled back on exception
- [ ] Test: Session is closed after use

### 4.4 Implement Session (Green)
- [ ] Implement get_session context manager
- [ ] Run tests - all should pass

### 4.5 Schema Tests (Red)
- [ ] Test: create_db_and_tables creates all SQLModel tables
- [ ] Test: Tables include stakeholders, goals, commitments, tasks
- [ ] Test: Foreign key constraints are created

### 4.6 Implement Schema (Green)
- [ ] Create `src/jdo/db/migrations.py`
- [ ] Implement create_db_and_tables
- [ ] Run tests - all should pass

## Phase 5: Model Conversion

### 5.1 Stakeholder SQLModel Tests (Red)
- [ ] Test: Stakeholder inherits from SQLModel with table=True
- [ ] Test: Stakeholder has tablename "stakeholders"
- [ ] Test: Stakeholder validates name non-empty
- [ ] Test: Stakeholder validates type is StakeholderType

### 5.2 Implement Stakeholder SQLModel (Green)
- [ ] Update `src/jdo/models/stakeholder.py` to use SQLModel
- [ ] Run tests - all should pass

### 5.3 Goal SQLModel Tests (Red)
- [ ] Test: Goal inherits from SQLModel with table=True
- [ ] Test: Goal has self-referential parent_goal_id FK
- [ ] Test: Goal validates required fields

### 5.4 Implement Goal SQLModel (Green)
- [ ] Update `src/jdo/models/goal.py` to use SQLModel
- [ ] Run tests - all should pass

### 5.5 Commitment SQLModel Tests (Red)
- [ ] Test: Commitment inherits from SQLModel with table=True
- [ ] Test: Commitment has stakeholder_id FK to stakeholders
- [ ] Test: Commitment has goal_id FK to goals (optional)
- [ ] Test: Commitment validates required fields

### 5.6 Implement Commitment SQLModel (Green)
- [ ] Update `src/jdo/models/commitment.py` to use SQLModel
- [ ] Run tests - all should pass

### 5.7 Task SQLModel Tests (Red)
- [ ] Test: Task inherits from SQLModel with table=True
- [ ] Test: Task has commitment_id FK to commitments
- [ ] Test: Task stores sub_tasks as JSON column
- [ ] Test: Task sub_tasks deserializes to list[SubTask]

### 5.8 Implement Task SQLModel (Green)
- [ ] Update `src/jdo/models/task.py` to use SQLModel
- [ ] Run tests - all should pass

## Phase 6: AI Agent Module

### 6.1 Agent Config Tests (Red)
- [ ] Test: Agent uses configured model from settings
- [ ] Test: Agent has system prompt
- [ ] Test: JDODependencies provides db_session access

### 6.2 Implement Agent Config (Green)
- [ ] Create `src/jdo/ai/__init__.py`
- [ ] Create `src/jdo/ai/agent.py` with PydanticAI setup
- [ ] Create `JDODependencies` dataclass
- [ ] Run tests - all should pass

### 6.3 Agent Tools Tests (Red)
- [ ] Test: get_current_commitments tool returns active commitments
- [ ] Test: Tool accesses database via dependencies
- [ ] Test: Tool returns structured dict

### 6.4 Implement Agent Tools (Green)
- [ ] Create `src/jdo/ai/tools.py`
- [ ] Implement get_current_commitments tool
- [ ] Run tests - all should pass

### 6.5 Streaming Tests (Red)
- [ ] Test: Agent supports streaming responses
- [ ] Test: Stream yields chunks as they arrive

### 6.6 Implement Streaming (Green)
- [ ] Add streaming handler
- [ ] Run tests - all should pass

## Phase 7: Auth Module Update

### 7.1 Auth Path Tests (Red)
- [ ] Test: AuthStore uses get_auth_path() for file location
- [ ] Test: Auth respects JDO_AUTH_PATH env var override

### 7.2 Implement Auth Path Update (Green)
- [ ] Update `src/jdo/auth/store.py` to use paths module
- [ ] Run tests - all should pass

## Phase 8: Integration Validation

### 8.1 Full Stack Tests
- [ ] Test: Settings → Engine → Session → CRUD cycle works
- [ ] Test: All models can be created and queried
- [ ] Test: Foreign key relationships work end-to-end
- [ ] Test: Agent can query via tools

### 8.2 Type Checking
- [ ] Run `uvx pyrefly check` and fix any errors

### 8.3 Linting
- [ ] Run `uv run ruff check src/ tests/` and fix any issues
- [ ] Run `uv run ruff format src/ tests/`

## Dependencies

- Phase 1 must complete first (dependencies installed)
- Phases 2-3 can run in parallel (paths and settings)
- Phase 4 depends on Phases 2-3 (needs paths for database)
- Phase 5 depends on Phase 4 (needs database for models)
- Phase 6 depends on Phases 3, 5 (needs settings and models)
- Phase 7 depends on Phase 2 (needs paths)
- Phase 8 requires all previous phases

## Running Tests

```bash
# Run all tests
uv run pytest

# Run config tests
uv run pytest tests/unit/config/ -v

# Run database tests
uv run pytest tests/integration/db/ -v

# Run with coverage
uv run pytest --cov=src/jdo --cov-report=term-missing

# Type check
uvx pyrefly check

# Lint
uv run ruff check src/ tests/
```
