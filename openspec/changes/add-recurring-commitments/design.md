# Design: Recurring Commitments

## Context

Users have regular obligations that repeat on predictable schedules. Rather than manually creating each instance, a recurring commitment acts as a **template with a timer** that spawns fresh commitment instances on-demand.

**Stakeholders**: Users with regular recurring obligations (weekly reports, monthly reviews, daily standups).

**Constraints**:
- Must integrate with existing Commitment model from `add-core-domain-models`
- On-demand generation (no pre-created series)
- Spawned instances are independent (no series editing)
- SQLite persistence

## Goals / Non-Goals

**Goals**:
- Define RecurringCommitment as a template that spawns Commitment instances
- Support comprehensive recurrence patterns (daily, weekly, monthly, yearly, custom)
- Support end conditions (never, after N, by date)
- Inherit task templates to spawned instances
- Provide management UI for recurring commitments

**Non-Goals**:
- Calendar sync/integration
- Complex RRULE compatibility (iCal format)
- Series editing ("edit all future instances")
- Pre-generation of future instances

## Decisions

### 1. Model Architecture

```
RecurringCommitment (template)
    │
    │ spawns on-demand
    ▼
Commitment (instance)
    │
    │ recurring_commitment_id (back-reference)
    ▼
Task (inherited from template, reset to pending)
```

**RecurringCommitment** is NOT a Commitment—it's a template that contains the blueprint for creating Commitments.

### 2. RecurringCommitment Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | UUID | Yes | Primary key |
| deliverable | str | Yes | Template deliverable text |
| stakeholder_id | UUID | Yes | FK to Stakeholder |
| goal_id | UUID | No | FK to Goal (optional) |
| due_time | time | No | Time of day when due |
| timezone | str | Yes | Default "America/New_York" |
| recurrence_type | enum | Yes | daily, weekly, monthly, yearly, custom |
| recurrence_pattern | JSON | Yes | Pattern-specific details (see below) |
| end_type | enum | Yes | never, after_count, by_date |
| end_after_count | int | No | Required if end_type=after_count |
| end_by_date | date | No | Required if end_type=by_date |
| task_templates | JSON | Yes | List of task templates to copy |
| notes | str | No | Template notes |
| is_active | bool | Yes | Can be paused without deleting |
| last_generated_date | date | No | Track what's been generated |
| created_at | datetime | Yes | Auto-set |
| updated_at | datetime | Yes | Auto-updated |

### 3. Recurrence Patterns

The `recurrence_pattern` JSON field stores pattern-specific data:

**Daily**:
```json
{"interval": 1}  // every day
{"interval": 2}  // every 2 days
```

**Weekly**:
```json
{"interval": 1, "days": ["monday", "wednesday", "friday"]}
{"interval": 2, "days": ["monday"]}  // every 2 weeks on Monday
```

**Monthly**:
```json
{"interval": 1, "day_of_month": 15}  // 15th of every month
{"interval": 1, "week": 2, "day": "friday"}  // 2nd Friday of every month
{"interval": 1, "week": -1, "day": "friday"}  // last Friday of every month
```

**Yearly**:
```json
{"interval": 1, "month": 1, "day": 15}  // Jan 15 every year
{"interval": 1, "month": 6, "week": 1, "day": "monday"}  // 1st Monday of June
```

### 4. On-Demand Generation Algorithm

```python
def get_next_due_date(recurring: RecurringCommitment, after: date) -> date | None:
    """Calculate next due date after the given date based on pattern."""
    # Returns None if recurrence has ended
    ...

def should_generate_instance(recurring: RecurringCommitment) -> bool:
    """Check if a new instance should be generated."""
    next_due = get_next_due_date(recurring, recurring.last_generated_date or today())
    if next_due is None:
        return False  # Recurrence ended
    # Generate if next_due is within the "upcoming" window (e.g., 7 days)
    return next_due <= today() + timedelta(days=7)

def generate_instance(recurring: RecurringCommitment) -> Commitment:
    """Spawn a new Commitment from the template."""
    next_due = get_next_due_date(recurring, recurring.last_generated_date or today())
    
    commitment = Commitment(
        deliverable=recurring.deliverable,
        stakeholder_id=recurring.stakeholder_id,
        goal_id=recurring.goal_id,
        due_date=next_due,
        due_time=recurring.due_time,
        timezone=recurring.timezone,
        notes=recurring.notes,
        recurring_commitment_id=recurring.id,  # Back-reference
    )
    
    # Copy task templates
    for template in recurring.task_templates:
        Task(
            commitment_id=commitment.id,
            title=template["title"],
            scope=template["scope"],
            sub_tasks=template.get("sub_tasks", []),
            order=template["order"],
            status="pending",  # Always reset
        )
    
    recurring.last_generated_date = next_due
    return commitment
```

**Generation triggers**:
1. User views "upcoming commitments" (home screen, `/show commitments`)
2. User completes the current instance of a recurring commitment
3. Background check on app startup (optional)

### 5. Task Template Structure

Task templates are stored as JSON in `task_templates`:

```json
[
  {
    "title": "Gather data from departments",
    "scope": "Collect Q4 numbers from sales, marketing, and engineering",
    "sub_tasks": [
      {"description": "Email sales for numbers"},
      {"description": "Email marketing for numbers"},
      {"description": "Email engineering for numbers"}
    ],
    "order": 1
  },
  {
    "title": "Compile spreadsheet",
    "scope": "Merge all department data into master spreadsheet",
    "sub_tasks": [],
    "order": 2
  }
]
```

When spawning an instance:
- All tasks created with `status="pending"`
- All sub-tasks created with `completed=false`
- Task order preserved

### 6. End Condition Handling

| End Type | Behavior |
|----------|----------|
| `never` | Generates indefinitely |
| `after_count` | Tracks `instances_generated`; stops when count reached |
| `by_date` | Stops generating if next_due > end_by_date |

Add `instances_generated: int` field to track count for `after_count`.

### 7. Commitment Model Changes

Add to existing Commitment model:
- `recurring_commitment_id: UUID | None` — Links instance to template

This enables:
- Showing "recurring" indicator in UI
- Finding all instances of a recurring commitment
- Triggering next generation on completion

### 8. UI Integration

**Conversational TUI** (add-conversational-tui):
- `/recurring` — List recurring commitments in data panel
- `/recurring new` — Create new recurring commitment via conversation
- `/recurring edit <id>` — Modify recurrence pattern
- `/recurring pause <id>` — Set is_active=false
- `/recurring resume <id>` — Set is_active=true
- `/recurring delete <id>` — Delete template (instances remain)

**Data Panel**:
- Recurring commitment view shows pattern, next due, instance count
- Commitment view shows "Recurring: Weekly on Mon, Wed, Fri" indicator

**Visual indicator**:
- Recurring commitments show ↻ symbol
- Template management clearly separated from instance editing

### 9. Database Schema

```sql
CREATE TABLE recurring_commitments (
    id TEXT PRIMARY KEY,
    deliverable TEXT NOT NULL,
    stakeholder_id TEXT NOT NULL REFERENCES stakeholders(id),
    goal_id TEXT REFERENCES goals(id),
    due_time TEXT,
    timezone TEXT NOT NULL DEFAULT 'America/New_York',
    recurrence_type TEXT NOT NULL,
    recurrence_pattern TEXT NOT NULL,  -- JSON
    end_type TEXT NOT NULL DEFAULT 'never',
    end_after_count INTEGER,
    end_by_date TEXT,
    task_templates TEXT NOT NULL DEFAULT '[]',  -- JSON
    notes TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    last_generated_date TEXT,
    instances_generated INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Add to commitments table
ALTER TABLE commitments ADD COLUMN recurring_commitment_id TEXT REFERENCES recurring_commitments(id);
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Complex pattern calculation | Use well-tested date library (dateutil or similar) |
| Missed generations if app not opened | Generate on startup; catch up missed instances |
| Task templates out of sync | Templates are snapshots; changes don't affect existing instances |
| Storage growth from instances | Instances are normal commitments; archive strategy applies |

## Migration Plan

1. Create RecurringCommitment model
2. Add recurring_commitment_id to Commitment model
3. Create SQLite schema migration
4. Implement recurrence pattern calculator
5. Implement on-demand generation logic
6. Add repository methods
7. Add TUI commands and data panel views
8. Write tests for pattern calculations

## Open Questions

1. **Catch-up behavior**: If user doesn't open app for 2 weeks, generate all missed instances or just the next one?
   - Recommendation: Generate only the current/next due instance, not historical ones
   
2. **Pause vs. Delete**: Should pausing preserve or skip missed instances?
   - Recommendation: Pausing skips; resume continues from current date

3. **Instance limit**: Should there be a limit on active instances from same recurring?
   - Recommendation: No limit initially; user can complete/abandon as needed
