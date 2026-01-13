# improve-ai-credential-usage Design

**Research Validation:** This design was validated against PydanticAI documentation and security best practices. See research findings at the end of this document.

## Architectural Decision

### Option 1: Explicit Provider Initialization (Selected)
Pass credentials directly to PydanticAI provider classes:

```python
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.models.openai import OpenAIModel

def create_agent() -> Agent[JDODependencies, str]:
    settings = get_settings()
    creds = get_credentials(settings.ai_provider)

    if creds is None:
        msg = f"No credentials found for {settings.ai_provider}. Run 'jdo auth' to configure."
        raise MissingCredentialsError(msg)

    if settings.ai_provider == "openrouter":
        provider = OpenRouterProvider(api_key=creds.api_key)
        model = OpenRouterModel(settings.ai_model, provider=provider)
    else:  # openai
        provider = OpenAIProvider(api_key=creds.api_key)
        model = OpenAIModel(settings.ai_model, provider=provider)

    return create_agent_with_model(model)
```

**Pros:**
- Single source of truth (JDO's credential store)
- Testable and mockable
- No environment variable pollution
- Secure (credentials stay in app-managed store)

**Cons:**
- Slightly more verbose than string-based approach

### Option 2: Environment Variable Export (Rejected)
Copy credentials to environment before agent creation.

**Why Rejected:** OWASP and industry best practices discourage using environment variables for secrets due to:
- Exposure through `/proc` filesystem
- Log leakage risks
- No audit trails or rotation

### Option 3: Provider Factory Pattern (Deferred)
Create abstraction layer for provider initialization.

**Why Deferred:** YAGNI (You Aren't Gonna Need It). With only 2 providers, inline if/else is simpler. The factory pattern adds premature abstraction. If more providers are added later, refactor then.

## Sequence Diagram

```
User → JDO REPL: Start app
JDO REPL → check_credentials(): Is authenticated?
check_credentials → get_credentials(): Fetch for provider
get_credentials → AuthStore: Check stored credentials
AuthStore → JDO REPL: Return credentials (or None)
JDO REPL → create_agent(): Create agent with credentials
create(): Get API key_agent → get_credentials
create_agent → OpenRouterProvider/OpenAIProvider: Create provider with key
create_agent → Agent: Initialize with provider
Agent → OpenRouter API: Make AI request
```

## File Changes

| File | Change |
|------|--------|
| `src/jdo/ai/agent.py` | Modify `create_agent()` to use explicit providers |
| `src/jdo/exceptions.py` | Add `MissingCredentialsError` exception |
| `tests/unit/ai/test_agent.py` | Update tests for credential passing |

## Provider-Specific Implementation

### OpenRouter
```python
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

provider = OpenRouterProvider(api_key=api_key)
model = OpenRouterModel(settings.ai_model, provider=provider)
```

### OpenAI
```python
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

provider = OpenAIProvider(api_key=api_key)
model = OpenAIModel(settings.ai_model, provider=provider)
```

## Error Handling

| Scenario | Behavior |
|----------|----------|
| No credentials found | Raise `MissingCredentialsError` with setup instructions |
| Stored credential available | Use stored credential |
| Invalid credential format | Raise `InvalidCredentialsError` |

## Testing Strategy

1. **Unit tests**: Mock `get_credentials()` and verify provider receives correct API key
2. **Integration tests**: Use real credentials with mock HTTP responses
3. **End-to-end**: Test with live API (skipped in CI, optional for manual testing)

## Research Findings

This design was validated through research against PydanticAI documentation and security best practices:

### Explicit Provider Initialization Validated
PydanticAI supports both explicit provider initialization and string-based identifiers. Explicit initialization is the recommended pattern when credentials come from non-environment sources.

**Source:** https://ai.pydantic.dev/models/openrouter/

### Factory Pattern Deferred
YAGNI applies. With only 2 providers, inline if/else is simpler than a factory abstraction.

**Source:** Analysis of current codebase showing only 2 providers defined in `settings.py`

### Environment Variable Fallback Removed
OWASP, Google Cloud Secret Manager, and CyberArk all recommend against using environment variables for secrets due to:
- Exposure through `/proc` filesystem
- Log leakage risks
- No audit trails or rotation

**Sources:**
- https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- https://cloud.google.com/secret-manager/docs/best-practices
- https://developer.cyberark.com/blog/environment-variables-dont-keep-secrets-best-practices-for-plugging-application-credential-leaks/
