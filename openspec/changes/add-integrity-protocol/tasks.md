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

### 4.3-4.4 Soft Enforcement
- [x] Abandon without notification shows warning
- [x] User can override warning with acknowledgment
- [x] Override sets CleanupPlan status to "skipped"
- [x] /abandon command handler implemented
- [x] Tests for soft enforcement added

## Phase 5: Integrity Metrics

### 5.1-5.2 On-Time Rate
- [x] on_time_rate = completed_on_time / total_completed
- [x] Returns 1.0 when no completions (clean slate)

### 5.3-5.4 Notification Timeliness
- [x] Returns 1.0 (clean slate default)
- [x] Actual calculation from marked_at_risk_at vs due_date implemented
- [x] 7+ days before = 1.0, 0 days = 0.0, linear interpolation
- [x] Tests added for timeliness calculation

### 5.5-5.6 Cleanup Completion Rate
- [x] cleanup_rate = completed / total cleanup plans
- [x] Returns 1.0 when no cleanup plans exist

### 5.7-5.8 Reliability Streak
- [x] Returns 0 (no streak tracking yet)
- [x] Count consecutive weeks with all on-time implemented
- [x] Streak breaks on late completion or abandonment
- [x] Tests added for streak calculation

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

---

## Deferred Work

The following items are deferred to future iterations. Each is tracked here with rationale and suggested implementation approach.

### D1: Notification Timeliness Calculation ✅ COMPLETED
**Status**: Implemented in `IntegrityService._calculate_notification_timeliness()`

**Implementation**:
- [x] Query commitments where marked_at_risk_at is not null
- [x] Calculate days_before_due = (due_date - marked_at_risk_at.date()).days
- [x] Normalize: 7+ days = 1.0, 0 days = 0.0, linear interpolation between
- [x] Handle edge cases: marked after due_date = 0.0
- [x] Update `IntegrityService.calculate_integrity_metrics()`
- [x] Added 6 unit tests in `tests/unit/integrity/test_service.py`

### D2: Reliability Streak Calculation ✅ COMPLETED
**Status**: Implemented in `IntegrityService._calculate_streak_weeks()`

**Implementation**:
- [x] Group completed commitments by ISO week
- [x] For each week (newest first), check if all were on_time
- [x] Count consecutive on-time weeks until a miss
- [x] Reset to 0 on: late completion, abandonment, skipped cleanup
- [x] Update `IntegrityService.calculate_integrity_metrics()`
- [x] Added 5 unit tests in `tests/unit/integrity/test_service.py`

### D3: Soft Enforcement on Abandon ✅ COMPLETED
**Status**: Implemented in `AbandonHandler`

**Implementation**:
- [x] Created `AbandonHandler` class in `src/jdo/commands/handlers.py`
- [x] In /abandon handler, check if commitment.status == at_risk
- [x] If at_risk, query CleanupPlan and notification task status
- [x] If notification incomplete, return HandlerResult with warning message
- [x] Add confirmation flow with options (yes/notify/cancel)
- [x] On confirm, sets CleanupPlan.status = skipped with skipped_reason
- [x] Registered handler in _HANDLERS dict
- [x] Added ABANDON command type to parser
- [x] Added 12 unit tests in `tests/unit/commands/test_handlers.py`
- [x] Updated /help to include /abandon command

### D4: Pre-Abandon At-Risk Prompt ✅ COMPLETED
**Status**: Implemented in `AbandonHandler._prompt_atrisk_first()`

**Implementation**:
- [x] In /abandon handler, check if commitment has stakeholder
- [x] If stakeholder exists and status not at_risk, show prompt
- [x] Offer options: "Mark at-risk first" or "Abandon directly"
- [x] If mark at-risk, user can type 'atrisk' to redirect to /atrisk flow
- [x] Tests added to verify prompt behavior

### D5: Visual Indicators for At-Risk Status
**Current**: No visual distinction in lists
**Target**: Warning color for at-risk commitments, distinct icon for notification tasks

**Implementation**:
- [ ] Add CSS class `.commitment-at-risk` with warning color (yellow/orange)
- [ ] Update commitment list rendering to apply class based on status
- [ ] Add notification task icon (e.g., 📢 or ⚠️) in task list
- [ ] Sort commitment lists: overdue > at_risk > pending > in_progress

**Effort**: Small (1-2 hours)
**Priority**: Low - Polish/UX improvement

### D6: Metric Trends
**Current**: Not implemented
**Target**: Show improving/stable/declining indicators for each metric

**Implementation**:
- [ ] Store previous period metrics (could use session cache or simple comparison)
- [ ] Calculate delta for each metric vs previous period
- [ ] Add trend indicator to IntegrityMetrics dataclass
- [ ] Display ↑/→/↓ in integrity dashboard

**Effort**: Medium (2-3 hours)
**Priority**: Low - Nice-to-have analytics

### D7: Commitments Affecting Score
**Current**: Not implemented
**Target**: List recent commitments that negatively impacted score

**Implementation**:
- [ ] Query commitments where: completed_on_time=False OR status=abandoned
- [ ] Filter to recent (last 30 days)
- [ ] Include in integrity dashboard response
- [ ] Render as list in DataPanel integrity mode

**Effort**: Small (1-2 hours)
**Priority**: Low - Helps user understand score

### D8: Recovery Flow (at_risk → in_progress)
**Current**: No handling when commitment recovers from at_risk
**Target**: Cancel CleanupPlan and prompt about notification task when recovering

**Implementation**:
- [ ] Add /recover command or status change handler
- [ ] When commitment status changes at_risk → in_progress:
  - Set CleanupPlan.status = CANCELLED
  - Prompt user: "Do you still need to notify [stakeholder], or has the situation resolved?"
  - If resolved: Mark notification task as skipped with reason "Situation resolved"
  - If still need to notify: Keep task active
- [ ] Update IntegrityService with recover_commitment() method
- [ ] Add tests for recovery flow

**Effort**: Medium (2-3 hours)
**Priority**: Medium - Completes the at-risk lifecycle

### D9: Snapshot Tests
**Current**: No snapshot tests for integrity views
**Target**: Visual regression tests for integrity UI

**Implementation**:
- [ ] Create snapshot app for integrity dashboard (A+ grade scenario)
- [ ] Create snapshot app for integrity dashboard (C- grade scenario)
- [ ] Create snapshot for commitment list with at_risk items
- [ ] Create snapshot for CleanupPlan view
- [ ] Run `uv run pytest --snapshot-update` to generate baselines

**Effort**: Small (1-2 hours)
**Priority**: Low - Testing infrastructure

---

### Deferred Work Priority Order

**Completed**:
1. ✅ **D1: Notification Timeliness** - Implemented
2. ✅ **D2: Reliability Streak** - Implemented
3. ✅ **D3: Soft Enforcement** - Implemented
4. ✅ **D4: Pre-Abandon Prompt** - Implemented

**Remaining**:
1. **D8: Recovery Flow** - Medium, completes at-risk lifecycle
2. **D5: Visual Indicators** - Low, polish
3. **D6: Metric Trends** - Low, analytics
4. **D7: Affecting Commitments** - Low, debugging aid
5. **D9: Snapshot Tests** - Low, infrastructure
