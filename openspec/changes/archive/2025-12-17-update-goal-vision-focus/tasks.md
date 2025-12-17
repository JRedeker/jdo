# Tasks: Update Goal Model for Vision-Focused Growth Mindset (TDD)

This task list follows Test-Driven Development: write failing tests first, then implement to pass.

**Dependencies**: 
- Requires core domain models (base Goal model) - already implemented
- Requires `implement-jdo-app` (TUI app shell and command infrastructure)

## Phase 1: Goal Model Updates ✅

### 1.1 GoalStatus Extension Tests (Red) ✅
- [x] Test: GoalStatus enum includes `on_hold` value
- [x] Test: Goal can transition active → on_hold
- [x] Test: Goal can transition on_hold → active

### 1.2 Implement GoalStatus Extension (Green) ✅
- [x] Add `on_hold` to GoalStatus enum
- [x] Run tests - all should pass

### 1.3 Motivation Field Tests (Red) ✅
- [x] Test: Goal accepts optional motivation field
- [x] Test: Motivation can be None
- [x] Test: Motivation can be non-empty string

### 1.4 Implement Motivation Field (Green) ✅
- [x] Add `motivation` field to Goal model
- [x] Run tests - all should pass

### 1.5 Review Field Tests (Red) ✅
- [x] Test: Goal accepts optional next_review_date
- [x] Test: Goal accepts optional review_interval_days
- [x] Test: review_interval_days only accepts 7, 30, or 90
- [x] Test: review_interval_days rejects other values (e.g., 14)
- [x] Test: Goal accepts optional last_reviewed_at

### 1.6 Implement Review Fields (Green) ✅
- [x] Add `next_review_date` field
- [x] Add `review_interval_days` field with validation
- [x] Add `last_reviewed_at` field
- [x] Run tests - all should pass

### 1.7 Target Date Removal Tests (Red) ✅
- [x] Test: Goal model does not have target_date field (never existed)
- [x] Test: Creating Goal with target_date raises error (n/a - field never existed)

### 1.8 Implement Target Date Removal (Green) ✅
- [x] Remove `target_date` field if present (n/a - field never existed)
- [x] Run tests - all should pass

## Phase 2: Goal Progress ✅

### 2.1 Progress Calculation Tests (Red) ✅
- [x] Test: get_commitment_progress returns counts by status
- [x] Test: Progress includes total, completed, in_progress, pending, abandoned
- [x] Test: Goal with no commitments returns all zeros

### 2.2 Implement Progress Calculation (Green) ✅
- [x] Create `GoalProgress` dataclass in `src/jdo/models/goal.py`
- [x] Implement `get_commitment_progress` in `src/jdo/db/session.py`
- [x] Run tests - all should pass

## Phase 3: Review System ✅

### 3.1 Due For Review Query Tests (Red) ✅
- [x] Test: Query returns goals where next_review_date <= today
- [x] Test: Query excludes on_hold goals
- [x] Test: Query excludes achieved/abandoned goals
- [x] Test: Query returns empty list if no goals due

### 3.2 Implement Due For Review Query (Green) ✅
- [x] Implement `get_goals_due_for_review` in `src/jdo/db/session.py`
- [x] Run tests - all should pass

### 3.3 Complete Review Tests (Red) ✅
- [x] Test: complete_review sets last_reviewed_at to now
- [x] Test: complete_review calculates next_review_date from interval
- [x] Test: complete_review with no interval clears next_review_date
- [x] Test: complete_review updates updated_at

### 3.4 Implement Complete Review (Green) ✅
- [x] Implement `Goal.complete_review()` method
- [x] Run tests - all should pass

## Phase 4: Review Interval Constraints ✅

### 4.1 Interval Validation Tests (Red) ✅
- [x] Test: Interval 7 accepted (weekly)
- [x] Test: Interval 30 accepted (monthly)
- [x] Test: Interval 90 accepted (quarterly)
- [x] Test: Interval 14 rejected
- [x] Test: Interval 60 rejected

### 4.2 Implement Interval Validation (Green) ✅
- [x] Add validator for allowed intervals (model_validator)
- [x] Run tests - all should pass

### 4.3 Interval Label Tests (Red) ✅
- [x] Test: Interval 7 displays as "Weekly"
- [x] Test: Interval 30 displays as "Monthly"
- [x] Test: Interval 90 displays as "Quarterly"

### 4.4 Implement Interval Labels (Green) ✅
- [x] Add `interval_label` property to Goal model
- [x] Run tests - all should pass

## Phase 5: TUI Commands (Deferred to add-conversational-tui)

### 5.1 /goal review Tests (Red)
- [ ] Test: /goal review lists goals due for review
- [ ] Test: /goal review <id> shows specific goal review
- [ ] Test: Review interface shows motivation
- [ ] Test: Review interface shows commitment progress

### 5.2 Implement /goal review Command (Green)
- [ ] Create review list handler
- [ ] Create review detail handler
- [ ] Run tests - all should pass

### 5.3 Review Reflection Tests (Red)
- [ ] Test: Review prompts reflection questions
- [ ] Test: Review offers status change options (continue, hold, achieve, abandon)
- [ ] Test: Completing review schedules next review

### 5.4 Implement Review Reflection (Green)
- [ ] Add reflection prompts
- [ ] Add status change flow
- [ ] Run tests - all should pass

### 5.5 Goal Creation Tests (Red)
- [ ] Test: /goal creation prompts for motivation
- [ ] Test: Motivation prompt is skippable
- [ ] Test: /goal creation suggests review interval
- [ ] Test: Interval options shown as Weekly/Monthly/Quarterly

### 5.6 Implement Goal Creation Updates (Green)
- [ ] Add motivation prompt to creation flow
- [ ] Add interval suggestion
- [ ] Run tests - all should pass

## Phase 6: Data Panel Views (Deferred to add-conversational-tui)

### 6.1 Goal Detail View Tests (Red)
- [ ] Test: Goal view shows motivation prominently
- [ ] Test: Goal view shows commitment progress summary
- [ ] Test: Goal view shows next_review_date
- [ ] Test: Goal view shows "Due for review" indicator when applicable

### 6.2 Implement Goal Detail View Updates (Green)
- [ ] Update GoalDetailView template
- [ ] Run tests - all should pass

### 6.3 Goal List View Tests (Red)
- [ ] Test: Goal list shows review status icon for due goals
- [ ] Test: "Achieved" status de-emphasized in UI

### 6.4 Implement Goal List View Updates (Green)
- [ ] Update GoalListView with review indicators
- [ ] Adjust status display emphasis
- [ ] Run tests - all should pass

## Phase 7: Home Screen Integration (Deferred to add-conversational-tui)

### 7.1 Home Screen Tests (Red)
- [ ] Test: Home screen shows count of goals due for review
- [ ] Test: Indicator is subtle (not blocking)
- [ ] Test: Clicking indicator opens /goal review

### 7.2 Implement Home Screen Integration (Green)
- [ ] Add review indicator to home screen
- [ ] Wire up navigation
- [ ] Run tests - all should pass

## Phase 8: Visual Regression (Deferred to add-conversational-tui)

### 8.1 Snapshot Tests
- [ ] Create snapshot: Goal view with motivation
- [ ] Create snapshot: Goal view with progress
- [ ] Create snapshot: Goal list with review indicators
- [ ] Create snapshot: Goal review interface
- [ ] Run `pytest --snapshot-update` to generate baselines

## Phase 9: Integration Tests (Deferred to add-conversational-tui)

### 9.1 End-to-End Tests
- [ ] Test: Full goal review flow (view → reflect → schedule next)
- [ ] Test: Goal creation with motivation and interval
- [ ] Test: Status transition from review interface

## Dependencies

- Phase 1 can start immediately ✅
- Phase 2 depends on Phase 1 (needs updated model) ✅
- Phase 3 depends on Phases 1-2 (needs model and progress) ✅
- Phase 4 depends on Phase 1 (needs review fields) ✅
- Phase 5 depends on Phases 3-4 (needs review system) - deferred
- Phase 6 depends on Phases 2-3 (needs progress and review) - deferred
- Phase 7 depends on Phase 3 (needs due query) - deferred
- Phases 8-9 require all previous phases - deferred

## Running Tests

```bash
# Run all tests
uv run pytest

# Run goal-specific tests
uv run pytest tests/unit/models/test_goal.py -v
uv run pytest tests/unit/models/test_goal_progress.py -v
uv run pytest tests/unit/models/test_goal_review.py -v

# Run with coverage
uv run pytest --cov=src/jdo --cov-report=term-missing

# Update snapshots
uv run pytest --snapshot-update
```

## Summary

**Completed (Phases 1-4):**
- Goal model with `on_hold` status, `motivation` field, review fields
- `GoalProgress` dataclass with completion_rate calculation
- `Goal.is_due_for_review()` method
- `Goal.complete_review()` method  
- `Goal.interval_label` property (Weekly/Monthly/Quarterly)
- `get_commitment_progress()` query in session module
- `get_goals_due_for_review()` query in session module
- 25 new tests across 3 test files

**Deferred (Phases 5-9):**
TUI commands, views, and integration tests are deferred to `add-conversational-tui` 
as they require the conversational TUI infrastructure to be in place.
