# Change: Add Core Domain Models for Commitment-Driven Todo Application

## Why

JDO currently lacks domain models. Users need a system that tracks **commitments**—clear agreements with stakeholders about delivering something by a specific time. Unlike typical todo apps that focus on tasks, JDO centers on accountability: "What (deliverable) to who (stakeholder) by when (due date)." This fundamental shift requires purpose-built Pydantic models for Commitments, Goals, Tasks, and Stakeholders, plus a text-focused TUI for creation and viewing.

## What Changes

- **ADDED** `Stakeholder` model: Entity representing who the user made the commitment to (person, team, self, etc.)
- **ADDED** `Commitment` model: Core entity answering "what to who by when" with required deliverable, stakeholder, and due date/datetime (EST default timezone)
- **ADDED** `Goal` model: Parent container for commitments with problem statement and solution vision; supports nesting
- **ADDED** `Task` model: Scoped work items linked to commitments; sub-tasks stored inline (not separate objects)
- **ADDED** TUI views for creating and viewing Goals, Commitments, Tasks, and Stakeholders
- **ADDED** SQLite persistence layer (designed for future sync capability)

### Key Design Decisions

1. **Commitment-centric**: Commitments are the atomic unit of accountability, not tasks
2. **Explicit completion**: User must explicitly mark commitments complete (tasks alone don't fulfill them)
3. **Single parent**: Commitments belong to exactly one Goal (or none)
4. **Nested goals**: Goals can have parent goals for hierarchical organization
5. **Inline sub-tasks**: Sub-tasks are data within Task, not separate objects
6. **Timezone-aware**: All datetimes use EST by default, stored with timezone info

## Impact

- Affected specs: `commitment`, `goal`, `task`, `stakeholder`, `tui-views` (all new)
- Affected code:
  - `src/jdo/models/` — New Pydantic model files
  - `src/jdo/persistence/` — New SQLite repository layer
  - `src/jdo/app.py` — TUI screens and widgets
- Dependencies: None new (uses existing Pydantic, Textual, Rich)
