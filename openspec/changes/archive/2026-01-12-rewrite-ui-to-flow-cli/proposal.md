# Change: Rewrite UI to Conversational Flow CLI

## Why

The current multi-widget Textual TUI (3,700+ LOC across screens/widgets) is difficult to maintain, extend, and test. Most TUI features are incomplete or broken, while the core backend (models, AI, handlers, database) is solid with 621 passing tests.

The user experience goal is a **conversational flow** like OpenCode itself - a persistent REPL where you chat naturally with an AI that understands your intent and executes actions, rather than navigating screens or memorizing slash commands.

Key problems with current approach:
1. **Complex state management**: Conversation, confirmation, draft, and panel state distributed across 914-line MainScreen + 8 widgets
2. **Tight coupling**: Changes require coordinating MainScreen + ChatContainer + DataPanel + PromptInput + NavSidebar + handlers
3. **Slash command burden**: Users must memorize /commit, /goal, /vision, /triage, etc.
4. **Testing friction**: TUI tests require Textual Pilot, which is verbose and fragile
5. **AI is secondary**: Current design treats AI as helper to slash commands rather than primary interface

## What Changes

Replace the Textual TUI with a **Click-based conversational CLI** that:

1. **Launches into a REPL chat loop** (like OpenCode)
2. **Hybrid interaction**: Natural language primary, slash commands for power users
3. **Streaming responses**: AI responses stream to terminal in real-time
4. **Rich output**: Tables, trees, formatted text via Rich library
5. **Minimal commands**: Only essential CLI commands (`jdo`, `jdo capture`, `jdo db`)

### Architecture Shift

**From** (current):
```
jdo → Textual App → Screens → Widgets → Handlers → AI
     └── Complex state management, message passing, async coordination
```

**To** (proposed):
```
jdo → REPL Loop → AI Agent → Tools → Database
     └── Simple input/output, streaming, Rich formatting
```

### Key Design Decisions

1. **Hybrid intent parsing**: Natural language is primary, but slash commands (`/commit`, `/list`) provide instant deterministic fallback. Both use same handlers. <!-- Research: Industry pattern (Aider, Copilot); OWASP LLM08 mitigation -->
2. **Confirmations in flow**: AI proposes actions, user confirms with "yes"/"no" or refines with natural language
3. **Lists/views on demand**: AI shows relevant data when contextually appropriate or when asked
4. **Session state in memory**: Conversation history (token-limited), current context, draft state - no complex widget state <!-- Research: Token-based limits preferred over message counts -->
5. **prompt_toolkit for input**: Rich readline-like input with history, completion <!-- Research: De facto standard, powers 40+ CLI tools -->

### Supersedes

This change **supersedes** and cancels the existing `simplify-interface` change proposal.

## Breaking Changes

- **BREAKING**: TUI architecture completely removed
- **BREAKING**: Most slash commands replaced with natural language intent (basic slash commands retained as escape hatch per research)
- **BREAKING**: pytest-textual-snapshot tests removed
- **BREAKING**: Keyboard shortcuts (1-9 navigation, etc.) removed

## Impact

### Affected Specs (DEPRECATED - to be removed or heavily modified)
- `tui-core` - Screen/Widget architecture deprecated entirely
- `tui-chat` - Slash commands deprecated, AI conversation patterns change
- `tui-nav` - Navigation sidebar removed
- `tui-views` - Data panel views removed

### New/Modified Specs
- `cli-interface` - New: REPL loop, input handling, session management
- `ai-conversation` - Modified: Hybrid intent parsing (NL + slash commands), confirmation flow
- `output-formatting` - New: Rich output formatters for lists/entities

### Unchanged Specs
- `ai-provider`, `app-config`, `data-persistence`, `provider-auth` - Backend unchanged
- `commitment`, `goal`, `task`, `vision`, `milestone`, `stakeholder` - Domain models unchanged
- `integrity`, `recurring-commitment`, `inbox` - Business logic unchanged
- `command-handlers` - Handlers remain, but invoked by AI tools not slash commands

### Code Impact

**Removed** (~3,700 LOC):
- `src/jdo/screens/` (7 files: `__init__.py`, `ai_required.py`, `chat.py`, `draft_restore.py`, `home.py`, `main.py`, `settings.py`)
- `src/jdo/widgets/` (8 files: `__init__.py`, `chat_container.py`, `chat_message.py`, `data_panel.py`, `hierarchy_view.py`, `integrity_summary.py`, `nav_sidebar.py`, `prompt_input.py`)
- `src/jdo/app.py` (458 LOC)
- `src/jdo/app.tcss`
- `src/jdo/theme.py`
- `tests/tui/` (if exists)

**Modified** (~600 LOC):
- `src/jdo/cli.py` - REPL loop entry point (currently has Click group, add REPL default)
- `src/jdo/ai/agent.py` - Enhanced for conversational flow (streaming integration)
- `src/jdo/ai/tools.py` - Update to return Rich-formatted output
- `src/jdo/commands/handlers.py` - Simplified output (remove panel_update complexity if present)
- `pyproject.toml` - Remove textual, add prompt_toolkit (keep Click, keep Rich)

**Added** (~1,000 LOC):
- `src/jdo/repl/__init__.py` - Module exports
- `src/jdo/repl/loop.py` - Main REPL loop with prompt_toolkit
- `src/jdo/repl/session.py` - Session state (if needed, split from loop.py)
- `src/jdo/output/__init__.py` - Module exports
- `src/jdo/output/formatters.py` - Base formatters (split by entity if >200 LOC each)
- `tests/repl/` - REPL tests (simpler than Pilot tests)
- `tests/output/` - Output formatter tests

## Success Criteria

1. Core workflow works: `jdo` → chat → "create commitment to X" → confirm → see list → quit
2. All existing backend tests pass (621 tests)
3. Less than 2,000 LOC for entire interface layer (vs. 3,700 LOC current)
4. AI agents can understand and modify interface code in single context window
5. Natural language is primary interaction; slash commands available as power-user shortcuts
6. Streaming AI responses render smoothly using Rich `Live` display

## Spec Conflicts

### tui-chat: Conversation History Management
- **Conflict**: `tui-chat` spec defines 50-message limit for conversation history (line 529)
- **Resolution**: This change supersedes with token-based limits (8000 tokens)
- **Rationale**: Token-based pruning is more accurate for LLM context window management per research findings
- **Action needed**: After this change deploys, update or archive `tui-chat` spec

### tui-chat: Slash Command Definitions
- **Conflict**: `tui-chat` defines extensive slash commands (/vision, /milestone, /atrisk, /cleanup, etc.)
- **Resolution**: This change retains only essential slash commands (/commit, /list, /complete, /help) as escape hatches
- **Rationale**: Natural language is primary; slash commands are power-user shortcuts
- **Action needed**: `tui-chat` spec will be deprecated when this change deploys

## Research Validation Status

**Validated** (Jan 2026): See `design.md` for detailed research findings. Key outcomes:
- prompt_toolkit ✅ confirmed as industry standard
- Rich library ✅ with streaming pattern correction (use `Live`, not `status`)
- Handler wrapping ✅ validated by Martin Fowler CLI Agent patterns
- AI-first ⚠️ modified to hybrid approach (slash command escape hatch added)
- Session pruning ⚠️ changed from 50-message to token-based limit
