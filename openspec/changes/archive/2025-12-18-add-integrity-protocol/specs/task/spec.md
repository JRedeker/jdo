# Capability: Task (Integrity Protocol Extension)

This spec extends the Task model to support notification tasks for the Honor-Your-Word protocol.

**Cross-reference**: See `specs/task/spec.md` for the base Task model definition.

## ADDED Requirements

### Requirement: Notification Task Support

The system SHALL extend the Task model to support notification tasks that are auto-created when a commitment is marked at-risk.

**Field Addition to Task model**:
- `is_notification_task` (bool): Flag indicating this is an auto-created notification task; defaults to False

#### Scenario: Identify notification tasks
- **WHEN** querying tasks for a commitment
- **THEN** notification tasks can be identified by is_notification_task=True

#### Scenario: Notification task ordering preserved
- **WHEN** user reorders tasks for a commitment
- **THEN** notification tasks with is_notification_task=True remain at order=0 (cannot be moved)

#### Scenario: Notification task skip warning
- **WHEN** user attempts to mark a notification task as "skipped"
- **THEN** the system warns: "Skipping stakeholder notification affects your integrity. Are you sure?" and requires confirmation
