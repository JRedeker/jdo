# improve-ai-credential-usage Tasks

## Phase 1: Exception Definitions

- [x] **Add `MissingCredentialsError` to `src/jdo/exceptions.py`**
   - Create exception class inheriting from `AuthError`
   - Include provider ID and setup instructions in message
   - *Verification*: Run `uv run python -c "from jdo.exceptions import MissingCredentialsError; print('MissingCredentialsError defined successfully')"`

- [x] **Add `UnsupportedProviderError` to `src/jdo/exceptions.py`**
   - Create exception class for invalid provider configuration
   - *Verification*: Run `uv run python -c "from jdo.exceptions import UnsupportedProviderError; print('UnsupportedProviderError defined successfully')"`

- [x] **Add `InvalidCredentialsError` to `src/jdo/exceptions.py`**
   - Create exception class for invalid credential format
   - Include provider ID and validation guidance in message
   - *Verification*: Run `uv run python -c "from jdo.exceptions import InvalidCredentialsError; print('InvalidCredentialsError defined successfully')"`

## Phase 2: Modify Agent Creation

- [x] **Update `src/jdo/ai/agent.py` - Import dependencies**
   - Import `get_credentials` from `jdo.auth.api`
   - Import `MissingCredentialsError`, `UnsupportedProviderError`, `InvalidCredentialsError` from `jdo.exceptions`
   - Import `OpenRouterProvider`, `OpenRouterModel` from `pydantic_ai.providers/models`
   - Import `OpenAIProvider`, `OpenAIChatModel` from `pydantic_ai.providers/models`
   - *Verification*: Run `uv run python -c "from jdo.ai.agent import create_agent; print('Agent module imports successfully')"`

- [x] **Modify `create_agent()` in `src/jdo/ai/agent.py`**
   - Call `get_credentials(settings.ai_provider)` to retrieve API key
   - Check if credentials exist, raise `MissingCredentialsError` if not
   - Validate credential format, raise `InvalidCredentialsError` if invalid
   - Use inline if/else to create appropriate provider and model:
     - For "openrouter": `OpenRouterProvider(api_key=creds.api_key)` → `OpenRouterModel(...)`
     - For "openai": `OpenAIProvider(api_key=creds.api_key)` → `OpenAIChatModel(...)`
   - Raise `UnsupportedProviderError` for unknown providers
   - *Verification*: Run `uv run python -c "from jdo.ai.agent import create_agent; print('Agent creation updated successfully')"`

- [x] **Add logging to `src/jdo/ai/agent.py`**
   - Import logger from `jdo.logging`
   - Add debug log for credential retrieval (provider ID only, no key)
   - Add error log with recovery hint for missing credentials
   - *Verification*: Run `uv run python -c "from jdo.ai.agent import create_agent; import jdo.logging; print('Logging added successfully')"`

## Phase 3: Testing

- [x] **Create unit tests in `tests/unit/ai/test_agent.py`**
   - Test `create_agent()` uses credentials from store
   - Test `create_agent()` raises `MissingCredentialsError` when no credentials
   - Test `create_agent()` raises `InvalidCredentialsError` for invalid format
   - Test `create_agent()` raises `UnsupportedProviderError` for unknown provider
   - *Verification*: Run `uv run pytest tests/unit/ai/test_agent.py -v` → 18 passed

- [x] **Add integration test for live AI endpoint**
   - Create test using real credentials (skipped if no credentials)
   - Verify successful AI response
   - *Verification*: Run `uv run python -c "from jdo.ai.agent import create_agent; print('Live endpoint works')"`

## Phase 4: Validation

- [x] **Run full test suite**
   - Run `uv run pytest` to ensure no regressions
   - *Verification*: 1478 tests pass

- [x] **Run lint and type checks**
   - Run `uv run ruff check --fix src/ tests/`
   - Run `uv run ruff format src/ tests/`
   - Run `uvx pyrefly check src/`
   - *Verification*: No linting or type errors

- [x] **Test with REPL**
   - Run `uv run jdo` and verify agent responds
   - *Verification*: AI agent works end-to-end with stored credentials

## Dependencies

- Phase 1 → Phase 2 (exceptions needed for agent modification)
- Phase 2 → Phase 3 (agent ready for tests)
- Phase 3 → Phase 4 (tests validate implementation)

## Parallelization Opportunities

- Tasks 1-3 can be done in parallel (all exception definitions)
- Tasks 4-5 must be sequential (imports before modification)
- Task 6 (logging) can be done in parallel with task 4
- Tasks 7-8 can be done in parallel (both test files)
