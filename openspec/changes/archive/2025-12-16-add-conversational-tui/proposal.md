# Change: Add Conversational AI-Driven TUI

## Why

The form-based TUI approach in `add-core-domain-models` requires users to navigate multiple screens and fill out structured forms. A conversational interface—inspired by [Elia](https://github.com/darrenburns/elia)—lets users naturally describe their commitments, goals, and tasks through AI chat. The AI guides users through creating and managing their data while a structured panel displays the extracted information in real-time, ensuring data integrity without sacrificing conversational fluidity.

## What Changes

- **EXTENDS** `tui-views` capability (base TUI structure spec created during add-core-domain-models)
- **ADDED** `tui-chat` capability: Elia-style conversational interface with AI-driven data creation
- **ADDED** Split-panel layout: Chat on left, structured data template on right
- **ADDED** Explicit commands for data extraction (e.g., `/commit`, `/goal`, `/task`)
- **ADDED** Conversation persistence (separate from domain objects, stored in SQLite)
- **ADDED** AI copies relevant context from chat into domain objects when created

### Key Design Decisions

1. **Elia-inspired architecture**: Keyboard-centric, streaming responses, conversation history
2. **Split-panel layout**: Conversational chat (left) + live data template panel (right)
3. **Explicit extraction**: Users trigger data creation with commands, AI proposes structured data
4. **Decoupled persistence**: Conversations stored separately; AI copies relevant info to objects
5. **Text-focused, impeccable formatting**: Minimal chrome, excellent alignment, monospace-friendly

### Dependencies on Future Specs

This spec requires a separate `ai-provider` capability spec to define:
- LLM provider configuration (OpenAI, Anthropic, Ollama, etc.)
- API key management
- Model selection
- Streaming response handling
- System prompt configuration

## Impact

- Affected specs:
  - `tui-views` (exists at `openspec/specs/tui-views/spec.md` - defines base TUI structure)
  - `tui-chat` (ADDED - conversational AI interface extending tui-views)
- Affected code:
  - `src/jdo/app.py` — Complete rewrite for chat-driven interface
  - `src/jdo/screens/` — New chat screen, home screen architecture
  - `src/jdo/widgets/` — Chat widgets, data panel, prompt input
  - `src/jdo/persistence/` — Add conversation storage
- Dependencies (all completed):
  - `ai-provider` spec ✅ - Created at `openspec/specs/ai-provider/spec.md`
  - `add-core-domain-models` ✅ - Archived, domain models implemented
  - `add-provider-auth` ✅ - Archived, auth screens implemented
  - `add-vision-milestone-hierarchy` - Pending (adds Vision/Milestone models)
