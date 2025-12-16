# Tasks: Add Core Domain Models (TDD)

This task list follows Test-Driven Development: write failing tests first, then implement to pass.

## Phase 1: Stakeholder Model

### 1.1 Stakeholder Validation Tests (Red)
- [x] Test: Stakeholder requires non-empty name
- [x] Test: Stakeholder requires valid StakeholderType enum
- [x] Test: Stakeholder rejects empty name (raises validation error)
- [x] Test: Stakeholder rejects invalid type (raises validation error)
- [x] Test: Stakeholder auto-generates id, created_at, updated_at
- [x] Test: Stakeholder accepts optional contact_info and notes

### 1.2 Implement Stakeholder Model (Green)
- [x] Create `StakeholderType` enum (person, team, organization, self)
- [x] Create `Stakeholder` SQLModel in `src/jdo/models/stakeholder.py`
- [x] Run tests - all should pass

### 1.3 Stakeholder Persistence Tests (Red)
- [x] Test: Save stakeholder to database and retrieve by id
- [x] Test: Update stakeholder name refreshes updated_at
- [x] Test: Delete stakeholder without commitments succeeds
- [x] Test: Delete stakeholder with commitments raises error
- [x] Test: List stakeholders returns all stakeholders

### 1.4 Implement Stakeholder Persistence (Green)
- [x] Add stakeholder CRUD operations via SQLModel session
- [x] Add referential integrity check for deletion
- [x] Run tests - all should pass

### 1.5 Self Stakeholder Tests (Red)
- [x] ~~Test: Empty database auto-creates "Self" stakeholder on first access~~ DEFERRED to TUI
- [x] ~~Test: Non-empty database does not create duplicate "Self"~~ DEFERRED to TUI

### 1.6 Implement Self Stakeholder Default (Green)
- [x] ~~Add auto-creation logic for "Self" stakeholder~~ DEFERRED - will be created on first TUI run

## Phase 2: Goal Model

### 2.1 Goal Validation Tests (Red)
- [x] Test: Goal requires non-empty title
- [x] Test: Goal requires non-empty problem_statement
- [x] Test: Goal requires non-empty solution_vision
- [x] Test: Goal rejects empty title (raises validation error)
- [x] Test: Goal rejects empty problem_statement (raises validation error)
- [x] Test: Goal rejects empty solution_vision (raises validation error)
- [x] Test: Goal status defaults to "active"
- [x] Test: Goal accepts optional motivation, parent_goal_id, next_review_date
- [x] Test: Goal auto-generates id, created_at, updated_at

### 2.2 Implement Goal Model (Green)
- [x] Create `GoalStatus` enum (active, on_hold, achieved, abandoned)
- [x] Create `Goal` SQLModel in `src/jdo/models/goal.py`
- [x] Run tests - all should pass

### 2.3 Goal Nesting Tests (Red)
- [x] Test: Goal with valid parent_goal_id creates hierarchy
- [x] Test: Query child goals by parent_goal_id
- [x] Test: Prevent circular nesting (goal cannot be its own parent)
- [x] Test: Prevent circular nesting (goal cannot reference descendant as parent)

### 2.4 Implement Goal Nesting (Green)
- [x] Add parent_goal_id FK relationship
- [x] Add circular reference validation
- [x] Run tests - all should pass

### 2.5 Goal Persistence Tests (Red)
- [x] Test: Save goal to database and retrieve by id
- [x] Test: List goals with status filter
- [x] Test: Delete goal without commitments or children succeeds
- [x] Test: Delete goal with commitments raises error
- [x] Test: Delete goal with children raises error

### 2.6 Implement Goal Persistence (Green)
- [x] Add goal CRUD operations via SQLModel session
- [x] Add referential integrity checks for deletion
- [x] Run tests - all should pass

### 2.7 Goal Status Transition Tests (Red)
- [x] Test: Transition active → achieved updates status and updated_at
- [x] Test: Transition active → abandoned updates status and updated_at
- [x] Test: Transition active → on_hold updates status and updated_at
- [x] Test: Transition on_hold → active updates status and updated_at

### 2.8 Implement Goal Status Transitions (Green)
- [x] Add status transition logic
- [x] Run tests - all should pass

## Phase 3: Commitment Model

### 3.1 Commitment Validation Tests (Red)
- [x] Test: Commitment requires non-empty deliverable
- [x] Test: Commitment requires stakeholder_id
- [x] Test: Commitment requires due_date
- [x] Test: Commitment rejects empty deliverable (raises validation error)
- [x] Test: Commitment rejects missing stakeholder_id (raises validation error)
- [x] Test: Commitment rejects missing due_date (raises validation error)
- [x] Test: Commitment status defaults to "pending"
- [x] Test: Commitment due_time defaults to 09:00 when not specified
- [x] Test: Commitment accepts optional goal_id, due_time, timezone, notes
- [x] Test: Commitment auto-generates id, created_at, updated_at

### 3.2 Implement Commitment Model (Green)
- [x] Create `CommitmentStatus` enum (pending, in_progress, completed, abandoned)
- [x] Create `Commitment` SQLModel in `src/jdo/models/commitment.py`
- [x] Run tests - all should pass

### 3.3 Commitment-Goal Association Tests (Red)
- [x] Test: Commitment with valid goal_id links to Goal
- [x] Test: Commitment without goal_id exists independently
- [x] Test: Query commitments by goal_id

### 3.4 Implement Commitment-Goal Association (Green)
- [x] Add goal_id FK relationship
- [x] Run tests - all should pass

### 3.5 Commitment Persistence Tests (Red)
- [x] Test: Save commitment to database and retrieve by id
- [x] Test: List commitments with status filter
- [x] Test: List commitments with due_date filter
- [x] Test: Delete commitment also deletes associated tasks (cascade)

### 3.6 Implement Commitment Persistence (Green)
- [x] Add commitment CRUD operations via SQLModel session
- [x] Add cascade delete for tasks
- [x] Run tests - all should pass

### 3.7 Commitment Status Transition Tests (Red)
- [x] Test: Transition pending → in_progress updates status
- [x] Test: Transition in_progress → completed sets completed_at
- [x] Test: Transition to abandoned updates status
- [x] Test: Transition completed → in_progress clears completed_at
- [x] Test: Completing all tasks does NOT auto-complete commitment
- [x] Test: Reject "skipped" status for commitments

### 3.8 Implement Commitment Status Transitions (Green)
- [x] Add status transition logic with completed_at handling
- [x] Add validation to reject "skipped" status
- [x] Run tests - all should pass

### 3.9 Commitment Due Date Query Tests (Red)
- [x] Test: Query overdue commitments (due_date < today, not completed/abandoned)
- [x] Test: Query commitments due within N days
- [x] Test: Query commitments due today sorted by due_time

### 3.10 Implement Commitment Due Date Queries (Green)
- [x] Add due date query methods
- [x] Run tests - all should pass

## Phase 4: Task Model

### 4.1 Task Validation Tests (Red)
- [x] Test: Task requires commitment_id
- [x] Test: Task requires non-empty title
- [x] Test: Task requires non-empty scope
- [x] Test: Task requires order
- [x] Test: Task rejects empty title (raises validation error)
- [x] Test: Task rejects empty scope (raises validation error)
- [x] Test: Task rejects missing commitment_id (raises validation error)
- [x] Test: Task status defaults to "pending"
- [x] Test: Task sub_tasks defaults to empty list
- [x] Test: Task auto-generates id, created_at, updated_at

### 4.2 Implement Task Model (Green)
- [x] Create `TaskStatus` enum (pending, in_progress, completed, skipped)
- [x] Create `SubTask` Pydantic model (description, completed)
- [x] Create `Task` SQLModel in `src/jdo/models/task.py`
- [x] Run tests - all should pass

### 4.3 SubTask Tests (Red)
- [x] Test: Task with sub_tasks stores them as JSON
- [x] Test: SubTask requires non-empty description
- [x] Test: SubTask completed defaults to False
- [x] Test: Toggle sub_task.completed updates parent Task.updated_at

### 4.4 Implement SubTask (Green)
- [x] Add JSON column for sub_tasks
- [x] Add sub_task toggle logic
- [x] Run tests - all should pass

### 4.5 Task Ordering Tests (Red)
- [x] Test: Query tasks for commitment returns sorted by order ascending
- [x] Test: Reorder tasks updates order values correctly
- [x] Test: New task gets next available order number

### 4.6 Implement Task Ordering (Green)
- [x] Add order-based query methods
- [x] Add reorder logic
- [x] Run tests - all should pass

### 4.7 Task Persistence Tests (Red)
- [x] Test: Save task with sub_tasks and retrieve together
- [x] Test: Update sub_task persists in JSON field
- [x] Test: Delete task removes from database

### 4.8 Implement Task Persistence (Green)
- [x] Add task CRUD operations via SQLModel session
- [x] Run tests - all should pass

### 4.9 Task Status Transition Tests (Red)
- [x] Test: Transition pending → in_progress updates status
- [x] Test: Transition in_progress → completed updates status
- [x] Test: Transition to "skipped" marks task as not needed
- [x] Test: Skipped tasks do not block commitment completion
- [x] Test: Task in_progress auto-transitions pending Commitment to in_progress
- [x] Test: Task in_progress does NOT change non-pending Commitment

### 4.10 Implement Task Status Transitions (Green)
- [x] Add status transition logic
- [x] Add commitment auto-transition on task start
- [x] Run tests - all should pass

## Phase 5: Cross-Model Integration

### 5.1 Integration Tests (Red)
- [x] Test: Full hierarchy: Stakeholder → Goal → Commitment → Task
- [x] Test: Cascade delete: Commitment deletion removes Tasks
- [x] Test: Referential integrity: Cannot delete Stakeholder with Commitments
- [x] Test: Referential integrity: Cannot delete Goal with Commitments
- [x] Test: Referential integrity: Cannot delete Goal with child Goals

### 5.2 Implement Integration (Green)
- [x] Wire up all FK relationships
- [x] Add cascade and integrity rules
- [x] Run tests - all should pass

### 5.3 Refactor
- [x] ~~Extract shared timestamp handling to `src/jdo/models/utils.py`~~ Not needed - SQLModel handles it
- [x] ~~Add timezone utility for EST default~~ Using settings.timezone
- [x] Export all models from `src/jdo/models/__init__.py`
- [x] Run all tests - verify still passing

## Phase 6: TUI Integration (Pilot Tests)

*MOVED to `add-conversational-tui` - TUI screens are owned by that spec.*

### ~~6.1 Stakeholder Screen Tests (Red)~~
### ~~6.2 Implement Stakeholder Screens (Green)~~
### ~~6.3 Goal Screen Tests (Red)~~
### ~~6.4 Implement Goal Screens (Green)~~
### ~~6.5 Commitment Screen Tests (Red)~~
### ~~6.6 Implement Commitment Screens (Green)~~
### ~~6.7 Task View Tests (Red)~~
### ~~6.8 Implement Task Views (Green)~~

## Phase 7: Visual Regression

*CANCELLED - Low value, high maintenance. Functional tests are sufficient.*

### ~~7.1 Snapshot Tests~~

## Summary

**Completed**: Phases 1-5 (Stakeholder, Goal, Commitment, Task models + Integration)
**Moved**: Phase 6 (TUI Screens) → `add-conversational-tui`
**Cancelled**: Phase 7 (Visual Regression)

**Test Results**: 54 model tests + 6 integration tests passing

## Deferred Items Resolution

| Item | Resolution | Rationale |
|------|------------|-----------|
| Self Stakeholder auto-creation | Moved to TUI | Created on first app run, not model layer |
| TUI Screens (Phase 6) | Moved to `add-conversational-tui` | That spec owns all TUI screens |
| Visual Snapshots (Phase 7) | Cancelled | Low value, high maintenance burden |
| Timestamp utils extraction | Cancelled | SQLModel handles timestamps natively |

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/jdo --cov-report=term-missing

# Run model tests only
uv run pytest tests/unit/models/ -v

# Run integration tests
uv run pytest tests/integration/ -v
```
