# Change: Wire AI Agent to Chat Interface

## Why

The AI agent exists (`ai/agent.py`) with tools and streaming support, but the chat interface (`screens/chat.py`) never invokes it. When users send non-command messages, nothing happens. This blocks the core conversational experience and all downstream features (integrity protocol, triage classification, etc.).

## What Changes

- **ChatScreen** handles `PromptInput.Submitted` messages and invokes the AI agent
- **ChatContainer** receives and displays streaming AI responses
- Non-command messages are sent to AI with conversation history
- AI responses stream into chat with real-time text updates
- Tools are registered with the agent for database queries
- Error handling shows user-friendly messages for AI failures
- Cancellation support allows stopping a streaming response

## Impact

- Affected specs: `tui-chat`, `ai-provider`
- Affected code:
  - `src/jdo/screens/chat.py` - Add message handling and AI invocation
  - `src/jdo/widgets/chat_container.py` - Add streaming message support
  - `src/jdo/widgets/chat_message.py` - Support incremental content updates
  - `src/jdo/ai/agent.py` - Ensure tools are registered on creation
- Dependencies: Requires OAuth/API key auth to be configured (existing `provider-auth` spec)
