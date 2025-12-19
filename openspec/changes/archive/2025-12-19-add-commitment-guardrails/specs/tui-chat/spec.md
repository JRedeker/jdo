# tui-chat Spec Delta

## ADDED Requirements

### Requirement: Commitment Guardrail Warnings

The system SHALL display coaching warnings when users create commitments beyond the configured threshold.

#### Scenario: No warning below threshold
- **WHEN** user confirms a commitment draft
- **AND** active commitment count is below the configured threshold
- **THEN** no guardrail warning is displayed

#### Scenario: Warning at threshold
- **WHEN** user confirms a commitment draft
- **AND** active commitment count equals or exceeds the configured threshold
- **THEN** a coaching note is appended to the confirmation message

#### Scenario: Warning includes current count
- **WHEN** guardrail warning is displayed
- **THEN** the message includes: "You have X active commitments."

#### Scenario: Warning suggests reflection
- **WHEN** guardrail warning is displayed
- **THEN** the message includes coaching: "Consider what you might need to defer or renegotiate."

#### Scenario: User can still proceed
- **WHEN** guardrail warning is displayed
- **THEN** the confirmation flow continues normally (no hard block)
- **AND** user can confirm to create the commitment

#### Scenario: Velocity warning for overcommitting
- **WHEN** user confirms a commitment draft
- **AND** commitments created > commitments completed in the past 7 days
- **THEN** an additional coaching note is displayed: "You've created X commitments this week but only completed Y. Are you overcommitting?"

#### Scenario: No velocity warning when balanced
- **WHEN** commitments created <= commitments completed in the past 7 days
- **THEN** no velocity warning is displayed

#### Scenario: Multiple warnings stack
- **WHEN** both threshold and velocity warnings apply
- **THEN** both coaching notes are displayed in the confirmation message
