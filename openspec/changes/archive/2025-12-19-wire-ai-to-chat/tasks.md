# Tasks: Wire AI Agent to Chat Interface

## Prerequisites
- [x] 0.1 Verify OAuth/API key auth is configured (check `provider-auth` spec)
- [x] 0.2 Run existing tests to confirm baseline: `uv run pytest`

## 1. Enable Streaming Message Updates
- [x] 1.1 Add `update_content(text: str)` method to `ChatMessage` widget (already exists)
- [x] 1.2 Add `set_thinking(is_thinking: bool)` method for loading indicator
- [x] 1.3 Write unit tests for `ChatMessage` content updates

## 2. Register Tools with Agent
- [x] 2.1 Update `create_agent()` to call `register_tools()` before returning
- [x] 2.2 Write unit test to verify tools are registered on agent creation

## 3. Implement Message Handling in ChatScreen
- [x] 3.1 Add `_conversation: list[dict[str, str]]` to track history
- [x] 3.2 Implement `on_prompt_input_submitted()` to receive user input
- [x] 3.3 Add user message to chat container and conversation history
- [x] 3.4 Write test for user message display

## 4. Implement AI Streaming Worker
- [x] 4.1 Create `_send_to_ai()` async worker method with `@work(exclusive=True)`
- [x] 4.2 Create agent with `create_agent()` and `JDODependencies(session=session)` from `get_session()`
- [x] 4.3 Create placeholder assistant message with "Thinking..." content
- [x] 4.4 Stream response using `stream_response()` and update message content
- [x] 4.5 Handle worker cancellation gracefully
- [x] 4.6 Write integration test for streaming flow (use `pydantic_ai.models.test.TestModel`)
- [x] 4.7 Disable PromptInput while AI is streaming, re-enable on completion/error

## 5. Credentials Pre-flight Check
- [x] 5.1 Add `_has_ai_credentials()` method to check for API key or OAuth token
- [x] 5.2 Check credentials before invoking AI in `_send_to_ai()`
- [x] 5.3 Show "AI not configured" error and guide to settings if missing
- [x] 5.4 Write test for missing credentials scenario

## 6. Error Handling
- [x] 6.1 Catch rate limit errors and show user-friendly message
- [x] 6.2 Catch authentication errors and guide to settings
- [x] 6.3 Catch network errors with retry guidance
- [x] 6.4 Catch generic errors with fallback message
- [x] 6.5 Write tests for each error case

## 7. Integration Testing
- [x] 7.1 Manual test: Send message and verify response streams
- [x] 7.2 Manual test: Send new message while previous is streaming (cancellation)
- [x] 7.3 Manual test: Verify conversation history is maintained
- [x] 7.4 Run full test suite: `uv run pytest`
- [x] 7.5 Run linting: `uv run ruff check src/ tests/`
- [x] 7.6 Run type checking: `uvx pyrefly check src/`

## 8. Documentation
- [x] 8.1 Update any inline comments explaining the flow
- [x] 8.2 Verify AGENTS.md if needed
