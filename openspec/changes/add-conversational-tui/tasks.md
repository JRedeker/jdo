# Tasks: Add Conversational AI-Driven TUI (TDD)

This task list follows Test-Driven Development: write failing tests first, then implement to pass.

**Dependencies**: Requires `add-core-domain-models` for domain entities, `refactor-core-libraries` for AI agent foundation.

## Phase 1: Draft Model

### 1.1 Draft Persistence Tests (Red)
- [ ] Test: Draft requires entity_type (commitment/goal/task)
- [ ] Test: Draft stores partial_data as JSON
- [ ] Test: Draft auto-generates id, created_at, updated_at
- [ ] Test: Save draft and retrieve by id
- [ ] Test: Only one active draft per entity_type
- [ ] Test: Draft older than 7 days flagged for expiration prompt

### 1.2 Implement Draft Model (Green)
- [ ] Create `Draft` SQLModel in `src/jdo/models/draft.py`
- [ ] Add draft CRUD operations
- [ ] Run tests - all should pass

## Phase 2: AI Agent Tools

*Moved from `refactor-core-libraries` - tools need a consumer (the TUI) to define the interface.*

### 2.1 Agent Tools Tests (Red)
- [ ] Test: get_current_commitments tool returns pending/in-progress commitments
- [ ] Test: get_overdue_commitments tool returns commitments past due date
- [ ] Test: get_commitments_for_goal tool returns commitments for goal_id
- [ ] Test: Tools access database via JDODependencies.session
- [ ] Test: Tools return structured dicts suitable for AI response

### 2.2 Implement Agent Tools (Green)
- [ ] Create `src/jdo/ai/tools.py` with commitment query tools
- [ ] Register tools with the agent
- [ ] Run tests - all should pass

### 2.3 Agent Integration Test
- [ ] Test: Agent can query commitments via tools (end-to-end with TestModel)

## Phase 3: Command Parser

### 3.1 Command Parser Tests (Red)
- [ ] Test: Recognize `/commit` as command
- [ ] Test: Recognize `/goal` as command
- [ ] Test: Recognize `/task` as command
- [ ] Test: Recognize `/show goals` with argument
- [ ] Test: Recognize `/help commit` with argument
- [ ] Test: Message without `/` is not a command
- [ ] Test: Unknown command returns error

### 3.2 Implement Command Parser (Green)
- [ ] Create command parser in `src/jdo/commands/parser.py`
- [ ] Run tests - all should pass

## Phase 4: Core Chat Widgets

### 4.1 PromptInput Widget Tests (Red)
- [ ] Test: PromptInput is a TextArea subclass
- [ ] Test: Enter key inserts newline (not submit)
- [ ] Test: Ctrl+Enter submits message
- [ ] Test: Empty submit is prevented
- [ ] Test: Message starting with `/` detected as command

### 4.2 Implement PromptInput Widget (Green)
- [ ] Create `PromptInput` widget in `src/jdo/widgets/prompt_input.py`
- [ ] Add custom key binding for Ctrl+Enter submit
- [ ] Run tests - all should pass

### 4.3 Message Display Tests (Red)
- [ ] Test: User message displays with "USER" label
- [ ] Test: Assistant message displays with "ASSISTANT" label
- [ ] Test: System message displays with "SYSTEM" label and warning style
- [ ] Test: Messages show timestamp
- [ ] Test: Streaming response updates incrementally

### 4.4 Implement Message Display (Green)
- [ ] Create message widgets in `src/jdo/widgets/chat_message.py`
- [ ] Add streaming update support
- [ ] Run tests - all should pass

### 4.5 Chat Container Tests (Red)
- [ ] Test: ChatContainer is a VerticalScroll
- [ ] Test: New message scrolls to bottom
- [ ] Test: Shift+Up scrolls through history
- [ ] Test: Shift+Down scrolls through history

### 4.6 Implement Chat Container (Green)
- [ ] Create `ChatContainer` in `src/jdo/widgets/chat_container.py`
- [ ] Add scroll-to-bottom on message add
- [ ] Add history navigation bindings
- [ ] Run tests - all should pass

## Phase 5: Data Panel Widgets

### 5.1 Data Panel Container Tests (Red)
- [ ] Test: DataPanel switches between list, view, draft modes
- [ ] Test: DataPanel state changes trigger re-render

### 5.2 Implement Data Panel Container (Green)
- [ ] Create `DataPanel` in `src/jdo/widgets/data_panel.py`
- [ ] Add mode switching with reactive state
- [ ] Run tests - all should pass

### 5.3 Draft Template Tests (Red)
- [ ] Test: CommitmentDraft shows all fields with "Draft" status
- [ ] Test: GoalDraft shows all fields with "Draft" status
- [ ] Test: TaskDraft shows all fields with "Draft" status
- [ ] Test: Field updates from AI extraction reflect immediately

### 5.4 Implement Draft Templates (Green)
- [ ] Create draft template widgets in `src/jdo/widgets/templates/`
- [ ] Wire up reactive field updates
- [ ] Run tests - all should pass

### 5.5 View Template Tests (Red)
- [ ] Test: CommitmentView shows all fields with current values
- [ ] Test: GoalView shows child commitments count
- [ ] Test: TaskView shows sub-task completion status

### 5.6 Implement View Templates (Green)
- [ ] Create view template widgets
- [ ] Run tests - all should pass

### 5.7 List View Tests (Red)
- [ ] Test: CommitmentList sorted by due_date ascending
- [ ] Test: GoalList shows hierarchy
- [ ] Test: j/k keys navigate list when focused
- [ ] Test: Enter selects item and switches to view mode

### 5.8 Implement List Views (Green)
- [ ] Create `ObjectListView` widget
- [ ] Add navigation bindings
- [ ] Run tests - all should pass

## Phase 6: Command Handlers

### 6.1 /commit Command Tests (Red)
- [ ] Test: /commit extracts deliverable from conversation
- [ ] Test: /commit extracts stakeholder from conversation
- [ ] Test: /commit extracts due_date from conversation
- [ ] Test: /commit prompts for missing required fields
- [ ] Test: /commit shows draft in data panel
- [ ] Test: Confirm creates commitment in database
- [ ] Test: Cancel discards draft

### 6.2 Implement /commit Command (Green)
- [ ] Create commit handler in `src/jdo/commands/commit.py`
- [ ] Wire up AI extraction
- [ ] Wire up draft panel updates
- [ ] Run tests - all should pass

### 6.3 /goal Command Tests (Red)
- [ ] Test: /goal extracts title from conversation
- [ ] Test: /goal extracts problem_statement from conversation
- [ ] Test: /goal extracts solution_vision from conversation
- [ ] Test: /goal prompts for missing required fields
- [ ] Test: /goal shows draft in data panel
- [ ] Test: Confirm creates goal in database

### 6.4 Implement /goal Command (Green)
- [ ] Create goal handler in `src/jdo/commands/goal.py`
- [ ] Run tests - all should pass

### 6.5 /task Command Tests (Red)
- [ ] Test: /task requires commitment context
- [ ] Test: /task extracts title from conversation
- [ ] Test: /task extracts scope from conversation
- [ ] Test: /task without context prompts for commitment selection

### 6.6 Implement /task Command (Green)
- [ ] Create task handler in `src/jdo/commands/task.py`
- [ ] Run tests - all should pass

### 6.7 /show Command Tests (Red)
- [ ] Test: /show goals displays goal list
- [ ] Test: /show commitments displays commitment list
- [ ] Test: /show tasks displays tasks for current commitment
- [ ] Test: /show stakeholders displays stakeholder list
- [ ] Test: /show orphans displays unlinked commitments

### 6.8 Implement /show Command (Green)
- [ ] Create show handler in `src/jdo/commands/show.py`
- [ ] Run tests - all should pass

### 6.9 Other Command Tests (Red)
- [ ] Test: /view <id> shows object in data panel
- [ ] Test: /edit enables modification via conversation
- [ ] Test: /complete marks object as completed
- [ ] Test: /help shows command list
- [ ] Test: /help <command> shows command details
- [ ] Test: /cancel discards current draft

### 6.10 Implement Other Commands (Green)
- [ ] Create remaining command handlers
- [ ] Run tests - all should pass

## Phase 7: Confirmation System

### 7.1 Confirmation Tests (Red)
- [ ] Test: "yes" confirms pending action
- [ ] Test: "yeah", "yep", "sure", "ok" confirm (fuzzy match)
- [ ] Test: "no", "cancel", "stop" cancels (fuzzy match)
- [ ] Test: Ambiguous response prompts for clarity
- [ ] Test: Fuzzy threshold is 80% similarity

### 7.2 Implement Confirmation (Green)
- [ ] Add confirmation matching with rapidfuzz
- [ ] Run tests - all should pass

## Phase 8: Split-Panel Layout

### 8.1 Layout Tests (Red)
- [ ] Test: ChatScreen has Horizontal with ChatPanel (60%) and DataPanel (40%)
- [ ] Test: Tab toggles focus between ChatPanel and DataPanel
- [ ] Test: Narrow terminal (<80 cols) collapses DataPanel

### 8.2 Implement Layout (Green)
- [ ] Create `ChatScreen` in `src/jdo/screens/chat.py`
- [ ] Add CSS for panel widths
- [ ] Add responsive collapse logic
- [ ] Run tests - all should pass

## Phase 9: Home Screen

### 9.1 Home Screen Tests (Red)
- [ ] Test: HomeScreen starts new conversation on open
- [ ] Test: Pending draft triggers restore prompt
- [ ] Test: 'g' key shows goals list
- [ ] Test: 'c' key shows commitments list
- [ ] Test: 's' key opens settings
- [ ] Test: 'o' key shows orphan commitments
- [ ] Test: 'q' key quits application

### 9.2 Implement Home Screen (Green)
- [ ] Create `HomeScreen` in `src/jdo/screens/home.py`
- [ ] Add keyboard bindings
- [ ] Run tests - all should pass

### 9.3 Settings Screen Tests (Red)
*Moved from `add-provider-auth` - requires TUI infrastructure.*
- [ ] Test: Settings screen shows auth status per provider
- [ ] Test: Settings screen launches OAuth flow for Claude (uses `OAuthScreen`)
- [ ] Test: Settings screen launches API key flow for others (uses `ApiKeyScreen`)
- [ ] Test: Provider switch prompts for new auth if needed
- [ ] Test: Settings shows current AI provider and model

### 9.4 Implement Settings Screen (Green)
- [ ] Create `SettingsScreen` in `src/jdo/screens/settings.py`
- [ ] Integrate with `jdo.auth` module (`is_authenticated`, `get_auth_methods`, screens)
- [ ] Run tests - all should pass

## Phase 10: AI Integration

### 10.1 AI Context Tests (Red)
- [ ] Test: Conversation formats as API messages
- [ ] Test: Streaming tokens update response widget
- [ ] Test: System prompt includes JDO instructions

### 10.2 Implement AI Context (Green)
- [ ] Create message formatting utilities
- [ ] Create system prompt template
- [ ] Wire up streaming to response widget
- [ ] Run tests - all should pass

### 10.3 Field Extraction Tests (Red)
- [ ] Test: AI extracts deliverable from natural language
- [ ] Test: AI extracts stakeholder name and matches existing
- [ ] Test: AI extracts date from "tomorrow", "next Friday", etc.
- [ ] Test: AI asks follow-up for missing fields

### 10.4 Implement Field Extraction (Green)
- [ ] Create extraction prompts
- [ ] Wire up to command handlers
- [ ] Run tests - all should pass

## Phase 11: Due Date Parsing

### 11.1 Due Date Tests (Red)
- [ ] Test: "tomorrow" resolves to next day
- [ ] Test: "next Friday" resolves to correct date
- [ ] Test: "December 20" resolves to specific date
- [ ] Test: "3pm" sets due_time to 15:00
- [ ] Test: "end of day" sets due_time to 17:00
- [ ] Test: "next week" rejected as too vague
- [ ] Test: Date without time defaults to 09:00

### 11.2 Implement Due Date Parsing (Green)
- [ ] Create date parsing utilities
- [ ] Integrate with commitment creation
- [ ] Run tests - all should pass

## Phase 12: Empty States & Onboarding

### 12.1 Empty State Tests (Red)
- [ ] Test: First-time user sees onboarding guidance
- [ ] Test: Empty commitments list shows guidance text
- [ ] Test: Empty goals list shows guidance text

### 12.2 Implement Empty States (Green)
- [ ] Add empty state messages to list views
- [ ] Add first-run onboarding screen
- [ ] Run tests - all should pass

## Phase 13: Error Handling

### 13.1 Error Display Tests (Red)
- [ ] Test: AI error shows as system message in chat
- [ ] Test: Validation error shows inline with field
- [ ] Test: Connection error disables input with message

### 13.2 Implement Error Handling (Green)
- [ ] Add error message styling
- [ ] Add connection retry logic
- [ ] Run tests - all should pass

## Phase 14: Visual Regression

### 14.1 Snapshot Tests
- [ ] Create snapshot: HomeScreen empty state
- [ ] Create snapshot: ChatScreen with conversation
- [ ] Create snapshot: DataPanel in draft mode
- [ ] Create snapshot: DataPanel in list mode
- [ ] Create snapshot: DataPanel in view mode
- [ ] Run `pytest --snapshot-update` to generate baselines

## Phase 15: Integration Tests

### 15.1 End-to-End Tests
- [ ] Test: Full commitment creation flow (conversation → /commit → confirm)
- [ ] Test: Full goal creation flow
- [ ] Test: Full task creation flow
- [ ] Test: Draft restore on app restart
- [ ] Test: Navigation between Home and Chat screens

## Dependencies

- Phase 1-3 can run in parallel (no interdependencies)
- Phase 4-5 depend on Phase 1 (draft model)
- Phase 6-7 depend on Phase 3-5 (parser + widgets)
- Phase 8-9 depend on Phase 4-6 (widgets + commands)
- Phase 10-11 depend on Phase 2 (AI provider)
- Phase 12-13 can start after Phase 8
- Phase 14-15 require all previous phases

## Running Tests

```bash
# Run all tests
uv run pytest

# Run TUI tests with pilot
uv run pytest tests/tui/ -v

# Run with coverage
uv run pytest --cov=src/jdo --cov-report=term-missing

# Update snapshots
uv run pytest --snapshot-update
```
