# Design: Vision-Focused Goal Management

## Context

JDO's core philosophy centers on **integrity through commitments**. The app helps users build self-trust by making and keeping specific promises. Goals serve a different purpose—they provide the *vision* that gives commitments meaning.

**The Hierarchy of Integrity**:
```
Vision (Goals)
    ↓ provides direction to
Commitments
    ↓ are fulfilled through
Tasks
```

Goals are not things you "complete"—they're directions you move toward. You don't complete "Become a senior engineer"; you make commitments that move you in that direction and periodically review whether you're still aligned.

**Stakeholders**: Users seeking personal growth through accountability and self-trust.

**Constraints**:
- Must integrate with existing Goal model from `add-core-domain-models`
- Goals remain optional—commitments can exist without goals
- Review system should encourage reflection, not create anxiety

## Goals / Non-Goals

**Goals**:
- Reframe goals as vision-holders with review dates instead of due dates
- Add motivation field to reinforce growth mindset ("why does this matter?")
- Implement periodic review workflow
- Show commitment progress as indicator of goal movement
- Support "on hold" status for paused goals

**Non-Goals**:
- Goal completion tracking (goals don't "complete")
- Automatic goal achievement detection
- Goal deadlines or due dates
- Complex OKR-style metrics

## Decisions

### 1. Updated Goal Model

| Field | Type | Change | Notes |
|-------|------|--------|-------|
| id | UUID | - | Primary key |
| title | str | - | Short name |
| problem_statement | str | - | What problem/gap exists |
| solution_vision | str | - | Desired future state |
| motivation | str | **NEW** | Why this matters to the user |
| parent_goal_id | UUID \| None | - | For nesting |
| status | enum | **MODIFIED** | active, achieved, abandoned, **on_hold** |
| ~~target_date~~ | ~~date~~ | **REMOVED** | Goals don't have due dates |
| next_review_date | date \| None | **NEW** | When to next review this goal |
| review_interval_days | int \| None | **NEW** | Optional recurring review (7, 14, 30, 90 days) |
| last_reviewed_at | datetime \| None | **NEW** | When user last reviewed |
| created_at | datetime | - | Auto-set |
| updated_at | datetime | - | Auto-updated |

### 2. Goal Status Semantics

| Status | Meaning |
|--------|---------|
| `active` | Actively pursuing this vision |
| `on_hold` | Temporarily paused (life circumstances, reprioritization) |
| `achieved` | Vision realized—user has arrived (rare, intentional) |
| `abandoned` | No longer pursuing (explicit decision, not failure) |

**Philosophy note**: "Achieved" should be rare and intentional. Most goals evolve rather than complete. "Abandon" is not failure—it's honest reprioritization.

### 3. Review System

**Review prompts** appear when `next_review_date <= today`:

```
┌─ Goal Review ──────────────────────────────────────────┐
│                                                        │
│  GOAL: Become a stronger technical leader              │
│                                                        │
│  WHY THIS MATTERS                                      │
│  I want to mentor others and have broader impact       │
│                                                        │
│  COMMITMENT PROGRESS                                   │
│  ✓ 3 completed    ● 2 in progress    ○ 1 pending      │
│                                                        │
│  REFLECTION                                            │
│  - Are you still moving toward this vision?            │
│  - What commitments should you make next?              │
│  - Does this goal still resonate?                      │
│                                                        │
│  [c]ontinue  [h]old  [a]bandon  [e]dit                │
└────────────────────────────────────────────────────────┘
```

**After review**:
- `last_reviewed_at` = now
- `next_review_date` = today + `review_interval_days` (if set)
- User can adjust goal, add commitments, or change status

### 4. Review Intervals

Common intervals with suggested use cases:

| Interval | Use Case |
|----------|----------|
| 7 days | Weekly goals, sprint-level |
| 14 days | Bi-weekly check-ins |
| 30 days | Monthly goals, project milestones |
| 90 days | Quarterly goals, career development |
| None | Review on-demand only |

### 5. Commitment Progress on Goals

When viewing a goal, show aggregated commitment status:

```python
class GoalProgress:
    total_commitments: int
    completed: int
    in_progress: int
    pending: int
    abandoned: int
    
    @property
    def completion_rate(self) -> float:
        """Percentage of non-abandoned commitments completed."""
        ...
```

This is **informational only**—it doesn't determine goal status. A goal with 100% commitment completion might still be "active" because the vision continues.

### 6. UI Integration

**Conversational TUI commands**:
- `/goal review` — Start review for goals due for review
- `/goal review <id>` — Review specific goal
- Goal creation prompts for motivation: "Why does this goal matter to you?"

**Data panel goal view**:
- Shows vision fields prominently
- Displays motivation
- Shows next review date and interval
- Shows commitment progress summary
- De-emphasizes "achieved" status (it's not the point)

**Home screen**:
- "Goals due for review" section (if any)
- Commitments remain primary focus

### 7. Motivation Field Purpose

The `motivation` field reinforces growth mindset:

- Prompts user to articulate *why* during creation
- Displayed during reviews to reconnect with purpose
- Helps distinguish genuine goals from obligations
- Supports reflection: "Does this still resonate?"

Example motivations:
- "I want to be someone my team can rely on for technical guidance"
- "Financial security means freedom to take creative risks"
- "Health is the foundation for everything else I want to do"

### 8. Migration from target_date

For any existing goals with `target_date`:
1. Convert `target_date` → `next_review_date`
2. Set `review_interval_days` = None (one-time review)
3. Set `motivation` = None (user can add later)
4. Set `last_reviewed_at` = None

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Users expect goal "completion" | Clear messaging: goals are visions, commitments are completable |
| Review fatigue | Intervals are optional; reviews are lightweight prompts |
| Motivation field feels forced | Optional during creation; prompt is gentle |
| "On hold" becomes graveyard | Periodic prompt to review on-hold goals |

## Open Questions

1. **Review reminders**: Should goals due for review appear in home screen or just when user runs `/goal review`?
   - Recommendation: Subtle indicator in home screen, not blocking

2. **Child goal reviews**: When parent goal is reviewed, prompt for child goals too?
   - Recommendation: No, review each independently

3. **Commitment alignment**: Should AI suggest when commitments don't align with any goal?
   - Recommendation: Future enhancement, not in this spec
