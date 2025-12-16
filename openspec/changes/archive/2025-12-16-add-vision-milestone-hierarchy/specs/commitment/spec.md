# Capability: Commitment Management (Milestone Hierarchy Extension)

This spec extends the base Commitment model from `add-core-domain-models` to add Milestone linkage.

**Cross-reference**: See `add-core-domain-models/specs/commitment` for the base Commitment model definition.

## ADDED Requirements

### Requirement: Commitment-Milestone Association

The system SHALL support optional association between a Commitment and a Milestone.

**Field Addition**:
- `milestone_id` (UUID | None): Optional reference to parent Milestone

#### Scenario: Create commitment linked to milestone
- **WHEN** user creates a Commitment with milestone_id referencing an existing Milestone
- **THEN** the Commitment is associated with that Milestone

#### Scenario: Create commitment without milestone
- **WHEN** user creates a Commitment without specifying milestone_id
- **THEN** the Commitment exists independently without a parent Milestone

#### Scenario: Query commitments for milestone
- **WHEN** user queries for commitments linked to a specific Milestone
- **THEN** the system returns all Commitments with milestone_id matching the Milestone's id

#### Scenario: Validate milestone exists
- **WHEN** user creates a Commitment with a milestone_id that doesn't exist
- **THEN** the system raises a foreign key validation error

### Requirement: Flexible Commitment Linkage

The system SHALL support commitments linked through either Goal or Milestone (or both, or neither).

#### Scenario: Commitment with milestone only
- **WHEN** user creates a Commitment with milestone_id but no goal_id
- **THEN** the Commitment is valid and inherits Goal context through the Milestone's goal_id

#### Scenario: Commitment with goal only
- **WHEN** user creates a Commitment with goal_id but no milestone_id
- **THEN** the Commitment is valid and directly linked to the Goal (simpler case)

#### Scenario: Commitment with both
- **WHEN** user creates a Commitment with both milestone_id and goal_id
- **THEN** the Commitment is valid (goal_id should match milestone's goal_id for consistency)

#### Scenario: Commitment with neither (orphan)
- **WHEN** user creates a Commitment with neither milestone_id nor goal_id
- **THEN** the Commitment is valid but surfaced in orphan tracking

### Requirement: Orphan Commitment Tracking (Extended)

The system SHALL track commitments not linked to goals OR milestones.

#### Scenario: Orphan definition
- **WHEN** determining if a commitment is an orphan
- **THEN** a commitment is orphan if BOTH goal_id IS NULL AND milestone_id IS NULL

#### Scenario: Partial linkage is not orphan
- **WHEN** a commitment has milestone_id but no goal_id
- **THEN** it is NOT considered orphan (it has hierarchy linkage through milestone)

#### Scenario: Display orphan status
- **WHEN** viewing an orphan commitment
- **THEN** the data panel shows an indicator that it's not linked to goals or milestones

### Requirement: Commitment Deletion with Milestone Link

The system SHALL handle commitment deletion consistently regardless of milestone linkage.

#### Scenario: Delete commitment with milestone link
- **WHEN** user deletes a Commitment that has a milestone_id
- **THEN** the Commitment and all associated Tasks are removed from the database
- **AND** the Milestone's commitment count is decremented

### Requirement: Milestone Progress via Commitments

The system SHALL calculate Milestone progress based on its linked Commitments.

#### Scenario: Commitment completion affects milestone
- **WHEN** a Commitment linked to a Milestone is marked completed
- **THEN** the Milestone's progress (X of Y commitments) is updated

#### Scenario: Milestone progress query
- **WHEN** viewing a Milestone
- **THEN** the system shows: "Commitments: X completed, Y in progress, Z pending"

### Requirement: AI Commitment Linking

The system SHALL guide users to link commitments appropriately.

#### Scenario: Prompt for milestone linkage
- **WHEN** AI creates a commitment draft and the selected goal has milestones
- **THEN** AI asks: "Which milestone is this commitment working toward?" and shows available milestones

#### Scenario: Prompt for goal linkage when no milestones
- **WHEN** AI creates a commitment draft and the selected goal has no milestones
- **THEN** AI links directly to the goal without asking about milestones

#### Scenario: Suggest creating milestone
- **WHEN** user creates multiple commitments for a goal without milestones
- **THEN** AI suggests: "You have several commitments for this goal. Would you like to organize them into milestones?"
