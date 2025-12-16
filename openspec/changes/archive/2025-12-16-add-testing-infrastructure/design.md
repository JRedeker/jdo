# Design: Testing Infrastructure

## Context

JDO is a commitment-tracking TUI application with 6 pending proposals spanning models, persistence, configuration, AI integration, authentication, and UI. Establishing a solid testing foundation before implementation enables TDD practices and ensures consistent test patterns across all features.

**Stakeholders**: Developers implementing JDO features.

**Constraints**:
- Python 3.11+, pytest 8.0+
- Must support async testing (Textual, PydanticAI)
- Must isolate database state between tests
- Must mock external services (AI APIs, OAuth endpoints)

## Goals / Non-Goals

**Goals**:
- Establish pytest configuration optimized for the JDO stack
- Provide reusable fixtures for database, settings, and TUI testing
- Enable visual regression testing for TUI components
- Support mocking HTTP requests for OAuth/AI integration
- Achieve high code coverage with fast test execution

**Non-Goals**:
- End-to-end testing with real AI providers (cost/speed prohibitive)
- Load/performance testing
- Browser-based testing

## Decisions

### Decision 1: pytest-asyncio Auto Mode

**What**: Use `asyncio_mode = "auto"` in pytest configuration.

**Why**:
- Textual and PydanticAI are async-first
- Auto mode eliminates need for `@pytest.mark.asyncio` on every test
- Async fixtures work seamlessly with async tests

**Implementation** (pyproject.toml):
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

**Context7 Reference**: pytest-asyncio documentation confirms auto mode automatically treats async functions as asyncio tests.

### Decision 2: In-Memory SQLite with StaticPool

**What**: Use in-memory SQLite database with `StaticPool` for test isolation.

**Why**:
- Fast: No disk I/O, tables created fresh per test
- Isolated: Each test gets clean database state
- Compatible: SQLModel patterns work identically to production

**Implementation**:
```python
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

@pytest.fixture
def db_engine():
    """Create in-memory database engine."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine

@pytest.fixture
def db_session(db_engine):
    """Provide database session for tests."""
    with Session(db_engine) as session:
        yield session
```

**Context7 Reference**: SQLModel testing docs recommend this exact pattern for FastAPI/SQLModel test isolation.

### Decision 3: Settings Override Fixture

**What**: Provide fixture that creates isolated `JDOSettings` with temporary paths.

**Why**:
- Tests shouldn't write to real user data directories
- Environment variables should be controlled per test
- Settings singleton must be reset between tests

**Implementation**:
```python
import tempfile
from pathlib import Path

@pytest.fixture
def temp_data_dir(tmp_path):
    """Provide temporary data directory."""
    data_dir = tmp_path / "jdo_data"
    data_dir.mkdir()
    return data_dir

@pytest.fixture
def test_settings(temp_data_dir, monkeypatch):
    """Provide isolated settings for tests."""
    monkeypatch.setenv("JDO_DATABASE_PATH", str(temp_data_dir / "test.db"))
    monkeypatch.setenv("JDO_AI_PROVIDER", "test")
    
    # Reset settings singleton
    from jdo.config import reset_settings
    reset_settings()
    
    from jdo.config import get_settings
    yield get_settings()
    
    reset_settings()
```

**Context7 Reference**: pydantic-settings supports environment variable overrides; pytest's `monkeypatch` fixture is the standard approach.

### Decision 4: Textual Pilot for TUI Testing

**What**: Use Textual's `run_test()` context manager and `Pilot` class for UI testing.

**Why**:
- Official Textual testing approach
- Simulates key presses, clicks, and screen navigation
- Works with pytest-asyncio auto mode
- Supports snapshot testing for visual regression

**Implementation**:
```python
from jdo.app import JDOApp

async def test_app_startup():
    """Test application starts without errors."""
    app = JDOApp()
    async with app.run_test() as pilot:
        # Verify initial screen
        assert app.screen is not None
        
        # Simulate key press
        await pilot.press("q")

async def test_navigation():
    """Test screen navigation."""
    app = JDOApp()
    async with app.run_test() as pilot:
        await pilot.press("g")  # Go to goals
        assert app.screen.__class__.__name__ == "GoalListScreen"
```

**Context7 Reference**: Textual docs provide comprehensive Pilot API for `press()`, `click()`, `hover()`, and `pause()`.

### Decision 5: pytest-httpx for HTTP Mocking

**What**: Use `pytest-httpx` fixture to mock OAuth token exchanges and AI API calls.

**Why**:
- Clean fixture-based API (`httpx_mock.add_response()`)
- Supports async httpx client used in auth module
- Can verify request details were correct
- Raises clear errors if unexpected requests occur

**Implementation**:
```python
from pytest_httpx import HTTPXMock

async def test_oauth_token_exchange(httpx_mock: HTTPXMock):
    """Test OAuth authorization code exchange."""
    httpx_mock.add_response(
        method="POST",
        url="https://console.anthropic.com/v1/oauth/token",
        json={
            "access_token": "test_access",
            "refresh_token": "test_refresh",
            "expires_in": 3600,
        },
    )
    
    from jdo.auth import exchange_code
    result = await exchange_code("test_code", "test_verifier")
    
    assert result["access_token"] == "test_access"
    
    # Verify request was made correctly
    request = httpx_mock.get_request()
    assert request.method == "POST"
```

**Context7 Reference**: pytest-httpx provides `add_response()`, `add_exception()`, and request verification methods.

### Decision 6: Snapshot Testing for TUI Visual Regression

**What**: Use `pytest-textual-snapshot` for visual regression testing of TUI screens.

**Why**:
- Catches unintended visual changes
- Baselines stored in version control
- Easy to update when changes are intentional

**Implementation**:
```python
def test_home_screen_snapshot(snap_compare):
    """Verify home screen renders correctly."""
    assert snap_compare("src/jdo/app.py")

def test_commitment_detail_snapshot(snap_compare):
    """Verify commitment detail screen layout."""
    assert snap_compare(
        "src/jdo/app.py",
        press=["enter"],  # Navigate to detail
    )
```

**Update baselines**:
```bash
pytest --snapshot-update
```

### Decision 7: Test Organization by Scope

**What**: Organize tests into `unit/`, `integration/`, and `tui/` directories.

**Why**:
- Clear separation of test types
- Can run subsets independently
- Unit tests fast, integration tests may need more setup
- TUI tests have unique fixture requirements

**Structure**:
```
tests/
├── conftest.py              # Shared fixtures (db, settings, etc.)
├── unit/
│   ├── conftest.py          # Unit-specific fixtures
│   ├── models/
│   │   ├── test_commitment.py
│   │   ├── test_goal.py
│   │   ├── test_task.py
│   │   └── test_stakeholder.py
│   ├── config/
│   │   └── test_settings.py
│   └── paths/
│       └── test_paths.py
├── integration/
│   ├── conftest.py          # Integration-specific fixtures
│   ├── db/
│   │   ├── test_crud.py
│   │   └── test_relationships.py
│   └── auth/
│       └── test_oauth.py
└── tui/
    ├── conftest.py          # TUI-specific fixtures
    ├── snapshots/           # Visual regression baselines
    ├── test_app.py
    ├── test_screens.py
    └── test_bindings.py
```

### Decision 8: Coverage Configuration

**What**: Configure pytest-cov with reasonable thresholds and exclusions.

**Why**:
- Track coverage progress
- Exclude generated/third-party code
- Fail CI below threshold (recommend 80% initially)

**Implementation** (pyproject.toml):
```toml
[tool.coverage.run]
source = ["src/jdo"]
branch = true
omit = [
    "*/migrations/*",
    "*/__init__.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
fail_under = 80
```

## Fixture Dependency Graph

```
                    ┌─────────────┐
                    │  tmp_path   │ (pytest built-in)
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
      ┌───────────────┐         ┌───────────────┐
      │ temp_data_dir │         │   db_engine   │
      └───────┬───────┘         └───────┬───────┘
              │                         │
              ▼                         ▼
      ┌───────────────┐         ┌───────────────┐
      │ test_settings │         │  db_session   │
      └───────────────┘         └───────────────┘

      ┌───────────────┐
      │  httpx_mock   │ (pytest-httpx)
      └───────────────┘

      ┌───────────────┐
      │  snap_compare │ (pytest-textual-snapshot)
      └───────────────┘
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Snapshot tests brittle to styling changes | Review snapshots in PRs; update intentional changes |
| In-memory SQLite differs from file-based | Acceptable for unit tests; add file-based integration tests if needed |
| HTTP mocks may drift from real API | Keep mock responses minimal; test happy path and error cases |
| Coverage threshold too aggressive | Start at 80%, adjust based on actual codebase |

## Migration Plan

Since this is greenfield, no migration needed:

1. Add dev dependencies to `pyproject.toml`
2. Create `tests/conftest.py` with shared fixtures
3. Create directory structure for test organization
4. Add sample tests demonstrating each pattern
5. Configure CI to run tests

## Open Questions

1. **Should we use factory_boy for test data?**
   - Recommendation: Not initially; SQLModel model creation is simple enough
   - Revisit if test data setup becomes verbose

2. **Should we test AI agent responses with real API calls?**
   - Recommendation: No; use mocks for speed and cost
   - Consider separate "smoke test" suite for manual validation

3. **Should we parallelize tests with pytest-xdist?**
   - Recommendation: Not initially; add if test suite becomes slow (>30s)
