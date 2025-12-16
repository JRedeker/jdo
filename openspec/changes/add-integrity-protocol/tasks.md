# Tasks: Honor-Your-Word Protocol and Integrity Metrics (TDD)

This task list follows Test-Driven Development: write failing tests first, then implement to pass.

**Dependencies**: 
- Requires core domain models (Commitment, Task, Stakeholder) - already implemented
- Requires `implement-jdo-app` (TUI app shell and command infrastructure)

## Phase 1: Commitment Model Extensions

### 1.1 At-Risk Status Tests (Red)
- [ ] Test: CommitmentStatus enum includes `at_risk` value
- [ ] Test: Commitment can transition pending → at_risk
- [ ] Test: Commitment can transition in_progress → at_risk
- [ ] Test: Commitment can transition at_risk → in_progress (recovery)
- [ ] Test: Commitment can transition at_risk → completed
- [ ] Test: Commitment can transition at_risk → abandoned
- [ ] Test: `marked_at_risk_at` timestamp set on at_risk transition
- [ ] Test: `marked_at_risk_at` preserved on recovery to in_progress

### 1.2 Implement At-Risk Status (Green)
- [ ] Add `at_risk` to CommitmentStatus enum
- [ ] Add `marked_at_risk_at` field to Commitment
- [ ] Implement status transition logic
- [ ] Run tests - all should pass

### 1.3 Completed On-Time Tests (Red)
- [ ] Test: `completed_on_time` is True when completed before due_date
- [ ] Test: `completed_on_time` is False when completed after due_date
- [ ] Test: `completed_on_time` considers due_time when set
- [ ] Test: `completed_on_time` is None for non-completed commitments

### 1.4 Implement Completed On-Time (Green)
- [ ] Add `completed_on_time` field to Commitment
- [ ] Calculate on completion status change
- [ ] Run tests - all should pass

## Phase 2: Task Model Extensions

### 2.1 Notification Task Tests (Red)
- [ ] Test: Task has `is_notification_task` field defaulting to False
- [ ] Test: Notification task (is_notification_task=True) has order=0
- [ ] Test: Notification task order cannot be changed from 0
- [ ] Test: Notification task skip triggers warning (returns warning flag)

### 2.2 Implement Notification Task (Green)
- [ ] Add `is_notification_task` field to Task
- [ ] Add order validation for notification tasks
- [ ] Run tests - all should pass

## Phase 3: CleanupPlan Model

### 3.1 CleanupPlan Validation Tests (Red)
- [ ] Test: CleanupPlan requires commitment_id
- [ ] Test: CleanupPlan rejects missing commitment_id
- [ ] Test: CleanupPlanStatus enum has planned, in_progress, completed, skipped
- [ ] Test: CleanupPlan status defaults to "planned"
- [ ] Test: CleanupPlan accepts optional impact_description
- [ ] Test: CleanupPlan stores mitigation_actions as JSON list
- [ ] Test: CleanupPlan auto-generates id, created_at, updated_at

### 3.2 Implement CleanupPlan Model (Green)
- [ ] Create `CleanupPlanStatus` enum
- [ ] Create `CleanupPlan` SQLModel
- [ ] Run tests - all should pass

### 3.3 CleanupPlan Persistence Tests (Red)
- [ ] Test: Save CleanupPlan and retrieve by id
- [ ] Test: Save CleanupPlan and retrieve by commitment_id
- [ ] Test: One CleanupPlan per commitment (reuse existing)
- [ ] Test: CleanupPlan links to notification_task via FK

### 3.4 Implement CleanupPlan Persistence (Green)
- [ ] Add FK relationships
- [ ] Add CRUD operations
- [ ] Run tests - all should pass

### 3.5 CleanupPlan Status Transition Tests (Red)
- [ ] Test: Transition planned → in_progress on notification task completion
- [ ] Test: Transition in_progress → completed on commitment completion
- [ ] Test: Transition to skipped on abandon without notification
- [ ] Test: Skipped requires skipped_reason

### 3.6 Implement CleanupPlan Status Transitions (Green)
- [ ] Implement status transition logic
- [ ] Run tests - all should pass

## Phase 4: At-Risk Workflow

### 4.1 Auto-Creation Tests (Red)
- [ ] Test: Marking commitment at_risk creates CleanupPlan
- [ ] Test: Marking at_risk creates notification Task at order=0
- [ ] Test: Notification task is_notification_task=True
- [ ] Test: Notification task scope contains stakeholder info
- [ ] Test: CleanupPlan links to notification task

### 4.2 Implement Auto-Creation (Green)
- [ ] Create CleanupPlan on at_risk transition
- [ ] Create notification task with draft content
- [ ] Link CleanupPlan to task
- [ ] Run tests - all should pass

### 4.3 Soft Enforcement Tests (Red)
- [ ] Test: Abandon without notification shows warning
- [ ] Test: User can override warning with acknowledgment
- [ ] Test: Override sets CleanupPlan status to "skipped"
- [ ] Test: Skipped cleanup records skipped_reason

### 4.4 Implement Soft Enforcement (Green)
- [ ] Add abandonment check for notification completion
- [ ] Add override flow
- [ ] Run tests - all should pass

## Phase 5: Integrity Metrics

### 5.1 On-Time Rate Tests (Red)
- [ ] Test: on_time_rate = completed_on_time / total_completed
- [ ] Test: on_time_rate = 1.0 when no completions (clean slate)
- [ ] Test: on_time_rate handles zero division

### 5.2 Implement On-Time Rate (Green)
- [ ] Create IntegrityMetrics dataclass
- [ ] Implement on_time_rate calculation
- [ ] Run tests - all should pass

### 5.3 Notification Timeliness Tests (Red)
- [ ] Test: timeliness measures days before due_date when marked at_risk
- [ ] Test: 7+ days early = 1.0 timeliness
- [ ] Test: 0 days (due date) = 0.0 timeliness
- [ ] Test: No at_risk history = 1.0 (clean slate)

### 5.4 Implement Notification Timeliness (Green)
- [ ] Implement notification_timeliness calculation
- [ ] Implement normalization (0-7 days → 0.0-1.0)
- [ ] Run tests - all should pass

### 5.5 Cleanup Completion Rate Tests (Red)
- [ ] Test: cleanup_rate = completed / total cleanup plans
- [ ] Test: cleanup_rate = 1.0 when no cleanup plans exist
- [ ] Test: Skipped counts against completion rate

### 5.6 Implement Cleanup Completion Rate (Green)
- [ ] Implement cleanup_completion_rate calculation
- [ ] Run tests - all should pass

### 5.7 Reliability Streak Tests (Red)
- [ ] Test: Streak counts consecutive weeks with all on-time
- [ ] Test: Late commitment resets streak to 0
- [ ] Test: Abandoned commitment resets streak to 0
- [ ] Test: Skipped cleanup resets streak to 0

### 5.8 Implement Reliability Streak (Green)
- [ ] Implement current_streak_weeks calculation
- [ ] Run tests - all should pass

### 5.9 Composite Score Tests (Red)
- [ ] Test: composite_score weights: on_time=0.4, timeliness=0.25, cleanup=0.25, streak=0.1
- [ ] Test: streak_bonus = min(weeks * 2, 10) / 100
- [ ] Test: Score range is 0-100

### 5.10 Implement Composite Score (Green)
- [ ] Implement composite_score property
- [ ] Run tests - all should pass

### 5.11 Letter Grade Tests (Red)
- [ ] Test: 97-100 = A+
- [ ] Test: 93-96 = A
- [ ] Test: 90-92 = A-
- [ ] Test: 87-89 = B+
- [ ] Test: 83-86 = B
- [ ] Test: 80-82 = B-
- [ ] Test: 77-79 = C+
- [ ] Test: 73-76 = C
- [ ] Test: 70-72 = C-
- [ ] Test: 67-69 = D+
- [ ] Test: 63-66 = D
- [ ] Test: 60-62 = D-
- [ ] Test: <60 = F
- [ ] Test: New user with no history = A+

### 5.12 Implement Letter Grade (Green)
- [ ] Implement letter_grade property
- [ ] Run tests - all should pass

## Phase 6: TUI Commands

### 6.1 /atrisk Command Tests (Red)
- [ ] Test: /atrisk recognized as command
- [ ] Test: /atrisk without commitment context prompts selection
- [ ] Test: /atrisk on already at_risk commitment shows error
- [ ] Test: /atrisk prompts for reason
- [ ] Test: /atrisk creates notification task with draft
- [ ] Test: /atrisk shows confirmation message

### 6.2 Implement /atrisk Command (Green)
- [ ] Create atrisk command handler
- [ ] Wire up AI prompts for reason and impact
- [ ] Wire up CleanupPlan and notification task creation
- [ ] Run tests - all should pass

### 6.3 /cleanup Command Tests (Red)
- [ ] Test: /cleanup shows CleanupPlan in data panel
- [ ] Test: /cleanup without CleanupPlan shows error message
- [ ] Test: /cleanup updates mitigation_actions from conversation

### 6.4 Implement /cleanup Command (Green)
- [ ] Create cleanup command handler
- [ ] Create CleanupPlan data panel view
- [ ] Run tests - all should pass

### 6.5 /integrity Command Tests (Red)
- [ ] Test: /integrity shows dashboard in data panel
- [ ] Test: Dashboard shows letter grade prominently
- [ ] Test: Dashboard shows all four metrics
- [ ] Test: Dashboard shows current streak
- [ ] Test: Empty history shows A+ with guidance message

### 6.6 Implement /integrity Command (Green)
- [ ] Create integrity command handler
- [ ] Create integrity dashboard widget
- [ ] Run tests - all should pass

## Phase 7: Home Screen Integration

### 7.1 Integrity Display Tests (Red)
- [ ] Test: Home screen shows integrity grade in header
- [ ] Test: Grade is color-coded (A=green, B=blue, C=yellow, D/F=red)
- [ ] Test: 'i' key opens integrity dashboard

### 7.2 Implement Integrity Display (Green)
- [ ] Add grade to home screen header
- [ ] Add 'i' keyboard binding
- [ ] Add color styling
- [ ] Run tests - all should pass

### 7.3 AI Risk Detection Tests (Red)
- [ ] Test: Launch detects overdue commitments
- [ ] Test: Launch detects due-within-24h pending commitments
- [ ] Test: Launch detects stalled in_progress (48h due, no activity 24h)
- [ ] Test: Detection shows summary message
- [ ] Test: User dismissal prevents repeat in session
- [ ] Test: User acceptance starts at_risk workflow

### 7.4 Implement AI Risk Detection (Green)
- [ ] Add startup check in on_mount
- [ ] Generate risk summary messages
- [ ] Wire up acceptance to /atrisk flow
- [ ] Run tests - all should pass

## Phase 8: Visual Indicators

### 8.1 At-Risk Styling Tests (Red)
- [ ] Test: At-risk commitment shows warning color
- [ ] Test: Commitment list sorts: overdue > at_risk > pending
- [ ] Test: Notification task shows distinct icon

### 8.2 Implement At-Risk Styling (Green)
- [ ] Add CSS classes for at_risk status
- [ ] Update list sorting logic
- [ ] Add notification task styling
- [ ] Run tests - all should pass

## Phase 9: Visual Regression

### 9.1 Snapshot Tests
- [ ] Create snapshot: Integrity dashboard with A+ grade
- [ ] Create snapshot: Integrity dashboard with C- grade
- [ ] Create snapshot: Commitment list with at_risk items
- [ ] Create snapshot: CleanupPlan view
- [ ] Run `pytest --snapshot-update` to generate baselines

## Phase 10: Integration Tests

### 10.1 End-to-End Tests
- [ ] Test: Full at-risk flow (mark → notify → complete)
- [ ] Test: Full at-risk flow (mark → notify → abandon with cleanup)
- [ ] Test: Abandon without cleanup (soft enforcement override)
- [ ] Test: Metrics update after commitment completion
- [ ] Test: Streak reset on late completion

## Dependencies

- Phase 1-3 can run in parallel (model extensions)
- Phase 4 depends on Phases 1-3 (needs all models)
- Phase 5 depends on Phase 1 (needs completed_on_time)
- Phase 6-7 depend on Phases 4-5 (needs workflow and metrics)
- Phase 8 depends on Phase 6 (needs commands working)
- Phase 9-10 require all previous phases

## Running Tests

```bash
# Run all tests
uv run pytest

# Run integrity-specific tests
uv run pytest tests/unit/models/test_cleanup_plan.py -v
uv run pytest tests/unit/test_integrity_metrics.py -v

# Run with coverage
uv run pytest --cov=src/jdo --cov-report=term-missing

# Update snapshots
uv run pytest --snapshot-update
```
