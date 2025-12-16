# Design: Honor-Your-Word Protocol and Integrity Metrics

## Overview

This design implements MPI's integrity framework: "Deliver, Notify, Clean Up." When commitments can't be met, the system guides users through a structured recovery workflow that maintains integrity even in failure.

## Architectural Decisions

### AD-1: At-Risk as Intermediate Status

**Decision**: Add `at_risk` status between `in_progress` and `abandoned` in CommitmentStatus enum.

**Rationale**:
- Provides a clear signal that commitment is in trouble but not yet failed
- Creates a checkpoint for stakeholder notification before abandonment
- Allows recovery back to `in_progress` if situation improves
- Supports metrics on how early users recognize and communicate risk

**Status Flow**:
```
pending → in_progress → at_risk → abandoned
                ↓           ↓
            completed   completed (late)
                ↑           ↑
            at_risk ←───────┘
```

**Implications**:
- CommitmentStatus enum gains new value
- UI needs visual distinction for at_risk (warning color)
- Queries for "active" commitments include at_risk

### AD-2: Notification as Task (Not Separate Entity)

**Decision**: When marking at-risk, auto-create a special Task at position 0 with notification details, rather than a separate Notification entity.

**Rationale**:
- Leverages existing Task infrastructure (no new table)
- User workflow is natural: complete the task = sent the notification
- Task title/scope contain the notification draft details
- Maintains simplicity while ensuring notification happens

**Task Structure**:
```python
Task(
    title="Notify [Stakeholder] about at-risk commitment",
    scope="""
    NOTIFICATION DRAFT:
    To: [Stakeholder name]
    Re: [Commitment deliverable]
    
    I need to let you know that I may not be able to deliver 
    [deliverable] by [due_date] as committed.
    
    Reason: [User-provided reason]
    Impact: [AI-suggested impact]
    Proposed resolution: [New date or alternative]
    
    Mark this task complete after you've sent the notification.
    """,
    order=0,  # First task
    status="pending",
    is_notification_task=True  # Flag for special handling
)
```

**Implications**:
- Task model needs `is_notification_task` boolean field
- Task position 0 ensures it's the immediate next action
- Task cannot be skipped (only completed or deleted with warning)

### AD-3: CleanupPlan as Separate Entity

**Decision**: Create CleanupPlan as a separate SQLModel entity linked to Commitment.

**Rationale**:
- Cleanup involves multiple fields beyond what Task can hold
- One-to-one relationship with at-risk/abandoned commitment
- Tracks completion status independently
- Supports integrity metrics calculation

**Implications**:
- New `cleanup_plans` table
- FK from CleanupPlan to Commitment
- CleanupPlan created when commitment marked at_risk

### AD-4: Soft Enforcement for Abandonment

**Decision**: Strongly prompt but allow override when abandoning without completed CleanupPlan.

**Rationale**:
- Strict blocking would frustrate users in edge cases
- Soft enforcement teaches the behavior without creating friction
- Override requires explicit acknowledgment ("I understand this affects my integrity score")
- Tracks overrides for potential coaching conversations

**Implications**:
- Abandonment flow checks CleanupPlan status
- If incomplete, show warning with override option
- Record whether cleanup was completed or overridden

### AD-5: Letter Grade with Sub-Scores

**Decision**: Display integrity as letter grade (A+ through D-) with 12-point scale.

**Grading Scale**:
```
A+: 97-100%    B+: 87-89%    C+: 77-79%    D+: 67-69%
A:  93-96%     B:  83-86%    C:  73-76%    D:  63-66%
A-: 90-92%     B-: 80-82%    C-: 70-72%    D-: 60-62%
                                           F:  <60%
```

**Rationale**:
- Familiar grading system (schools, credit ratings)
- Sub-scores provide granularity without overwhelming precision
- More motivating than raw percentages
- Grade changes are meaningful events

**Implications**:
- IntegrityScore calculation returns percentage
- Display logic converts to letter grade
- Home screen shows grade prominently

### AD-6: Proactive AI Risk Detection on Launch

**Decision**: AI checks for at-risk commitments on app launch (proactive, not reactive).

**Triggers checked on launch**:
1. Overdue commitments (due_date < today, status not completed/abandoned)
2. Due within 24 hours with status=pending (no progress started)
3. Due within 48 hours with status=in_progress but no task activity in 24h

**Rationale**:
- Catch problems before they become emergencies
- App launch is natural checkpoint for review
- Doesn't interrupt mid-session work
- Gives user opportunity to mark at-risk early

**Implications**:
- Startup check queries commitments
- AI prompt generated for detected risks
- User can dismiss or act on warnings

### AD-7: Metric Calculation and Storage

**Decision**: Calculate metrics on-demand from commitment history, cache in memory for session.

**Metrics**:
| Metric | Calculation | Weight |
|--------|-------------|--------|
| On-time rate | completed_on_time / total_completed | 40% |
| Notification timeliness | avg(days before due when marked at_risk) | 25% |
| Cleanup completion | cleanup_completed / cleanup_required | 25% |
| Streak bonus | weeks of perfect reliability | 10% |

**Rationale**:
- Avoids separate metrics table (complexity)
- Commitment history contains all needed data
- Session cache prevents repeated calculation
- Can add persistence later if needed for trends

**Implications**:
- IntegrityMetrics module calculates from Commitment queries
- Add `marked_at_risk_at` timestamp to Commitment for timeliness calc
- Consider adding `completed_on_time` boolean for efficient queries

## Data Model

### Commitment Extensions

```python
class CommitmentStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    at_risk = "at_risk"          # NEW
    completed = "completed"
    abandoned = "abandoned"

class Commitment(SQLModel, table=True):
    # ... existing fields ...
    marked_at_risk_at: datetime | None  # NEW: When marked at-risk
    completed_on_time: bool | None      # NEW: Set on completion
```

### Task Extension

```python
class Task(SQLModel, table=True):
    # ... existing fields ...
    is_notification_task: bool = False  # NEW: Special task flag
```

### CleanupPlan Entity

```python
class CleanupPlanStatus(str, Enum):
    planned = "planned"
    in_progress = "in_progress"
    completed = "completed"
    skipped = "skipped"  # User overrode requirement

class CleanupPlan(SQLModel, table=True):
    id: UUID
    commitment_id: UUID               # Required FK
    impact_description: str | None    # What harm does missing cause?
    mitigation_actions: list[str]     # What will you do? (JSON)
    notification_task_id: UUID | None # Reference to notification task
    status: CleanupPlanStatus         # Default: planned
    completed_at: datetime | None
    skipped_reason: str | None        # If user overrode
    created_at: datetime
    updated_at: datetime
```

### IntegrityMetrics (Calculated, Not Stored)

```python
@dataclass
class IntegrityMetrics:
    on_time_rate: float              # 0.0-1.0
    notification_timeliness: float   # 0.0-1.0 (normalized)
    cleanup_completion_rate: float   # 0.0-1.0
    current_streak_weeks: int
    
    total_completed: int
    total_on_time: int
    total_at_risk: int
    total_abandoned: int
    
    @property
    def composite_score(self) -> float:
        """Returns 0-100 score"""
        streak_bonus = min(self.current_streak_weeks * 2, 10) / 100
        return (
            self.on_time_rate * 0.40 +
            self.notification_timeliness * 0.25 +
            self.cleanup_completion_rate * 0.25 +
            streak_bonus
        ) * 100
    
    @property
    def letter_grade(self) -> str:
        """Returns A+ through F"""
        score = self.composite_score
        # ... grade calculation
```

## Workflow: Marking At-Risk

```
1. User: /atrisk (or AI detects risk)
   
2. System: 
   - Change commitment status to at_risk
   - Set marked_at_risk_at = now()
   - Create CleanupPlan (status=planned)
   
3. AI prompts for details:
   - "Why might you miss this commitment?"
   - "What impact will this have on [stakeholder]?"
   - "Can you propose a new deadline or alternative?"

4. System creates notification Task:
   - order=0 (top of list)
   - is_notification_task=True
   - scope contains AI-drafted notification
   - Links to CleanupPlan

5. AI: "I've added a task to notify [stakeholder]. 
        Please send the notification and mark the task complete."

6. User completes notification task
   - CleanupPlan status → in_progress

7. User completes mitigation actions or marks commitment:
   - completed (late) → CleanupPlan status → completed
   - abandoned → CleanupPlan status → completed (or skipped with warning)
```

## Home Screen Integration

```
┌─────────────────────────────────────────────────────────┐
│  JDO                                    Integrity: A-   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ⚠ 2 commitments need attention                        │
│    • "Send report" is overdue                          │
│    • "Review PR" due in 4 hours, no progress           │
│                                                         │
│  Today's commitments:                                   │
│    ...                                                  │
└─────────────────────────────────────────────────────────┘
```

## Cross-References

- **add-core-domain-models/specs/commitment**: Base Commitment model
- **add-core-domain-models/specs/task**: Base Task model  
- **add-conversational-tui/specs/tui-chat**: TUI command infrastructure
- **FRC.yaml lines 28-212**: Feature specifications
