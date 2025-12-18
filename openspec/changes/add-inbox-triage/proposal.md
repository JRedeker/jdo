# Change: Add Inbox Capture and Triage System

## Why

Users need a way to quickly capture ideas, tasks, and commitments from external contexts (scripts, shell aliases, iOS Shortcuts, webhooks) without launching the full TUI. Currently, creating any object requires interactive TUI use with explicit type selection. This friction causes users to lose ideas or defer capture until they forget.

Additionally, when users enter vague descriptions in chat without specifying object type, the system has no graceful fallback - it either guesses wrong or fails to act.

## What Changes

### New Capability: `inbox`

- **CLI capture command**: `jdo capture "text"` stores raw text for later triage
- **Triage workflow**: AI-assisted classification of captured items into proper object types
- **Triage command**: `/triage` starts guided processing of inbox items

### Modified Capabilities

- **data-persistence**: Add `UNKNOWN` to `EntityType` enum for unclassified items
- **tui-chat**: Add `/triage` command, handle vague chat input by creating triage items
- **jdo-app**: Add home screen triage indicator with count and `t` key binding

## Impact

- Affected specs: `data-persistence` (modified), `tui-chat` (modified), `jdo-app` (modified), `inbox` (new)
- Affected code:
  - `src/jdo/models/draft.py` - EntityType enum
  - `src/jdo/db/session.py` - triage query helper
  - `src/jdo/cli.py` - new capture CLI
  - `src/jdo/commands/triage.py` - triage handler
  - `src/jdo/ai/triage.py` - AI classification
  - `src/jdo/screens/home.py` - triage indicator
  - `src/jdo/screens/chat.py` - message handling
  - `pyproject.toml` - CLI entry point
- Breaking changes: None - all additions are backwards compatible
