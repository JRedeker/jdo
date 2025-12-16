# Change: Add Honor-Your-Word Protocol and Integrity Metrics

## Why

JDO is built on Meta Performance Institute (MPI) principles where integrity is the engine of workability. Currently, when a commitment can't be met, the only option is "abandoned" - a dead end with no structured recovery. MPI teaches that integrity has three parts:

1. **Do what you said** by when you said
2. **Notify the right people** as soon as you know you won't
3. **Clean up the mess** caused by the miss

This change implements the Honor-Your-Word protocol to transform broken commitments into structured recovery workflows, and adds integrity metrics to give users visibility into their reliability patterns.

## What Changes

### New Status: `at_risk`

Add `at_risk` status to CommitmentStatus enum, representing commitments that may not be met and require stakeholder notification.

### New Entity: CleanupPlan

A CleanupPlan tracks the recovery workflow when a commitment is at-risk or abandoned:
- Impact description (what harm does missing this cause?)
- Mitigation actions (what will you do about it?)
- Notification task (auto-created, must be completed)
- Status tracking (planned → in_progress → completed)

### Notification via Task

When a commitment is marked at-risk, a special notification Task is auto-created at position 0 (first in order). This task:
- Contains AI-drafted notification details (stakeholder, reason, impact, proposed resolution)
- Must be marked complete (user confirms they sent the notification externally)
- Blocks CleanupPlan completion until done

### Integrity Metrics

Track and display reliability metrics:
- **On-time rate**: % of commitments completed by due date
- **Notification timeliness**: How early user notifies when at-risk
- **Cleanup completion rate**: % of cleanup plans fully completed
- **Reliability streak**: Consecutive periods with all commitments met

### Integrity Score

Composite letter grade (A+ through D-) displayed on home screen, calculated from weighted metrics.

### AI Risk Detection

Proactive checks on app launch for:
- Overdue commitments
- Commitments due within 24 hours with no task progress
- Commitments approaching deadline with no recent interaction

### New Commands

- `/atrisk` - Mark commitment as at-risk, start notification workflow
- `/cleanup` - View or update cleanup plan
- `/integrity` - Show integrity dashboard with metrics

## Impact

- **Affected specs**:
  - `commitment` (modified - add `at_risk` status)
  - `integrity` (new capability - CleanupPlan, metrics, scoring)
  - `tui-chat` (modified - new commands, home screen integrity score, AI risk detection)

- **Affected code**:
  - CommitmentStatus enum extension
  - New CleanupPlan SQLModel entity
  - New IntegrityMetrics calculation module
  - TUI home screen modification
  - AI prompt extensions for risk detection and notification drafting

- **Breaking changes**: None - `at_risk` is additive to existing statuses

## Dependencies

- Requires core domain models (Commitment, Task, Stakeholder) - already implemented
- Should be implemented after `implement-jdo-app` (TUI app shell and commands infrastructure)

## References

- FRC.yaml `honor_your_word_protocol` feature (lines 28-130)
- FRC.yaml `integrity_metrics` feature (lines 135-212)
- MPI Integrity Framework: "Deliver, Notify, Clean Up"
