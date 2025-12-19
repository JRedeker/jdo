# tui-views Specification Delta

## MODIFIED Requirements

### Requirement: Home Screen

The system SHALL provide a main view showing commitments due soon and quick actions via the NavSidebar.

#### Scenario: Display due soon commitments
- **WHEN** user selects "Commitments" from NavSidebar
- **THEN** commitments due within 7 days are listed, sorted by due date ascending

#### Scenario: Display overdue commitments prominently
- **WHEN** there are overdue commitments
- **THEN** they appear at the top of the commitments list with visual distinction

#### Scenario: Quick create commitment
- **WHEN** user types `/commit` in PromptInput
- **THEN** the Commitment creation flow starts

#### Scenario: Display goals due for review
- **WHEN** user selects "Goals" from NavSidebar and goals are due for review
- **THEN** a subtle indicator shows next to due goals in the list

#### Scenario: Goal review indicator is subtle
- **WHEN** goals are due for review
- **THEN** the indicator does not block or interrupt the primary view

#### Scenario: Navigate to goal review
- **WHEN** user selects a goal due for review and activates it
- **THEN** the `/goal review` flow starts

#### Scenario: Quick access goals via sidebar
- **WHEN** user presses '2' (Goals nav item) or selects "Goals" from NavSidebar
- **THEN** the data panel shows the goals list


