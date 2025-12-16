# Change: Add Recurring Commitments

## Why

Many commitments repeat on a schedule—weekly reports, monthly reviews, daily standups. Currently, users must manually create each instance. A **recurring commitment** acts as a template with a schedule that automatically spawns individual commitment instances on-demand, reducing friction for regular obligations.

## What Changes

- **ADDED** `RecurringCommitment` model: Template with recurrence pattern that generates Commitment instances
- **ADDED** Recurrence patterns: daily, weekly, monthly, yearly, day-of-week, day-of-month, custom intervals
- **ADDED** End conditions: no end, after N occurrences, by specific date
- **ADDED** Task template inheritance: spawned commitments inherit tasks (reset to pending)
- **ADDED** Recurring commitment management screen in TUI
- **MODIFIED** `Commitment` model: Add optional `recurring_commitment_id` to link instances to their template

### Key Design Decisions

1. **Template model, not series**: RecurringCommitment is a template that spawns individual Commitments on-demand—no pre-generated series
2. **On-demand generation**: Next instance created when user views upcoming commitments or previous instance is completed
3. **Task inheritance**: Each spawned instance gets a fresh copy of the template's tasks (all reset to pending)
4. **Instance independence**: Spawned commitments are fully independent; edits don't affect template or other instances
5. **Separate management**: Dedicated screen for managing recurrence patterns; instances edited normally

## Impact

- Affected specs:
  - `recurring-commitment` (ADDED - new capability)
  - `commitment` (MODIFIED - add recurring_commitment_id field)
- Affected code:
  - `src/jdo/models/recurring_commitment.py` — New model
  - `src/jdo/models/commitment.py` — Add recurring_commitment_id field
  - `src/jdo/persistence/` — New repository, schema changes
  - `src/jdo/screens/` or chat commands — Recurring management UI
- Dependencies:
  - Builds on `add-core-domain-models` (Commitment, Task models)
  - Integrates with `add-conversational-tui` (commands for recurring)
