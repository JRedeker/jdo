# Design: Core Library Refactoring

## Context

JDO is a commitment-tracking TUI application being built from scratch. Multiple pending proposals define overlapping implementations for:

1. **Data persistence**: Manual Pydantic models + SQLite repositories with custom ORM-like code
2. **Configuration**: Hardcoded paths, scattered env var handling
3. **AI integration**: Custom `AIProvider` protocol, manual streaming
4. **Path management**: Hardcoded `~/.local/share/jdo/` paths

By adopting proven libraries early (before implementation begins), we reduce future code by ~50%, gain cross-platform support, and benefit from battle-tested implementations.

**Stakeholders**: Developers implementing JDO, end users who benefit from cross-platform support.

**Constraints**:
- Python 3.11+, Pydantic v2, Textual TUI
- Must integrate cleanly with existing Pydantic models
- No breaking changes to user-facing behavior (greenfield project)

## Goals / Non-Goals

**Goals**:
- Adopt SQLModel for unified Pydantic + SQLAlchemy persistence
- Use pydantic-settings for environment-based configuration
- Use platformdirs for cross-platform data/config paths
- Use PydanticAI for AI agent interactions with streaming
- Minimize custom infrastructure code

**Non-Goals**:
- Async database access (SQLModel sync is sufficient for local SQLite)
- Multiple AI providers in a single session
- Complex configuration hierarchies or secrets management

## Decisions

### Decision 1: SQLModel for Domain Models

**What**: Replace manual Pydantic models + repository pattern with SQLModel table classes.

**Why**:
- SQLModel = Pydantic + SQLAlchemy in one class
- Single source of truth for validation and persistence
- Built-in relationship support with type hints
- Reduces code by ~40% (no separate repository implementations)

**Implementation**:
```python
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON  # For JSON columns
from uuid import UUID, uuid4
from datetime import datetime, date

class Commitment(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    deliverable: str = Field(min_length=1)
    stakeholder_id: UUID = Field(foreign_key="stakeholder.id")
    goal_id: UUID | None = Field(default=None, foreign_key="goal.id")
    due_date: date
    status: str = Field(default="pending")
    
    # Relationships
    stakeholder: "Stakeholder" = Relationship(back_populates="commitments")
    goal: "Goal | None" = Relationship(back_populates="commitments")
    tasks: list["Task"] = Relationship(back_populates="commitment")
```

**Self-Referential Relationships** (e.g., Goal nesting):

Self-referential relationships require BOTH directions with `sa_relationship_kwargs` to specify the remote side:

```python
class Goal(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(min_length=1)
    parent_goal_id: UUID | None = Field(default=None, foreign_key="goal.id")
    
    # Self-referential: parent points to one Goal, children points to many
    parent: "Goal | None" = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "Goal.id"}
    )
    children: list["Goal"] = Relationship(back_populates="parent")
```

**JSON Columns for Embedded Data** (e.g., Task.sub_tasks):

For storing Pydantic models as JSON in SQLite, use SQLAlchemy's `Column(JSON)` with `sa_column`:

```python
from sqlalchemy import Column, JSON
from pydantic import BaseModel

class SubTask(BaseModel):
    """Embedded model - NOT a table, stored as JSON."""
    description: str
    completed: bool = False

class Task(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    commitment_id: UUID = Field(foreign_key="commitment.id")
    title: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    status: str = Field(default="pending")
    order: int
    
    # JSON column for embedded SubTask list
    sub_tasks: list[SubTask] = Field(default=[], sa_column=Column(JSON))
    
    # Relationship
    commitment: "Commitment" = Relationship(back_populates="tasks")
```

**Note**: When reading JSON columns, SQLModel returns raw dicts. Use Pydantic parsing:
```python
task = session.get(Task, task_id)
sub_tasks = [SubTask(**st) for st in task.sub_tasks]  # Parse dicts to models
```

**Alternatives Considered**:
- Raw SQLAlchemy: More flexible but loses Pydantic validation
- Tortoise ORM: Async-first, unnecessary complexity for local SQLite
- Peewee: Simple but no Pydantic integration

### Decision 2: pydantic-settings for Configuration

**What**: Use `pydantic-settings` for all configuration with automatic env var binding.

**Why**:
- Unified validation for config values
- Automatic environment variable loading
- .env file support out of the box
- Type-safe settings access

**Implementation**:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class JDOSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="JDO_",
        env_file=".env",
        env_file_encoding="utf-8",
    )
    
    # Database
    database_path: Path | None = None  # Falls back to platformdirs
    
    # AI Provider
    ai_provider: str = "anthropic"
    ai_model: str = "claude-sonnet-4-20250514"
    
    # UI
    timezone: str = "America/New_York"
```

**Runtime Settings Persistence**:

User preferences that can change at runtime (e.g., active AI provider) are stored in `settings.json`:

```python
from pydantic import BaseModel
from pathlib import Path
import json

class RuntimeSettings(BaseModel):
    active_provider: str = "anthropic"
    
    @classmethod
    def load(cls) -> "RuntimeSettings":
        path = get_settings_path()
        if path.exists():
            return cls.model_validate_json(path.read_text())
        return cls()
    
    def save(self) -> None:
        path = get_settings_path()
        path.write_text(self.model_dump_json(indent=2))
```

**Settings Hierarchy**:
1. Environment variables (highest priority, via pydantic-settings)
2. `.env` file
3. `settings.json` (runtime user preferences)
4. Defaults in code (lowest priority)

**Alternatives Considered**:
- python-dotenv + manual parsing: No validation, no type safety
- dynaconf: Overkill for single-user app
- Custom config loader: Reinventing the wheel

### Decision 3: platformdirs for Cross-Platform Paths

**What**: Use `platformdirs` for all user data and config paths.

**Why**:
- Works correctly on Windows, macOS, and Linux
- Follows platform conventions (XDG on Linux, AppData on Windows)
- Auto-creates directories with `ensure_exists=True`
- No more hardcoded `~/.local/share/jdo/`

**Implementation**:
```python
from platformdirs import user_data_dir, user_config_dir

def get_data_dir() -> Path:
    return Path(user_data_dir("jdo", ensure_exists=True))

def get_config_dir() -> Path:
    return Path(user_config_dir("jdo", ensure_exists=True))

def get_database_path() -> Path:
    return get_data_dir() / "jdo.db"

def get_auth_path() -> Path:
    return get_data_dir() / "auth.json"

def get_settings_path() -> Path:
    return get_data_dir() / "settings.json"
```

**Platform Results**:
| Platform | Data Dir | Config Dir |
|----------|----------|------------|
| Linux | `~/.local/share/jdo` | `~/.config/jdo` |
| macOS | `~/Library/Application Support/jdo` | `~/Library/Application Support/jdo` |
| Windows | `C:\Users\<user>\AppData\Local\jdo` | `C:\Users\<user>\AppData\Local\jdo` |

### Decision 4: PydanticAI for AI Agent Integration

**What**: Use `pydantic-ai` for all AI interactions instead of custom `AIProvider` protocol.

**Why**:
- Built-in streaming support
- Tool/function calling with Pydantic models
- Dependency injection for runtime context
- Structured output extraction
- Model-agnostic (Anthropic, OpenAI, etc.)

**Implementation**:
```python
from pydantic_ai import Agent
from pydantic import BaseModel

class CommitmentSuggestion(BaseModel):
    deliverable: str
    suggested_due_date: date
    reasoning: str

agent = Agent(
    "anthropic:claude-sonnet-4-20250514",
    deps_type=JDODependencies,
    output_type=CommitmentSuggestion,
    system_prompt="You help users track their commitments...",
)

@agent.tool
async def get_current_commitments(ctx: RunContext[JDODependencies]) -> list[dict]:
    """Get user's current commitments for context."""
    return ctx.deps.get_commitments()

# Streaming usage
async with agent.run_stream("Help me plan my week") as response:
    async for chunk in response.stream_text():
        yield chunk
```

**Context Window Management**:

PydanticAI provides `history_processors` for managing conversation context size. Use the "keep last N messages" approach for simplicity:

```python
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage

def keep_last_n_messages(messages: list[ModelMessage], n: int = 20) -> list[ModelMessage]:
    """Keep only the last N messages to manage context window."""
    if len(messages) <= n:
        return messages
    return messages[-n:]

agent = Agent(
    "anthropic:claude-sonnet-4-20250514",
    deps_type=JDODependencies,
    system_prompt="You help users track their commitments...",
    history_processors=[lambda msgs: keep_last_n_messages(msgs, 20)],
)
```

**Alternatives Considered**:
- Custom AIProvider protocol: More control but significant implementation effort
- LangChain: Heavy dependency, complex abstraction
- Direct API calls: No streaming abstraction, manual tool handling

### Decision 5: RapidFuzz for Flexible String Matching

**What**: Use `rapidfuzz` for fuzzy string matching on user confirmations and commands.

**Why**:
- Lightweight (pure Python with optional C speedups)
- Handles typos and variations ("yep", "yeah", "yes" all match "yes")
- `token_set_ratio` works well for phrase matching
- No AI call needed for simple confirmation detection

**Implementation**:
```python
from rapidfuzz import fuzz

CONFIRMATIONS = ["yes", "yeah", "yep", "sure", "ok", "okay", "confirm", "do it", "looks good"]
CANCELLATIONS = ["no", "nope", "cancel", "stop", "nevermind", "wait"]

def match_intent(user_input: str, phrases: list[str], threshold: int = 80) -> bool:
    """Check if user input fuzzy-matches any phrase in the list."""
    user_lower = user_input.lower().strip()
    for phrase in phrases:
        if fuzz.token_set_ratio(user_lower, phrase) >= threshold:
            return True
    return False

def is_confirmation(user_input: str) -> bool:
    return match_intent(user_input, CONFIRMATIONS)

def is_cancellation(user_input: str) -> bool:
    return match_intent(user_input, CANCELLATIONS)
```

**Alternatives Considered**:
- AI classification: Overkill for simple yes/no, adds latency
- Exact matching: Too rigid, poor UX
- regex patterns: Fragile, hard to maintain

### Decision 6: Session Management Pattern

**What**: Use a context manager pattern for SQLModel sessions.

**Why**:
- Automatic transaction handling
- Clean resource cleanup
- Works with Textual's async patterns

**Eager Loading Relationships**:

For eager loading, use `selectinload` from SQLAlchemy (not SQLModel):

```python
from sqlalchemy.orm import selectinload
from sqlmodel import select

# Eager load tasks when fetching commitments
statement = select(Commitment).options(selectinload(Commitment.tasks))
results = session.exec(statement)
for commitment in results:
    # commitment.tasks is already loaded, no additional query
    print(f"{commitment.deliverable}: {len(commitment.tasks)} tasks")
```

**Implementation**:
```python
from contextlib import contextmanager
from sqlmodel import Session, create_engine

engine = create_engine(f"sqlite:///{get_database_path()}")

@contextmanager
def get_session():
    with Session(engine) as session:
        yield session

# Usage
def get_commitment(id: UUID) -> Commitment | None:
    with get_session() as session:
        return session.get(Commitment, id)

def save_commitment(commitment: Commitment) -> Commitment:
    with get_session() as session:
        session.add(commitment)
        session.commit()
        session.refresh(commitment)
        return commitment
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| SQLModel is relatively new | Well-maintained by Tiangolo, used in production |
| PydanticAI is evolving rapidly | Pin version, test before upgrades |
| platformdirs adds dependency | Tiny, stable, widely used |
| Session management in Textual async | Use sync sessions, Textual handles threading |

## Module Structure

```
src/jdo/
├── config/
│   ├── __init__.py      # Exports JDOSettings
│   └── settings.py      # pydantic-settings configuration
├── db/
│   ├── __init__.py      # Exports engine, get_session
│   ├── engine.py        # SQLModel engine setup
│   └── migrations.py    # Schema creation/updates
├── ai/
│   ├── __init__.py      # Exports agent
│   ├── agent.py         # PydanticAI agent configuration
│   └── tools.py         # Agent tools for commitment access
├── models/
│   ├── __init__.py      # Exports all models
│   ├── commitment.py    # SQLModel: Commitment
│   ├── goal.py          # SQLModel: Goal
│   ├── task.py          # SQLModel: Task
│   └── stakeholder.py   # SQLModel: Stakeholder
└── paths.py             # platformdirs helpers
```

## Migration Plan

Since this is a greenfield project with no production data:

1. **Add dependencies**: `sqlmodel`, `pydantic-settings`, `platformdirs`, `pydantic-ai`, `rapidfuzz`
2. **Create config module**: Settings with env var binding
3. **Create paths module**: Cross-platform directory helpers
4. **Create db module**: Engine, session management
5. **Update model specs**: Change from Pydantic to SQLModel
6. **Create AI agent**: PydanticAI configuration

No data migration needed—all changes are to pending specs, not deployed code.

## Open Questions

1. **Should settings support config file in addition to env vars?**
   - Recommendation: Not initially; env vars + .env sufficient for TUI app
   
2. **Should we use async SQLModel sessions?**
   - Recommendation: No; sync is simpler and Textual handles async boundaries
   
3. **How to handle PydanticAI model switching?**
   - Recommendation: Settings-driven model selection, restart required for changes
