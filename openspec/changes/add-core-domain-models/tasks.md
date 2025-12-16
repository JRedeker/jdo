# Tasks: Add Core Domain Models (TDD)

This task list follows Test-Driven Development: write failing tests first, then implement to pass.

## Phase 1: Stakeholder Model

### 1.1 Stakeholder Validation Tests (Red)
- [ ] Test: Stakeholder requires non-empty name
- [ ] Test: Stakeholder requires valid StakeholderType enum
- [ ] Test: Stakeholder rejects empty name (raises validation error)
- [ ] Test: Stakeholder rejects invalid type (raises validation error)
- [ ] Test: Stakeholder auto-generates id, created_at, updated_at
- [ ] Test: Stakeholder accepts optional contact_info and notes

### 1.2 Implement Stakeholder Model (Green)
- [ ] Create `StakeholderType` enum (person, team, organization, self)
- [ ] Create `Stakeholder` SQLModel in `src/jdo/models/stakeholder.py`
- [ ] Run tests - all should pass

### 1.3 Stakeholder Persistence Tests (Red)
- [ ] Test: Save stakeholder to database and retrieve by id
- [ ] Test: Update stakeholder name refreshes updated_at
- [ ] Test: Delete stakeholder without commitments succeeds
- [ ] Test: Delete stakeholder with commitments raises error
- [ ] Test: List stakeholders returns all stakeholders

### 1.4 Implement Stakeholder Persistence (Green)
- [ ] Add stakeholder CRUD operations via SQLModel session
- [ ] Add referential integrity check for deletion
- [ ] Run tests - all should pass

### 1.5 Self Stakeholder Tests (Red)
- [ ] Test: Empty database auto-creates "Self" stakeholder on first access
- [ ] Test: Non-empty database does not create duplicate "Self"

### 1.6 Implement Self Stakeholder Default (Green)
- [ ] Add auto-creation logic for "Self" stakeholder
- [ ] Run tests - all should pass

## Phase 2: Goal Model

### 2.1 Goal Validation Tests (Red)
- [ ] Test: Goal requires non-empty title
- [ ] Test: Goal requires non-empty problem_statement
- [ ] Test: Goal requires non-empty solution_vision
- [ ] Test: Goal rejects empty title (raises validation error)
- [ ] Test: Goal rejects empty problem_statement (raises validation error)
- [ ] Test: Goal rejects empty solution_vision (raises validation error)
- [ ] Test: Goal status defaults to "active"
- [ ] Test: Goal accepts optional motivation, parent_goal_id, next_review_date
- [ ] Test: Goal auto-generates id, created_at, updated_at

### 2.2 Implement Goal Model (Green)
- [ ] Create `GoalStatus` enum (active, on_hold, achieved, abandoned)
- [ ] Create `Goal` SQLModel in `src/jdo/models/goal.py`
- [ ] Run tests - all should pass

### 2.3 Goal Nesting Tests (Red)
- [ ] Test: Goal with valid parent_goal_id creates hierarchy
- [ ] Test: Query child goals by parent_goal_id
- [ ] Test: Prevent circular nesting (goal cannot be its own parent)
- [ ] Test: Prevent circular nesting (goal cannot reference descendant as parent)

### 2.4 Implement Goal Nesting (Green)
- [ ] Add parent_goal_id FK relationship
- [ ] Add circular reference validation
- [ ] Run tests - all should pass

### 2.5 Goal Persistence Tests (Red)
- [ ] Test: Save goal to database and retrieve by id
- [ ] Test: List goals with status filter
- [ ] Test: Delete goal without commitments or children succeeds
- [ ] Test: Delete goal with commitments raises error
- [ ] Test: Delete goal with children raises error

### 2.6 Implement Goal Persistence (Green)
- [ ] Add goal CRUD operations via SQLModel session
- [ ] Add referential integrity checks for deletion
- [ ] Run tests - all should pass

### 2.7 Goal Status Transition Tests (Red)
- [ ] Test: Transition active → achieved updates status and updated_at
- [ ] Test: Transition active → abandoned updates status and updated_at
- [ ] Test: Transition active → on_hold updates status and updated_at
- [ ] Test: Transition on_hold → active updates status and updated_at

### 2.8 Implement Goal Status Transitions (Green)
- [ ] Add status transition logic
- [ ] Run tests - all should pass

## Phase 3: Commitment Model

### 3.1 Commitment Validation Tests (Red)
- [ ] Test: Commitment requires non-empty deliverable
- [ ] Test: Commitment requires stakeholder_id
- [ ] Test: Commitment requires due_date
- [ ] Test: Commitment rejects empty deliverable (raises validation error)
- [ ] Test: Commitment rejects missing stakeholder_id (raises validation error)
- [ ] Test: Commitment rejects missing due_date (raises validation error)
- [ ] Test: Commitment status defaults to "pending"
- [ ] Test: Commitment due_time defaults to 09:00 when not specified
- [ ] Test: Commitment accepts optional goal_id, due_time, timezone, notes
- [ ] Test: Commitment auto-generates id, created_at, updated_at

### 3.2 Implement Commitment Model (Green)
- [ ] Create `CommitmentStatus` enum (pending, in_progress, completed, abandoned)
- [ ] Create `Commitment` SQLModel in `src/jdo/models/commitment.py`
- [ ] Run tests - all should pass

### 3.3 Commitment-Goal Association Tests (Red)
- [ ] Test: Commitment with valid goal_id links to Goal
- [ ] Test: Commitment without goal_id exists independently
- [ ] Test: Query commitments by goal_id

### 3.4 Implement Commitment-Goal Association (Green)
- [ ] Add goal_id FK relationship
- [ ] Run tests - all should pass

### 3.5 Commitment Persistence Tests (Red)
- [ ] Test: Save commitment to database and retrieve by id
- [ ] Test: List commitments with status filter
- [ ] Test: List commitments with due_date filter
- [ ] Test: Delete commitment also deletes associated tasks (cascade)

### 3.6 Implement Commitment Persistence (Green)
- [ ] Add commitment CRUD operations via SQLModel session
- [ ] Add cascade delete for tasks
- [ ] Run tests - all should pass

### 3.7 Commitment Status Transition Tests (Red)
- [ ] Test: Transition pending → in_progress updates status
- [ ] Test: Transition in_progress → completed sets completed_at
- [ ] Test: Transition to abandoned updates status
- [ ] Test: Transition completed → in_progress clears completed_at
- [ ] Test: Completing all tasks does NOT auto-complete commitment
- [ ] Test: Reject "skipped" status for commitments

### 3.8 Implement Commitment Status Transitions (Green)
- [ ] Add status transition logic with completed_at handling
- [ ] Add validation to reject "skipped" status
- [ ] Run tests - all should pass

### 3.9 Commitment Due Date Query Tests (Red)
- [ ] Test: Query overdue commitments (due_date < today, not completed/abandoned)
- [ ] Test: Query commitments due within N days
- [ ] Test: Query commitments due today sorted by due_time

### 3.10 Implement Commitment Due Date Queries (Green)
- [ ] Add due date query methods
- [ ] Run tests - all should pass

## Phase 4: Task Model

### 4.1 Task Validation Tests (Red)
- [ ] Test: Task requires commitment_id
- [ ] Test: Task requires non-empty title
- [ ] Test: Task requires non-empty scope
- [ ] Test: Task requires order
- [ ] Test: Task rejects empty title (raises validation error)
- [ ] Test: Task rejects empty scope (raises validation error)
- [ ] Test: Task rejects missing commitment_id (raises validation error)
- [ ] Test: Task status defaults to "pending"
- [ ] Test: Task sub_tasks defaults to empty list
- [ ] Test: Task auto-generates id, created_at, updated_at

### 4.2 Implement Task Model (Green)
- [ ] Create `TaskStatus` enum (pending, in_progress, completed, skipped)
- [ ] Create `SubTask` Pydantic model (description, completed)
- [ ] Create `Task` SQLModel in `src/jdo/models/task.py`
- [ ] Run tests - all should pass

### 4.3 SubTask Tests (Red)
- [ ] Test: Task with sub_tasks stores them as JSON
- [ ] Test: SubTask requires non-empty description
- [ ] Test: SubTask completed defaults to False
- [ ] Test: Toggle sub_task.completed updates parent Task.updated_at

### 4.4 Implement SubTask (Green)
- [ ] Add JSON column for sub_tasks
- [ ] Add sub_task toggle logic
- [ ] Run tests - all should pass

### 4.5 Task Ordering Tests (Red)
- [ ] Test: Query tasks for commitment returns sorted by order ascending
- [ ] Test: Reorder tasks updates order values correctly
- [ ] Test: New task gets next available order number

### 4.6 Implement Task Ordering (Green)
- [ ] Add order-based query methods
- [ ] Add reorder logic
- [ ] Run tests - all should pass

### 4.7 Task Persistence Tests (Red)
- [ ] Test: Save task with sub_tasks and retrieve together
- [ ] Test: Update sub_task persists in JSON field
- [ ] Test: Delete task removes from database

### 4.8 Implement Task Persistence (Green)
- [ ] Add task CRUD operations via SQLModel session
- [ ] Run tests - all should pass

### 4.9 Task Status Transition Tests (Red)
- [ ] Test: Transition pending → in_progress updates status
- [ ] Test: Transition in_progress → completed updates status
- [ ] Test: Transition to "skipped" marks task as not needed
- [ ] Test: Skipped tasks do not block commitment completion
- [ ] Test: Task in_progress auto-transitions pending Commitment to in_progress
- [ ] Test: Task in_progress does NOT change non-pending Commitment

### 4.10 Implement Task Status Transitions (Green)
- [ ] Add status transition logic
- [ ] Add commitment auto-transition on task start
- [ ] Run tests - all should pass

## Phase 5: Cross-Model Integration

### 5.1 Integration Tests (Red)
- [ ] Test: Full hierarchy: Stakeholder → Goal → Commitment → Task
- [ ] Test: Cascade delete: Commitment deletion removes Tasks
- [ ] Test: Referential integrity: Cannot delete Stakeholder with Commitments
- [ ] Test: Referential integrity: Cannot delete Goal with Commitments
- [ ] Test: Referential integrity: Cannot delete Goal with child Goals

### 5.2 Implement Integration (Green)
- [ ] Wire up all FK relationships
- [ ] Add cascade and integrity rules
- [ ] Run tests - all should pass

### 5.3 Refactor
- [ ] Extract shared timestamp handling to `src/jdo/models/utils.py`
- [ ] Add timezone utility for EST default
- [ ] Export all models from `src/jdo/models/__init__.py`
- [ ] Run all tests - verify still passing

## Phase 6: TUI Integration (Pilot Tests)

### 6.1 Stakeholder Screen Tests (Red)
- [ ] Test: StakeholderListScreen displays stakeholders
- [ ] Test: Stakeholder creation form validates input
- [ ] Test: "Self" stakeholder appears on first run

### 6.2 Implement Stakeholder Screens (Green)
- [ ] Create StakeholderListScreen
- [ ] Create stakeholder form
- [ ] Run tests - all should pass

### 6.3 Goal Screen Tests (Red)
- [ ] Test: GoalListScreen displays hierarchical goals
- [ ] Test: GoalDetailScreen shows goal info and commitments
- [ ] Test: Goal creation flow collects required fields

### 6.4 Implement Goal Screens (Green)
- [ ] Create GoalListScreen with hierarchy display
- [ ] Create GoalDetailScreen
- [ ] Create goal creation flow
- [ ] Run tests - all should pass

### 6.5 Commitment Screen Tests (Red)
- [ ] Test: CommitmentListScreen sorts by due date
- [ ] Test: CommitmentDetailScreen shows tasks
- [ ] Test: Commitment creation validates deliverable, stakeholder, due_date
- [ ] Test: Commitment status transitions work via UI

### 6.6 Implement Commitment Screens (Green)
- [ ] Create CommitmentListScreen with sorting
- [ ] Create CommitmentDetailScreen with task list
- [ ] Create commitment creation flow
- [ ] Run tests - all should pass

### 6.7 Task View Tests (Red)
- [ ] Test: Tasks display within CommitmentDetailScreen
- [ ] Test: Task creation validates title and scope
- [ ] Test: Sub-task toggle updates display
- [ ] Test: Task reordering works

### 6.8 Implement Task Views (Green)
- [ ] Add task list to CommitmentDetailScreen
- [ ] Create task creation flow
- [ ] Add sub-task toggle
- [ ] Add reordering
- [ ] Run tests - all should pass

## Phase 7: Visual Regression

### 7.1 Snapshot Tests
- [ ] Create snapshot: HomeScreen with commitments
- [ ] Create snapshot: StakeholderListScreen
- [ ] Create snapshot: GoalListScreen with hierarchy
- [ ] Create snapshot: CommitmentDetailScreen with tasks
- [ ] Run `pytest --snapshot-update` to generate baselines

## Dependencies

- Phase 1-4 can be parallelized per model (each has independent test/implement cycles)
- Phase 5 requires all models from Phases 1-4
- Phase 6 requires Phase 5 (persistence layer)
- Phase 7 requires Phase 6 (screens exist)

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/jdo --cov-report=term-missing

# Run specific phase
uv run pytest tests/unit/models/test_stakeholder.py -v

# Update snapshots after intentional UI changes
uv run pytest --snapshot-update
```
