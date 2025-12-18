## Context

JDO is a terminal application with AI integration, SQLite persistence, and a Textual TUI. The codebase has strict linting rules but lacks infrastructure for:
- Debugging production issues (no structured logging)
- Graceful error handling (no exception taxonomy)
- Enforcing code quality pre-commit
- Monitoring AI interactions and errors in production
- Evolving database schema over time

Stakeholders: Developers maintaining the codebase, future users experiencing errors.

## Goals / Non-Goals

### Goals
- Enable structured, queryable logging with minimal code changes
- Provide a clear exception hierarchy for error categorization and recovery
- Enforce existing ruff/pyrefly rules before commits land
- Establish test coverage standards and missing test categories
- Enable production error tracking and AI call observability
- Support versioned database migrations without data loss

### Non-Goals
- Real-time log aggregation (local file logging is sufficient for v1)
- Custom dashboards or alerting (Sentry defaults are sufficient)
- Complex migration strategies (simple forward migrations only)
- Performance profiling (basic Sentry tracing is sufficient)

## Decisions

### Logging: Loguru

**Decision**: Use Loguru as the primary logging library.

**Why**:
- Zero-config setup with sensible defaults
- Built-in file rotation, compression, and retention
- Structured logging with JSON serialization
- Easy interception of stdlib logging (for third-party libs)
- Lazy evaluation of log messages for performance
- Better exception formatting with full traceback context

**Alternatives considered**:
- `structlog`: More powerful but requires more configuration; Loguru's simplicity fits our needs
- `logging` (stdlib): Verbose configuration, no built-in rotation, weaker exception support
- `logfire` (Pydantic): Tied to their observability platform; we want Sentry

**Configuration approach**:
```python
# Single configuration point in src/jdo/logging.py
from loguru import logger

def configure_logging(level: str, log_path: Path | None = None) -> None:
    logger.remove()  # Remove default handler
    logger.add(sys.stderr, level=level, format="...")  # Console
    if log_path:
        logger.add(log_path, rotation="10 MB", retention="7 days", serialize=True)
```

### Error Handling: Domain-Based Exception Hierarchy

**Decision**: Create a custom exception hierarchy organized by domain.

**Why**:
- Enables catch-all handlers per domain (e.g., catch all AI errors)
- Supports recovery hints for user-facing errors
- Allows consistent error logging with context
- Best practice per Python community consensus

**Hierarchy**:
```
JDOError (base)
├── ConfigError          # Settings, environment issues
├── DatabaseError        # SQLModel, SQLite issues
│   └── MigrationError   # Alembic-specific
├── AIError              # Provider, model, tool issues
│   ├── ProviderError    # API failures
│   └── ExtractionError  # Response parsing
├── AuthError            # OAuth, token issues
└── TUIError             # Textual, widget issues
```

**Alternatives considered**:
- Flat exceptions: Loses categorization benefits
- Per-module exceptions: Too granular, hard to catch related errors

### Pre-commit Hooks: Ruff + Type Checking

**Decision**: Use pre-commit framework with ruff and pyrefly hooks.

**Why**:
- Ensures code passes lint/format before commit
- Runs fast (ruff is extremely fast)
- Matches existing CI requirements
- Industry standard for Python projects

**Configuration** (`.pre-commit-config.yaml`):
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: local
    hooks:
      - id: pyrefly
        name: pyrefly type check
        entry: uvx pyrefly check src/
        language: system
        types: [python]
        pass_filenames: false
```

### Test Coverage: Structured Requirements

**Decision**: Define coverage targets and required test categories.

**Why**:
- Current 70% threshold is arbitrary without category requirements
- Widget tests are completely missing
- Integration tests need clearer patterns

**Categories**:
1. **Unit tests** (`tests/unit/`): Every module, mock external dependencies
2. **Widget tests** (`tests/tui/`): Textual Pilot tests for each widget
3. **Integration tests** (`tests/integration/`): Database, full screen flows
4. **Snapshot tests** (`tests/tui/__snapshots__/`): Visual regression

**Targets**:
- Overall: 80% line coverage
- Critical paths (AI, database): 90%+
- New code: Must include tests

### Observability: Sentry SDK

**Decision**: Use Sentry for error tracking and basic performance monitoring.

**Why**:
- Industry standard for error tracking
- Free tier sufficient for individual use
- Automatic exception capture with context
- Performance tracing for AI calls
- Works well with Loguru (integration available)

**Configuration**:
```python
import sentry_sdk

sentry_sdk.init(
    dsn=settings.sentry_dsn,  # Optional, disabled if not set
    environment=settings.environment,
    traces_sample_rate=0.1,  # 10% of transactions
    attach_stacktrace=True,
    send_default_pii=False,
)
```

**Integration with Loguru**:
```python
from loguru import logger
import sentry_sdk

def sentry_sink(message):
    record = message.record
    if record["level"].no >= 40:  # ERROR and above
        sentry_sdk.capture_message(record["message"], level=record["level"].name.lower())

logger.add(sentry_sink, level="ERROR")
```

### Database Migrations: Alembic with SQLModel

**Decision**: Use Alembic for database migrations, integrated with SQLModel metadata.

**Why**:
- Standard tool for SQLAlchemy-based ORMs
- SQLModel is built on SQLAlchemy, full compatibility
- Supports autogenerate from model changes
- Version control for schema changes
- Rollback support for failed migrations

**Directory structure**:
```
migrations/
├── alembic.ini
├── env.py           # Configured for SQLModel
├── script.py.mako   # Template for new migrations
└── versions/        # Migration scripts
```

**Integration approach**:
```python
# migrations/env.py
from sqlmodel import SQLModel
from jdo.models import *  # Import all models
target_metadata = SQLModel.metadata
```

**Alternatives considered**:
- Manual migrations: Error-prone, no version tracking
- `yoyo-migrations`: Less SQLAlchemy integration
- Custom solution: Reinventing the wheel

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Loguru adds dependency | Small, well-maintained, worth the DX improvement |
| Sentry requires account | Optional; app works without it; free tier available |
| Alembic learning curve | Well-documented; autogenerate reduces manual work |
| Pre-commit slows commits | Ruff is fast; can skip with `--no-verify` if needed |
| Exception hierarchy over-engineering | Start minimal; only add exceptions when needed |

## Migration Plan

1. **Phase 1**: Logging + Error handling (no breaking changes)
2. **Phase 2**: Pre-commit hooks + test coverage (dev workflow)
3. **Phase 3**: Observability (optional Sentry)
4. **Phase 4**: Database migrations (Alembic setup, initial migration from current schema)

Rollback: All changes are additive; reverting is safe.

## Open Questions

1. Should Loguru intercept all stdlib logging, or just specific libraries (httpx, sqlalchemy)?
   - **Recommendation**: Intercept all for consistency
2. Should migrations auto-run on app start, or require explicit `jdo migrate` command?
   - **Recommendation**: Explicit command to avoid surprises
3. What Sentry sampling rate for AI calls specifically?
   - **Recommendation**: 100% for AI calls (low volume, high value)

## Technology Validation (Context7 Research)

### Loguru - VALIDATED

**Research findings**:
- 10x faster than built-in logging (claims to be optimized, with C implementation planned)
- Built-in features: rotation, retention, compression, JSON serialization
- Lazy evaluation via `opt()` for expensive log messages
- `catch()` decorator for thread exception handling
- Native `bind()` for structured context propagation
- Library-friendly: `disable()`/`enable()` pattern for library authors

**Comparison with structlog**:
- structlog is more powerful with customizable processors and async support
- structlog requires more upfront configuration
- Loguru's zero-config approach better fits our "simplicity first" goal
- structlog's `make_filtering_bound_logger()` is faster but less flexible

**Verdict**: Loguru is the right choice for our use case - simple TUI app needing structured logging with minimal setup.

### Sentry SDK - VALIDATED

**Research findings**:
- Official `LoguruIntegration` available (released May 2023)
- Native breadcrumb capture for INFO+ logs
- Configurable `event_level` for when to create Sentry events
- Zero-config integrations for 30+ frameworks
- Scope-based context management for async operations
- `before_send` hooks for filtering sensitive data

**Loguru integration** (official, not custom sink needed):
```python
from sentry_sdk.integrations.loguru import LoguruIntegration

sentry_sdk.init(
    dsn=settings.sentry_dsn,
    integrations=[
        LoguruIntegration(
            level="INFO",       # Breadcrumbs threshold
            event_level="ERROR" # Events threshold
        )
    ],
)
```

**Comparison with Logfire (Pydantic)**:
- Logfire: Native Pydantic/FastAPI integration, OpenTelemetry-based, SQL querying
- Logfire: Better for teams using full Pydantic ecosystem
- Sentry: More mature, industry-standard, free tier, broader framework support
- Sentry: Better error grouping and alerting out of the box

**Verdict**: Sentry is the right choice - established platform, native Loguru integration, optional (works without DSN).

### Alembic - VALIDATED

**Research findings**:
- Standard migration tool for SQLAlchemy (SQLModel is built on SQLAlchemy)
- Native `autogenerate` from model changes
- SQLite batch mode support via `render_as_batch=True` (critical for our use case)
- Batch operations handle SQLite's ALTER TABLE limitations
- `process_revision_directives` hook prevents empty migrations
- Offline mode (`--sql`) for review before execution

**SQLite-specific configuration**:
```python
# migrations/env.py
context.configure(
    connection=connection,
    target_metadata=SQLModel.metadata,
    render_as_batch=True  # Required for SQLite ALTER TABLE
)
```

**SQLModel compatibility**: Confirmed - SQLModel uses `SQLModel.metadata` which is standard SQLAlchemy metadata.

**Verdict**: Alembic is the only real choice for SQLModel migrations - it's the official SQLAlchemy tool with proper SQLite support.

### Pre-commit + Ruff - VALIDATED

**Research findings**:
- Official `ruff-pre-commit` repository maintained by Astral
- Two hook IDs: `ruff-check` (linter) and `ruff-format` (formatter)
- `--fix` argument enables auto-fix on commit
- Extremely fast - community consensus on Reddit/forums
- `types_or: [python, pyi]` to exclude Jupyter if needed

**Recommended configuration** (updated from Context7):
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff-check
        args: [--fix, --config=pyproject.toml]
      - id: ruff-format
        args: [--config=pyproject.toml]
```

**Pyrefly consideration**: Local hook required since no official pre-commit repo exists.

**Verdict**: Pre-commit + Ruff is the industry standard - fast, well-maintained, matches our existing CI.

### Exception Hierarchy - VALIDATED (Best Practices)

**Research findings** (community consensus):
- "Design exception hierarchies based on distinctions that catching code needs" - SE Stack Exchange
- Place all user-defined exceptions in a separate file (`exceptions.py`)
- Always subclass builtin `Exception` for consistency
- Namespace by module like `requests` library does
- Include recovery hints for user-facing errors

**Python community patterns**:
```python
class JDOError(Exception):
    """Base for all JDO exceptions."""
    def __init__(self, message: str, recovery_hint: str | None = None):
        super().__init__(message)
        self.message = message
        self.recovery_hint = recovery_hint
```

**Verdict**: Our domain-based hierarchy follows established best practices.

## Updated Configuration Examples

### Sentry with Loguru (using official integration)

```python
import sentry_sdk
from sentry_sdk.integrations.loguru import LoguruIntegration

def init_observability(settings: JDOSettings) -> None:
    if not settings.sentry_dsn:
        return
    
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=settings.version,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        integrations=[
            LoguruIntegration(
                level="INFO",        # Capture INFO+ as breadcrumbs
                event_level="ERROR"  # Send ERROR+ as events
            )
        ],
        attach_stacktrace=True,
        send_default_pii=False,
    )
```

### Pre-commit Config (finalized)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=500']

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff-check
        args: [--fix, --config=pyproject.toml]
      - id: ruff-format
        args: [--config=pyproject.toml]

  - repo: local
    hooks:
      - id: pyrefly
        name: pyrefly type check
        entry: uvx pyrefly check src/
        language: system
        types: [python]
        pass_filenames: false
```
