# Tasks: Vision and Milestone Hierarchy (TDD)

This task list follows Test-Driven Development: write failing tests first, then implement to pass.

**Dependencies**: Extends `add-core-domain-models` (archived) with Vision and Milestone entities.

**Status**: ✅ COMPLETE - All model layer tasks done. TUI tasks migrated to `add-conversational-tui`.

## Phase 1: Vision Model ✅ COMPLETE

### 1.1 Vision Validation Tests (Red) ✅
- [x] Test: Vision requires non-empty title
- [x] Test: Vision requires non-empty narrative
- [x] Test: Vision rejects empty title (raises validation error)
- [x] Test: Vision rejects empty narrative (raises validation error)
- [x] Test: VisionStatus enum has active, achieved, evolved, abandoned
- [x] Test: Vision status defaults to "active"
- [x] Test: Vision metrics stored as JSON list
- [x] Test: Vision next_review_date defaults to 90 days from creation
- [x] Test: Vision auto-generates id, created_at, updated_at

### 1.2 Implement Vision Model (Green) ✅
- [x] Create `VisionStatus` enum
- [x] Create `Vision` SQLModel in `src/jdo/models/vision.py`
- [x] Run tests - all should pass

### 1.3 Vision Persistence Tests (Red) ✅
- [x] Test: Save vision and retrieve by id
- [x] Test: List visions with status filter
- [x] Test: Query visions due for review

### 1.4 Implement Vision Persistence (Green) ✅
- [x] Add vision CRUD operations (via SQLModel session)
- [x] Run tests - all should pass

### 1.5 Vision Review Tests (Red) ✅
- [x] Test: Vision due for review when next_review_date <= today
- [x] Test: Complete review sets last_reviewed_at to now
- [x] Test: Complete review sets next_review_date to now + 90 days

### 1.6 Implement Vision Review (Green) ✅
- [x] Implement `is_due_for_review()` method
- [x] Implement `complete_review()` method
- [x] Run tests - all should pass

## Phase 2: Milestone Model ✅ COMPLETE

### 2.1 Milestone Validation Tests (Red) ✅
- [x] Test: Milestone requires goal_id
- [x] Test: Milestone requires non-empty title
- [x] Test: Milestone requires target_date
- [x] Test: Milestone rejects missing goal_id (raises validation error)
- [x] Test: Milestone rejects empty title (raises validation error)
- [x] Test: Milestone rejects missing target_date (raises validation error)
- [x] Test: MilestoneStatus enum has pending, in_progress, completed, missed
- [x] Test: Milestone status defaults to "pending"
- [x] Test: Milestone auto-generates id, created_at, updated_at

### 2.2 Implement Milestone Model (Green) ✅
- [x] Create `MilestoneStatus` enum
- [x] Create `Milestone` SQLModel in `src/jdo/models/milestone.py`
- [x] Run tests - all should pass

### 2.3 Milestone Persistence Tests (Red) ✅
- [x] Test: Save milestone and retrieve by id
- [x] Test: List milestones by goal_id sorted by target_date
- [x] Test: Query milestones at risk (target_date within 7 days, status=pending)

### 2.4 Implement Milestone Persistence (Green) ✅
- [x] Add milestone CRUD operations (via SQLModel session)
- [x] Run tests - all should pass

### 2.5 Milestone Status Tests (Red) ✅
- [x] Test: Transition pending → in_progress (`start()` method)
- [x] Test: Transition in_progress → completed sets completed_at (`complete()` method)
- [x] Test: Overdue milestone detection (`is_overdue()` method)
- [x] Test: Mark milestone as missed (`mark_missed()` method)
- [x] Test: Missed milestone can still be completed (late completion)

### 2.6 Implement Milestone Status (Green) ✅
- [x] Implement `start()`, `complete()`, `mark_missed()` methods
- [x] Implement `is_overdue()` method
- [x] Run tests - all should pass

## Phase 3: Goal Model Extension ✅ COMPLETE

### 3.1 Goal-Vision Link Tests (Red) ✅
- [x] Test: Goal accepts optional vision_id
- [x] Test: Goal with valid vision_id links to Vision
- [x] Test: Query goals by vision_id

### 3.2 Implement Goal-Vision Link (Green) ✅
- [x] Add vision_id field to Goal
- [x] Add FK relationship
- [x] Run tests - all should pass

## Phase 4: Commitment Model Extension ✅ COMPLETE

### 4.1 Commitment-Milestone Link Tests (Red) ✅
- [x] Test: Commitment accepts optional milestone_id
- [x] Test: Commitment with valid milestone_id links to Milestone
- [x] Test: Orphan = no goal_id AND no milestone_id (`is_orphan()` method)
- [x] Test: Commitment with milestone_id but no goal_id is NOT orphan
- [x] Test: Query orphan commitments

### 4.2 Implement Commitment-Milestone Link (Green) ✅
- [x] Add milestone_id field to Commitment
- [x] Add FK relationship
- [x] Implement `is_orphan()` method
- [x] Run tests - all should pass

## Phase 5: Hierarchy Queries ✅ COMPLETE

### 5.1 Query Tests (Red) ✅
- [x] Test: Query orphan commitments (no goal AND no milestone)
- [x] Test: Query visions due for review
- [x] Test: Query milestones at risk (target_date within 7 days, status=pending)

### 5.2 Implement Queries (Green) ✅
- [x] Queries implemented via SQLModel select statements
- [x] Run tests - all should pass

---

## Summary

### Completed
| Phase | Description | Tests |
|-------|-------------|-------|
| 1 | Vision Model | 20 tests |
| 2 | Milestone Model | 22 tests |
| 3 | Goal-Vision Link | 4 tests |
| 4 | Commitment-Milestone Link | 7 tests |
| 5 | Hierarchy Queries | 4 tests |

**Total: 57 new tests, all passing**

### Files Created
- `src/jdo/models/vision.py` - Vision entity with VisionStatus enum
- `src/jdo/models/milestone.py` - Milestone entity with MilestoneStatus enum
- `tests/unit/models/test_vision.py` - 20 tests
- `tests/unit/models/test_milestone.py` - 22 tests

### Files Modified
- `src/jdo/models/goal.py` - Added `vision_id` FK
- `src/jdo/models/commitment.py` - Added `milestone_id` FK, `is_orphan()` method
- `src/jdo/models/__init__.py` - Exports Vision, VisionStatus, Milestone, MilestoneStatus
- `tests/unit/models/test_goal.py` - Added 4 Goal-Vision link tests
- `tests/unit/models/test_commitment.py` - Added 7 Commitment-Milestone/orphan tests

### Migrated to add-conversational-tui
The following TUI-related tasks were migrated to `add-conversational-tui`:
- Phase 6: /vision and /milestone TUI Commands
- Phase 7: Keyboard Navigation (v, m, h keys)
- Phase 8: Hierarchy View widget
- Phase 9: AI Integration (vision/milestone prompts)
- Phase 10: Review System (startup prompts, auto-missed)
- Phase 11: Visual Regression (snapshots)
- Phase 12: Integration Tests (end-to-end flows)

## Running Tests

```bash
# Run vision/milestone tests
uv run pytest tests/unit/models/test_vision.py -v
uv run pytest tests/unit/models/test_milestone.py -v

# Run all model tests
uv run pytest tests/unit/models/ -v

# Run with coverage
uv run pytest --cov=src/jdo --cov-report=term-missing
```
