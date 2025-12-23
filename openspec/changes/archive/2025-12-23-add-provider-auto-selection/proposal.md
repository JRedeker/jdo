# Change: Add Provider Auto-Selection and UI Toggle

## Why

When a user saves an OpenRouter API key via the Settings screen, the app still shows the "AI not configured" modal on next run because:
1. The default `ai_provider` setting is `openai` (from env/defaults)
2. Credentials are stored per-provider in `auth.json`
3. The startup check only validates the *currently configured* provider, not any provider with credentials

Users should not be blocked from using the app when they have valid credentials for *any* supported provider.

## What Changes

1. **Auto-selection on startup**: If the configured provider lacks credentials but another provider has valid credentials, automatically switch to that provider (preferring `openai` if multiple are authenticated)

2. **Persist provider choice**: When auto-selecting or manually switching, persist the choice to the `.env` file so it survives restarts

3. **Provider selector UI**: Add a `RadioSet` widget in SettingsScreen allowing users to switch between authenticated providers

4. **Updated default models**: Update default model selections to current best options:
   - OpenAI: `gpt-4.1` (smartest non-reasoning model, best for general tasks)
   - OpenRouter: `anthropic/claude-sonnet-4` (current best Sonnet model)

## Impact

- Affected specs: `provider-auth`, `app-config`, `tui-core`
- Affected code:
  - `src/jdo/config/settings.py` - Add `set_ai_provider()`, env file persistence helpers
  - `src/jdo/config/__init__.py` - Export new function
  - `src/jdo/app.py` - Add `_find_authenticated_provider()`, update `_ensure_ai_configured()`
  - `src/jdo/screens/settings.py` - Add RadioSet for provider selection
  - Tests for all above

## Roadmap Addition

- Future: Move `.env` file to XDG config directory (`~/.config/jdo/.env`) for cross-directory operation
