# Tasks: Honor-Your-Word Protocol and Integrity Metrics

This task list tracks implementation status for the integrity protocol.

**Dependencies**: 
- Requires core domain models (Commitment, Task, Stakeholder) - ✓ Complete
- Requires `implement-jdo-app` (TUI app shell and command infrastructure) - ✓ Complete
- Requires `wire_ai_to_chat` - ✓ Complete
- Requires `persist_handler_results` - ✓ Complete

## Phase 0: Prerequisites Check
- [x] 0.1 Verify /commit command persists Commitment to database
- [x] 0.2 Verify /goal command persists Goal to database
- [x] 0.3 Test: Created entities appear in /show output

## Phase 1: Commitment Model Extensions

### 1.1-1.2 At-Risk Status
- [x] CommitmentStatus enum includes `at_risk` value
- [x] Add `marked_at_risk_at` field to Commitment
- [x] Implement status transition logic

### 1.3-1.4 Completed On-Time
- [x] Add `completed_on_time` field to Commitment
- [x] Calculate on completion status change

## Phase 2: Task Model Extensions

### 2.1-2.2 Notification Task
- [x] Task has `is_notification_task` field defaulting to False
- [x] Notification task created at order=0

## Phase 3: CleanupPlan Model

### 3.1-3.4 CleanupPlan Entity
- [x] Create `CleanupPlanStatus` enum (planned, in_progress, completed, skipped, cancelled)
- [x] Create `CleanupPlan` SQLModel with all required fields
- [x] Save CleanupPlan and retrieve by id/commitment_id
- [x] CleanupPlan links to notification_task via FK

### 3.5-3.6 CleanupPlan Status Transitions
- [x] Transition planned → in_progress on notification task completion
- [x] Transition to completed on commitment completion
- [x] Transition to skipped on abandon without notification
- [x] Transition to cancelled on recovery (at_risk → in_progress)

## Phase 4: At-Risk Workflow

### 4.1-4.2 Auto-Creation
- [x] Marking commitment at_risk creates CleanupPlan
- [x] Creates notification Task at order=0 with is_notification_task=True
- [x] Notification task scope contains stakeholder info
- [x] CleanupPlan links to notification task

### 4.3-4.4 Soft Enforcement (Deferred)
- [ ] Abandon without notification shows warning
- [ ] User can override warning with acknowledgment
- [ ] Override sets CleanupPlan status to "skipped"

**Note**: Soft enforcement deferred to future iteration. Current implementation allows direct abandonment.

## Phase 5: Integrity Metrics

### 5.1-5.2 On-Time Rate
- [x] on_time_rate = completed_on_time / total_completed
- [x] Returns 1.0 when no completions (clean slate)

### 5.3-5.4 Notification Timeliness (Simplified)
- [x] Returns 1.0 (clean slate default)
- [ ] Actual calculation from marked_at_risk_at vs due_date (deferred)

**Note**: Full timeliness calculation deferred. Returns 1.0 for now.

### 5.5-5.6 Cleanup Completion Rate
- [x] cleanup_rate = completed / total cleanup plans
- [x] Returns 1.0 when no cleanup plans exist

### 5.7-5.8 Reliability Streak (Simplified)
- [x] Returns 0 (no streak tracking yet)
- [ ] Count consecutive weeks with all on-time (deferred)

**Note**: Full streak calculation deferred. Returns 0 for now.

### 5.9-5.12 Composite Score and Letter Grade
- [x] composite_score with weights: on_time=0.4, timeliness=0.25, cleanup=0.25, streak=0.1
- [x] streak_bonus = min(weeks * 2, 10) / 100
- [x] Score range is 0-100
- [x] Letter grade conversion (A+ through F)
- [x] Empty history shows A- (90 score due to 0 streak)

## Phase 6: TUI Commands

### 6.1-6.2 /atrisk Command
- [x] /atrisk recognized as command
- [x] /atrisk handler creates CleanupPlan and notification task
- [x] Returns result with panel_update for ATRISK_WORKFLOW mode

### 6.3-6.4 /cleanup Command
- [x] /cleanup shows CleanupPlan in data panel
- [x] /cleanup handler retrieves CleanupPlan for commitment

### 6.5-6.6 /integrity Command
- [x] /integrity shows dashboard in data panel
- [x] Dashboard shows letter grade prominently
- [x] Dashboard shows all four metrics
- [x] Dashboard shows totals (completed, on_time, at_risk, abandoned)

## Phase 7: Home Screen Integration

### 7.1-7.2 Integrity Display
- [x] Home screen shows integrity grade in header
- [x] Grade is color-coded (A=green, B=blue, C=yellow, D/F=red)
- [x] 'i' key opens integrity dashboard (posts ShowIntegrity message)

### 7.3-7.4 AI Risk Detection
- [x] Launch detects overdue commitments
- [x] Launch detects due-within-24h pending commitments
- [x] Launch detects stalled in_progress (48h due, no activity 24h)
- [x] Detection shows summary message in chat
- [x] User dismissal prevents repeat in session

## Phase 8: Visual Indicators

### 8.1-8.2 At-Risk Styling
- [x] DataPanel has INTEGRITY, CLEANUP, ATRISK_WORKFLOW modes
- [x] Rendering methods for each new mode
- [ ] At-risk commitment shows warning color in lists (deferred)
- [ ] Notification task shows distinct icon (deferred)

## Phase 9: Integration Tests
- [x] Integration tests for integrity dashboard flows
- [x] Integration tests for cleanup plan flows
- [x] Integration tests for at-risk workflow flows
- [x] Integration tests for ChatScreen integrity features
- [x] Integration tests for HomeScreen integrity features

## Phase 10: Snapshot Tests (Deferred)
- [ ] Snapshot: Integrity dashboard
- [ ] Snapshot: Commitment list with at_risk items
- [ ] Snapshot: CleanupPlan view

## Summary

**Implemented**:
- Core models (CommitmentStatus.AT_RISK, CleanupPlan, IntegrityMetrics)
- IntegrityService (mark_at_risk, calculate_metrics, detect_risks)
- Commands (/atrisk, /cleanup, /integrity)
- TUI integration (HomeScreen grade, ChatScreen risk detection, DataPanel modes)
- Full test coverage

**Deferred to Future Iterations**:
- Notification timeliness calculation (returns 1.0)
- Reliability streak calculation (returns 0)
- Soft enforcement warnings on abandon
- Visual indicators (warning colors, icons)
- Snapshot tests
- Metric trends (improving/stable/declining)

## Running Tests

```bash
# Run all tests
uv run pytest

# Run integrity-specific tests
uv run pytest tests/unit/models/test_cleanup_plan.py tests/unit/models/test_integrity_metrics.py tests/unit/integrity/ -v

# Run TUI integrity tests
uv run pytest tests/tui/test_chat_screen.py tests/tui/test_home_screen.py tests/tui/test_data_panel.py -v -k integrity

# Run integration tests
uv run pytest tests/integration/tui/test_flows.py -v
```
