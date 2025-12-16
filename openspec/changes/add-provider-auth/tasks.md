# Tasks: Add Provider Authentication Module (TDD)

This task list follows Test-Driven Development: write failing tests first, then implement to pass.

## Phase 1: Auth Models

### 1.1 Credential Model Tests (Red)
- [ ] Test: OAuthCredentials requires access_token
- [ ] Test: OAuthCredentials requires refresh_token
- [ ] Test: OAuthCredentials requires expires_at
- [ ] Test: ApiKeyCredentials requires api_key
- [ ] Test: ProviderAuth discriminated union selects correct type

### 1.2 Implement Credential Models (Green)
- [ ] Create `OAuthCredentials` Pydantic model
- [ ] Create `ApiKeyCredentials` Pydantic model
- [ ] Create `ProviderAuth` discriminated union
- [ ] Run tests - all should pass

## Phase 2: Auth Store

### 2.1 Auth Store Tests (Red)
- [ ] Test: AuthStore creates auth.json if not exists
- [ ] Test: AuthStore creates file with 0600 permissions (Unix)
- [ ] Test: AuthStore reads credentials by provider_id
- [ ] Test: AuthStore writes credentials by provider_id
- [ ] Test: AuthStore updates existing credentials
- [ ] Test: AuthStore deletes credentials by provider_id
- [ ] Test: AuthStore returns None for unknown provider

### 2.2 Implement Auth Store (Green)
- [ ] Create `AuthStore` class in `src/jdo/auth/store.py`
- [ ] Implement file read/write with permission handling
- [ ] Run tests - all should pass

### 2.3 Path Integration Tests (Red)
- [ ] Test: AuthStore uses platformdirs user_data_dir
- [ ] Test: Auth path is ~/.local/share/jdo/auth.json (Linux)
- [ ] Test: Auth path handles Windows equivalent

### 2.4 Implement Path Integration (Green)
- [ ] Wire up platformdirs for auth path
- [ ] Run tests - all should pass

## Phase 3: OAuth Implementation

### 3.1 PKCE Tests (Red)
- [ ] Test: generate_pkce_pair creates verifier and challenge
- [ ] Test: Verifier is 43-128 characters
- [ ] Test: Challenge is base64url-encoded SHA256 of verifier

### 3.2 Implement PKCE (Green)
- [ ] Create PKCE generation in `src/jdo/auth/oauth.py`
- [ ] Run tests - all should pass

### 3.3 Authorization URL Tests (Red)
- [ ] Test: build_authorization_url includes client_id
- [ ] Test: build_authorization_url includes redirect_uri
- [ ] Test: build_authorization_url includes code_challenge
- [ ] Test: build_authorization_url includes scope
- [ ] Test: build_authorization_url includes state

### 3.4 Implement Authorization URL (Green)
- [ ] Implement URL builder with all OAuth params
- [ ] Run tests - all should pass

### 3.5 Token Exchange Tests (Red)
- [ ] Test: exchange_code sends POST to token endpoint
- [ ] Test: exchange_code includes code and verifier
- [ ] Test: exchange_code returns OAuthCredentials on success
- [ ] Test: exchange_code raises error on 401
- [ ] Test: exchange_code raises error on network failure

### 3.6 Implement Token Exchange (Green)
- [ ] Implement async exchange_code with httpx
- [ ] Run tests using pytest-httpx mocks - all should pass

### 3.7 Token Refresh Tests (Red)
- [ ] Test: refresh_tokens sends POST with refresh_token
- [ ] Test: refresh_tokens updates credentials on success
- [ ] Test: refresh_tokens clears credentials on 401 (revoked)
- [ ] Test: refresh_tokens raises error on network failure

### 3.8 Implement Token Refresh (Green)
- [ ] Implement async refresh_tokens
- [ ] Run tests - all should pass

## Phase 4: Auth Public API

### 4.1 get_credentials Tests (Red)
- [ ] Test: get_credentials returns stored credentials
- [ ] Test: get_credentials auto-refreshes expired OAuth tokens
- [ ] Test: get_credentials returns None if not authenticated
- [ ] Test: get_credentials checks env var fallback

### 4.2 Implement get_credentials (Green)
- [ ] Implement with auto-refresh logic
- [ ] Run tests - all should pass

### 4.3 get_auth_headers Tests (Red)
- [ ] Test: get_auth_headers returns Bearer token for OAuth
- [ ] Test: get_auth_headers returns x-api-key for API key
- [ ] Test: get_auth_headers raises if not authenticated

### 4.4 Implement get_auth_headers (Green)
- [ ] Implement header generation by auth type
- [ ] Run tests - all should pass

### 4.5 Utility Function Tests (Red)
- [ ] Test: is_authenticated returns True when credentials exist
- [ ] Test: is_authenticated returns False when no credentials
- [ ] Test: clear_credentials removes stored credentials
- [ ] Test: clear_credentials is idempotent (no error if not exists)

### 4.6 Implement Utility Functions (Green)
- [ ] Implement is_authenticated and clear_credentials
- [ ] Run tests - all should pass

## Phase 5: TUI Auth Screens

### 5.1 OAuth Screen Tests (Red)
- [ ] Test: OAuthScreen displays authorization URL
- [ ] Test: OAuthScreen has input for auth code
- [ ] Test: OAuthScreen validates code format
- [ ] Test: OAuthScreen dismiss(True) on success
- [ ] Test: OAuthScreen dismiss(False) on cancel
- [ ] Test: OAuthScreen shows error on exchange failure

### 5.2 Implement OAuth Screen (Green)
- [ ] Create `OAuthScreen(ModalScreen[bool])` in `src/jdo/auth/screens.py`
- [ ] Add URL display and code input
- [ ] Wire up exchange and dismiss
- [ ] Run tests - all should pass

### 5.3 API Key Screen Tests (Red)
- [ ] Test: ApiKeyScreen has input for API key
- [ ] Test: ApiKeyScreen validates key format (non-empty)
- [ ] Test: ApiKeyScreen masks key input
- [ ] Test: ApiKeyScreen dismiss(True) on save
- [ ] Test: ApiKeyScreen dismiss(False) on cancel

### 5.4 Implement API Key Screen (Green)
- [ ] Create `ApiKeyScreen(ModalScreen[bool])`
- [ ] Add masked input and validation
- [ ] Run tests - all should pass

## Phase 6: Provider Registry

### 6.1 Registry Tests (Red)
- [ ] Test: Registry maps "anthropic" to OAuth
- [ ] Test: Registry maps "openai" to API key
- [ ] Test: Registry maps "openrouter" to API key
- [ ] Test: get_auth_method returns correct type for provider

### 6.2 Implement Registry (Green)
- [ ] Create provider registry mapping
- [ ] Run tests - all should pass

## Phase 7: Settings Integration

### 7.1 Settings Auth Tests (Red)
- [ ] Test: Settings screen shows auth status per provider
- [ ] Test: Settings screen launches OAuth flow for Claude
- [ ] Test: Settings screen launches API key flow for others
- [ ] Test: Provider switch prompts for new auth if needed

### 7.2 Implement Settings Integration (Green)
- [ ] Add auth status to settings
- [ ] Wire up auth flow launches
- [ ] Run tests - all should pass

## Phase 8: Visual Regression

### 8.1 Snapshot Tests
- [ ] Create snapshot: OAuth screen with URL
- [ ] Create snapshot: API key entry screen
- [ ] Create snapshot: Settings with auth status
- [ ] Run `pytest --snapshot-update` to generate baselines

## Phase 9: Integration Tests

### 9.1 End-to-End Tests
- [ ] Test: Full OAuth flow (mock endpoints)
- [ ] Test: Full API key flow
- [ ] Test: Token refresh on expired credentials
- [ ] Test: Logout clears credentials

## Dependencies

- Phase 1-2 can run in parallel (models and store)
- Phase 3 depends on Phase 1-2 (needs models and store)
- Phase 4 depends on Phase 3 (needs OAuth functions)
- Phase 5 depends on Phase 4 (needs public API)
- Phase 6 depends on Phase 1 (needs auth types)
- Phase 7 depends on Phases 5-6 (needs screens and registry)
- Phase 8-9 require all previous phases

## Running Tests

```bash
# Run all tests
uv run pytest

# Run auth tests
uv run pytest tests/unit/auth/ -v
uv run pytest tests/integration/auth/ -v

# Run with coverage
uv run pytest --cov=src/jdo --cov-report=term-missing

# Update snapshots
uv run pytest --snapshot-update
```
