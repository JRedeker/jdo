# Tasks: Update Goal Model for Vision-Focused Growth Mindset (TDD)

This task list follows Test-Driven Development: write failing tests first, then implement to pass.

**Dependencies**: 
- Requires core domain models (base Goal model) - already implemented
- Requires `implement-jdo-app` (TUI app shell and command infrastructure)

## Phase 1: Goal Model Updates

### 1.1 GoalStatus Extension Tests (Red)
- [ ] Test: GoalStatus enum includes `on_hold` value
- [ ] Test: Goal can transition active → on_hold
- [ ] Test: Goal can transition on_hold → active

### 1.2 Implement GoalStatus Extension (Green)
- [ ] Add `on_hold` to GoalStatus enum
- [ ] Run tests - all should pass

### 1.3 Motivation Field Tests (Red)
- [ ] Test: Goal accepts optional motivation field
- [ ] Test: Motivation can be None
- [ ] Test: Motivation can be non-empty string

### 1.4 Implement Motivation Field (Green)
- [ ] Add `motivation` field to Goal model
- [ ] Run tests - all should pass

### 1.5 Review Field Tests (Red)
- [ ] Test: Goal accepts optional next_review_date
- [ ] Test: Goal accepts optional review_interval_days
- [ ] Test: review_interval_days only accepts 7, 30, or 90
- [ ] Test: review_interval_days rejects other values (e.g., 14)
- [ ] Test: Goal accepts optional last_reviewed_at

### 1.6 Implement Review Fields (Green)
- [ ] Add `next_review_date` field
- [ ] Add `review_interval_days` field with validation
- [ ] Add `last_reviewed_at` field
- [ ] Run tests - all should pass

### 1.7 Target Date Removal Tests (Red)
- [ ] Test: Goal model does not have target_date field
- [ ] Test: Creating Goal with target_date raises error

### 1.8 Implement Target Date Removal (Green)
- [ ] Remove `target_date` field if present
- [ ] Run tests - all should pass

## Phase 2: Goal Progress

### 2.1 Progress Calculation Tests (Red)
- [ ] Test: get_commitment_progress returns counts by status
- [ ] Test: Progress includes total, completed, in_progress, pending, abandoned
- [ ] Test: Goal with no commitments returns all zeros

### 2.2 Implement Progress Calculation (Green)
- [ ] Create `GoalProgress` dataclass
- [ ] Implement progress query
- [ ] Run tests - all should pass

## Phase 3: Review System

### 3.1 Due For Review Query Tests (Red)
- [ ] Test: Query returns goals where next_review_date <= today
- [ ] Test: Query excludes on_hold goals
- [ ] Test: Query excludes achieved/abandoned goals
- [ ] Test: Query returns empty list if no goals due

### 3.2 Implement Due For Review Query (Green)
- [ ] Create `src/jdo/goals/review.py`
- [ ] Implement get_goals_due_for_review
- [ ] Run tests - all should pass

### 3.3 Complete Review Tests (Red)
- [ ] Test: complete_review sets last_reviewed_at to now
- [ ] Test: complete_review calculates next_review_date from interval
- [ ] Test: complete_review with no interval clears next_review_date
- [ ] Test: complete_review updates updated_at

### 3.4 Implement Complete Review (Green)
- [ ] Implement complete_review function
- [ ] Run tests - all should pass

## Phase 4: Review Interval Constraints

### 4.1 Interval Validation Tests (Red)
- [ ] Test: Interval 7 accepted (weekly)
- [ ] Test: Interval 30 accepted (monthly)
- [ ] Test: Interval 90 accepted (quarterly)
- [ ] Test: Interval 14 rejected
- [ ] Test: Interval 60 rejected

### 4.2 Implement Interval Validation (Green)
- [ ] Add validator for allowed intervals
- [ ] Run tests - all should pass

### 4.3 Interval Label Tests (Red)
- [ ] Test: Interval 7 displays as "Weekly"
- [ ] Test: Interval 30 displays as "Monthly"
- [ ] Test: Interval 90 displays as "Quarterly"

### 4.4 Implement Interval Labels (Green)
- [ ] Add interval_label property or helper
- [ ] Run tests - all should pass

## Phase 5: TUI Commands

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

## Phase 6: Data Panel Views

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

## Phase 7: Home Screen Integration

### 7.1 Home Screen Tests (Red)
- [ ] Test: Home screen shows count of goals due for review
- [ ] Test: Indicator is subtle (not blocking)
- [ ] Test: Clicking indicator opens /goal review

### 7.2 Implement Home Screen Integration (Green)
- [ ] Add review indicator to home screen
- [ ] Wire up navigation
- [ ] Run tests - all should pass

## Phase 8: Visual Regression

### 8.1 Snapshot Tests
- [ ] Create snapshot: Goal view with motivation
- [ ] Create snapshot: Goal view with progress
- [ ] Create snapshot: Goal list with review indicators
- [ ] Create snapshot: Goal review interface
- [ ] Run `pytest --snapshot-update` to generate baselines

## Phase 9: Integration Tests

### 9.1 End-to-End Tests
- [ ] Test: Full goal review flow (view → reflect → schedule next)
- [ ] Test: Goal creation with motivation and interval
- [ ] Test: Status transition from review interface

## Dependencies

- Phase 1 can start immediately
- Phase 2 depends on Phase 1 (needs updated model)
- Phase 3 depends on Phases 1-2 (needs model and progress)
- Phase 4 depends on Phase 1 (needs review fields)
- Phase 5 depends on Phases 3-4 (needs review system)
- Phase 6 depends on Phases 2-3 (needs progress and review)
- Phase 7 depends on Phase 3 (needs due query)
- Phases 8-9 require all previous phases

## Running Tests

```bash
# Run all tests
uv run pytest

# Run goal-specific tests
uv run pytest tests/unit/models/test_goal.py -v
uv run pytest tests/unit/goals/test_review.py -v

# Run with coverage
uv run pytest --cov=src/jdo --cov-report=term-missing

# Update snapshots
uv run pytest --snapshot-update
```
