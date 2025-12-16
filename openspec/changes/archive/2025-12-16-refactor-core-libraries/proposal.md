# Change: Refactor Core Libraries for Reduced Complexity

## Why

Multiple pending proposals (`add-core-domain-models`, `add-provider-auth`, `add-conversational-tui`) each define custom implementations for common concerns:

1. **Data persistence**: Manual Pydantic models + SQLite repositories with custom ORM-like code
2. **Configuration**: Hardcoded paths, scattered env var handling, custom settings loading
3. **AI integration**: Custom `AIProvider` protocol, manual streaming, custom structured extraction
4. **Path management**: Hardcoded `~/.local/share/jdo/` that won't work on Windows/macOS

By adopting proven libraries, we reduce code by ~50%, gain cross-platform support, and benefit from battle-tested implementations.

## What Changes

### New Dependencies

| Library | Version | Replaces |
|---------|---------|----------|
| `sqlmodel` | >=0.0.24 | Manual Pydantic + SQLite repositories |
| `pydantic-settings` | >=2.0.0 | Custom config loading, env var handling |
| `platformdirs` | >=4.0.0 | Hardcoded XDG paths |
| `pydantic-ai` | >=0.1.0 | Custom AIProvider protocol |

### Affected Specs (Modifications)

| Proposal | Capability | Changes |
|----------|------------|---------|
| `add-core-domain-models` | commitment | SQLModel table classes, Relationship() for FKs |
| `add-core-domain-models` | goal | SQLModel table classes, self-referential relationship |
| `add-core-domain-models` | task | SQLModel table classes, JSON column for sub_tasks |
| `add-core-domain-models` | stakeholder | SQLModel table classes |
| `add-provider-auth` | provider-auth | platformdirs for paths, pydantic-settings for env vars |
| `add-conversational-tui` | tui-chat | PydanticAI agent for AI interactions |

### New Capabilities

| Capability | Purpose |
|------------|---------|
| `app-config` | Centralized pydantic-settings configuration |
| `data-persistence` | SQLModel engine, session management |
| `ai-provider` | PydanticAI agent configuration and tools |

## Impact

- **Breaking**: Existing model definitions in pending specs need updates
- **Migration**: None (greenfield project)
- **Dependencies**: 4 new runtime dependencies
- **Code reduction**: ~50% less persistence code, ~40% less AI integration code

## Implementation Order

This change MUST be implemented before the affected proposals. The recommended order is:

1. **refactor-core-libraries** (this change) - Establish library patterns
2. **add-core-domain-models** - Use SQLModel patterns from this change
3. **add-provider-auth** - Use platformdirs/pydantic-settings from this change
4. **add-conversational-tui** - Use PydanticAI agent from this change

When implementing `add-core-domain-models`, the implementer SHALL:
- Use `SQLModel` with `table=True` instead of plain Pydantic models
- Use `Relationship()` for foreign key relationships
- Use `Field(foreign_key="table.id")` for FK columns
- Import `get_session()` from `jdo.db` instead of implementing repositories

When implementing `add-provider-auth`, the implementer SHALL:
- Use `get_auth_path()` from `jdo.paths` instead of hardcoded paths
- Use `JDOSettings` for env var fallback (e.g., `ANTHROPIC_API_KEY`)

When implementing `add-conversational-tui`, the implementer SHALL:
- Use the `agent` from `jdo.ai` instead of custom AIProvider implementations
- Use `agent.run_stream()` for streaming responses
