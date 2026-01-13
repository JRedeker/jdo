## ADDED Requirements

### Requirement: Commitment-First Coaching

The system SHALL guide users toward commitment-level thinking when they provide task-like inputs without stakeholder or deliverable context. This coaching helps users discover the meaningful promise behind their work.

<!-- Research validation: System prompt coaching is standard practice (PydanticAI, Aider patterns).
     One question at a time reduces cognitive load (clig.dev, CHI 2024, NN/g).
     Non-blocking guidance aligns with nudge theory (Blink UX, LSE research). -->

#### Scenario: Task-like input triggers coaching question
- **GIVEN** user enters input that describes work without a stakeholder or deliverable
- **WHEN** user says something like "I need to gather the sales data" or "write unit tests"
- **THEN** AI asks a single clarifying question to surface the larger commitment
- **AND** AI uses a helpful, curious tone (not lecturing)

#### Scenario: User provides commitment context in response
- **GIVEN** AI has asked a coaching question
- **WHEN** user responds with stakeholder and/or deliverable information
- **THEN** AI proposes creating a commitment with the extracted details
- **AND** AI suggests adding the original work as a task within that commitment

#### Scenario: User provides full commitment context upfront
- **GIVEN** user input includes deliverable, stakeholder, and due date
- **WHEN** user says "I need to send the quarterly report to Sarah by Friday"
- **THEN** AI proceeds directly to commitment creation (no coaching needed)

#### Scenario: User declines to provide commitment context
- **GIVEN** AI has asked a coaching question
- **WHEN** user declines or says "just add it as a task"
- **THEN** AI acknowledges the request
- **AND** AI briefly explains that tasks in JDO belong to commitments
- **AND** AI offers to help identify a parent commitment
- **AND** AI does not block the conversation

#### Scenario: User provides partial commitment context
- **GIVEN** AI has asked a coaching question
- **WHEN** user responds with stakeholder but no deliverable (e.g., "it's for Sarah")
- **THEN** AI acknowledges the stakeholder information
- **AND** AI asks ONE follow-up question about the deliverable
- **AND** AI does not ask multiple questions at once

#### Scenario: AI provider error during coaching
- **GIVEN** user enters input that would trigger coaching
- **WHEN** AI provider returns an error before completing the coaching response
- **THEN** the standard AI provider error handling applies (per ai-conversation spec)
- **AND** user can retry the input

> **Integration with inbox spec**: Commitment-First Coaching applies to *work-like* inputs
> (tasks, activities). If the user declines coaching AND the input remains truly vague
> (unclear entity type), the inbox spec's "Vague Chat Input Detection" may create a triage item.
> These behaviors are complementary: coaching surfaces commitment context; inbox handles
> unclassifiable items.

<!-- Note: "Task vs Commitment Education" and "Contextual Commitment Suggestions" are emergent
     behaviors from this coaching and existing conversation history. They do not require
     separate requirements per architectural research (2026-01-13). -->
