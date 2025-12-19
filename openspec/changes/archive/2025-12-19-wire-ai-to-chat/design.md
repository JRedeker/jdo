# Design: Wire AI Agent to Chat Interface

## Context

JDO has a fully functional PydanticAI agent (`ai/agent.py`) with:
- `create_agent()` factory that builds an agent with configured model
- `JDODependencies` dataclass for injecting session and timezone
- 5 query tools in `ai/tools.py` for commitments, goals, milestones, visions
- `stream_response()` async generator in `ai/context.py`

The chat screen (`screens/chat.py`) has:
- `ChatContainer` for displaying messages
- `PromptInput` that emits `Submitted` messages
- `DataPanel` for structured data display

However, `PromptInput.Submitted` is never handled - messages go nowhere.

## Goals

- Connect user messages to AI agent with streaming responses
- Maintain conversation history across the session
- Handle AI errors gracefully with user feedback
- Support response cancellation for long-running queries
- Keep UI responsive during AI processing

## Non-Goals

- Multi-turn conversation persistence across app restarts (future enhancement)
- Structured output extraction from AI (handled by command handlers)
- Tool result visualization in the data panel (future enhancement)

## Decisions

### 1. Use Textual Workers for AI Calls

**Decision**: Use `@work(exclusive=True)` decorator for the streaming AI call.

**Rationale**:
- Textual workers run async code without blocking the event loop
- `exclusive=True` cancels previous AI calls when a new message is sent
- Built-in cancellation support via `worker.is_cancelled`
- Workers can update widgets safely via `call_from_thread` (though we use async)

**Alternative considered**: Raw asyncio tasks - rejected because Textual's worker system provides better integration with the app lifecycle and cancellation.

### 2. Streaming Display Pattern

**Decision**: Create an "assistant" message immediately, then update its content as chunks arrive.

**Rationale**:
- Provides immediate visual feedback that AI is processing
- Shows a "thinking" indicator while waiting for first token
- Updates the same message widget rather than creating new ones
- Matches user expectations from ChatGPT-style interfaces

**Implementation**:
```python
# Create placeholder message
msg = await self.chat_container.add_message("assistant", "Thinking...")

# Stream updates
async for chunk in stream_response(agent, prompt, deps):
    msg.update_content(accumulated_text)
```

### 3. Conversation History Management

**Decision**: Maintain conversation history in `ChatScreen` as a list of dicts with `role` and `content`.

**Rationale**:
- Simple and matches PydanticAI's expected message format
- Easy to serialize for future persistence
- Allows `build_context()` to truncate to MAX_CONTEXT_MESSAGES

**Schema**:
```python
self._conversation: list[dict[str, str]] = []
# Example: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
```

### 4. Error Handling Strategy

**Decision**: Catch specific AI errors and show contextual guidance.

| Error Type | User Message |
|------------|--------------|
| Rate limit | "AI is busy. Please wait a moment and try again." |
| Auth error | "AI authentication failed. Check your API key in settings." |
| Network error | "Couldn't reach AI provider. Check your connection." |
| Unknown error | "Something went wrong. Your message was not processed." |

**Rationale**: Users need actionable guidance, not stack traces.

### 5. Tool Registration

**Decision**: Call `register_tools(agent)` in `create_agent()` before returning.

**Rationale**: Tools must be registered before the agent is used. Doing this in the factory ensures consistent behavior.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Long AI responses block other messages | `exclusive=True` cancels previous; add visual "Stop" button later |
| Memory growth from conversation history | `MAX_CONTEXT_MESSAGES=50` truncation in `build_context()` |
| API key not configured | Check before sending; guide user to settings |

## Migration Plan

1. Add `ChatMessage.update_content()` method for streaming updates
2. Add `ChatScreen._conversation` history and `on_prompt_input_submitted` handler
3. Create `_send_to_ai()` worker method that streams response
4. Register tools in `create_agent()` factory
5. Add error handling for common AI provider errors

No database migrations required. No breaking changes.

## Open Questions

- Should we persist conversation history to database? (Deferred to future enhancement)
- Should tool calls be visible in the chat? (Deferred - currently hidden)
