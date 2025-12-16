# Capability: Commitment Management (Recurring Commitments Extension)

This spec extends the base Commitment model from `add-core-domain-models` to add recurring commitment linkage.

**Cross-reference**: See `add-core-domain-models/specs/commitment` for the base Commitment model definition. See `add-integrity-protocol/specs/commitment` for `at_risk` status extension.

## MODIFIED Requirements

### Requirement: Commitment Model

The system SHALL extend the Commitment model with the following field:

**Field Addition**:
- `recurring_commitment_id` (UUID | None): Optional reference to parent RecurringCommitment template

#### Scenario: Create commitment from recurring template
- **WHEN** system generates a Commitment from a RecurringCommitment
- **THEN** the Commitment has recurring_commitment_id set to the template's id

## ADDED Requirements

### Requirement: Recurring Instance Linking

The system SHALL support linking Commitment instances to their RecurringCommitment template.

#### Scenario: Query instances by recurring template
- **WHEN** user queries commitments with recurring_commitment_id filter
- **THEN** the system returns all instances generated from that template

#### Scenario: Instance remains after template deletion
- **WHEN** a RecurringCommitment is deleted
- **THEN** existing Commitment instances retain their data and recurring_commitment_id is set to NULL (ON DELETE SET NULL)

#### Scenario: Trigger next generation on completion
- **WHEN** user completes a Commitment that has a recurring_commitment_id
- **THEN** the system checks whether to generate the next instance from the template
