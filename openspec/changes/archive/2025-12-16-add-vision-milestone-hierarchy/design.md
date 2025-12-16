# Design: Vision and Milestone Hierarchy

## Overview

This design introduces Vision and Milestone entities to complete the MPI planning hierarchy:
**Vision -> Goal -> Milestone -> Commitment -> Task**

## Architectural Decisions

### AD-1: Vision as Top-Level Entity

**Decision**: Vision is a standalone SQLModel entity that Goals can optionally reference.

**Rationale**: 
- Visions are long-term (3-5+ years) and relatively stable
- Multiple goals can share a vision
- Visions need their own review cadence (quarterly)
- Separating Vision from Goal allows Goal's `solution_vision` field to remain for goal-specific context

**Implications**:
- New `visions` table in SQLite
- Goal gains `vision_id` FK (optional)
- Vision has its own status lifecycle (active, achieved, evolved, abandoned)

### AD-2: Milestone Between Goal and Commitment

**Decision**: Milestone is a concrete checkpoint entity with required target_date that sits between Goal and Commitment.

**Rationale**:
- Goals are aspirational and may not have dates
- Commitments are tactical (what/who/when) but need intermediate grouping
- Milestones provide measurable progress points with concrete deadlines
- MPI emphasizes breaking large goals into achievable checkpoints

**Implications**:
- New `milestones` table in SQLite
- Commitment gains `milestone_id` FK (optional)
- Milestone requires `goal_id` FK (required) - every milestone belongs to a goal
- Milestone has a distinct status enum including "missed" (unlike Goal)

### AD-3: Flexible Commitment Linkage

**Decision**: Commitment can link to Milestone, Goal, both, or neither.

**Rationale**:
- Quick capture: User may want to create commitment before organizing it
- Simple cases: Some commitments don't need milestone granularity
- Migration: Existing commitments with goal_id continue working
- Orphan tracking: Unlinked commitments are surfaced for user attention

**Implications**:
- Commitment has both `goal_id` (existing) and `milestone_id` (new)
- Either or both can be NULL
- Business logic prefers linking through milestone when possible
- Orphan view surfaces commitments with no goal OR milestone linkage

### AD-4: Vision Review Cadence

**Decision**: Visions have a quarterly review cadence by default, tracked via `last_reviewed_at` and `next_review_date`.

**Rationale**:
- Visions are foundational and shouldn't change frequently
- Quarterly review aligns with business planning cycles
- Proactive prompting keeps visions relevant

**Implications**:
- Vision entity includes review tracking fields
- TUI prompts review when `next_review_date` is past
- Review updates `last_reviewed_at` and calculates next `next_review_date`

### AD-5: Milestone Status Includes "Missed"

**Decision**: Milestone status enum is: `pending`, `in_progress`, `completed`, `missed`.

**Rationale**:
- Unlike Goals (which are aspirational), Milestones have hard dates
- A missed milestone is different from an abandoned goal
- "Missed" supports the Honor-Your-Word protocol (FRC feature)
- Tracking misses enables integrity metrics

**Implications**:
- MilestoneStatus is distinct from GoalStatus
- Automatic transition to "missed" when target_date passes without completion
- User can still complete a missed milestone (late completion)

### AD-6: Cascade Delete Behavior

**Decision**: 
- Deleting a Vision: Block if any Goals reference it
- Deleting a Goal: Block if any Milestones OR Commitments reference it
- Deleting a Milestone: Block if any Commitments reference it

**Rationale**:
- Preserves data integrity
- Follows same pattern as existing Goal/Commitment/Task cascades
- User must explicitly unlink or delete children first

**Implications**:
- DELETE operations check FK references before proceeding
- Clear error messages guide user to unlink/delete children first

## Data Model

### Vision Entity

```python
class VisionStatus(str, Enum):
    active = "active"
    achieved = "achieved"
    evolved = "evolved"  # Vision transformed into something else
    abandoned = "abandoned"

class Vision(SQLModel, table=True):
    id: UUID
    title: str                    # Short inspiring headline
    timeframe: str | None         # e.g., "5 years", "2027", "Q4 2026"
    narrative: str                # Vivid description of future state
    metrics: list[str]            # How will you know? (stored as JSON)
    why_it_matters: str | None    # Why this ignites passion
    status: VisionStatus          # Default: active
    next_review_date: date | None # Default: 90 days from creation
    last_reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
```

### Milestone Entity

```python
class MilestoneStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    missed = "missed"

class Milestone(SQLModel, table=True):
    id: UUID
    goal_id: UUID                 # Required - every milestone belongs to a goal
    title: str
    description: str | None
    target_date: date             # Required - concrete deadline
    status: MilestoneStatus       # Default: pending
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
```

### Goal Modifications

```python
class Goal(SQLModel, table=True):
    # ... existing fields ...
    vision_id: UUID | None        # NEW: Optional link to parent Vision
```

### Commitment Modifications

```python
class Commitment(SQLModel, table=True):
    # ... existing fields ...
    milestone_id: UUID | None     # NEW: Optional link to parent Milestone
```

## Hierarchy Visualization

```
Vision (optional top level)
├── title: "Be a recognized thought leader in AI ethics"
├── timeframe: "5 years"
├── narrative: "I'm invited to speak at major conferences..."
└── metrics: ["50+ speaking engagements", "Book published"]

    Goal (optionally linked to Vision)
    ├── vision_id: → Vision
    ├── title: "Write AI Ethics book"
    ├── problem_statement: "No accessible guide exists"
    └── solution_vision: "The definitive practitioner guide"

        Milestone (required link to Goal)
        ├── goal_id: → Goal
        ├── title: "Complete first draft"
        ├── target_date: 2025-06-01
        └── status: in_progress

            Commitment (optionally linked to Milestone or Goal)
            ├── milestone_id: → Milestone
            ├── deliverable: "Chapter 3 draft"
            ├── stakeholder: "Editor"
            └── due_date: 2025-01-15

                Task (existing, linked to Commitment)
                ├── title: "Research case studies"
                └── scope: "Find 5 examples of AI bias"
```

## Query Patterns

### Orphan Commitments (No Goal AND No Milestone)
```sql
SELECT * FROM commitment 
WHERE goal_id IS NULL AND milestone_id IS NULL 
AND status NOT IN ('completed', 'abandoned')
```

### Visions Due for Review
```sql
SELECT * FROM vision 
WHERE status = 'active' 
AND next_review_date <= CURRENT_DATE
```

### Milestones at Risk (Target date soon, not in_progress)
```sql
SELECT * FROM milestone 
WHERE target_date <= DATE('now', '+7 days')
AND status = 'pending'
```

### Goal Progress via Milestones
```sql
SELECT 
    g.id, g.title,
    COUNT(m.id) as total_milestones,
    COUNT(CASE WHEN m.status = 'completed' THEN 1 END) as completed_milestones
FROM goal g
LEFT JOIN milestone m ON m.goal_id = g.id
GROUP BY g.id
```

## Migration Strategy

Since this is before initial implementation, no data migration is needed. However, the design supports future migration:

1. Vision and Milestone tables are additive
2. Existing Goal records will have `vision_id = NULL` (valid)
3. Existing Commitment records will have `milestone_id = NULL` (valid)
4. Orphan tracking surfaces unlinked records for user attention

## Cross-Reference Notes

- **FRC.yaml lines 214-298**: Vision model detailed specification
- **FRC.yaml lines 300-375**: Milestone model detailed specification
- **add-core-domain-models/specs/goal**: Base Goal model this modifies
- **add-core-domain-models/specs/commitment**: Base Commitment model this modifies
- **add-conversational-tui/specs/tui-chat**: TUI commands this extends
