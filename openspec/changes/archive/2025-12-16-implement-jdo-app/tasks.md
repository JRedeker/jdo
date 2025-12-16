# Tasks: Implement JDO App Shell

This change wires together all TUI components into a functioning application.

**Note**: The `add-tui-core` change has already converted HomeScreen, ChatScreen, and SettingsScreen to proper Screen subclasses. This change focuses on implementing the JdoApp shell that integrates them.

## Phase 1: Core App Shell

### 1.1 App Startup Tests (Red)
- [x] Test: App starts without errors
- [x] Test: App displays header with title "JDO"
- [x] Test: App displays footer with key bindings
- [x] Test: Database tables created on startup
- [x] Test: Home screen shown after initialization

### 1.2 Implement App Startup (Green)
- [x] Update `src/jdo/app.py` with screen registration
- [x] Add database initialization in `on_mount`
- [x] Configure header and footer widgets
- [x] Push HomeScreen on startup
- [x] Run tests - all should pass

## Phase 2: Screen Navigation

### 2.1 Navigation Tests (Red)
- [x] Test: 'n' key on Home navigates to Chat screen
- [x] Test: 's' key on Home navigates to Settings screen
- [x] Test: Escape on Chat returns to Home
- [x] Test: Escape on Settings returns to Home
- [x] Test: HomeScreen.NewChat message triggers navigation
- [x] Test: HomeScreen.OpenSettings message triggers navigation

### 2.2 Implement Navigation (Green)
- [x] Add message handlers for HomeScreen messages
- [x] Implement `on_home_screen_new_chat` handler
- [x] Implement `on_home_screen_open_settings` handler
- [x] Add Escape binding for screen pop
- [x] Run tests - all should pass

## Phase 3: Draft Restoration

### 3.1 Draft Restore Tests (Red)
- [x] Test: Pending draft triggers restore prompt on startup
- [x] Test: No prompt when no pending drafts
- [x] Test: Choosing restore opens Chat with draft
- [x] Test: Choosing discard deletes draft

### 3.2 Implement Draft Restoration (Green)
- [x] Add `_check_pending_drafts()` method
- [x] Create draft restore prompt dialog (DraftRestoreScreen)
- [x] Navigate to Chat with draft on restore
- [x] Delete draft on discard
- [x] Run tests - all should pass

## Phase 4: Vision Review Prompts

### 4.1 Review Prompt Tests (Red)
- [x] Test: Vision due for review shows notification
- [x] Test: No notification when no reviews due
- [x] Test: Dismissing notification snoozes for session
- [x] Test: Snoozed review doesn't prompt again

### 4.2 Implement Review Prompts (Green)
- [x] Add `_check_vision_reviews()` method
- [x] Add `_snoozed_reviews` session state
- [x] Implement snooze_vision_review() and get_unsnoozed_reviews() methods
- [x] Run tests - all should pass

## Phase 5: Global Bindings

### 5.1 Global Binding Tests (Red)
- [x] Test: 'q' quits application
- [x] Test: 'd' toggles dark mode
- [x] Test: Escape on Home does nothing (no screen to pop)

### 5.2 Implement Global Bindings (Green)
- [x] Configure BINDINGS with q, d, escape
- [x] Implement action_quit
- [x] Implement action_toggle_dark
- [x] Handle escape at root screen
- [x] Run tests - all should pass

## Phase 6: Enable Skipped Tests

### 6.1 Update test_app.py
- [x] Remove skip decorators from TestAppStartup tests
- [x] Remove skip decorators from TestKeyBindings tests
- [x] Add pilot fixture for app testing
- [x] Run tests - all 5 previously skipped tests should pass

## Phase 7: Deferred Integration Tasks

*These tasks were deferred from add-conversational-tui and require the app shell.*

### 7.1 End-to-End Creation Flows
- [x] Test: Full commitment creation flow (conversation → /commit → confirm)
- [x] Test: Full goal creation flow (conversation → /goal → confirm)
- [x] Test: Full vision creation flow (conversation → /vision → confirm)
- [x] Test: Full milestone creation flow (conversation → /milestone → confirm)

### 7.2 Enhanced View Templates
- [x] Test: CommitmentView shows "Milestone: [title]" when linked
- [x] Test: GoalView shows "Vision: [title]" when linked
- [x] Test: GoalView shows "Milestones: X of Y completed"
- [x] Test: VisionView shows linked goals count
- [x] Implement hierarchy breadcrumb in views

### 7.3 List Navigation
- [x] Test: j/k keys navigate list when focused
- [x] Test: Enter selects item and switches to view mode
- [x] Test: CommitmentList sorted by due_date ascending

### 7.4 Hierarchy Commands
- [x] Test: /show hierarchy displays tree view
- [x] Test: 'h' key on Home shows hierarchy view
- [x] Test: /show orphan-goals lists goals without vision

### 7.5 Responsive Design
- [x] Test: Narrow terminal (<80 cols) collapses DataPanel

## Dependencies

- Phase 1-2 can run in parallel (no interdependencies)
- Phase 3-4 depend on Phase 1 (app startup)
- Phase 5 depends on Phase 2 (navigation working)
- Phase 6 depends on Phase 1-5 (core app complete)
- Phase 7 depends on Phase 6 (all core tests passing)

## Running Tests

```bash
# Run app tests
uv run pytest tests/tui/test_app.py -v

# Run all TUI tests
uv run pytest tests/tui/ -v

# Run full test suite
uv run pytest
```
