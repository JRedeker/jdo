# Change: Update Goal Model for Vision-Focused Growth Mindset

## Why

JDO is built on a philosophy of **high-integrity commitment management** where users build self-trust through honoring their commitments. In this system:

- **Commitments** are the primary unit of integrity—concrete agreements with stakeholders that enforce action and build self-trust
- **Goals** are secondary, aspirational containers that provide **vision and direction**, not deadlines

The current Goal model has a `target_date` field which implies a deadline. This conflicts with the app's philosophy: goals should be forward-looking visions that users **review** periodically, not targets they "complete by" a date. A goal like "Become a better engineer" or "Q4 Project Success" doesn't have a due date—it has checkpoints where users reflect on progress and adjust their commitments accordingly.

## What Changes

- **MODIFIED** `target_date` → `next_review_date`: Goals have review dates, not due dates
- **ADDED** `review_interval_days`: Optional recurring review cadence (e.g., every 7 days, every 30 days)
- **ADDED** `last_reviewed_at`: Track when user last reviewed the goal
- **ADDED** `motivation` field: Why this goal matters (growth mindset reinforcement)
- **ADDED** Goal review workflow: Prompt users to reflect on progress and adjust commitments
- **MODIFIED** Goal status: Add `on_hold` status for goals temporarily paused
- **ADDED** Commitment progress summary on goal view

### Philosophy Clarification

| Concept | Purpose | Enforces |
|---------|---------|----------|
| **Commitment** | What you promised, to whom, by when | Integrity, self-trust, action |
| **Goal** | Where you're heading, why it matters | Vision, direction, growth mindset |

Goals answer: *"What future am I working toward?"*
Commitments answer: *"What specific promise am I keeping today?"*

## Impact

- Affected specs:
  - `goal` (MODIFIED - review-focused fields, new status)
- Affected code:
  - `src/jdo/models/goal.py` — Field changes
  - `src/jdo/persistence/` — Schema migration
  - TUI/commands — Review workflow, progress display
- Dependencies:
  - Modifies `add-core-domain-models` goal capability
  - Integrates with `add-conversational-tui` for review prompts
