# Design: Conversational AI-Driven TUI

## Context

JDO needs a user interface that makes commitment tracking feel natural, not bureaucratic. The Elia chat TUI demonstrates that conversational interfaces can be fast, keyboard-centric, and pleasant in the terminal. By combining AI conversation with structured data display, users can think out loud while the system captures their commitments precisely.

**Stakeholders**: End users who want to quickly capture and manage commitments through natural conversation.

**Constraints**:
- Python 3.11+, Textual TUI framework
- Must integrate with domain models from `add-core-domain-models`
- AI provider configuration deferred to separate `ai-provider` spec
- SQLite for conversation persistence (separate from domain objects)

## Goals / Non-Goals

**Goals**:
- Elia-style keyboard-centric chat interface with streaming AI responses
- Split-panel layout: chat (left) + structured data template (right)
- Explicit command-driven data extraction (`/commit`, `/goal`, `/task`)
- Conversation history with search and resume
- AI copies relevant context from conversation into domain objects
- Impeccable text formatting and alignment

**Non-Goals**:
- AI provider implementation (separate spec)
- Voice input
- Multi-user/collaboration features
- Mobile or web interface

## Decisions

### 1. Screen Architecture (Elia-inspired)

```
┌─────────────────────────────────────────────────────────────────────┐
│  JDO                                              Model: gpt-4o    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─ Recent Conversations ─────────────────────────────────────────┐ │
│  │  ● Planning Q4 commitments              Today, 2:30 PM         │ │
│  │  ○ Weekly review with team              Yesterday              │ │
│  │  ○ Project kickoff notes                Dec 12                 │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ What would you like to work on?                                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│ [n]ew chat  [/]search  [g]oals  [c]ommitments  [q]uit              │
└─────────────────────────────────────────────────────────────────────┘
```

**HomeScreen**: Shows recent conversations, quick-access to domain objects, prompt for new chat.

### 2. Chat Screen with Data Panel

```
┌─────────────────────────────────────────────────────────────────────┐
│  Planning Q4 commitments                          Model: gpt-4o    │
├────────────────────────────────────────┬────────────────────────────┤
│                                        │                            │
│  USER                                  │  COMMITMENT (draft)        │
│  I need to send the quarterly report   │                            │
│  to the finance team by Friday 3pm.    │  Deliverable:              │
│                                        │  Send quarterly report     │
│  ASSISTANT                             │                            │
│  I can help you create a commitment    │  Stakeholder:              │
│  for that. Based on what you said:     │  Finance Team              │
│                                        │                            │
│  - Deliverable: Send quarterly report  │  Due:                      │
│  - Stakeholder: Finance Team           │  Fri Dec 20, 3:00 PM EST   │
│  - Due: Friday 3:00 PM                 │                            │
│                                        │  Status:                   │
│  Would you like me to create this      │  ○ Draft                   │
│  commitment? Use /commit to confirm,   │                            │
│  or tell me what to change.            │  Goal:                     │
│                                        │  (none)                    │
│  USER                                  │                            │
│  /commit                               │  ─────────────────────────│
│                                        │                            │
│  ASSISTANT                             │  TASKS                     │
│  ✓ Commitment created! I've added it   │  (none yet)                │
│  under "Finance Team". Would you like  │                            │
│  to break this down into tasks?        │  ─────────────────────────│
│                                        │                            │
│                                        │  Type /task to add tasks   │
├────────────────────────────────────────┤                            │
│ > _                                    │                            │
├────────────────────────────────────────┴────────────────────────────┤
│ [ctrl+j]send  [esc]home  [/]commands  [tab]panel                   │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Layout Elements**:
- **Left panel (60-70%)**: Chat messages with user/assistant labels
- **Right panel (30-40%)**: Structured data template showing current draft or selected object
- **Bottom**: Prompt input with command hints
- **Footer**: Context-sensitive keyboard shortcuts

### 3. Data Panel States

The right panel displays contextual structured data:

| State | Panel Shows |
|-------|-------------|
| No active draft | Quick stats (due soon, overdue count) + "Start with /goal, /commit, or /task" |
| Drafting Commitment | Commitment template with fields being populated |
| Drafting Goal | Goal template (title, problem, vision, parent) |
| Drafting Task | Task template (title, scope, sub-tasks) |
| Viewing object | Full details of selected Goal/Commitment/Task |
| Listing objects | Scrollable list with status indicators |

### 4. Command System

Commands are explicit triggers for data operations:

| Command | Action |
|---------|--------|
| `/commit` | Create commitment from conversation context |
| `/goal` | Create goal from conversation context |
| `/task` | Add task to current commitment |
| `/show <type>` | List goals, commitments, or tasks in panel |
| `/view <id>` | Show specific object in panel |
| `/edit` | Edit currently displayed object |
| `/complete` | Mark current commitment/task complete |
| `/help` | Show available commands |

**AI Behavior on Commands**:
1. User types `/commit`
2. AI reviews recent conversation context
3. AI proposes structured data in response AND updates right panel
4. User can confirm, modify via chat, or cancel

### 5. Conversation Model

```python
@dataclass
class Conversation:
    id: UUID
    title: str | None  # Auto-generated or user-set
    created_at: datetime
    updated_at: datetime
    model: str  # AI model used

@dataclass  
class ConversationMessage:
    id: UUID
    conversation_id: UUID
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    # Extracted data references (optional)
    created_commitment_id: UUID | None
    created_goal_id: UUID | None
    created_task_id: UUID | None
```

**Persistence**: Conversations stored in SQLite, separate tables from domain objects. When AI creates a domain object, the message records the created object's ID for traceability.

### 6. AI Context Copying

When the AI creates a domain object, it:
1. Extracts structured fields from conversation
2. Copies relevant conversational context into the object's `notes` field
3. Records the source conversation/message ID for traceability

Example: User discusses quarterly report in detail → AI creates Commitment with `notes` containing key points from the conversation.

### 7. Widget Architecture

```
src/jdo/
├── screens/
│   ├── home_screen.py      # Conversation list + quick actions
│   └── chat_screen.py      # Main chat interface
├── widgets/
│   ├── chat/
│   │   ├── chat_container.py   # Scrollable message list
│   │   ├── chatbox.py          # Individual message display
│   │   ├── prompt_input.py     # Multi-line input with commands
│   │   └── response_status.py  # "AI is typing..." indicator
│   ├── data_panel/
│   │   ├── panel_container.py  # Right panel wrapper
│   │   ├── commitment_view.py  # Commitment template/display
│   │   ├── goal_view.py        # Goal template/display
│   │   ├── task_view.py        # Task template/display
│   │   └── object_list.py      # List view for browsing
│   ├── conversation_list.py    # Home screen conversation list
│   └── app_header.py           # Title + model indicator
└── persistence/
    └── conversation_repository.py
```

### 8. Keyboard Navigation

| Context | Key | Action |
|---------|-----|--------|
| Global | `ctrl+j` / `alt+enter` | Send message |
| Global | `esc` | Return to home / focus prompt |
| Global | `tab` | Toggle focus between chat and data panel |
| Chat | `shift+up/down` | Scroll chat history |
| Chat | `g` / `G` | Jump to first/last message |
| Panel | `j` / `k` | Navigate list items |
| Panel | `enter` | Select/expand item |
| Home | `n` | New conversation |
| Home | `/` | Search conversations |

### 9. AI Provider Interface (Stub)

This spec defines the interface; implementation in separate `ai-provider` spec:

```python
class AIProvider(Protocol):
    async def stream_response(
        self,
        messages: list[ConversationMessage],
        system_prompt: str,
    ) -> AsyncIterator[str]:
        """Stream response chunks from AI."""
        ...

    def extract_structured_data(
        self,
        messages: list[ConversationMessage],
        target_type: Literal["commitment", "goal", "task"],
    ) -> dict[str, Any]:
        """Extract structured data from conversation context."""
        ...
```

### 10. System Prompt Strategy

The AI system prompt will instruct the model to:
1. Help users think through their commitments (what, to whom, by when)
2. Recognize when users describe commitments/goals/tasks
3. Propose structured data when appropriate
4. Respond to commands by extracting and confirming data
5. Copy relevant context into object notes

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| AI extraction accuracy | User confirms before creating; easy edit flow |
| Panel takes screen space | Collapsible panel; responsive sizing |
| Command discoverability | `/help` command; hints in UI; onboarding |
| AI provider dependency | Stub interface allows development; clear spec boundary |
| Conversation storage growth | Future: archival/cleanup strategy |

## Migration Plan

1. Implement conversation persistence layer
2. Build chat widgets (prompt, chatbox, container)
3. Build data panel widgets (templates for each type)
4. Implement HomeScreen with conversation list
5. Implement ChatScreen with split layout
6. Add command parsing and routing
7. Integrate AI provider (after `ai-provider` spec)
8. Wire up domain object creation from commands

## Open Questions

1. **Conversation auto-titling**: Should AI auto-generate titles, or use first user message?
   - Recommendation: Auto-generate after 2-3 exchanges
2. **Draft persistence**: Should uncommitted drafts survive app restart?
   - Recommendation: Yes, store draft state in conversation
3. **Multi-object creation**: Can user create multiple objects in one conversation?
   - Recommendation: Yes, panel shows most recent; `/show` to browse

## Requirements for `ai-provider` Spec

This spec depends on a future `ai-provider` capability that must define:

1. **Provider Configuration**
   - Support for OpenAI, Anthropic, Ollama (local models)
   - API key storage and management
   - Model selection and switching

2. **Streaming Interface**
   - Async streaming response API
   - Token-by-token delivery for responsive UI
   - Error handling and retry logic

3. **Structured Extraction**
   - Function/tool calling for data extraction
   - JSON schema validation for extracted data
   - Confidence scoring (optional)

4. **System Prompt Management**
   - Default system prompt for JDO context
   - User customization options
   - Per-conversation prompt overrides
