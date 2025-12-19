# inbox Specification Delta

## ADDED Requirements

### Requirement: Triage Workflow

The system SHALL provide triage access via NavSidebar with badge indicator.

#### Scenario: Triage available from sidebar
- **WHEN** user selects "Triage" from NavSidebar with items needing triage
- **THEN** the system starts triage mode in the chat area

#### Scenario: Triage badge shows count
- **WHEN** items need triage
- **THEN** NavSidebar shows badge with count on Triage item
