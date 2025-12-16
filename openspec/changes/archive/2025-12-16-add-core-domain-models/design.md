# Design: Core Domain Models

## Context

JDO is a commitment-tracking TUI application. Unlike task managers, it centers on **accountability agreements**—what you promised, to whom, by when. This design establishes the foundational data model and persistence approach.

**Stakeholders**: End users who want to track and fulfill their commitments reliably.

**Constraints**:
- Python 3.11+, Pydantic v2, Textual TUI
- SQLite for local persistence (future sync planned)
- EST timezone default for datetime fields

## Goals / Non-Goals

**Goals**:
- Define clear, validated domain models for Commitment, Goal, Task, Stakeholder
- Establish relationships: Goal → Commitment → Task, Goal → Goal (nesting)
- Provide SQLite persistence with repository pattern
- Create minimal, text-focused TUI screens for CRUD operations

**Non-Goals**:
- Sync/collaboration features (future work)
- Complex scheduling or calendar integration
- Notification system
- Mobile or web interface

## Decisions

### 1. Model Hierarchy

```
Stakeholder (standalone)
     │
     ▼
Goal ◄──────┐ (self-referential for nesting)
  │         │
  │ parent_goal_id
  │
  ▼
Commitment (must have stakeholder, may have goal)
  │
  ▼
Task (must have commitment)
  │
  └── sub_tasks: list[SubTask]  (inline, not separate table)
```

**Rationale**: Commitments are the core unit. Goals provide optional grouping/vision. Tasks break down work. Sub-tasks are lightweight and don't need their own identity.

### 2. Commitment Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | UUID | Yes | Primary key |
| deliverable | str | Yes | What is being delivered |
| stakeholder_id | UUID | Yes | FK to Stakeholder |
| goal_id | UUID | No | FK to Goal (optional parent) |
| due_date | date \| datetime | Yes | When it's due |
| due_has_time | bool | Yes | True if specific time matters |
| timezone | str | Yes | Default "America/New_York" |
| status | enum | Yes | pending, in_progress, completed, abandoned |
| completed_at | datetime | No | When marked complete |
| created_at | datetime | Yes | Auto-set |
| updated_at | datetime | Yes | Auto-updated |
| notes | str | No | Additional context |

**Rationale**: `due_has_time` distinguishes "by end of day Dec 20" from "by 3pm Dec 20". Storing both date and datetime in one field with a discriminator keeps queries simple.

### 3. Goal Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | UUID | Yes | Primary key |
| title | str | Yes | Short name |
| problem_statement | str | Yes | What problem this solves |
| solution_vision | str | Yes | Desired end state |
| parent_goal_id | UUID | No | FK to Goal (for nesting) |
| status | enum | Yes | active, achieved, abandoned |
| target_date | date | No | Optional target completion |
| created_at | datetime | Yes | Auto-set |
| updated_at | datetime | Yes | Auto-updated |

### 4. Task Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | UUID | Yes | Primary key |
| commitment_id | UUID | Yes | FK to Commitment |
| title | str | Yes | Short description |
| scope | str | Yes | Clear definition of done |
| status | enum | Yes | pending, in_progress, completed, skipped |
| sub_tasks | list[SubTask] | No | Inline checklist items |
| order | int | Yes | Display/execution order |
| created_at | datetime | Yes | Auto-set |
| updated_at | datetime | Yes | Auto-updated |

**SubTask** (embedded, not a table):
- `description: str`
- `completed: bool`

### 5. Stakeholder Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | UUID | Yes | Primary key |
| name | str | Yes | Display name |
| type | enum | Yes | person, team, organization, self |
| contact_info | str | No | Email, phone, etc. |
| notes | str | No | Additional context |
| created_at | datetime | Yes | Auto-set |
| updated_at | datetime | Yes | Auto-updated |

### 6. Persistence Strategy

**Repository Pattern**: Abstract storage behind repository interfaces.

```python
class CommitmentRepository(Protocol):
    def get(self, id: UUID) -> Commitment | None: ...
    def list(self, filters: CommitmentFilters) -> list[Commitment]: ...
    def save(self, commitment: Commitment) -> Commitment: ...
    def delete(self, id: UUID) -> bool: ...
```

**SQLite Implementation**: Single `jdo.db` file in user data directory. Tables mirror model fields. JSON column for `sub_tasks` in Task table.

**Rationale**: Repository pattern allows future sync backends without changing business logic.

### 7. TUI Architecture

**Screens**:
- `HomeScreen`: List commitments due soon, quick actions
- `CommitmentListScreen`: Filterable list of all commitments
- `CommitmentDetailScreen`: View/edit single commitment with tasks
- `GoalListScreen`: Hierarchical goal browser
- `GoalDetailScreen`: View/edit goal with child commitments
- `StakeholderListScreen`: Manage stakeholders

**Design Principles**:
- Minimal panels, maximum text clarity
- Consistent alignment and spacing (monospace-friendly)
- Keyboard-first navigation
- Status indicators using Unicode symbols (not color alone)

**Layout Philosophy**:
```
┌─ Header ─────────────────────────────────────┐
│ JDO - Commitment Detail                      │
├──────────────────────────────────────────────┤
│                                              │
│  DELIVERABLE                                 │
│  Send quarterly report to finance team       │
│                                              │
│  STAKEHOLDER          DUE                    │
│  Finance Team         Dec 20, 2025 3:00 PM   │
│                                              │
│  STATUS               GOAL                   │
│  ● In Progress        Q4 Reporting           │
│                                              │
│  TASKS (2/4 complete)                        │
│  ✓ Gather department data                    │
│  ✓ Compile spreadsheet                       │
│  ○ Write executive summary                   │
│  ○ Send email with attachment                │
│                                              │
├──────────────────────────────────────────────┤
│ [e]dit  [t]ask  [c]omplete  [q]uit           │
└──────────────────────────────────────────────┘
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Sub-tasks in JSON lose queryability | Acceptable—sub-tasks don't need independent queries |
| Single timezone default may confuse travelers | Store timezone per commitment; UI shows local conversion |
| Goal nesting can get deep | UI limits display depth; no enforcement limit |
| SQLite locks on concurrent access | Single-user app; future sync will handle conflicts |

## Migration Plan

1. Create models in `src/jdo/models/`
2. Create SQLite schema and repositories in `src/jdo/persistence/`
3. Add TUI screens incrementally (Stakeholder → Goal → Commitment → Task)
4. No migration needed—greenfield implementation

## Open Questions

1. **Recurring commitments**: Should we support "every Monday" type commitments? (Recommend: defer to future spec)
2. **Archival**: How long to keep completed/abandoned items? (Recommend: keep forever, add archive view later)
3. **Import/export**: Support for importing from other todo apps? (Recommend: defer to future spec)
