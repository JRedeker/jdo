# Tasks: Fix Navigation Messages and Review Textual Implementation

## Phase 1: Fix Navigation Message Handlers

### 1.1 Add ShowGoals Handler
- [ ] Add `on_home_screen_show_goals` method to JdoApp
- [ ] Push ChatScreen with goals list loaded in DataPanel
- [ ] Query goals from database and pass to DataPanel.show_list()
- [ ] Test: Press 'g' on HomeScreen shows goals

### 1.2 Add ShowCommitments Handler
- [ ] Add `on_home_screen_show_commitments` method to JdoApp
- [ ] Push ChatScreen with commitments list loaded in DataPanel
- [ ] Query commitments from database and pass to DataPanel.show_list()
- [ ] Test: Press 'c' on HomeScreen shows commitments

### 1.3 Add ShowVisions Handler
- [ ] Add `on_home_screen_show_visions` method to JdoApp
- [ ] Push ChatScreen with visions list loaded in DataPanel
- [ ] Query visions from database and pass to DataPanel.show_list()
- [ ] Test: Press 'v' on HomeScreen shows visions

### 1.4 Add ShowMilestones Handler
- [ ] Add `on_home_screen_show_milestones` method to JdoApp
- [ ] Push ChatScreen with milestones list loaded in DataPanel
- [ ] Query milestones from database and pass to DataPanel.show_list()
- [ ] Test: Press 'm' on HomeScreen shows milestones

### 1.5 Add ShowOrphans Handler
- [ ] Add `on_home_screen_show_orphans` method to JdoApp
- [ ] Push ChatScreen with orphan commitments loaded in DataPanel
- [ ] Query commitments where goal_id, milestone_id, recurring_commitment_id are all null
- [ ] Test: Press 'o' on HomeScreen shows orphan commitments

### 1.6 Add ShowHierarchy Handler
- [ ] Add `on_home_screen_show_hierarchy` method to JdoApp
- [ ] Push ChatScreen with hierarchy view loaded in DataPanel
- [ ] Use DataPanel.show_hierarchy() or similar method
- [ ] Test: Press 'h' on HomeScreen shows hierarchy tree

### 1.7 Add ShowIntegrity Handler  
- [ ] Add `on_home_screen_show_integrity` method to JdoApp
- [ ] Push ChatScreen with integrity dashboard loaded in DataPanel
- [ ] Calculate metrics and pass to DataPanel.show_integrity_dashboard()
- [ ] Test: Press 'i' on HomeScreen shows integrity dashboard

## Phase 2: DataPanel State Initialization

### 2.1 Add ChatScreen Initialization Parameters
- [ ] Add optional `initial_mode` parameter to ChatScreen.__init__
- [ ] Add optional `initial_data` parameter to ChatScreen.__init__
- [ ] In on_mount(), check if initial data provided and load into DataPanel
- [ ] Test: ChatScreen can be initialized with pre-loaded data

### 2.2 Update Message Handlers to Use Parameters
- [ ] Update all navigation handlers to pass initial_mode and initial_data
- [ ] Ensure DataPanel shows correct data immediately on screen mount
- [ ] Test: Each navigation shortcut shows data without delay

## Phase 3: Textual Implementation Review

### 3.1 Audit Worker Context Usage
- [ ] Review all `push_screen_wait()` calls - must be in worker
- [ ] Review all `run_worker()` calls - verify exclusive flag usage
- [ ] Document pattern: blocking ops in workers, UI in main thread
- [ ] Create checklist of worker requirements

### 3.2 Audit Async Lifecycle Methods
- [ ] Review all `on_mount()` implementations
- [ ] Review all `on_show()` and `on_resume()` implementations
- [ ] Verify no blocking I/O in lifecycle methods
- [ ] Document async patterns we use

### 3.3 Review Message Handling
- [ ] Audit all Message classes and handlers
- [ ] Verify message bubbling behavior
- [ ] Document our message conventions
- [ ] Ensure no message types are undefined

### 3.4 Review Screen Navigation
- [ ] Audit all `push_screen()` and `pop_screen()` calls
- [ ] Verify screen stack management
- [ ] Document navigation patterns
- [ ] Check for screen memory leaks

### 3.5 Review Focus Management
- [ ] Audit all `.focus()` calls
- [ ] Verify focus restoration after screen transitions
- [ ] Document focus patterns
- [ ] Test keyboard navigation

## Phase 4: Documentation

### 4.1 Create Textual Patterns Document
- [ ] Create `/docs/textual-patterns.md`
- [ ] Document worker context requirements
- [ ] Document async lifecycle patterns
- [ ] Document message handling conventions

### 4.2 Document Common Pitfalls
- [ ] Document `push_screen_wait` worker requirement
- [ ] Document `NoActiveWorker` error and solution
- [ ] Document proper async/await usage in Textual
- [ ] Document testing patterns for Textual

### 4.3 Create Reference Examples
- [ ] Example: Correct worker usage
- [ ] Example: Message handling
- [ ] Example: Screen navigation
- [ ] Example: DataPanel state management

## Phase 5: Testing

### 5.1 Integration Tests for Navigation
- [ ] Test: All HomeScreen shortcuts navigate correctly
- [ ] Test: DataPanel shows correct data for each shortcut
- [ ] Test: Back navigation returns to HomeScreen
- [ ] Test: Navigation works with and without data

### 5.2 Textual Pattern Tests
- [ ] Test: Worker context violations caught in tests
- [ ] Test: Message bubbling works correctly
- [ ] Test: Screen stack management
- [ ] Test: Focus restoration after navigation

## Phase 6: Validation

### 6.1 Manual Testing
- [ ] Test all keyboard shortcuts on HomeScreen
- [ ] Verify data appears correctly in each view
- [ ] Test navigation flow: Home → View → Back → Home
- [ ] Verify no broken shortcuts remain

### 6.2 Code Review
- [ ] Review all new message handlers
- [ ] Review documentation for accuracy
- [ ] Ensure consistent patterns across codebase
- [ ] Verify no regressions in existing functionality

## Summary

**Priority**: Critical (6/10 keyboard shortcuts broken)
**Complexity**: Low (navigation) + Medium (review/documentation)
**Estimated Effort**: 
- Phase 1-2: 2-3 hours (navigation fix)
- Phase 3-4: 3-4 hours (review and documentation)
- Phase 5-6: 1-2 hours (testing and validation)
- **Total**: 6-9 hours

**Dependencies**: None - all required components exist
**Risks**: Minimal - straightforward message handler implementation
