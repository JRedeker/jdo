# Design: AI Coaching and Time Management System

## Context

JDO helps users track commitments and maintain integrity. The current implementation has an integrity scoring system but lacks the foundational data to provide meaningful coaching. Users can over-commit without warning, the AI doesn't push back, and there's no historical learning about estimation accuracy.

**Stakeholders**: Users who want to improve their reliability and avoid over-commitment.

**Constraints**:
- Must not break existing commitment/task workflows
- Must use SQLite (existing database)
- Must integrate with PydanticAI agent framework
- Must preserve user autonomy while providing firm coaching

## Goals / Non-Goals

### Goals
1. Enable AI to calculate whether user is over-committed based on time math
2. Provide estimation accuracy feedback based on historical data
3. Create immutable task history for AI learning
4. Deliver proactive coaching that pushes back on over-commitment
5. Credit stakeholder notification while preserving learning history

### Non-Goals
- Time tracking (start/stop timers) - out of scope
- Calendar integration - out of scope
- Automatic task scheduling - out of scope
- Changing integrity score formula fundamentally - minimal changes only

## Decisions

### Decision 1: Task Time Fields are Optional with 15-Minute Increments

**What**: Add `estimated_hours` (15-minute increments), `actual_hours_category` (5-point scale), `estimation_confidence` as optional fields to Task.

**Why**: Backward compatible with existing tasks. AI will prompt for estimates but won't block creation without them.

**Time Increments**: 15-minute increments (0.25, 0.5, 0.75, 1.0, etc.). Ambiguous inputs rounded up.

**Actual Hours as Categories**: Instead of exact hours, users select from 5-point scale:
- Much Shorter (<50% of estimate)
- Shorter (50-85%)
- On Target (85-115%)
- Longer (115-150%)
- Much Longer (>150%)

**Alternatives**:
- Required fields: Would break existing workflows, force migrations
- Exact actual hours: Too much friction, users don't want to track precisely
- Separate TimeEstimate table: Over-engineering for this use case

### Decision 2: TaskHistoryEntry as Separate Audit Table

**What**: Create `task_history` table with immutable event records rather than modifying Task directly.

**Why**: 
- Audit log pattern (events are immutable, never deleted)
- Easy to query patterns without complex Task joins
- Denormalized commitment_id for fast queries
- Survives task deletion (history preserved)

**Schema**:
```python
class TaskHistoryEntry(SQLModel, table=True):
    id: UUID
    task_id: UUID  # FK to tasks
    commitment_id: UUID  # Denormalized
    event_type: str  # "created", "started", "completed", "skipped", "abandoned"
    previous_status: TaskStatus | None
    new_status: TaskStatus
    estimated_hours: float | None  # Snapshot at event time
    actual_hours: float | None  # Only for completed
    notes: str | None
    created_at: datetime
```

**Alternatives**:
- Store history as JSON in Task: Loses queryability, harder for AI to analyze
- Event sourcing: Over-engineering for this use case
- Soft deletes only: Doesn't capture status transitions

### Decision 3: User Context is Session-Scoped (Not Persisted Initially)

**What**: Track `available_hours_remaining` in application state, prompt user each session.

**Why**:
- "Hours remaining" (not total workday) - more actionable for immediate planning
- Changes throughout the day as user works
- Keeps interaction lightweight
- Can persist later as DailyPlan if needed

**Update Behavior**: User-initiated updates only. AI does NOT proactively re-ask for hours during session.

**Alternatives**:
- Persistent UserContext table: Premature optimization
- Store on Commitment: Available hours are daily, commitments span days
- Store in app config: Would persist stale data
- Proactive re-asking: Annoying to users

### Decision 4: Estimation Accuracy is 10% of Integrity Score

**What**: Add `estimation_accuracy` metric with 10% weight, reducing `on_time_rate` from 40% to 35%.

**Why**:
- Recognizes estimation as a skill that affects reliability
- Low weight because new users have no history (defaults to 1.0)
- On-time delivery remains most important

**New Formula**:
```
streak_bonus = min(current_streak_weeks * 2, 5) / 100  # Max 5%, was max 10%
composite_score = (
    on_time_rate * 0.35 +           # Was 0.40
    notification_timeliness * 0.25 +
    cleanup_completion_rate * 0.25 +
    estimation_accuracy * 0.10 +    # NEW
    streak_bonus                    # Max 0.05, was 0.10
) * 100
```

**Alternatives**:
- Keep existing weights: Loses opportunity to improve estimation habits
- Higher weight for accuracy: Unfair to new users
- Separate accuracy score: Adds UI complexity

### Decision 5: Coaching System Prompt Structure

**What**: Enhanced system prompt with three coaching modes:
1. **Time-Based Pushback**: Compare available hours vs. task estimates
2. **Integrity-Based Coaching**: Reference letter grade and history
3. **Estimation Coaching**: Use historical accuracy to calibrate estimates

**Why**: Clear coaching framework that AI can follow consistently.

**Pushback Style**: Suggestive, not blocking. AI warns and suggests alternatives but does NOT prevent user from proceeding.

**Similarity Matching**: AI infers task similarity from user's own task history only (title keywords, same commitment). No cross-user comparison.

**Prompt Structure**:
```
You are a commitment integrity coach...

## Coaching Behaviors

### Time-Based Pushback
ALWAYS ask: "How many hours do you have remaining today?"
- Compare available hours vs. task estimates
- Warn if total estimates exceed available time
- SUGGEST alternatives, do NOT block user actions

### Integrity-Based Coaching  
- Reference letter grade: "Your grade is C+. Taking more may risk it."
- Reference history: "You marked 2 commitments at-risk last week."

### Estimation Coaching
- Request estimates for EVERY task
- Show historical accuracy from user's own history: "You estimated 2h but took 4h on similar tasks"
- Infer similarity from title keywords and same commitment
```

### Decision 6: Four New AI Tools

**What**: Add query tools for time/coaching context:
1. `query_user_time_context` - Available hours, allocation, capacity
2. `query_task_history` - Completion patterns, estimation accuracy
3. `query_commitment_time_rollup` - Hours breakdown per commitment
4. `query_integrity_with_context` - Grade + trends + coaching areas

**Why**: AI needs structured data access to make coaching decisions.

**Tool Return Format**: String summaries (not raw JSON) for natural conversation integration.

### Decision 7: Notification Credit Preserves History

**What**: When user completes stakeholder notification:
- `cleanup_completion_rate` improves (credit given)
- `marked_at_risk_at` timestamp preserved on commitment
- TaskHistoryEntry records the at-risk event permanently

**Why**: User earns credit for doing the right thing (notifying), but AI can still see pattern ("3 at-risk commitments this month") for future coaching.

### Decision 8: At-Risk Recovery Grants Full Credit

**What**: If a user marks a commitment at-risk but then delivers by the original due date:
- Full credit for on_time_rate (counts as on-time)
- `marked_at_risk_at` timestamp preserved
- `at_risk_recovered` flag set to True
- AI sees the recovery for positive coaching context

**Why**: Encourages early warning behavior. User who flags risk early and still delivers deserves credit.

**Conditions**: Only applies if delivered ON or BEFORE original due date. Late delivery still counts against score.

### Decision 9: Estimation Accuracy Uses Exponential Decay

**What**: Recent task completions weighted more heavily than older ones.
- Last 7 days: full weight (1.0)
- Weight halves every 7 days (14 days = 0.5, 21 days = 0.25)
- Tasks older than 90 days excluded

**Why**: User's estimation skills may improve over time. Recent performance more predictive than historical average.

### Decision 10: Integrity Grade Always Visible

**What**: Integrity letter grade displayed prominently on home screen at all times.

**Why**: Constant visibility reinforces the importance of integrity and provides ambient awareness without requiring explicit queries.

## Risks / Trade-offs

### Risk: Users Resist Pushback
**Mitigation**: Make coaching opt-out via settings, start with soft suggestions.

### Risk: Estimation Accuracy Unfair to New Users
**Mitigation**: Default estimation_accuracy to 1.0 with no history. Only decreases as user builds track record.

### Risk: Task History Table Grows Large
**Mitigation**: 
- Index on task_id, commitment_id, created_at
- Consider retention policy in future (archive entries > 1 year)
- Events are small (few hundred bytes each)

### Risk: Session-Scoped Context Lost on Crash
**Mitigation**: Prompt user again on restart. Consider persisting to config in future.

## Migration Plan

### Phase 1: Database Schema
1. Add columns to `tasks` table:
   - `estimated_hours FLOAT NULL` (15-minute increments)
   - `actual_hours_category VARCHAR(20) NULL` (much_shorter|shorter|on_target|longer|much_longer)
   - `estimation_confidence VARCHAR(10) NULL`

2. Add columns to `commitments` table:
   - `at_risk_recovered BOOLEAN DEFAULT FALSE`

3. Create `task_history` table

4. No backfill needed (new tasks only)

### Phase 2: Task History Logging
1. Add logging calls to task status change handlers
2. Log only forward (no backfill of historical tasks)

### Phase 3: AI Enhancement
1. Update system prompt
2. Add new tools
3. Deploy and monitor coaching quality

### Rollback
- Schema changes are additive (no column removal needed)
- Remove new code, AI falls back to old prompt
- Task history table can remain (harmless)

## Open Questions

### Resolved
1. **Q: Should available hours be persisted?**
   A: No, session-scoped initially. Can add persistence later if needed.

2. **Q: How to handle tasks without estimates?**
   A: AI prompts for estimate, but creation proceeds without one. Accuracy calculation skips tasks without estimates.

3. **Q: Should estimation_accuracy affect letter grade immediately?**
   A: Yes, from day one. But new users start at 1.0 (perfect accuracy assumed until proven otherwise).

4. **Q: What does "available hours" mean?**
   A: Hours remaining right now, not total workday hours.

5. **Q: How firm should pushback be?**
   A: Suggestive, not blocking. AI warns but doesn't prevent actions.

6. **Q: How should actual hours be recorded?**
   A: 5-point category scale (Much Shorter → Much Longer), not exact hours.

7. **Q: How far back for accuracy calculation?**
   A: Exponential decay - last 7 days full weight, halves every 7 days, max 90 days.

8. **Q: How does AI determine "similar tasks"?**
   A: Infers from user's own task history only (title keywords, same commitment).

9. **Q: What happens if at-risk commitment is delivered on time?**
   A: Full credit if delivered by original due date. Timestamp preserved with `at_risk_recovered=True`.

10. **Q: Should integrity grade be always visible?**
    A: Yes, prominently displayed on home screen.

### Open (for implementation)
1. What's the minimum task history needed before accuracy is meaningful? (Decided: 5 completed tasks)
2. Should AI coaching intensity be configurable? (Suggest: Yes, add `coaching_intensity` setting: gentle/firm/strict)
