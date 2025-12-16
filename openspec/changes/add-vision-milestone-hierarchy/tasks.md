# Tasks: Vision and Milestone Hierarchy (TDD)

This task list follows Test-Driven Development: write failing tests first, then implement to pass.

**Dependencies**: Should be implemented WITH `add-core-domain-models` to establish correct hierarchy from the start.

## Phase 1: Vision Model

### 1.1 Vision Validation Tests (Red)
- [ ] Test: Vision requires non-empty title
- [ ] Test: Vision requires non-empty narrative
- [ ] Test: Vision rejects empty title (raises validation error)
- [ ] Test: Vision rejects empty narrative (raises validation error)
- [ ] Test: VisionStatus enum has active, achieved, evolved, abandoned
- [ ] Test: Vision status defaults to "active"
- [ ] Test: Vision metrics stored as JSON list
- [ ] Test: Vision next_review_date defaults to 90 days from creation
- [ ] Test: Vision auto-generates id, created_at, updated_at

### 1.2 Implement Vision Model (Green)
- [ ] Create `VisionStatus` enum
- [ ] Create `Vision` SQLModel in `src/jdo/models/vision.py`
- [ ] Run tests - all should pass

### 1.3 Vision Persistence Tests (Red)
- [ ] Test: Save vision and retrieve by id
- [ ] Test: List visions with status filter
- [ ] Test: Delete vision without goals succeeds
- [ ] Test: Delete vision with goals raises error

### 1.4 Implement Vision Persistence (Green)
- [ ] Add vision CRUD operations
- [ ] Add referential integrity check
- [ ] Run tests - all should pass

### 1.5 Vision Review Tests (Red)
- [ ] Test: Vision due for review when next_review_date <= today
- [ ] Test: Complete review sets last_reviewed_at to now
- [ ] Test: Complete review sets next_review_date to now + 90 days
- [ ] Test: Vision status transition active → achieved
- [ ] Test: Vision status transition active → evolved
- [ ] Test: Vision status transition active → abandoned

### 1.6 Implement Vision Review (Green)
- [ ] Implement review date queries
- [ ] Implement review completion logic
- [ ] Run tests - all should pass

## Phase 2: Milestone Model

### 2.1 Milestone Validation Tests (Red)
- [ ] Test: Milestone requires goal_id
- [ ] Test: Milestone requires non-empty title
- [ ] Test: Milestone requires target_date
- [ ] Test: Milestone rejects missing goal_id (raises validation error)
- [ ] Test: Milestone rejects empty title (raises validation error)
- [ ] Test: Milestone rejects missing target_date (raises validation error)
- [ ] Test: MilestoneStatus enum has pending, in_progress, completed, missed
- [ ] Test: Milestone status defaults to "pending"
- [ ] Test: Milestone auto-generates id, created_at, updated_at

### 2.2 Implement Milestone Model (Green)
- [ ] Create `MilestoneStatus` enum
- [ ] Create `Milestone` SQLModel in `src/jdo/models/milestone.py`
- [ ] Run tests - all should pass

### 2.3 Milestone Persistence Tests (Red)
- [ ] Test: Save milestone and retrieve by id
- [ ] Test: List milestones by goal_id sorted by target_date
- [ ] Test: Delete milestone without commitments succeeds
- [ ] Test: Delete milestone with commitments raises error

### 2.4 Implement Milestone Persistence (Green)
- [ ] Add milestone CRUD operations
- [ ] Add referential integrity check
- [ ] Run tests - all should pass

### 2.5 Milestone Status Tests (Red)
- [ ] Test: Transition pending → in_progress
- [ ] Test: Transition in_progress → completed sets completed_at
- [ ] Test: Overdue milestone (target_date passed, status=pending) → missed
- [ ] Test: Missed milestone can still be completed (late completion)

### 2.6 Implement Milestone Status (Green)
- [ ] Implement status transitions
- [ ] Implement auto-missed detection
- [ ] Run tests - all should pass

## Phase 3: Goal Model Extension

### 3.1 Goal-Vision Link Tests (Red)
- [ ] Test: Goal accepts optional vision_id
- [ ] Test: Goal with valid vision_id links to Vision
- [ ] Test: Goal with invalid vision_id raises FK error
- [ ] Test: Query goals by vision_id

### 3.2 Implement Goal-Vision Link (Green)
- [ ] Add vision_id field to Goal
- [ ] Add FK relationship
- [ ] Run tests - all should pass

### 3.3 Goal-Milestone Relationship Tests (Red)
- [ ] Test: Query milestones for goal
- [ ] Test: Goal progress = milestones completed / total milestones
- [ ] Test: Deleting goal with milestones raises error

### 3.4 Implement Goal-Milestone Relationship (Green)
- [ ] Add milestone query methods
- [ ] Add progress calculation
- [ ] Add deletion check
- [ ] Run tests - all should pass

## Phase 4: Commitment Model Extension

### 4.1 Commitment-Milestone Link Tests (Red)
- [ ] Test: Commitment accepts optional milestone_id
- [ ] Test: Commitment with valid milestone_id links to Milestone
- [ ] Test: Commitment with invalid milestone_id raises FK error
- [ ] Test: Orphan = no goal_id AND no milestone_id
- [ ] Test: Commitment with milestone_id but no goal_id is NOT orphan

### 4.2 Implement Commitment-Milestone Link (Green)
- [ ] Add milestone_id field to Commitment
- [ ] Add FK relationship
- [ ] Update orphan query logic
- [ ] Run tests - all should pass

## Phase 5: Hierarchy Queries

### 5.1 Query Tests (Red)
- [ ] Test: Query orphan commitments (no goal AND no milestone)
- [ ] Test: Query orphan goals (no vision)
- [ ] Test: Query visions due for review
- [ ] Test: Query milestones at risk (target_date within 7 days, status=pending)
- [ ] Test: Query full hierarchy tree

### 5.2 Implement Queries (Green)
- [ ] Implement all custom queries
- [ ] Run tests - all should pass

## Phase 6: TUI Commands

### 6.1 /vision Command Tests (Red)
- [ ] Test: /vision lists all visions
- [ ] Test: /vision new starts creation flow
- [ ] Test: /vision review lists visions due for review
- [ ] Test: Vision draft shows in data panel
- [ ] Test: Confirm creates vision in database

### 6.2 Implement /vision Command (Green)
- [ ] Create vision command handler
- [ ] Create vision draft panel
- [ ] Create vision view panel
- [ ] Run tests - all should pass

### 6.3 /milestone Command Tests (Red)
- [ ] Test: /milestone lists milestones for current goal
- [ ] Test: /milestone new requires goal context
- [ ] Test: /milestone new prompts for target_date
- [ ] Test: Milestone draft shows in data panel
- [ ] Test: Confirm creates milestone in database

### 6.4 Implement /milestone Command (Green)
- [ ] Create milestone command handler
- [ ] Create milestone draft panel
- [ ] Create milestone view panel
- [ ] Run tests - all should pass

### 6.5 Extended Command Tests (Red)
- [ ] Test: /show hierarchy displays tree view
- [ ] Test: /show orphan-goals lists goals without vision
- [ ] Test: /commit prompts for milestone when goal has milestones
- [ ] Test: /goal prompts for vision when visions exist

### 6.6 Implement Extended Commands (Green)
- [ ] Update existing commands
- [ ] Add hierarchy view
- [ ] Run tests - all should pass

## Phase 7: Keyboard Navigation

### 7.1 Shortcut Tests (Red)
- [ ] Test: 'v' key shows visions list
- [ ] Test: 'm' key shows milestones list
- [ ] Test: 'h' key shows hierarchy view
- [ ] Test: Footer shows new shortcuts

### 7.2 Implement Shortcuts (Green)
- [ ] Add bindings to HomeScreen
- [ ] Update footer
- [ ] Run tests - all should pass

## Phase 8: Views & Panels

### 8.1 Hierarchy View Tests (Red)
- [ ] Test: Tree shows Vision > Goal > Milestone > Commitment
- [ ] Test: Nodes expand on Enter/right arrow
- [ ] Test: Nodes collapse on left arrow
- [ ] Test: Enter on leaf navigates to item view

### 8.2 Implement Hierarchy View (Green)
- [ ] Create tree view widget
- [ ] Add navigation bindings
- [ ] Run tests - all should pass

### 8.3 Extended View Tests (Red)
- [ ] Test: Goal view shows "Vision: [title]" when linked
- [ ] Test: Goal view shows "Milestones: X of Y completed"
- [ ] Test: Commitment view shows "Milestone: [title]" when linked
- [ ] Test: Commitment view shows hierarchy breadcrumb

### 8.4 Implement Extended Views (Green)
- [ ] Update goal view template
- [ ] Update commitment view template
- [ ] Run tests - all should pass

## Phase 9: AI Integration

### 9.1 AI Prompt Tests (Red)
- [ ] Test: Vision creation prompts for vivid narrative
- [ ] Test: AI suggests metrics for vision
- [ ] Test: AI suggests milestones for goal
- [ ] Test: AI prompts for vision linkage on goal creation
- [ ] Test: AI prompts for milestone linkage on commitment creation

### 9.2 Implement AI Prompts (Green)
- [ ] Create vision prompt templates
- [ ] Create milestone suggestion logic
- [ ] Wire up linkage prompts
- [ ] Run tests - all should pass

## Phase 10: Review System

### 10.1 Vision Review Tests (Red)
- [ ] Test: App launch prompts when vision due for review
- [ ] Test: Review snooze doesn't repeat in session
- [ ] Test: Review completion updates timestamps

### 10.2 Implement Vision Review (Green)
- [ ] Add startup check
- [ ] Add review flow
- [ ] Run tests - all should pass

### 10.3 Milestone Auto-Update Tests (Red)
- [ ] Test: Startup checks for overdue milestones
- [ ] Test: Overdue pending milestone transitions to missed

### 10.4 Implement Milestone Auto-Update (Green)
- [ ] Add startup check
- [ ] Implement auto-transition
- [ ] Run tests - all should pass

## Phase 11: Visual Regression

### 11.1 Snapshot Tests
- [ ] Create snapshot: Visions list
- [ ] Create snapshot: Milestones list
- [ ] Create snapshot: Hierarchy tree view
- [ ] Create snapshot: Goal view with vision link
- [ ] Create snapshot: Commitment view with milestone link
- [ ] Run `pytest --snapshot-update` to generate baselines

## Phase 12: Integration Tests

### 12.1 End-to-End Tests
- [ ] Test: Create Vision → Goal → Milestone → Commitment flow
- [ ] Test: Hierarchy navigation end-to-end
- [ ] Test: Vision review flow
- [ ] Test: Milestone missed detection on startup

## Dependencies

- Phase 1-2 can run in parallel (Vision and Milestone models)
- Phase 3-4 depend on Phases 1-2 (need models for FKs)
- Phase 5 depends on Phases 1-4 (needs all models)
- Phase 6-8 depend on Phase 5 (needs queries)
- Phase 9-10 depend on Phase 6 (needs commands)
- Phase 11-12 require all previous phases

## Running Tests

```bash
# Run all tests
uv run pytest

# Run vision/milestone tests
uv run pytest tests/unit/models/test_vision.py -v
uv run pytest tests/unit/models/test_milestone.py -v

# Run with coverage
uv run pytest --cov=src/jdo --cov-report=term-missing

# Update snapshots
uv run pytest --snapshot-update
```
