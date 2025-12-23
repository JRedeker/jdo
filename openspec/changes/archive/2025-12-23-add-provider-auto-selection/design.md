# Design: Provider Auto-Selection and UI Toggle

## Context

JDO requires an AI provider with valid credentials to function. Currently:
- Settings are loaded from environment variables with `JDO_` prefix or `.env` file
- Credentials are stored per-provider in `auth.json` via `jdo.auth` module
- The app checks only the configured provider at startup, blocking if no credentials exist

Users who configure OpenRouter (not the default) are blocked because the default `ai_provider=openai` has no credentials, even though they have valid OpenRouter credentials saved.

## Goals

1. **Unblock users**: If any provider has credentials, allow app usage
2. **Prefer stability**: Auto-select openai if multiple providers authenticated (most common case)
3. **User control**: Let users explicitly choose their preferred provider via Settings UI
4. **Persistence**: Save provider choice so it survives app restarts
5. **Up-to-date defaults**: Use current best models for each provider

## Non-Goals

- OAuth or other auth methods (API key only for now)
- Model selection UI (provider only; model stays in env/config)
- Moving `.env` to XDG location (roadmap item)

## Decisions

### Decision 1: In-memory singleton update + .env persistence

**What**: Update the settings singleton in memory AND write `JDO_AI_PROVIDER` to `.env` file.

**Why**:
- In-memory update ensures immediate effect without restart
- `.env` persistence ensures choice survives restarts
- Keeps existing pydantic-settings loading pattern intact
- Simple file I/O, no new dependencies

**Alternatives considered**:
- Environment variable only (lost on restart) - rejected
- Database storage (overkill, adds complexity) - rejected
- Separate config file (fragmented configuration) - rejected

### Decision 2: Simple .env file read/write helpers

**What**: Add `_load_env_file()` and `_write_env_file()` functions in `config/settings.py`.

**Why**:
- Minimal implementation (< 30 lines)
- Handles KEY=VALUE format used by pydantic-settings
- Preserves existing values when writing
- No new dependencies

**Implementation notes**:
- Parse lines as `KEY=VALUE` pairs, skip comments and blank lines
- Sort keys alphabetically for deterministic output
- Create parent directory if needed

### Decision 3: RadioSet widget for provider selection

**What**: Use Textual's standard `RadioSet` widget with `RadioButton` children.

**Why**:
- Standard Textual widget (per user request)
- Clear visual indication of current selection
- Keyboard-friendly (arrow keys, enter)
- Only 2-3 options, so radio buttons fit perfectly
- Emits `RadioSet.Changed` message for easy handling

**Implementation notes**:
- Show only authenticated providers in RadioSet
- Pre-select current `settings.ai_provider`
- On change, call `set_ai_provider()` and update display

### Decision 4: Fallback provider selection logic

**What**: When auto-selecting a fallback provider, prefer `openai` if authenticated, otherwise first authenticated.

**Why**:
- OpenAI is the default, so users likely expect it
- Deterministic behavior (not random)
- Simple logic: check openai first, then iterate others

### Decision 5: Updated default models

**What**: Update default model values in app-config spec:
- OpenAI: `gpt-5.1-mini` (was `gpt-4o-mini`)
- OpenRouter default: `anthropic/claude-haiku-4.5` (was `anthropic/claude-3.5-sonnet`)

**Why**:
- GPT-5.1-mini is OpenAI's current efficient model, ideal for general chat/coding tasks
- Claude Haiku 4.5 is Anthropic's fast/efficient model available on OpenRouter
- Both are production-ready, cost-effective, and well-suited for the JDO use case (conversational task management)

**Note**: The default model only applies when no `JDO_AI_MODEL` is set. Users can always override via environment variable.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| `.env` file corruption on crash | Write to temp file first, atomic rename |
| User confusion about which provider active | Clear RadioSet UI with current selection highlighted |
| Model incompatibility after provider switch | Model stays unchanged; user can update via env var |

## Migration Plan

1. No breaking changes - existing `.env` files work as before
2. Auto-selection only triggers when configured provider lacks credentials
3. If both providers authenticated, no change unless user manually switches

## Open Questions

None - all questions resolved in prior discussion:
- Persist to `.env`: Yes
- XDG location: Roadmap (not this change)
- Widget type: RadioSet
- Model defaults: GPT-5.1-mini and Claude Haiku 4.5
