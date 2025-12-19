# Design: Commitment Guardrails

## Context

JDO implements the MPI (Meta Performance Institute) principle: "make fewer, keep them all." Currently, users can create unlimited active commitments without guidance, increasing risk of overcommitment and broken promises.

This feature adds coaching guardrails during commitment creation to nudge users toward sustainable commitment loads.

## Goals

- **Primary**: Track commitment velocity to detect overcommitment patterns
- **Secondary**: Provide coaching prompts without blocking user actions
- **Tertiary**: Support sustainable commitment-making behavior

## Non-Goals

- Hard limits on commitment creation (preserve user autonomy)
- AI-powered commitment prioritization (future feature)
- Stakeholder-specific thresholds (future enhancement)
- Historical velocity analytics dashboard (separate feature)

## Decisions

### 1. No Ceiling on Active Commitments (Removed)

**Rationale**: A fixed ceiling doesn't account for temporal distribution. A commitment due in 3 months shouldn't count the same as one due tomorrow. The cognitive load concern is better addressed by velocity tracking.

**Change from original design**: Originally included a configurable `max_active_commitments: int = 7` setting with threshold warnings. Removed after user feedback that it didn't make sense given varying due dates.

**Why velocity is sufficient**: 
- Velocity (created vs completed) catches the actual problem: making commitments faster than delivering
- Works regardless of commitment timescales
- No arbitrary threshold to configure or maintain

### 2. 7-Day Velocity Window

**Rationale**: Weekly cadence aligns with common planning cycles (sprint planning, weekly reviews).

**Why not 30 days?**: Too long to be actionable. Users need immediate feedback.

**Alternatives considered**:
- 3 days: Too short, not enough signal
- 14 days: Dilutes recent behavior patterns

### 3. Warnings in Confirmation Flow

**Placement**: Append coaching notes to the confirmation message in `CommitHandler._build_confirmation_message()`.

**Rationale**: 
- User has already expressed intent (minimizes interruption)
- Still in decision window (can reconsider)
- Contextual (appears with the draft details)

**Why not block creation?**: Violates MPI principle of personal responsibility. Users must own their choices.

### 4. Query Location: PersistenceService

**Rationale**: 
- Already exists and owns database queries
- Handler depends on PersistenceService for saves
- Follows existing pattern (see `save_commitment()`)

**Alternatives considered**:
- Separate `MetricsService`: Premature - only 2 queries
- Direct queries in handler: Violates separation of concerns
- Static methods on Commitment model: Clutters domain model

## Implementation Pattern

```python
# 1. Queries (db/persistence.py)
class PersistenceService:
    def get_commitment_velocity(self, days: int = 7) -> tuple[int, int]:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        
        created = self.session.exec(
            select(func.count()).select_from(Commitment)
            .where(Commitment.created_at >= cutoff)
        ).one()
        
        completed = self.session.exec(
            select(func.count()).select_from(Commitment)
            .where(
                Commitment.completed_at >= cutoff,
                Commitment.status == CommitmentStatus.COMPLETED
            )
        ).one()
        
        return (created, completed)

# 2. Handler Integration (commands/handlers.py)
class CommitHandler:
    def execute(self, context: dict[str, Any]) -> HandlerResult:
        # ... existing draft building ...
        
        # Get velocity for guardrail context
        try:
            with get_session() as session:
                service = PersistenceService(session)
                created, completed = service.get_commitment_velocity()
        except Exception:
            # Graceful degradation if database unavailable
            created = 0
            completed = 0
        
        message = self._build_confirmation_message(draft_data, created, completed)
        # ...
    
    def _build_confirmation_message(
        self, 
        draft_data: dict[str, Any],
        velocity_created: int,
        velocity_completed: int,
    ) -> str:
        lines = ["Here's the commitment I'll create:", "", ...]
        
        # Velocity warning
        if velocity_created > velocity_completed:
            lines.append("")
            lines.append(
                f"**Note**: You've created {created} commitments this week "
                f"but only completed {completed}. Are you overcommitting?"
            )
        
        return "\n".join(lines)
```

## Risks / Trade-offs

### Risk: Database Query Performance
**Impact**: Two additional queries per commitment creation

**Mitigation**: 
- Queries are simple counts with indexed columns
- Only executed during confirmation (not every keystroke)
- Profile in production, add index if needed
- Graceful degradation if queries fail

**Acceptable**: Commitment creation is infrequent (~5-10/day max)

### Risk: Warning Fatigue
**Impact**: Users ignore velocity warnings if they appear too frequently

**Mitigation**:
- Only warns when created > completed (not equals)
- 7-day window smooths out daily fluctuations
- Warnings are coaching, not errors
- User can proceed regardless

**Monitor**: Track warning frequency in future integrity metrics

### Trade-off: Simplicity vs Sophistication
**Choice**: Simple count-based thresholds vs ML-based predictions

**Rationale**: 
- Count-based is transparent and debuggable
- No training data yet for ML
- Can evolve later without breaking changes

## Migration Plan

**No migration required** - all changes are additive:
1. New setting field (defaults applied)
2. New query methods (unused until handlers call them)
3. Handler updates (backwards compatible)

**Rollback**: Remove handler calls to query methods. Settings field is ignored if unused.

## Open Questions

~~None - spec is complete.~~

## References

- ROADMAP.yaml: commitment_guardrails feature
- Miller's Law: Cognitive limit of 7±2 items
- MPI Principles: "Make fewer, keep them all"
- Existing patterns: `integrity/service.py` (func.count usage)
