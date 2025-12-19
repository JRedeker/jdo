# app-config Spec Delta

## ADDED Requirements

### Requirement: Commitment Threshold Configuration

The system SHALL support a configurable threshold for active commitment warnings.

#### Scenario: Load default threshold
- **WHEN** application starts without `JDO_MAX_ACTIVE_COMMITMENTS` set
- **THEN** `JDOSettings.max_active_commitments` defaults to 7

#### Scenario: Override threshold via environment variable
- **WHEN** environment variable `JDO_MAX_ACTIVE_COMMITMENTS=5` is set
- **THEN** `JDOSettings.max_active_commitments` equals 5

#### Scenario: Override threshold via .env file
- **WHEN** `.env` file contains `JDO_MAX_ACTIVE_COMMITMENTS=10`
- **THEN** `JDOSettings.max_active_commitments` equals 10

#### Scenario: Validate threshold is positive integer
- **WHEN** `JDO_MAX_ACTIVE_COMMITMENTS=0` is set
- **THEN** settings validation raises a ValueError with message "max_active_commitments must be at least 1"

#### Scenario: Non-integer threshold uses Pydantic type validation
- **WHEN** `JDO_MAX_ACTIVE_COMMITMENTS=abc` is set
- **THEN** Pydantic's built-in int validator raises a validation error

#### Scenario: Negative threshold rejected
- **WHEN** `JDO_MAX_ACTIVE_COMMITMENTS=-5` is set
- **THEN** settings validation raises a ValueError with message "max_active_commitments must be at least 1"
