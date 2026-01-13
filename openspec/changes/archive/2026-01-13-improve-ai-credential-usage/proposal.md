# improve-ai-credential-usage

**Date:** 2025-01-12  
**Status:** Draft

## Summary

Improve API key storage and usage by passing credentials explicitly to PydanticAI providers instead of relying on environment variables. This ensures that API keys stored in JDO's credential store are actually used by the AI agent.

## Problem Statement

JDO currently has two credential sources:
1. **JDO credential store** (`~/.local/share/jdo/auth.json`) - managed by `jdo.auth.api`
2. **Environment variables** (`OPENAI_API_KEY`, `OPENROUTER_API_KEY`)

The `is_authenticated()` check in `src/jdo/repl/loop.py:check_credentials()` correctly detects credentials from both sources. However, when PydanticAI creates an agent, it reads directly from `OPENROUTER_API_KEY` environment variable, ignoring JDO's credential store entirely.

This causes the app to report "authenticated" but fail at runtime when trying to make AI requests.

## Why

1. **Security**: OWASP recommends against using environment variables for secrets due to `/proc` filesystem exposure and log leakage risks
2. **User Experience**: Users who configure credentials via `jdo auth` expect them to work, not fail silently
3. **Architecture**: Single source of truth for credentials (credential store) rather than dual sources with precedence rules

## What Changes

Pass API keys explicitly to PydanticAI providers by:
1. Fetching credentials from JDO's auth store using `get_credentials()`
2. Instantiating provider classes with explicit `api_key` parameters
3. Removing environment variable fallback for agent creation
4. Adding structured logging for credential operations

### Affected Code

| File | Change |
|------|--------|
| `src/jdo/ai/agent.py` | Modify `create_agent()` to use explicit providers |
| `src/jdo/exceptions.py` | Add `MissingCredentialsError`, `UnsupportedProviderError`, `InvalidCredentialsError` |
| `src/jdo/logging.py` | Add structured logging for credential operations |
| `tests/unit/ai/test_agent.py` | Update tests for credential passing |

### Supersedes

- `openspec/specs/provider-auth/spec.md` - Removes env var fallback and auto-selection behaviors for agent creation

## Scope

| Included | Excluded |
|----------|----------|
| OpenRouter provider credential passing | OAuth/bearer token providers |
| OpenAI provider credential passing | Credential rotation/re-encryption |
| Anthropic/Google provider support | Multi-factor auth |
| Structured logging for credentials | Provider auto-selection on failure |

## References

- [PydanticAI OpenRouter docs](https://ai.pydantic.dev/models/openrouter/)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- Current implementation: `src/jdo/ai/agent.py`, `src/jdo/auth/api.py`
- Existing spec: `openspec/specs/provider-auth/spec.md`
