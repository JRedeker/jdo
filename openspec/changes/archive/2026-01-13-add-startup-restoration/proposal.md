# Change: Add vision review prompts on startup

## Why

Users with visions due for quarterly review (`next_review_date <= today`) should be reminded at startup. This encourages engagement with long-term planning without being intrusive.

## What Changes

**Vision review notices on startup**: When a vision's `next_review_date <= today` and it hasn't been snoozed this session, show a non-blocking notice with option to review.

This integrates into the existing `_show_startup_guidance()` flow in the REPL loop.

## Research Validation

- **Session-only snooze**: Validated as correct pattern. Vision reviews should resurface next session if declined.
- **Non-blocking notices**: CLI UX best practices recommend notices over blocking prompts at startup.
- **Draft persistence removed**: Adds complexity (new model, migration, save-on-exit) for an edge case. Existing in-memory `PendingDraft` loss on exit is acceptable.

## Impact

- Affected specs: `ai-conversation` (MODIFIED: Proactive Guidance requirement)
- Supersedes: `vision` spec scenario "Prompt for vision review" (line 86-88) - changes from interactive AI prompt to non-blocking CLI notice
- Affected code:
  - `src/jdo/repl/session.py` - Add `snoozed_vision_ids: set[UUID]`
  - `src/jdo/repl/loop.py` - Extend `_show_startup_guidance()` with vision review notice
  - `src/jdo/db/session.py` - Query already exists: `get_visions_due_for_review()` (lines 51-69)
