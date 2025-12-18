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

### D1: Notification Timeliness Calculation
**Current**: Returns 1.0 (clean slate default)
**Target**: Calculate average (due_date - marked_at_risk_at) normalized to 0.0-1.0 scale

**Implementation**:
- [ ] Query commitments where marked_at_risk_at is not null
- [ ] Calculate days_before_due = (due_date - marked_at_risk_at.date()).days
- [ ] Normalize: 7+ days = 1.0, 0 days = 0.0, linear interpolation between
- [ ] Handle edge cases: marked after due_date = 0.0
- [ ] Update `IntegrityService.calculate_integrity_metrics()`

**Effort**: Small (1-2 hours)
**Priority**: Medium - Improves accuracy of integrity score

### D2: Reliability Streak Calculation
**Current**: Returns 0
**Target**: Count consecutive weeks where all commitments were completed on time

**Implementation**:
- [ ] Group completed commitments by ISO week
- [ ] For each week (newest first), check if all were on_time
- [ ] Count consecutive on-time weeks until a miss
- [ ] Reset to 0 on: late completion, abandonment, skipped cleanup
- [ ] Update `IntegrityService.calculate_integrity_metrics()`

**Effort**: Medium (2-4 hours)
**Priority**: Medium - Gamification element for sustained performance

### D3: Soft Enforcement on Abandon
**Current**: Direct abandonment allowed without warning
**Target**: Warn user when abandoning at-risk commitment without completing notification

**Implementation**:
- [ ] In /abandon handler, check if commitment.status == at_risk
- [ ] If at_risk, query CleanupPlan and notification task status
- [ ] If notification incomplete, return HandlerResult with warning message
- [ ] Add confirmation flow: "This will affect your integrity score. Continue? (y/n)"
- [ ] On confirm, set CleanupPlan.status = skipped with skipped_reason

**Effort**: Medium (2-3 hours)
**Priority**: High - Core to Honor-Your-Word philosophy

### D4: Pre-Abandon At-Risk Prompt
**Current**: Direct abandonment from pending/in_progress allowed
**Target**: Prompt user to mark at-risk first before abandoning

**Implementation**:
- [ ] In /abandon handler, check if commitment has stakeholder
- [ ] If stakeholder exists and status not at_risk, show prompt
- [ ] Offer options: "Mark at-risk first" or "Abandon directly"
- [ ] If mark at-risk, redirect to /atrisk flow

**Effort**: Small (1-2 hours)
**Priority**: Medium - Encourages proper notification workflow

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

### D8: Snapshot Tests
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

1. **D3: Soft Enforcement** - High priority, core to integrity philosophy
2. **D1: Notification Timeliness** - Medium, improves score accuracy
3. **D2: Reliability Streak** - Medium, gamification
4. **D4: Pre-Abandon Prompt** - Medium, encourages workflow
5. **D5: Visual Indicators** - Low, polish
6. **D6: Metric Trends** - Low, analytics
7. **D7: Affecting Commitments** - Low, debugging aid
8. **D8: Snapshot Tests** - Low, infrastructure
