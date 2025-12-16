# Tasks: Add Conversational AI-Driven TUI (TDD)

This task list follows Test-Driven Development: write failing tests first, then implement to pass.

**Dependencies**: Requires `add-core-domain-models` for domain entities, `refactor-core-libraries` for AI agent foundation, `add-vision-milestone-hierarchy` for Vision/Milestone models.

## Implementation Status

**Status: Core Implementation Complete**

| Metric | Value |
|--------|-------|
| Total Tests | 539 passed, 5 skipped |
| Pyrefly Errors | 0 (5 suppressed) |
| Snapshot Tests | 6 |
| Completed Tasks | 280 |
| Deferred Tasks | 27 (require JDOApp) |

### Completed Phases
- **Phase 1**: Draft Model - 14 tests
- **Phase 2**: AI Agent Tools - 10 tests
- **Phase 3**: Command Parser - 15 tests
- **Phase 4**: Core Chat Widgets - Multiple tests
- **Phase 5**: Data Panel Widgets - Multiple tests
- **Phase 6**: Command Handlers - Multiple tests
- **Phase 7**: Confirmation System - Multiple tests
- **Phase 8**: Split-Panel Layout - Multiple tests
- **Phase 9**: Home Screen & Settings - Multiple tests
- **Phase 10**: AI Integration - 32 tests (context, extraction, vision extraction)
- **Phase 11**: Due Date Parsing - 29 tests
- **Phase 12**: Hierarchy View - 12 tests
- **Phase 13**: Review System - 10 tests
- **Phase 14**: Empty States & Onboarding - 11 tests
- **Phase 15**: Error Handling - 9 tests
- **Phase 16**: Visual Regression - 6 snapshot tests
- **Phase 17**: Integration Tests - 15 tests

### Deferred Items (Require JDOApp)
- Full end-to-end creation flows
- Draft restore on app restart
- Vision review flow on startup
- Advanced view templates with hierarchy links
- Narrow terminal responsive design

## Phase 1: Draft Model

### 1.1 Draft Persistence Tests (Red)
- [x] Test: Draft requires entity_type (commitment/goal/task/vision/milestone)
- [x] Test: Draft stores partial_data as JSON
- [x] Test: Draft auto-generates id, created_at, updated_at
- [x] Test: Save draft and retrieve by id
- [x] Test: Only one active draft per entity_type
- [x] Test: Draft older than 7 days flagged for expiration prompt

### 1.2 Implement Draft Model (Green)
- [x] Create `Draft` SQLModel in `src/jdo/models/draft.py`
- [x] Add draft CRUD operations
- [x] Run tests - all should pass (14 tests in `test_draft.py`)

## Phase 2: AI Agent Tools

*Moved from `refactor-core-libraries` - tools need a consumer (the TUI) to define the interface.*

### 2.1 Agent Tools Tests (Red)
- [x] Test: get_current_commitments tool returns pending/in-progress commitments
- [x] Test: get_overdue_commitments tool returns commitments past due date
- [x] Test: get_commitments_for_goal tool returns commitments for goal_id
- [x] Test: get_milestones_for_goal tool returns milestones for goal_id
- [x] Test: get_visions_due_for_review tool returns visions needing review
- [x] Test: Tools access database via JDODependencies.session
- [x] Test: Tools return structured dicts suitable for AI response

### 2.2 Implement Agent Tools (Green)
- [x] Create `src/jdo/ai/tools.py` with commitment query tools
- [x] Add vision/milestone query tools
- [x] Register tools with the agent
- [x] Run tests - all should pass (10 tests in `test_tools.py`)

### 2.3 Agent Integration Test
- [x] Test: Agent can query commitments via tools (end-to-end with TestModel)
- [x] Test: Agent can query visions/milestones via tools

## Phase 3: Command Parser

### 3.1 Command Parser Tests (Red)
- [x] Test: Recognize `/commit` as command
- [x] Test: Recognize `/goal` as command
- [x] Test: Recognize `/task` as command
- [x] Test: Recognize `/vision` as command
- [x] Test: Recognize `/milestone` as command
- [x] Test: Recognize `/show goals` with argument
- [x] Test: Recognize `/help commit` with argument
- [x] Test: Message without `/` is not a command
- [x] Test: Unknown command returns error

### 3.2 Implement Command Parser (Green)
- [x] Create command parser in `src/jdo/commands/parser.py`
- [x] Run tests - all should pass (15 tests in `test_parser.py`)

## Phase 4: Core Chat Widgets

### 4.1 PromptInput Widget Tests (Red)
- [x] Test: PromptInput is a TextArea subclass
- [x] Test: Enter key inserts newline (not submit)
- [x] Test: Ctrl+Enter submits message
- [x] Test: Empty submit is prevented
- [x] Test: Message starting with `/` detected as command

### 4.2 Implement PromptInput Widget (Green)
- [x] Create `PromptInput` widget in `src/jdo/widgets/prompt_input.py`
- [x] Add custom key binding for Ctrl+Enter submit
- [x] Run tests - all should pass

### 4.3 Message Display Tests (Red)
- [x] Test: User message displays with "USER" label
- [x] Test: Assistant message displays with "ASSISTANT" label
- [x] Test: System message displays with "SYSTEM" label and warning style
- [x] Test: Messages show timestamp
- [x] Test: Streaming response updates incrementally

### 4.4 Implement Message Display (Green)
- [x] Create message widgets in `src/jdo/widgets/chat_message.py`
- [x] Add streaming update support
- [x] Run tests - all should pass

### 4.5 Chat Container Tests (Red)
- [x] Test: ChatContainer is a VerticalScroll
- [x] Test: New message scrolls to bottom
- [x] Test: Shift+Up scrolls through history
- [x] Test: Shift+Down scrolls through history

### 4.6 Implement Chat Container (Green)
- [x] Create `ChatContainer` in `src/jdo/widgets/chat_container.py`
- [x] Add scroll-to-bottom on message add
- [x] Add history navigation bindings
- [x] Run tests - all should pass

## Phase 5: Data Panel Widgets

### 5.1 Data Panel Container Tests (Red)
- [x] Test: DataPanel switches between list, view, draft modes
- [x] Test: DataPanel state changes trigger re-render

### 5.2 Implement Data Panel Container (Green)
- [x] Create `DataPanel` in `src/jdo/widgets/data_panel.py`
- [x] Add mode switching with reactive state
- [x] Run tests - all should pass

### 5.3 Draft Template Tests (Red)
- [x] Test: CommitmentDraft shows all fields with "Draft" status
- [x] Test: GoalDraft shows all fields with "Draft" status
- [x] Test: TaskDraft shows all fields with "Draft" status
- [x] Test: VisionDraft shows all fields with "Draft" status
- [x] Test: MilestoneDraft shows all fields with "Draft" status
- [x] Test: Field updates from AI extraction reflect immediately

### 5.4 Implement Draft Templates (Green)
- [x] Create draft template methods in `DataPanel`
- [x] Wire up reactive field updates
- [x] Run tests - all should pass

### 5.5 View Template Tests (Red)
- [x] Test: CommitmentView shows all fields with current values
- [x] Test: GoalView shows all goal fields
- [x] Test: VisionView shows all vision fields
- [x] Test: MilestoneView shows all milestone fields
- [ ] Test: CommitmentView shows "Milestone: [title]" when linked (deferred)
- [ ] Test: CommitmentView shows hierarchy breadcrumb (deferred)
- [ ] Test: GoalView shows child commitments count (deferred)
- [ ] Test: GoalView shows "Vision: [title]" when linked (deferred)
- [ ] Test: GoalView shows "Milestones: X of Y completed" (deferred)
- [ ] Test: VisionView shows linked goals count (deferred)

### 5.6 Implement View Templates (Green)
- [x] Create view template methods in `DataPanel`
- [x] Run tests - all should pass

### 5.7 List View Tests (Red)
- [x] Test: show_list displays items in list mode
- [ ] Test: CommitmentList sorted by due_date ascending (deferred)
- [ ] Test: j/k keys navigate list when focused (deferred)
- [ ] Test: Enter selects item and switches to view mode (deferred)

### 5.8 Implement List Views (Green)
- [x] Create `show_list()` method in `DataPanel`
- [x] Run tests - all should pass

## Phase 6: Command Handlers

### 6.1 /commit Command Tests (Red)
- [x] Test: /commit extracts deliverable from conversation
- [x] Test: /commit extracts stakeholder from conversation
- [x] Test: /commit extracts due_date from conversation
- [x] Test: /commit prompts for missing required fields
- [x] Test: /commit prompts for milestone when goal has milestones
- [x] Test: /commit shows draft in data panel
- [x] Test: Confirm creates commitment in database
- [x] Test: Cancel discards draft

### 6.2 Implement /commit Command (Green)
- [x] Create commit handler in `src/jdo/commands/handlers.py`
- [x] Wire up AI extraction (placeholder - full integration in Phase 10)
- [x] Wire up draft panel updates
- [x] Run tests - all should pass

### 6.3 /goal Command Tests (Red)
- [x] Test: /goal extracts title from conversation
- [x] Test: /goal extracts problem_statement from conversation
- [x] Test: /goal extracts solution_vision from conversation
- [x] Test: /goal prompts for missing required fields
- [x] Test: /goal prompts for vision when visions exist
- [x] Test: /goal shows draft in data panel
- [x] Test: Confirm creates goal in database

### 6.4 Implement /goal Command (Green)
- [x] Create goal handler in `src/jdo/commands/handlers.py`
- [x] Run tests - all should pass

### 6.5 /task Command Tests (Red)
- [x] Test: /task requires commitment context
- [x] Test: /task extracts title from conversation
- [x] Test: /task extracts scope from conversation
- [x] Test: /task without context prompts for commitment selection

### 6.6 Implement /task Command (Green)
- [x] Create task handler in `src/jdo/commands/handlers.py`
- [x] Run tests - all should pass

### 6.7 /vision Command Tests (Red)
*Migrated from add-vision-milestone-hierarchy Phase 6*
- [x] Test: /vision lists all visions
- [x] Test: /vision new starts creation flow
- [x] Test: /vision review lists visions due for review
- [x] Test: Vision draft shows in data panel
- [x] Test: Vision creation prompts for vivid narrative
- [ ] Test: AI suggests metrics for vision (deferred to Phase 10)
- [ ] Test: Confirm creates vision in database (deferred to Phase 10)

### 6.8 Implement /vision Command (Green)
- [x] Create vision handler in `src/jdo/commands/handlers.py`
- [x] Create vision draft panel (uses DataPanel)
- [x] Create vision view panel (uses DataPanel)
- [x] Run tests - all should pass

### 6.9 /milestone Command Tests (Red)
*Migrated from add-vision-milestone-hierarchy Phase 6*
- [x] Test: /milestone lists milestones for current goal
- [x] Test: /milestone new requires goal context
- [x] Test: /milestone new prompts for target_date
- [x] Test: Milestone draft shows in data panel
- [ ] Test: AI suggests milestones for goal (deferred to Phase 10)
- [ ] Test: Confirm creates milestone in database (deferred to Phase 10)

### 6.10 Implement /milestone Command (Green)
- [x] Create milestone handler in `src/jdo/commands/handlers.py`
- [x] Create milestone draft panel (uses DataPanel)
- [x] Create milestone view panel (uses DataPanel)
- [x] Run tests - all should pass

### 6.11 /show Command Tests (Red)
- [x] Test: /show goals displays goal list
- [x] Test: /show commitments displays commitment list
- [x] Test: /show tasks displays tasks for current commitment
- [x] Test: /show stakeholders displays stakeholder list
- [x] Test: /show orphans displays unlinked commitments
- [x] Test: /show visions displays vision list
- [x] Test: /show milestones displays milestones for current goal
- [ ] Test: /show hierarchy displays tree view (deferred to Phase 12)
- [ ] Test: /show orphan-goals lists goals without vision (deferred to Phase 12)

### 6.12 Implement /show Command (Green)
- [x] Create show handler in `src/jdo/commands/handlers.py`
- [x] Run tests - all should pass

### 6.13 Other Command Tests (Red)
- [x] Test: /view <id> shows object in data panel
- [x] Test: /edit enables modification via conversation
- [x] Test: /complete marks object as completed
- [x] Test: /help shows command list
- [x] Test: /help <command> shows command details
- [x] Test: /cancel discards current draft

### 6.14 Implement Other Commands (Green)
- [x] Create remaining command handlers
- [x] Run tests - all should pass

## Phase 7: Confirmation System

### 7.1 Confirmation Tests (Red)
- [x] Test: "yes" confirms pending action
- [x] Test: "yeah", "yep", "sure", "ok" confirm (fuzzy match)
- [x] Test: "no", "cancel", "stop" cancels (fuzzy match)
- [x] Test: Ambiguous response prompts for clarity
- [x] Test: Fuzzy threshold is 80% similarity

### 7.2 Implement Confirmation (Green)
- [x] Add confirmation matching with rapidfuzz (`src/jdo/commands/confirmation.py`)
- [x] Run tests - all should pass

## Phase 8: Split-Panel Layout

### 8.1 Layout Tests (Red)
- [x] Test: ChatScreen has Horizontal with ChatPanel (60%) and DataPanel (40%)
- [x] Test: Tab toggles focus between ChatPanel and DataPanel
- [x] Test: Toggle panel visibility via action
- [ ] Test: Narrow terminal (<80 cols) collapses DataPanel (deferred)

### 8.2 Implement Layout (Green)
- [x] Create `ChatScreen` in `src/jdo/screens/chat.py`
- [x] Add CSS for panel widths (60%/40% split)
- [x] Add toggle panel action
- [x] Run tests - all should pass

## Phase 9: Home Screen

### 9.1 Home Screen Tests (Red)
- [x] Test: HomeScreen renders
- [x] Test: 'g' key shows goals action
- [x] Test: 'c' key shows commitments action
- [x] Test: 'v' key shows visions action
- [x] Test: 'q' key quits application action
- [x] Test: HomeScreen has BINDINGS defined
- [x] Test: action methods exist (new_chat, show_goals, show_commitments, show_visions)
- [ ] Test: Pending draft triggers restore prompt (deferred to Phase 10)
- [ ] Test: 'h' key shows hierarchy view (deferred to Phase 12)

### 9.2 Implement Home Screen (Green)
- [x] Create `HomeScreen` in `src/jdo/screens/home.py`
- [x] Add keyboard bindings (n, g, c, v, m, o, s, q)
- [x] Add custom Message classes for parent app handling
- [x] Run tests - all should pass

### 9.3 Settings Screen Tests (Red)
*Moved from `add-provider-auth` - requires TUI infrastructure.*
- [x] Test: Settings screen shows auth status per provider
- [x] Test: Settings screen launches OAuth flow for Claude (uses `OAuthScreen`)
- [x] Test: Settings screen launches API key flow for others (uses `ApiKeyScreen`)
- [x] Test: Provider switch prompts for new auth if needed
- [x] Test: Settings shows current AI provider and model

### 9.4 Implement Settings Screen (Green)
- [x] Create `SettingsScreen` in `src/jdo/screens/settings.py`
- [x] Integrate with `jdo.auth` module (`is_authenticated`, `get_auth_methods`, screens)
- [x] Run tests - all should pass

## Phase 10: AI Integration

### 10.1 AI Context Tests (Red)
- [x] Test: Conversation formats as API messages
- [x] Test: Streaming tokens update response widget
- [x] Test: System prompt includes JDO instructions

### 10.2 Implement AI Context (Green)
- [x] Create message formatting utilities (`src/jdo/ai/context.py`)
- [x] Create system prompt template (`get_system_prompt()`, `JDO_SYSTEM_PROMPT`)
- [x] Wire up streaming to response widget (`stream_response()`)
- [x] Run tests - all should pass (11 tests in `test_context.py`)

### 10.3 Field Extraction Tests (Red)
- [x] Test: AI extracts deliverable from natural language
- [x] Test: AI extracts stakeholder name and matches existing
- [x] Test: AI extracts date from "tomorrow", "next Friday", etc.
- [x] Test: AI asks follow-up for missing fields (`get_missing_fields()`)

### 10.4 Implement Field Extraction (Green)
- [x] Create extraction prompts (`src/jdo/ai/extraction.py`)
- [x] Create `ExtractedCommitment`, `ExtractedGoal`, `ExtractedTask` models
- [x] Create `extract_commitment()`, `extract_goal()`, `extract_task()` async functions
- [x] Run tests - all should pass (16 tests in `test_extraction.py`)

### 10.5 Vision/Milestone AI Prompts Tests (Red)
*Migrated from add-vision-milestone-hierarchy Phase 9*
- [x] Test: Vision creation prompts for vivid narrative (`VISION_EXTRACTION_PROMPT`)
- [x] Test: AI suggests metrics for vision (`SUGGEST_METRICS_PROMPT`)
- [x] Test: AI suggests milestones for goal (`SUGGEST_MILESTONES_PROMPT`)
- [x] Test: AI prompts for vision linkage on goal creation (`VISION_LINKAGE_PROMPT`)
- [x] Test: AI prompts for milestone linkage on commitment creation (`MILESTONE_LINKAGE_PROMPT`)

### 10.6 Implement Vision/Milestone AI Prompts (Green)
- [x] Create vision prompt templates (`src/jdo/ai/extraction.py`)
- [x] Create `ExtractedVision`, `ExtractedMilestone` models
- [x] Create `extract_vision()`, `extract_milestone()` async functions
- [x] Add linkage prompts (`VISION_LINKAGE_PROMPT`, `MILESTONE_LINKAGE_PROMPT`)
- [x] Run tests - all should pass (21 tests in `test_vision_extraction.py`)

## Phase 11: Due Date Parsing

### 11.1 Due Date Tests (Red)
- [x] Test: "tomorrow" resolves to next day
- [x] Test: "next Friday" resolves to correct date
- [x] Test: "December 20" resolves to specific date
- [x] Test: "3pm" sets due_time to 15:00
- [x] Test: "end of day" sets due_time to 17:00
- [x] Test: "next week" rejected as too vague (`VagueDateError`)
- [x] Test: Date without time defaults to 09:00

### 11.2 Implement Due Date Parsing (Green)
- [x] Create date parsing utilities (`src/jdo/ai/dates.py`)
- [x] `parse_date()` - relative (today, tomorrow, next Monday) and absolute (Dec 20, 2025-12-25)
- [x] `parse_time()` - 12h (3pm), 24h (15:00), named (noon, end of day)
- [x] `parse_datetime()` - combined parsing with default time
- [x] Run tests - all should pass (29 tests in `test_date_parsing.py`)

## Phase 12: Hierarchy View

*Migrated from add-vision-milestone-hierarchy Phase 8*

### 12.1 Hierarchy View Tests (Red)
- [x] Test: Tree shows Vision > Goal > Milestone > Commitment
- [x] Test: Nodes expand on Enter/right arrow
- [x] Test: Nodes collapse on left arrow
- [x] Test: Enter on leaf posts ItemSelected message

### 12.2 Implement Hierarchy View (Green)
- [x] Create `HierarchyView` tree widget (`src/jdo/widgets/hierarchy_view.py`)
- [x] Add navigation bindings (enter, left, right, j, k)
- [x] Add methods: `add_vision()`, `add_goal()`, `add_milestone()`, `add_commitment()`
- [x] Handle orphan goals/commitments sections
- [x] Run tests - all should pass (12 tests in `test_hierarchy_view.py`)

## Phase 13: Review System

*Migrated from add-vision-milestone-hierarchy Phase 10*

### 13.1 Vision Review Tests (Red)
- [x] Test: Vision `is_due_for_review()` returns True when past date
- [x] Test: Vision `complete_review()` updates timestamps
- [x] Test: `get_visions_due_for_review()` function exists
- [ ] Test: App launch prompts when vision due for review (deferred - requires app integration)
- [ ] Test: Review snooze doesn't repeat in session (deferred - requires app state)

### 13.2 Implement Vision Review (Green)
- [x] Add `get_visions_due_for_review()` in `src/jdo/db/session.py`
- [ ] Add startup check in app (deferred - requires JDOApp)
- [ ] Add review flow (deferred - requires JDOApp)

### 13.3 Milestone Auto-Update Tests (Red)
- [x] Test: Milestone `is_overdue()` returns True when past target date
- [x] Test: Milestone `mark_missed()` transitions status
- [x] Test: `get_overdue_milestones()` function exists
- [x] Test: `update_overdue_milestones()` function exists

### 13.4 Implement Milestone Auto-Update (Green)
- [x] Add `get_overdue_milestones()` in `src/jdo/db/session.py`
- [x] Add `update_overdue_milestones()` in `src/jdo/db/session.py`
- [x] Run tests - all should pass (10 tests in `test_review_system.py`)

## Phase 14: Empty States & Onboarding

### 14.1 Empty State Tests (Red)
- [x] Test: First-time user sees onboarding guidance (`get_onboarding_message()`)
- [x] Test: Empty commitments list shows guidance text
- [x] Test: Empty goals list shows guidance text
- [x] Test: Empty visions list shows guidance text
- [x] Test: Empty tasks list shows guidance text
- [x] Test: Empty milestones list shows guidance text
- [x] Test: Quick stats message function exists
- [x] Test: Quick stats shows due_soon count
- [x] Test: Quick stats shows overdue count
- [x] Test: DataPanel uses empty state messages in list mode

### 14.2 Implement Empty States (Green)
- [x] Add `get_empty_state_message(entity_type)` in `src/jdo/widgets/data_panel.py`
- [x] Add `get_onboarding_message()` in `src/jdo/widgets/data_panel.py`
- [x] Add `get_quick_stats_message(stats)` in `src/jdo/widgets/data_panel.py`
- [x] Update `_render_list()` to use empty state guidance
- [x] Run tests - all should pass (11 tests in `test_empty_states.py`)

## Phase 15: Error Handling

### 15.1 Error Display Tests (Red)
- [x] Test: AI error shows as system message in chat
- [x] Test: AI error message contains error text
- [x] Test: Validation error message exists
- [x] Test: Validation error includes field name
- [x] Test: Validation error includes message
- [x] Test: Connection error message exists
- [x] Test: Connection error suggests retry
- [x] Test: Recoverable error flag
- [x] Test: Default error is recoverable

### 15.2 Implement Error Handling (Green)
- [x] Add `create_error_message()` in `src/jdo/widgets/chat_message.py`
- [x] Add `create_connection_error_message()` in `src/jdo/widgets/chat_message.py`
- [x] Add `recoverable` property to ChatMessage
- [x] Add `create_validation_error()` in `src/jdo/widgets/data_panel.py`
- [x] Run tests - all should pass (9 tests in `test_error_handling.py`)

## Phase 16: Visual Regression

### 16.1 Snapshot Tests
- [x] Create snapshot: HomeScreen empty state
- [x] Create snapshot: ChatScreen in initial state
- [x] Create snapshot: DataPanel in draft mode
- [x] Create snapshot: DataPanel in list mode
- [x] Create snapshot: DataPanel empty list with guidance
- [x] Create snapshot: Hierarchy tree view
- [x] Run `pytest --snapshot-update` to generate baselines (6 snapshots)
- [ ] Create snapshot: Goal view with vision link (deferred - needs view templates)
- [ ] Create snapshot: Commitment view with milestone link (deferred - needs view templates)

## Phase 17: Integration Tests

### 17.1 End-to-End Tests
- [x] Test: ChatScreen displays prompt, container, and data panel
- [x] Test: User can type messages in prompt input
- [x] Test: DataPanel starts in list mode by default
- [x] Test: HomeScreen has action bindings (n, g, c keys)
- [x] Test: HierarchyView displays tree structure with domain objects
- [x] Test: HierarchyView supports keyboard navigation
- [x] Test: DataPanel switches between draft, view, and list modes
- [x] Test: ChatContainer maintains message order in conversation
- [x] Test: Multiple messages display correctly (user, assistant, user)
- [x] Test: HomeScreen renders successfully
- [x] Test: ChatScreen renders successfully
- [x] Test: ChatScreen has all required widgets
- [ ] Test: Full commitment creation flow (deferred - needs JDOApp)
- [ ] Test: Full goal creation flow (deferred - needs JDOApp)
- [ ] Test: Draft restore on app restart (deferred - needs JDOApp)

### 17.2 Integration Test Coverage (15 tests)
- [x] `tests/integration/tui/test_flows.py` - 15 integration tests
  - TestChatScreenFlows: 3 tests
  - TestHomeScreenFlows: 1 test
  - TestHierarchyViewFlows: 2 tests
  - TestDataPanelFlows: 3 tests
  - TestChatMessageFlows: 3 tests
  - TestScreenNavigationFlows: 3 tests

## Dependencies

- Phase 1-3 can run in parallel (no interdependencies)
- Phase 4-5 depend on Phase 1 (draft model)
- Phase 6-7 depend on Phase 3-5 (parser + widgets)
- Phase 8-9 depend on Phase 4-6 (widgets + commands)
- Phase 10-11 depend on Phase 2 (AI provider)
- Phase 12-13 can start after Phase 6 (/vision, /milestone commands)
- Phase 14-15 can start after Phase 8
- Phase 16-17 require all previous phases

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
