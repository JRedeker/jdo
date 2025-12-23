# Tasks: Add Provider Auto-Selection and UI Toggle

## 1. Config Module Updates

- [x] 1.1 Add `SUPPORTED_PROVIDERS` constant tuple in `config/settings.py`
- [x] 1.2 Add `_load_env_file(path: Path) -> dict[str, str]` helper function
- [x] 1.3 Add `_write_env_file(path: Path, values: dict[str, str])` helper function
- [x] 1.4 Add `_get_env_file_path() -> Path` helper (respects `JDO_ENV_FILE` override)
- [x] 1.5 Add `set_ai_provider(provider: str) -> AIProvider` function that updates singleton and persists to .env
- [x] 1.6 Export `set_ai_provider` from `config/__init__.py`
- [x] 1.7 Update default `ai_model` to `gpt-5.1-mini` in JDOSettings

## 2. App Startup Auto-Selection

- [x] 2.1 Import `list_providers` from `jdo.auth.registry` in `app.py`
- [x] 2.2 Import `set_ai_provider` from `jdo.config` in `app.py`
- [x] 2.3 Add `_find_authenticated_provider(self) -> str | None` method to JdoApp
- [x] 2.4 Update `_ensure_ai_configured()` to call `_find_authenticated_provider()` before showing modal
- [x] 2.5 Call `set_ai_provider()` with fallback provider if found

## 3. Settings Screen Provider Selector

- [x] 3.1 Import `RadioSet`, `RadioButton` from `textual.widgets` in `settings.py`
- [x] 3.2 Import `set_ai_provider` from `jdo.config` in `settings.py`
- [x] 3.3 Add RadioSet widget in compose() showing authenticated providers only
- [x] 3.4 Pre-select current `settings.ai_provider` RadioButton
- [x] 3.5 Add `on_radio_set_changed()` handler to call `set_ai_provider()` and update display
- [x] 3.6 Add CSS for RadioSet styling (consistent with existing settings layout)
- [x] 3.7 Update "Current AI Configuration" display when provider changes

## 4. Unit Tests - Config Module

- [x] 4.1 Test `set_ai_provider()` updates singleton instance
- [x] 4.2 Test `set_ai_provider()` writes to .env file
- [x] 4.3 Test `set_ai_provider()` preserves other .env values
- [x] 4.4 Test `set_ai_provider()` raises for invalid provider
- [x] 4.5 Test `_load_env_file()` parses KEY=VALUE format correctly
- [x] 4.6 Test `_load_env_file()` skips comments and blank lines
- [x] 4.7 Test `_write_env_file()` creates parent directory if needed

## 5. TUI Tests - App Startup

- [x] 5.1 Test auto-selects authenticated provider when default lacks credentials
- [x] 5.2 Test prefers openai when multiple providers authenticated
- [x] 5.3 Test returns None when no providers authenticated
- [x] 5.4 Test persists auto-selected provider to .env (covered by unit tests)

## 6. TUI Tests - Settings Screen

- [x] 6.1 Test RadioSet shows only authenticated providers (via hidden check)
- [x] 6.2 Test RadioSet pre-selects current provider
- [x] 6.3 Test selecting provider calls set_ai_provider()
- [x] 6.4 Test provider display updates after selection (manual verification)
- [x] 6.5 Test RadioSet hidden when only one provider authenticated

## 7. Validation

- [x] 7.1 Run `uv run ruff check --fix src/ tests/`
- [x] 7.2 Run `uv run ruff format src/ tests/`
- [x] 7.3 Run `uvx pyrefly check src/`
- [x] 7.4 Run `uv run pytest tests/unit/config/ -v`
- [x] 7.5 Run `uv run pytest tests/tui/test_app.py tests/tui/test_settings_screen.py -v`
- [x] 7.6 Manual test: Start app with only OpenRouter credentials, verify no blocking modal
