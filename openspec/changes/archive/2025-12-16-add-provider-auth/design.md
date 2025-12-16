# Design: Provider Authentication Module

## Context

JDO is a Textual TUI application that will integrate with AI providers. Users need to authenticate with these providers before using AI features. Different providers have different authentication mechanisms:

- **Anthropic Claude Max/Pro**: OAuth 2.0 PKCE flow (same as OpenCode)
- **Anthropic API**: Manual API key
- **OpenAI**: Manual API key
- **OpenRouter**: Manual API key

The settings menu will display available providers. When a user selects a provider requiring authentication, the appropriate auth flow is launched within the TUI.

## Goals

- Provide a unified interface for managing provider credentials
- Implement Claude OAuth using the same endpoints/flow as OpenCode
- Support manual API key entry for all providers
- Store credentials securely with automatic token refresh
- Integrate seamlessly with Textual TUI (no external browser automation)

## Non-Goals

- Browser automation or localhost callback servers
- Keyring/OS credential storage (use file-based storage)
- Provider-specific API client wrappers (just auth, not API calls)

## Decisions

### Decision 1: Use OpenCode's OAuth Client ID and Endpoints

**What**: Use the same OAuth client ID (`9d1c250a-e61b-44d9-88ed-5944d1962f5e`) and endpoints as OpenCode.

**Why**: This is the established client ID for CLI/terminal OAuth flows with Anthropic. Using it ensures compatibility with the same OAuth scopes and redirect URI.

**Endpoints**:
- Authorization: `https://claude.ai/oauth/authorize`
- Token exchange: `https://console.anthropic.com/v1/oauth/token`
- Redirect URI: `https://console.anthropic.com/oauth/code/callback`

### Decision 2: PKCE Authorization Code Flow with Manual Code Entry

**What**: Generate PKCE challenge, open URL in browser (via `webbrowser` module), user copies code back to TUI input.

**Why**: 
- No localhost server needed (simpler, works in SSH/remote sessions)
- Matches OpenCode's "code" method approach
- Works within TUI constraints

**Flow**:
1. Generate PKCE verifier and challenge
2. Build authorization URL with challenge
3. Display URL to user (optionally open browser)
4. User authenticates in browser, gets code
5. User pastes code into TUI input
6. Exchange code + verifier for tokens

### Decision 3: File-based Token Storage with platformdirs

**What**: Store all credentials in `{platformdirs.user_data_dir("jdo")}/auth.json` with `chmod 0600` on Unix.

**Why**:
- Cross-platform: works correctly on Windows, macOS, and Linux
- Uses `platformdirs` library (from `refactor-core-libraries`) for path resolution
- Easy to backup/inspect
- Follows platform conventions (XDG on Linux, AppData on Windows, Library on macOS)

**Platform Paths**:
| Platform | Path |
|----------|------|
| Linux | `~/.local/share/jdo/auth.json` |
| macOS | `~/Library/Application Support/jdo/auth.json` |
| Windows | `C:\Users\<user>\AppData\Local\jdo\auth.json` |

**Implementation**:
```python
from jdo.paths import get_auth_path  # Uses platformdirs internally

def get_auth_file() -> Path:
    return get_auth_path()  # Returns {user_data_dir}/auth.json
```

**Schema**:
```json
{
  "anthropic": {
    "type": "oauth",
    "access": "...",
    "refresh": "...",
    "expires": 1234567890
  },
  "openai": {
    "type": "api",
    "key": "sk-..."
  }
}
```

### Decision 4: Automatic Token Refresh

**What**: Check token expiry before use; refresh automatically if expired.

**Why**: Seamless user experience; OAuth access tokens expire (typically 1 hour).

**Implementation**: The `get_credentials()` function checks expiry and refreshes if needed before returning.

### Decision 5: Provider-Agnostic Auth Types

**What**: Two auth types - `oauth` and `api` - that work across providers.

**Why**: 
- API key entry is identical for OpenAI, OpenRouter, Anthropic
- OAuth flow is currently Anthropic-only but designed for extensibility
- Clean separation allows adding new providers easily

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| OAuth client ID could be revoked | Document that this uses OpenCode's client ID; could register JDO-specific ID later |
| Token refresh fails silently | Return clear error, prompt re-authentication |
| File permissions not enforced on Windows | Document limitation; Windows has different security model |
| User pastes wrong code | Validate code format, show clear error message |

## Module Structure

```
src/jdo/auth/
├── __init__.py          # Public API exports
├── store.py             # Token storage (auth.json read/write)
├── oauth.py             # Claude OAuth PKCE flow
├── models.py            # Pydantic models for credentials
└── screens.py           # TUI screens for auth flows
```

## Implementation Patterns

### Pydantic Discriminated Union for Credentials

Use `Literal` types with `Field(discriminator=...)` for type-safe credential handling:

```python
from typing import Literal, Union
from pydantic import BaseModel, Field

class OAuthCredentials(BaseModel):
    type: Literal["oauth"]
    access: str
    refresh: str
    expires: int  # milliseconds since epoch

class ApiKeyCredentials(BaseModel):
    type: Literal["api"]
    key: str

ProviderAuth = Union[OAuthCredentials, ApiKeyCredentials]

class AuthEntry(BaseModel):
    credentials: ProviderAuth = Field(discriminator="type")
```

### Textual ModalScreen Pattern

Auth screens should use `ModalScreen` with `dismiss()` to return results:

```python
from textual.screen import ModalScreen

class OAuthScreen(ModalScreen[bool]):
    """Returns True on successful auth, False on cancel."""
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit":
            # Exchange code, store credentials...
            self.dismiss(True)
        else:
            self.dismiss(False)

# Caller uses push_screen with callback:
def show_oauth(self) -> None:
    self.push_screen(OAuthScreen(), callback=self.on_oauth_complete)

def on_oauth_complete(self, success: bool) -> None:
    if success:
        self.notify("Authentication successful")
```

### Async HTTP with httpx

Use `AsyncClient` context manager for token operations:

```python
import httpx

async def exchange_code(code: str, verifier: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://console.anthropic.com/v1/oauth/token",
            json={...},
        )
        response.raise_for_status()
        return response.json()
```

## Dependencies

This module depends on `refactor-core-libraries` for:
- `jdo.paths.get_auth_path()` - Cross-platform auth file location
- `jdo.config.JDOSettings` - Environment variable fallback for API keys

## Open Questions

1. Should we support environment variables as fallback (e.g., `ANTHROPIC_API_KEY`)? 
   - Recommendation: Yes, use `JDOSettings` from `jdo.config` which reads `JDO_ANTHROPIC_API_KEY` etc.
2. Should the auth module emit events when credentials change?
   - Recommendation: Yes, for settings UI to update status indicators
