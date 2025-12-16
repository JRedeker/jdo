# Tasks: Add Recurring Commitments (TDD)

This task list follows Test-Driven Development: write failing tests first, then implement to pass.

**Dependencies**: 
- Requires core domain models (Commitment, Task) - already implemented
- Requires `implement-jdo-app` (TUI app shell and command infrastructure)

## Phase 1: RecurringCommitment Model

### 1.1 RecurringCommitment Validation Tests (Red)
- [ ] Test: RecurringCommitment requires non-empty deliverable_template
- [ ] Test: RecurringCommitment requires stakeholder_id
- [ ] Test: RecurringCommitment requires recurrence_type
- [ ] Test: RecurrenceType enum has daily, weekly, monthly, yearly
- [ ] Test: RecurringCommitment status defaults to "active"
- [ ] Test: RecurringCommitment rejects empty deliverable_template
- [ ] Test: RecurringCommitment auto-generates id, created_at, updated_at

### 1.2 Implement RecurringCommitment Model (Green)
- [ ] Create `RecurrenceType` enum
- [ ] Create `EndType` enum (never, after_count, by_date)
- [ ] Create `RecurringCommitment` SQLModel
- [ ] Run tests - all should pass

### 1.3 Weekly Pattern Tests (Red)
- [ ] Test: days_of_week accepts list of 0-6 integers
- [ ] Test: days_of_week rejects values outside 0-6
- [ ] Test: days_of_week requires at least one day
- [ ] Test: Weekly pattern without days_of_week raises error

### 1.4 Implement Weekly Pattern (Green)
- [ ] Add days_of_week field validation
- [ ] Run tests - all should pass

### 1.5 Monthly Pattern Tests (Red)
- [ ] Test: day_of_month accepts 1-31
- [ ] Test: day_of_month rejects values outside 1-31
- [ ] Test: week_of_month accepts 1-5 with day_of_week
- [ ] Test: Monthly requires either day_of_month OR (week_of_month + day_of_week)

### 1.6 Implement Monthly Pattern (Green)
- [ ] Add day_of_month and week_of_month validation
- [ ] Run tests - all should pass

### 1.7 End Condition Tests (Red)
- [ ] Test: end_type=never has no end constraints
- [ ] Test: end_type=after_count requires end_after_count > 0
- [ ] Test: end_type=by_date requires end_by_date in future
- [ ] Test: Reject after_count without end_after_count

### 1.8 Implement End Conditions (Green)
- [ ] Add end condition validation
- [ ] Run tests - all should pass

## Phase 2: Task Template Model

### 2.1 TaskTemplate Tests (Red)
- [ ] Test: TaskTemplate requires non-empty title
- [ ] Test: TaskTemplate requires non-empty scope
- [ ] Test: TaskTemplate requires order
- [ ] Test: TaskTemplate sub_tasks defaults to empty list
- [ ] Test: Task templates stored as JSON in RecurringCommitment

### 2.2 Implement TaskTemplate (Green)
- [ ] Create `TaskTemplate` Pydantic model
- [ ] Add task_templates JSON field to RecurringCommitment
- [ ] Run tests - all should pass

## Phase 3: Commitment Model Extension

### 3.1 Commitment Link Tests (Red)
- [ ] Test: Commitment accepts optional recurring_commitment_id
- [ ] Test: Commitment with valid recurring_commitment_id links to template
- [ ] Test: Query commitments by recurring_commitment_id
- [ ] Test: Delete RecurringCommitment sets instances' recurring_commitment_id to NULL

### 3.2 Implement Commitment Link (Green)
- [ ] Add recurring_commitment_id field to Commitment
- [ ] Add FK with ON DELETE SET NULL
- [ ] Run tests - all should pass

## Phase 4: Recurrence Calculator

### 4.1 Daily Pattern Tests (Red)
- [ ] Test: get_next_due_date for daily returns next day
- [ ] Test: get_next_due_date for daily with interval=2 returns every other day

### 4.2 Implement Daily Pattern (Green)
- [ ] Create `src/jdo/recurrence/calculator.py`
- [ ] Implement daily calculation
- [ ] Run tests - all should pass

### 4.3 Weekly Pattern Tests (Red)
- [ ] Test: Weekly on Mon returns next Monday
- [ ] Test: Weekly on Mon,Wed,Fri returns next occurrence
- [ ] Test: Weekly with interval=2 returns every other week

### 4.4 Implement Weekly Pattern (Green)
- [ ] Implement weekly calculation
- [ ] Run tests - all should pass

### 4.5 Monthly Pattern Tests (Red)
- [ ] Test: Monthly on 15th returns next 15th
- [ ] Test: Monthly on 31st handles short months (uses last day)
- [ ] Test: Monthly on "2nd Tuesday" returns correct date
- [ ] Test: Monthly on "last Friday" returns correct date

### 4.6 Implement Monthly Pattern (Green)
- [ ] Implement monthly calculation with edge cases
- [ ] Run tests - all should pass

### 4.7 Yearly Pattern Tests (Red)
- [ ] Test: Yearly on March 15 returns next occurrence
- [ ] Test: Yearly on Feb 29 handles non-leap years

### 4.8 Implement Yearly Pattern (Green)
- [ ] Implement yearly calculation
- [ ] Run tests - all should pass

## Phase 5: Instance Generation

### 5.1 Generation Tests (Red)
- [ ] Test: generate_instance creates Commitment from template
- [ ] Test: Generated commitment has correct deliverable, stakeholder, due_date
- [ ] Test: Generated commitment has recurring_commitment_id set
- [ ] Test: Tasks copied from task_templates with status=pending
- [ ] Test: Sub-tasks copied with completed=false
- [ ] Test: last_generated_date updated after generation
- [ ] Test: instances_generated incremented after generation

### 5.2 Implement Generation (Green)
- [ ] Create `src/jdo/recurrence/generator.py`
- [ ] Implement generate_instance function
- [ ] Run tests - all should pass

### 5.3 End Condition Tests (Red)
- [ ] Test: Generation stops when instances_generated >= end_after_count
- [ ] Test: Generation stops when next_due_date > end_by_date
- [ ] Test: Generation continues indefinitely when end_type=never

### 5.4 Implement End Condition Checking (Green)
- [ ] Add should_generate check
- [ ] Run tests - all should pass

### 5.5 Catch-Up Logic Tests (Red)
- [ ] Test: Missed occurrences generate only current instance (not historical)
- [ ] Test: Multiple missed occurrences still generate only one

### 5.6 Implement Catch-Up Logic (Green)
- [ ] Implement current-only generation
- [ ] Run tests - all should pass

## Phase 6: Generation Triggers

### 6.1 Trigger Tests (Red)
- [ ] Test: Viewing upcoming commitments triggers generation check
- [ ] Test: Completing instance triggers next generation
- [ ] Test: /show commitments includes generated instances

### 6.2 Implement Triggers (Green)
- [ ] Add generation check to commitment queries
- [ ] Add generation on completion
- [ ] Run tests - all should pass

## Phase 7: TUI Commands

### 7.1 /recurring Command Tests (Red)
- [ ] Test: /recurring lists all recurring commitments
- [ ] Test: /recurring shows pattern summary (e.g., "Weekly on Mon, Wed")
- [ ] Test: /recurring shows next due date
- [ ] Test: /recurring shows active/paused status

### 7.2 Implement /recurring List (Green)
- [ ] Create recurring list command handler
- [ ] Create pattern summary formatter
- [ ] Run tests - all should pass

### 7.3 /recurring new Tests (Red)
- [ ] Test: /recurring new extracts pattern from conversation
- [ ] Test: AI suggests pattern from "every Monday"
- [ ] Test: AI extracts days from "Mon, Wed, Fri"
- [ ] Test: Confirm creates recurring commitment

### 7.4 Implement /recurring new (Green)
- [ ] Create recurring creation flow
- [ ] Wire up AI extraction
- [ ] Run tests - all should pass

### 7.5 Management Command Tests (Red)
- [ ] Test: /recurring pause <id> sets status to paused
- [ ] Test: /recurring resume <id> sets status to active
- [ ] Test: /recurring delete <id> prompts for confirmation
- [ ] Test: Delete removes template, instances keep recurring_commitment_id=NULL

### 7.6 Implement Management Commands (Green)
- [ ] Create pause, resume, delete handlers
- [ ] Run tests - all should pass

## Phase 8: Data Panel Views

### 8.1 View Tests (Red)
- [ ] Test: RecurringCommitmentListView shows all templates
- [ ] Test: RecurringCommitmentDetailView shows pattern details
- [ ] Test: Commitment view shows ↻ indicator when recurring
- [ ] Test: Instance count displayed in detail view

### 8.2 Implement Views (Green)
- [ ] Create list view widget
- [ ] Create detail view widget
- [ ] Add recurring indicator to commitment views
- [ ] Run tests - all should pass

## Phase 9: Visual Regression

### 9.1 Snapshot Tests
- [ ] Create snapshot: Recurring commitment list
- [ ] Create snapshot: Recurring commitment detail
- [ ] Create snapshot: Commitment with recurring indicator
- [ ] Run `pytest --snapshot-update` to generate baselines

## Phase 10: Integration Tests

### 10.1 End-to-End Tests
- [ ] Test: Create recurring → generate first instance → complete → generate next
- [ ] Test: Pause recurring → no new instances generated
- [ ] Test: Resume recurring → instances generated again
- [ ] Test: Delete recurring → instances remain with NULL reference

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
