## MODIFIED Requirements

### Requirement: Proactive Guidance

The system SHALL provide helpful guidance at appropriate moments.

#### Scenario: First-run guidance
- **GIVEN** the database has no entities
- **WHEN** user starts JDO with no data
- **THEN** AI provides brief intro: "I'm JDO, your commitment assistant. Tell me what you need to do and I'll help you track it."

#### Scenario: At-risk commitment notification
- **GIVEN** user has overdue or soon-due commitments in the database
- **WHEN** user has overdue or soon-due commitments
- **THEN** AI may mention them at session start
- **AND** offers to help address them

#### Scenario: Triage reminder
- **GIVEN** user starts a new REPL session
- **WHEN** user has items in triage queue
- **THEN** AI may mention them
- **AND** offers to process them

#### Scenario: Session returning user
- **GIVEN** user has used JDO before
- **WHEN** user starts a new REPL session
- **THEN** AI may provide a brief status summary (e.g., "You have 3 active commitments, 1 due tomorrow")
- **AND** AI asks how it can help

#### Scenario: Vision review notice
- **GIVEN** user has a Vision with next_review_date <= today
- **AND** the vision has not been snoozed this session
- **WHEN** user starts a new REPL session
- **THEN** the system displays a non-blocking notice: "Your vision '[title]' is due for review. Type /review to reflect on it."
- **AND** the REPL prompt appears immediately (no blocking)

#### Scenario: Vision review snooze
- **GIVEN** user sees a vision review notice
- **WHEN** user continues without typing /review
- **THEN** the vision is marked as snoozed for this session only
- **AND** the notice will appear again on next REPL session

#### Scenario: Multiple visions due for review
- **GIVEN** user has multiple Visions with next_review_date <= today
- **WHEN** user starts a new REPL session
- **THEN** the system shows a consolidated notice: "You have N visions due for review. Type /review to start."

#### Scenario: No visions due for review
- **GIVEN** user has Visions but all have next_review_date > today
- **WHEN** user starts a new REPL session
- **THEN** no vision review notice is displayed
- **AND** other startup guidance (at-risk commitments, triage) still appears normally

#### Scenario: Vision query error during startup
- **GIVEN** user starts a new REPL session
- **WHEN** the database query for due visions fails
- **THEN** the error is logged but does not block startup
- **AND** the REPL prompt appears normally
- **AND** other startup guidance still displays

> **Supersedes vision spec**: The deployed `vision` spec (line 86-88) says AI prompts interactively: "Would you like to reflect on it now?"
> This change updates to a non-blocking notice pattern: "Type /review to reflect on it."
> Non-blocking notices are CLI UX best practice per research findings.

> **Note**: Logging/observability - Vision review notice display is logged at DEBUG level for troubleshooting.
> Security/config concerns are N/A for this change (no new auth or config options).
