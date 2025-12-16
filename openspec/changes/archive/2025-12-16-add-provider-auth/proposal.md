# Change: Add Provider Authentication Module

## Why

JDO needs to authenticate with AI providers (Anthropic Claude, OpenAI, OpenRouter) to enable AI-powered features. Claude Pro/Max subscribers can use OAuth to authenticate without managing API keys, while other providers require manual API key entry. A unified authentication module allows the settings menu to launch appropriate auth flows based on provider requirements.

## What Changes

- Add `provider-auth` capability for managing provider credentials
- Implement Claude Max/Pro OAuth flow (PKCE authorization code) matching OpenCode's approach
- Implement generic API key entry for OpenAI, OpenRouter, and Anthropic API keys
- Store credentials in `auth.json` with secure file permissions (0600)
- Provide TUI screens for OAuth code entry and API key input
- Support token refresh for OAuth providers

## Impact

- Affected specs: `provider-auth` (new capability)
- Affected code: `src/jdo/auth/` (new module), `src/jdo/models/` (auth models)
- Dependencies: `httpx` for HTTP requests (async)
