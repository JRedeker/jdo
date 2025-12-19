# Change: Add Commitment Guardrails

## Why

The core MPI principle states: "make fewer, keep them all." Currently, JDO has no mechanism to prevent commitment overload. Users can create unlimited active commitments without warning, increasing the risk of broken promises and reduced integrity.

Research shows that overcommitment leads to:
- Lower completion rates (spreading too thin)
- Increased stress and cognitive load
- Higher likelihood of missing deadlines
- Degraded stakeholder trust

By adding guardrails, we nudge users toward quality over quantity while preserving autonomy (warnings, not hard blocks).

## What Changes

- **Track commitment velocity** (commitments created vs completed per week)
- **Warn when creating faster than completing** to prevent overcommitment
- **AI coaching prompts** that encourage reflection ("You've created 8 this week but only completed 2")
- **No hard ceiling** on active commitments (removed after user feedback - temporal distribution matters)

This is a **non-breaking** change - existing behavior is preserved, we just add velocity-based warnings and coaching.

## Impact

**Affected specs:**
- `commitment`: Add velocity tracking queries
- `tui-chat`: Add velocity checks during commitment creation flow

**Affected code:**
- `src/jdo/commands/handlers.py`: Add velocity check in CommitHandler
- `src/jdo/db/persistence.py`: Add `get_commitment_velocity()` method
- Tests for new behavior

**User experience:**
- Users creating commitments when velocity is unbalanced see a coaching prompt
- Can still proceed but are encouraged to reflect
- AI incorporates velocity data into coaching ("You've created 8 commitments this week but only completed 2. Are you overcommitting?")

**No migration required** - all changes are additive.
