# Tasks: Add Recurring Commitments (TDD)

This task list follows Test-Driven Development: write failing tests first, then implement to pass.

**Dependencies**: 
- Requires core domain models (Commitment, Task) - already implemented
- Requires `implement-jdo-app` (TUI app shell and command infrastructure)

## Phase 1: RecurringCommitment Model

### 1.1 RecurringCommitment Validation Tests (Red)
- [x] Test: RecurringCommitment requires non-empty deliverable_template
- [x] Test: RecurringCommitment requires stakeholder_id
- [x] Test: RecurringCommitment requires recurrence_type
- [x] Test: RecurrenceType enum has daily, weekly, monthly, yearly
- [x] Test: RecurringCommitment status defaults to "active"
- [x] Test: RecurringCommitment rejects empty deliverable_template
- [x] Test: RecurringCommitment auto-generates id, created_at, updated_at

### 1.2 Implement RecurringCommitment Model (Green)
- [x] Create `RecurrenceType` enum
- [x] Create `EndType` enum (never, after_count, by_date)
- [x] Create `RecurringCommitment` SQLModel
- [x] Run tests - all should pass

### 1.3 Weekly Pattern Tests (Red)
- [x] Test: days_of_week accepts list of 0-6 integers
- [x] Test: days_of_week rejects values outside 0-6
- [x] Test: days_of_week requires at least one day
- [x] Test: Weekly pattern without days_of_week raises error

### 1.4 Implement Weekly Pattern (Green)
- [x] Add days_of_week field validation
- [x] Run tests - all should pass

### 1.5 Monthly Pattern Tests (Red)
- [x] Test: day_of_month accepts 1-31
- [x] Test: day_of_month rejects values outside 1-31
- [x] Test: week_of_month accepts 1-5 with day_of_week
- [x] Test: Monthly requires either day_of_month OR (week_of_month + day_of_week)

### 1.6 Implement Monthly Pattern (Green)
- [x] Add day_of_month and week_of_month validation
- [x] Run tests - all should pass

### 1.7 End Condition Tests (Red)
- [x] Test: end_type=never has no end constraints
- [x] Test: end_type=after_count requires end_after_count > 0
- [x] Test: end_type=by_date requires end_by_date in future
- [x] Test: Reject after_count without end_after_count

### 1.8 Implement End Conditions (Green)
- [x] Add end condition validation
- [x] Run tests - all should pass

## Phase 2: Task Template Model

### 2.1 TaskTemplate Tests (Red)
- [x] Test: TaskTemplate requires non-empty title
- [x] Test: TaskTemplate requires non-empty scope
- [x] Test: TaskTemplate requires order
- [x] Test: TaskTemplate sub_tasks defaults to empty list
- [x] Test: Task templates stored as JSON in RecurringCommitment

### 2.2 Implement TaskTemplate (Green)
- [x] Create `TaskTemplate` Pydantic model
- [x] Add task_templates JSON field to RecurringCommitment
- [x] Run tests - all should pass

## Phase 3: Commitment Model Extension

### 3.1 Commitment Link Tests (Red)
- [x] Test: Commitment accepts optional recurring_commitment_id
- [x] Test: Commitment with valid recurring_commitment_id links to template
- [x] Test: Query commitments by recurring_commitment_id
- [x] Test: Delete RecurringCommitment sets instances' recurring_commitment_id to NULL

### 3.2 Implement Commitment Link (Green)
- [x] Add recurring_commitment_id field to Commitment
- [x] Add FK with ON DELETE SET NULL
- [x] Run tests - all should pass

## Phase 4: Recurrence Calculator

### 4.1 Daily Pattern Tests (Red)
- [x] Test: get_next_due_date for daily returns next day
- [x] Test: get_next_due_date for daily with interval=2 returns every other day

### 4.2 Implement Daily Pattern (Green)
- [x] Create `src/jdo/recurrence/calculator.py`
- [x] Implement daily calculation
- [x] Run tests - all should pass

### 4.3 Weekly Pattern Tests (Red)
- [x] Test: Weekly on Mon returns next Monday
- [x] Test: Weekly on Mon,Wed,Fri returns next occurrence
- [x] Test: Weekly with interval=2 returns every other week

### 4.4 Implement Weekly Pattern (Green)
- [x] Implement weekly calculation
- [x] Run tests - all should pass

### 4.5 Monthly Pattern Tests (Red)
- [x] Test: Monthly on 15th returns next 15th
- [x] Test: Monthly on 31st handles short months (uses last day)
- [x] Test: Monthly on "2nd Tuesday" returns correct date
- [x] Test: Monthly on "last Friday" returns correct date

### 4.6 Implement Monthly Pattern (Green)
- [x] Implement monthly calculation with edge cases
- [x] Run tests - all should pass

### 4.7 Yearly Pattern Tests (Red)
- [x] Test: Yearly on March 15 returns next occurrence
- [x] Test: Yearly on Feb 29 handles non-leap years

### 4.8 Implement Yearly Pattern (Green)
- [x] Implement yearly calculation
- [x] Run tests - all should pass

## Phase 5: Instance Generation

### 5.1 Generation Tests (Red)
- [x] Test: generate_instance creates Commitment from template
- [x] Test: Generated commitment has correct deliverable, stakeholder, due_date
- [x] Test: Generated commitment has recurring_commitment_id set
- [x] Test: Tasks copied from task_templates with status=pending
- [x] Test: Sub-tasks copied with completed=false
- [x] Test: last_generated_date updated after generation
- [x] Test: instances_generated incremented after generation

### 5.2 Implement Generation (Green)
- [x] Create `src/jdo/recurrence/generator.py`
- [x] Implement generate_instance function
- [x] Run tests - all should pass

### 5.3 End Condition Tests (Red)
- [x] Test: Generation stops when instances_generated >= end_after_count
- [x] Test: Generation stops when next_due_date > end_by_date
- [x] Test: Generation continues indefinitely when end_type=never

### 5.4 Implement End Condition Checking (Green)
- [x] Add should_generate check
- [x] Run tests - all should pass

### 5.5 Catch-Up Logic Tests (Red)
- [x] Test: Missed occurrences generate only current instance (not historical)
- [x] Test: Multiple missed occurrences still generate only one

### 5.6 Implement Catch-Up Logic (Green)
- [x] Implement current-only generation
- [x] Run tests - all should pass

## Phase 6: Generation Triggers

### 6.1 Trigger Tests (Red)
- [x] Test: Viewing upcoming commitments triggers generation check
- [x] Test: Completing instance triggers next generation
- [x] Test: /show commitments includes generated instances

### 6.2 Implement Triggers (Green)
- [x] Add generation check to commitment queries
- [x] Add generation on completion
- [x] Run tests - all should pass

## Phase 7: TUI Commands

### 7.1 /recurring Command Tests (Red)
- [x] Test: /recurring lists all recurring commitments
- [x] Test: /recurring shows pattern summary (e.g., "Weekly on Mon, Wed")
- [x] Test: /recurring shows next due date
- [x] Test: /recurring shows active/paused status

### 7.2 Implement /recurring List (Green)
- [x] Create recurring list command handler
- [x] Create pattern summary formatter
- [x] Run tests - all should pass

### 7.3 /recurring new Tests (Red)
- [x] Test: /recurring new extracts pattern from conversation
- [x] Test: AI suggests pattern from "every Monday"
- [x] Test: AI extracts days from "Mon, Wed, Fri"
- [x] Test: Confirm creates recurring commitment

### 7.4 Implement /recurring new (Green)
- [x] Create recurring creation flow
- [x] Wire up AI extraction
- [x] Run tests - all should pass

### 7.5 Management Command Tests (Red)
- [x] Test: /recurring pause <id> sets status to paused
- [x] Test: /recurring resume <id> sets status to active
- [x] Test: /recurring delete <id> prompts for confirmation
- [x] Test: Delete removes template, instances keep recurring_commitment_id=NULL

### 7.6 Implement Management Commands (Green)
- [x] Create pause, resume, delete handlers
- [x] Run tests - all should pass

## Phase 8: Data Panel Views

### 8.1 View Tests (Red)
- [x] Test: RecurringCommitmentListView shows all templates
- [x] Test: RecurringCommitmentDetailView shows pattern details
- [x] Test: Commitment view shows ↻ indicator when recurring
- [x] Test: Instance count displayed in detail view

### 8.2 Implement Views (Green)
- [x] Create list view widget
- [x] Create detail view widget
- [x] Add recurring indicator to commitment views
- [x] Run tests - all should pass

## Phase 9: Visual Regression (DEFERRED)

Visual regression snapshots deferred to FRC (recurring_commitment_snapshots).

### 9.1 Snapshot Tests
- [x] Create snapshot: Recurring commitment list (DEFERRED to FRC)
- [x] Create snapshot: Recurring commitment detail (DEFERRED to FRC)
- [x] Create snapshot: Commitment with recurring indicator (DEFERRED to FRC)
- [x] Run `pytest --snapshot-update` to generate baselines (N/A)

## Phase 10: Integration Tests

### 10.1 End-to-End Tests
- [x] Test: Create recurring → generate first instance → complete → generate next
- [x] Test: Pause recurring → no new instances generated
- [x] Test: Resume recurring → instances generated again
- [x] Test: Delete recurring → instances remain with NULL reference

## Dependencies

- Phase 1-2 can run in parallel (RecurringCommitment and TaskTemplate)
- Phase 3 depends on Phase 1 (needs RecurringCommitment model)
- Phase 4 depends on Phase 1 (needs RecurrenceType)
- Phase 5 depends on Phases 1-4 (needs all models and calculator)
- Phase 6 depends on Phase 5 (needs generator)
- Phase 7-8 depend on Phase 6 (needs triggers working)
- Phase 9-10 require all previous phases

## Running Tests

```bash
# Run all tests
uv run pytest

# Run recurrence tests
uv run pytest tests/unit/models/test_recurring_commitment.py -v
uv run pytest tests/unit/recurrence/ -v

# Run with coverage
uv run pytest --cov=src/jdo --cov-report=term-missing

# Update snapshots
uv run pytest --snapshot-update
```
