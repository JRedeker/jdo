# Capability: Goal Management (Vision Hierarchy Extension)

This spec extends the base Goal model from `add-core-domain-models` to add Vision linkage and Milestone support.

**Cross-reference**: 
- See `add-core-domain-models/specs/goal` for the base Goal model definition.
- See `update-goal-vision-focus/specs/goal` for review system enhancements.
- Goal progress can show both milestone-based progress (this spec) and commitment-based progress (`update-goal-vision-focus`).

## MODIFIED Requirements

### Requirement: Goal-Vision Association

The system SHALL support optional association between a Goal and a parent Vision.

**Field Addition**:
- `vision_id` (UUID | None): Optional reference to parent Vision

#### Scenario: Create goal linked to vision
- **WHEN** user creates a Goal with vision_id referencing an existing Vision
- **THEN** the Goal is associated with that Vision

#### Scenario: Create goal without vision
- **WHEN** user creates a Goal without specifying vision_id
- **THEN** the Goal exists independently without a parent Vision

#### Scenario: Query goals for vision
- **WHEN** user queries for goals linked to a specific Vision
- **THEN** the system returns all Goals with vision_id matching the Vision's id

#### Scenario: Validate vision exists
- **WHEN** user creates a Goal with a vision_id that doesn't exist
- **THEN** the system raises a foreign key validation error

#### Scenario: Prompt for vision linkage
- **WHEN** AI creates a goal draft without a vision_id and active visions exist
- **THEN** AI asks: "Would you like to link this goal to one of your visions?" and shows available visions

#### Scenario: Allow unlinked goal
- **WHEN** user declines to link goal to a vision
- **THEN** the goal is created with vision_id=NULL (allowed)

### Requirement: Goal-Milestone Relationship

The system SHALL support Milestones as children of Goals.

#### Scenario: Query milestones for goal
- **WHEN** user queries for milestones belonging to a Goal
- **THEN** the system returns all Milestones with goal_id matching the Goal's id

#### Scenario: Goal progress via milestones
- **WHEN** user views a Goal that has Milestones
- **THEN** the system displays milestone-based progress: "X of Y milestones completed"

#### Scenario: Suggest milestone creation
- **WHEN** user creates a Goal and confirms it
- **THEN** AI offers: "Would you like to break this into milestones? Milestones have concrete dates and make progress measurable."

### Requirement: Goal Deletion with Milestones

The system SHALL prevent deletion of Goals that have Milestones.

#### Scenario: Prevent deletion of goal with milestones
- **WHEN** user attempts to delete a Goal that has associated Milestones
- **THEN** the system raises an error: "Cannot delete goal with linked milestones. Delete the milestones first."

### Requirement: Goal Field Behavior with Vision

The system SHALL adjust field requirements based on Vision context.

#### Scenario: Goal with vision inherits context
- **WHEN** a Goal is linked to a Vision
- **THEN** the Goal's `problem_statement` and `solution_vision` fields remain available but are understood as goal-specific context (not the overarching vision)

#### Scenario: Standalone goal requires vision fields
- **WHEN** a Goal has no vision_id
- **THEN** the `problem_statement` and `solution_vision` fields are especially important for context

### Requirement: Vision Orphan Tracking

The system SHALL surface Goals without Vision linkage for user attention.

#### Scenario: List orphan goals
- **WHEN** user executes `/show orphan-goals`
- **THEN** the data panel shows all Goals where vision_id is NULL and status is "active"

#### Scenario: Orphan goal indicator
- **WHEN** displaying a goal without vision_id
- **THEN** an optional indicator can show it's not linked to a vision (configurable)

#### Scenario: Suggest linking orphan goals
- **WHEN** user views an orphan goal and active visions exist
- **THEN** AI may suggest: "This goal isn't connected to a vision. Would you like to link it?"
