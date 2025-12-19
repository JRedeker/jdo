# commitment Spec Delta

## ADDED Requirements

### Requirement: Active Commitment Count Query

The system SHALL provide efficient queries for counting active commitments.

#### Scenario: Count active commitments
- **WHEN** querying for active commitment count
- **THEN** the system returns the count of commitments with status "pending" or "in_progress"

#### Scenario: Exclude completed and abandoned
- **WHEN** counting active commitments
- **THEN** commitments with status "completed" or "abandoned" are not included

#### Scenario: Exclude at-risk from active count
- **WHEN** counting active commitments
- **THEN** commitments with status "at_risk" are included in the active count

#### Scenario: Empty database returns zero
- **WHEN** no commitments exist in the database
- **THEN** active commitment count returns 0

### Requirement: Commitment Velocity Tracking

The system SHALL track commitment creation and completion rates over time.

#### Scenario: Query commitments created in time window
- **WHEN** querying for commitments created in the last 7 days
- **THEN** the system returns the count of commitments with `created_at` within that window

#### Scenario: Query commitments completed in time window
- **WHEN** querying for commitments completed in the last 7 days
- **THEN** the system returns the count of commitments with `completed_at` within that window and status "completed"

#### Scenario: Calculate velocity ratio
- **WHEN** retrieving commitment velocity
- **THEN** the system returns a tuple of (created_count, completed_count) for the specified time window

#### Scenario: Default time window is 7 days
- **WHEN** querying velocity without specifying a time window
- **THEN** the system uses a 7-day lookback period

#### Scenario: Handle zero completed commitments
- **WHEN** no commitments were completed in the time window
- **THEN** completed_count returns 0 (not an error)
