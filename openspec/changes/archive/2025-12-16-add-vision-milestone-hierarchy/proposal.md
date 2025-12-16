# Change: Add Vision and Milestone Models with Hierarchy Restructure

## Why

JDO is built on Meta Performance Institute (MPI) principles where "vision leads" - all goals and commitments must trace back to a vivid picture of the future. The current hierarchy (Goal → Commitment → Task) lacks:

1. **Vision as a first-class entity** - Currently `solution_vision` is just a text field on Goal, not a standalone entity that can be reviewed, tracked, and serve as the root of the planning hierarchy.

2. **Milestones for goal decomposition** - Goals are aspirational and long-term. Users need intermediate checkpoints with concrete dates to make progress measurable. Currently commitments link directly to goals, skipping this important planning layer.

The MPI planning hierarchy should be: **Vision → Goal → Milestone → Commitment → Task**

## What Changes

### New Entities
- **Vision**: Top-level entity representing a vivid, inspiring picture of the future with title, timeframe, narrative, success metrics, and quarterly review cadence
- **Milestone**: Intermediate entity between Goal and Commitment with concrete target dates that break goals into achievable checkpoints

### Modified Entities
- **Goal**: Add `vision_id` foreign key; repurpose `problem_statement` and `solution_vision` fields to be goal-specific (optional when vision provides context)
- **Commitment**: Add `milestone_id` foreign key; commitments can link to milestone OR goal (or neither for quick captures)

### New TUI Commands
- `/vision` - List, create, review visions
- `/milestone` - List, create milestones for goals

### Hierarchy Enforcement
- Goals are encouraged (but not required) to link to a Vision
- Milestones must link to a Goal
- Commitments can link to Milestone, Goal, or neither (orphan tracking surfaces unlinked commitments)

## Impact

- **Affected specs**: 
  - `vision` (new capability)
  - `milestone` (new capability)  
  - `goal` (modified - add vision_id)
  - `commitment` (modified - add milestone_id)
  - `tui-chat` (modified - new commands)
  
- **Affected code**: 
  - New SQLModel entities: Vision, Milestone
  - Modified entities: Goal, Commitment
  - New TUI commands and data panel views
  - Database migration to add new tables and foreign keys

- **Breaking changes**: None - all new fields are optional, existing data remains valid

## Dependencies

This change extends the domain models from `add-core-domain-models` (now archived). The base hierarchy (Stakeholder → Goal → Commitment → Task) is complete. This change adds Vision and Milestone to create the full MPI hierarchy.

**Requires (completed):**
- `add-core-domain-models` - Provides Goal, Commitment, Task models to extend

## References

- FRC.yaml `vision_model` and `milestone_model` features
- MPI "Vision leads" principle
- MPI Planning Hierarchy: Vision → Goals → Milestones → Commitments
