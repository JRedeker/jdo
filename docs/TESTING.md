# JDO Testing Guide

Best practices and guidelines for writing tests in the JDO codebase.

## Quick Reference

```bash
# Run all tests
uv run pytest

# Run tests in parallel (faster)
uv run pytest -n auto

# Run with coverage
uv run pytest --cov=src/jdo --cov-report=term-missing

# Run specific test categories
uv run pytest -m unit           # Unit tests only
uv run pytest -m integration    # Integration tests only
uv run pytest tests/repl/       # REPL tests only

# Run a single test file
uv run pytest tests/unit/ai/test_agent.py -v

# Run hypothesis tests with more examples
uv run pytest tests/unit/ai/test_date_parsing_hypothesis.py --hypothesis-seed=0
```

---

## Test Organization

```
tests/
├── conftest.py              # Shared fixtures (db_engine, db_session, test_settings)
├── unit/                    # Fast, isolated tests (no I/O)
│   ├── ai/                  # AI agent, tools, extraction tests
│   ├── auth/                # Authentication tests
│   ├── commands/            # Command parser and handler tests
│   ├── config/              # Settings and paths tests
│   ├── db/                  # Database service tests (mocked)
│   ├── integrity/           # Integrity service tests
│   ├── models/              # SQLModel entity tests
│   └── recurrence/          # Recurrence calculation tests
├── integration/             # Tests with real database
│   ├── conftest.py          # Integration-specific fixtures
│   ├── auth/                # OAuth flow integration tests
│   └── db/                  # CRUD and migration tests
├── output/                  # Rich formatter tests
└── repl/                    # REPL loop and session tests
```

### Test Categories (Markers)

| Marker | Description | Example |
|--------|-------------|---------|
| `@pytest.mark.unit` | Fast tests, no external dependencies | Model validation |
| `@pytest.mark.integration` | Tests with real database | CRUD operations |
| `@pytest.mark.repl` | REPL-specific tests | Command handling |
| `@pytest.mark.slow` | Tests needing extended timeout | Complex AI workflows |

---

## Writing Tests

### Basic Test Structure

```python
"""Tests for [module description]."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest


class TestFeatureName:
    """Tests for [feature description]."""

    def test_specific_behavior(self) -> None:
        """[Behavior] when [condition]."""
        # Arrange
        input_data = "test input"
        
        # Act
        result = function_under_test(input_data)
        
        # Assert
        assert result == expected_value

    def test_edge_case(self) -> None:
        """[Edge case description]."""
        with pytest.raises(ValueError, match="expected message"):
            function_under_test(invalid_input)
```

### Test Naming Conventions

- **Test files**: `test_<module_name>.py`
- **Test classes**: `Test<FeatureName>`
- **Test methods**: `test_<behavior>_<condition>` or `test_<what_it_does>`

Good examples:
```python
def test_commitment_status_defaults_to_pending(self) -> None: ...
def test_parse_date_raises_error_for_vague_input(self) -> None: ...
def test_save_commitment_creates_missing_stakeholder(self) -> None: ...
```

---

## Fixtures

### Core Fixtures (from `tests/conftest.py`)

| Fixture | Scope | Description |
|---------|-------|-------------|
| `db_engine` | function | In-memory SQLite engine with tables |
| `db_session` | function | Database session with auto-rollback |
| `temp_data_dir` | function | Temporary directory for file tests |
| `test_settings` | function | Settings with test environment variables |

### Using Database Fixtures

```python
def test_save_commitment(self, db_session) -> None:
    """Test saving a commitment to the database."""
    from jdo.models import Commitment, CommitmentStatus
    
    commitment = Commitment(
        deliverable="Test task",
        stakeholder_id=uuid4(),
        due_date=date(2025, 12, 31),
        status=CommitmentStatus.PENDING,
    )
    db_session.add(commitment)
    db_session.commit()
    
    assert commitment.id is not None
```

### Integration Test Fixtures (from `tests/integration/conftest.py`)

| Fixture | Description |
|---------|-------------|
| `populated_db` | Database pre-seeded with stakeholders, goals, commitments |
| `auth_store_path` | Temporary path for auth.json |

---

## Testing Async Code

JDO uses `pytest-asyncio` with automatic mode. Async tests are detected automatically.

```python
async def test_agent_can_run_with_test_model(self) -> None:
    """Agent can be run with TestModel for testing."""
    from pydantic_ai.models.test import TestModel
    from jdo.ai.agent import JDODependencies, create_agent_with_model

    mock_session = MagicMock()
    deps = JDODependencies(session=mock_session)
    agent = create_agent_with_model(TestModel(), with_tools=False)

    result = await agent.run("Test prompt", deps=deps)

    assert result.output == "success (no tool calls)"
```

---

## Testing AI Components

### Using TestModel (Recommended)

PydanticAI provides `TestModel` for testing without real API calls:

```python
from pydantic_ai.models.test import TestModel
from jdo.ai.agent import create_agent_with_model

def test_agent_has_tools_registered(self) -> None:
    """Agent should have expected tools registered."""
    agent = create_agent_with_model(TestModel())
    
    toolset = agent._function_toolset
    tool_names = list(toolset.tools)
    
    assert "query_current_commitments" in tool_names
```

### Mocking HTTP Requests (pytest-httpx)

For testing real provider integrations:

```python
def test_openai_request(self, httpx_mock) -> None:
    """Test request to OpenAI API."""
    httpx_mock.add_response(
        url="https://api.openai.com/v1/chat/completions",
        json={
            "choices": [{"message": {"content": "Test response"}}]
        }
    )
    
    # Your test code that makes HTTP requests
```

### Testing AI Extraction

```python
def test_extract_commitment_from_text(self) -> None:
    """Extraction should identify commitment components."""
    from jdo.ai.extraction import extract_commitment_data
    
    result = extract_commitment_data(
        "Send the report to Sarah by Friday"
    )
    
    assert result["deliverable"] == "Send the report"
    assert result["stakeholder"] == "Sarah"
    # Date assertions with mocked today
```

---

## Property-Based Testing (Hypothesis)

Use hypothesis for testing functions with many possible inputs.

### When to Use Hypothesis

- Date/time parsing functions
- Recurrence calculations
- Input validation
- String processing
- Numerical calculations

### Basic Pattern

```python
from hypothesis import given, settings
from hypothesis import strategies as st

class TestDateParsingRobustness:
    """Property-based tests for date parser."""

    @given(st.text(max_size=200))
    @settings(max_examples=100)
    def test_parse_date_never_crashes(self, text: str) -> None:
        """parse_date should handle any string without crashing."""
        from jdo.ai.dates import ParseError, VagueDateError, parse_date

        try:
            result = parse_date(text)
            assert isinstance(result, date)
        except (ParseError, VagueDateError):
            pass  # Expected for invalid input
```

### Useful Strategies

```python
# Generate valid dates
valid_dates = st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31))

# Generate integers in range
st.integers(min_value=1, max_value=12)

# Sample from specific values
st.sampled_from(["Monday", "Tuesday", "Wednesday"])

# Generate text with constraints
st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('L', 'N')))
```

### Filtering with assume()

```python
from hypothesis import assume

@given(st.integers(), st.integers())
def test_division(self, a: int, b: int) -> None:
    assume(b != 0)  # Skip cases where b is zero
    result = a / b
    assert result * b == a
```

---

## Parametrized Tests

Use `@pytest.mark.parametrize` for testing multiple cases:

```python
@pytest.mark.parametrize("status,expected_color", [
    (CommitmentStatus.PENDING, "yellow"),
    (CommitmentStatus.IN_PROGRESS, "blue"),
    (CommitmentStatus.COMPLETED, "green"),
    (CommitmentStatus.AT_RISK, "red"),
    (CommitmentStatus.ABANDONED, "dim"),
])
def test_status_colors(self, status, expected_color) -> None:
    """Each status should have the correct color."""
    from jdo.output.formatters import get_status_color
    
    assert get_status_color(status) == expected_color
```

### Parametrize with IDs

```python
@pytest.mark.parametrize("input_text,expected_date", [
    pytest.param("tomorrow", date(2025, 1, 2), id="tomorrow"),
    pytest.param("next Friday", date(2025, 1, 3), id="next-friday"),
    pytest.param("December 25", date(2025, 12, 25), id="absolute-date"),
])
def test_date_parsing(self, input_text, expected_date) -> None:
    ...
```

---

## Mocking Best Practices

### Use `patch` for External Dependencies

```python
from unittest.mock import patch, MagicMock

def test_with_mocked_settings(self) -> None:
    """Test with mocked settings."""
    with patch("jdo.config.settings.get_settings") as mock_settings:
        mock_settings.return_value.ai_provider = "openai"
        mock_settings.return_value.ai_model = "gpt-4o"
        
        # Test code that uses settings
```

### Use `monkeypatch` for Environment Variables

```python
def test_with_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test with environment variable override."""
    monkeypatch.setenv("JDO_DATABASE_PATH", "/tmp/test.db")
    
    from jdo.config.settings import reset_settings, get_settings
    reset_settings()
    
    settings = get_settings()
    assert str(settings.database_path) == "/tmp/test.db"
```

### Mock Database Queries

```python
def test_list_command(self, mock_db_session) -> None:
    """Test list command with mocked results."""
    mock_db_session.exec.return_value.all.return_value = [
        MagicMock(deliverable="Task 1"),
        MagicMock(deliverable="Task 2"),
    ]
    
    result = handle_list_command(mock_db_session)
    
    assert len(result) == 2
```

---

## Testing REPL Components

### Session State Tests

```python
def test_session_tracks_message_history(self) -> None:
    """Session should maintain message history."""
    from jdo.repl.session import Session
    
    session = Session()
    session.add_user_message("Hello")
    session.add_assistant_message("Hi there!")
    
    assert len(session.message_history) == 2
    assert session.message_history[0]["role"] == "user"
```

### Slash Command Tests

```python
async def test_help_command_returns_true(self, mock_db_session) -> None:
    """Help command should return True (handled)."""
    from jdo.repl.loop import handle_slash_command
    from jdo.repl.session import Session
    
    session = Session()
    result = await handle_slash_command("/help", session, mock_db_session)
    
    assert result is True
```

---

## Test Timeouts

All tests have a default 30-second timeout. For slower tests:

```python
@pytest.mark.timeout(60)
def test_slow_operation(self) -> None:
    """Test that needs more time."""
    ...

@pytest.mark.slow
@pytest.mark.timeout(120)
def test_very_slow_operation(self) -> None:
    """Test that needs extended time."""
    ...
```

---

## Running Tests in Parallel

Use pytest-xdist for faster test runs:

```bash
# Auto-detect CPU count
uv run pytest -n auto

# Specific number of workers
uv run pytest -n 4

# Group tests by module (better for fixtures)
uv run pytest -n auto --dist loadscope
```

**Note**: Tests must be independent to run in parallel. Avoid shared state.

---

## Coverage Requirements

- Minimum coverage: **70%** (configured in `pyproject.toml`)
- Current coverage: ~85%

```bash
# Run with coverage report
uv run pytest --cov=src/jdo --cov-report=term-missing

# Generate HTML report
uv run pytest --cov=src/jdo --cov-report=html
# Open htmlcov/index.html
```

### Excluding Code from Coverage

```python
if TYPE_CHECKING:  # Automatically excluded
    from some_module import SomeType

def debug_function():  # pragma: no cover
    """Only used for debugging."""
    ...
```

---

## Common Patterns

### Testing Model Validation

```python
def test_commitment_requires_deliverable(self) -> None:
    """Commitment should require a deliverable."""
    from pydantic import ValidationError
    from jdo.models import Commitment
    
    with pytest.raises(ValidationError):
        Commitment(stakeholder_id=uuid4(), due_date=date.today())
```

### Testing Database Constraints

```python
@pytest.mark.integration
def test_stakeholder_name_unique(self, populated_db) -> None:
    """Stakeholder names should be unique."""
    from sqlalchemy.exc import IntegrityError
    from jdo.models import Stakeholder
    
    # populated_db already has "Self" stakeholder
    duplicate = Stakeholder(name="Self", type=StakeholderType.SELF)
    populated_db.add(duplicate)
    
    with pytest.raises(IntegrityError):
        populated_db.commit()
```

### Testing Error Messages

```python
def test_vague_date_error_message(self) -> None:
    """Vague date should include helpful message."""
    from jdo.ai.dates import VagueDateError, parse_date
    
    with pytest.raises(VagueDateError) as exc_info:
        parse_date("soon")
    
    assert "too vague" in str(exc_info.value)
    assert "specific date" in str(exc_info.value)
```

---

## Troubleshooting

### Resource Warnings

If you see `ResourceWarning: unclosed database`, ensure fixtures properly close connections:

```python
@pytest.fixture
def db_session(db_engine):
    session = Session(db_engine)
    try:
        yield session
    finally:
        session.close()  # Always close
```

### Flaky Tests

1. Check for shared state between tests
2. Use `@pytest.mark.timeout` to catch hanging tests
3. Mock time-dependent operations
4. Use `hypothesis` for edge case discovery

### Slow Tests

1. Run in parallel: `pytest -n auto`
2. Use in-memory SQLite instead of file-based
3. Mock external services (AI, HTTP)
4. Mark slow tests: `@pytest.mark.slow`

---

## Pre-commit Checklist

Before committing, ensure:

1. All tests pass: `uv run pytest`
2. Coverage is maintained: `uv run pytest --cov=src/jdo`
3. Linting passes: `uv run ruff check src/ tests/`
4. Formatting is correct: `uv run ruff format src/ tests/`
5. Types are correct: `uvx pyrefly check src/`
