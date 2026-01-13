# ai-conversation Specification

## Purpose
Define the conversational AI interaction patterns for the JDO REPL, including natural language intent parsing, confirmation flows for entity creation/modification, contextual data display, conversation history management, error communication, proactive user guidance, and hybrid input handling (natural language + slash commands).
## Requirements
### Requirement: Intent-Based Interaction

The system SHALL use AI to parse user intent from natural language rather than requiring explicit commands.

#### Scenario: Create commitment from natural language
- **GIVEN** the REPL is running and awaiting input
- **WHEN** user says "I need to send the report to Sarah by Friday"
- **THEN** AI extracts: deliverable="send the report", stakeholder="Sarah", due_date=Friday
- **AND** AI proposes the commitment for confirmation

#### Scenario: Create goal from natural language
- **GIVEN** the REPL is running and awaiting input
- **WHEN** user says "I want to get better at public speaking"
- **THEN** AI extracts goal details from context
- **AND** AI may ask clarifying questions if needed
- **AND** AI proposes the goal for confirmation

#### Scenario: Query from natural language
- **GIVEN** the REPL is running and awaiting input
- **WHEN** user says "what commitments do I have?" or "show my stuff"
- **THEN** AI shows relevant list(s)
- **AND** no specific command syntax required

#### Scenario: Ambiguous intent prompts clarification
- **GIVEN** the REPL is running and awaiting input
- **WHEN** user says something unclear like "add that thing"
- **THEN** AI asks for clarification
- **AND** does not make assumptions about user intent

### Requirement: Conversational Confirmation Flow

The system SHALL use natural conversation for confirmations rather than modal dialogs.

#### Scenario: AI proposes action and awaits confirmation
- **GIVEN** user has expressed intent to create/modify/delete an entity
- **WHEN** AI determines user wants to create/modify/delete an entity
- **THEN** AI displays the proposed action with details
- **AND** AI asks for confirmation (e.g., "Does this look right?")

#### Scenario: User confirms with affirmative
- **GIVEN** AI has proposed an action and is awaiting confirmation
- **WHEN** user responds with "yes", "y", "correct", "do it", etc.
- **THEN** AI executes the proposed action
- **AND** AI confirms completion

#### Scenario: User refines before confirming
- **GIVEN** AI has proposed an action and is awaiting confirmation
- **WHEN** user responds with a modification (e.g., "change the date to Monday")
- **THEN** AI updates the proposal
- **AND** AI shows updated proposal and asks for confirmation again

#### Scenario: User cancels with negative
- **GIVEN** AI has proposed an action and is awaiting confirmation
- **WHEN** user responds with "no", "n", "cancel", "never mind", etc.
- **THEN** AI cancels the pending action
- **AND** AI acknowledges cancellation
- **AND** conversation continues normally

#### Scenario: User provides unrelated input during confirmation
- **GIVEN** AI has proposed an action and is awaiting confirmation
- **WHEN** user asks something unrelated while confirmation is pending
- **THEN** AI answers the unrelated question
- **AND** confirmation state may be cleared or preserved based on context

### Requirement: Contextual Data Display

The system SHALL show relevant data at appropriate times without explicit requests.

#### Scenario: Show created entity after creation
- **GIVEN** AI has proposed an entity and user has confirmed
- **WHEN** user confirms entity creation
- **THEN** AI displays the created entity details
- **AND** AI may show related context (e.g., "You now have 5 active commitments")

#### Scenario: Show list when contextually relevant
- **GIVEN** the REPL is running
- **WHEN** user mentions viewing or checking on entities
- **THEN** AI shows the relevant list
- **AND** format is appropriate for the data type

#### Scenario: Show integrity impact
- **GIVEN** user has completed or abandoned a commitment
- **WHEN** user completes or abandons a commitment
- **THEN** AI may mention integrity score impact
- **AND** guidance is provided if score is declining

### Requirement: Conversation History Context

The system SHALL provide conversation history to AI for contextual understanding.

#### Scenario: AI references earlier conversation
- **GIVEN** user and AI have been discussing an entity
- **WHEN** user says "actually, make that for Monday instead"
- **THEN** AI understands what "that" refers to from context
- **AND** updates accordingly

#### Scenario: History pruning for long conversations
- **GIVEN** a conversation has been ongoing
- **WHEN** conversation history exceeds token budget (e.g., 8000 tokens)
- **THEN** oldest messages are pruned
- **AND** most recent context is preserved
- **AND** AI behavior remains coherent

> **Supersedes tui-chat**: The deployed `tui-chat` spec uses a 50-message limit.
> This change updates to token-based limits (8000 tokens) per research findings.
> Token-based pruning is more accurate for context window management.

#### Scenario: Entity context persists in conversation
- **GIVEN** user has created or viewed an entity in the current session
- **WHEN** user creates or views an entity
- **THEN** subsequent references like "edit it" or "delete this" resolve correctly

### Requirement: Error Communication

The system SHALL communicate errors in a user-friendly, conversational manner.

#### Scenario: Validation error
- **GIVEN** user has provided input for entity creation
- **WHEN** user input would create invalid entity (e.g., past due date)
- **THEN** AI explains the issue in natural language
- **AND** AI suggests how to fix it

#### Scenario: Database error
- **GIVEN** user has confirmed an action requiring database operation
- **WHEN** a database operation fails
- **THEN** AI explains something went wrong
- **AND** AI suggests retrying or provides guidance

#### Scenario: AI provider error
- **GIVEN** user has sent a message to AI
- **WHEN** AI provider returns an error
- **THEN** user sees a friendly message (not technical error)
- **AND** specific guidance is provided (rate limit → wait, auth → check key)

#### Scenario: AI timeout error
- **GIVEN** user has sent a message to AI
- **WHEN** AI response times out (no response within 120 seconds)
- **THEN** user sees message: "The AI took too long to respond. Please try again."
- **AND** REPL returns to prompt for retry

#### Scenario: Network connection error
- **GIVEN** user has sent a message to AI
- **WHEN** network connection to AI provider fails
- **THEN** user sees message: "Couldn't reach the AI service. Check your internet connection."
- **AND** REPL returns to prompt

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

## Requirements (Modified)

### Requirement: AI Message Handling

The system SHALL invoke the AI agent for natural language input in the REPL (slash commands bypass AI).

#### Scenario: User sends natural language in REPL
- **GIVEN** the REPL is running and awaiting input
- **WHEN** user submits text not starting with `/`
- **THEN** the message is sent to the AI agent
- **AND** AI response streams to the console

#### Scenario: AI response completes
- **GIVEN** AI is processing a user request
- **WHEN** AI agent finishes responding
- **THEN** the complete response is displayed
- **AND** the prompt reappears for next input

#### Scenario: AI uses tools to fulfill requests
- **GIVEN** AI is processing a user request
- **WHEN** AI determines a tool call is needed
- **THEN** the tool is invoked
- **AND** tool results are incorporated into AI response

### Requirement: Hybrid Input Handling

The system SHALL support both natural language and slash commands as input methods.

<!-- Research Note: Industry pattern (Aider, GitHub Copilot) uses hybrid approaches.
     OWASP LLM08 "Excessive Agency" recommends deterministic escape hatches.
     Power users prefer instant slash commands for frequent operations.
     Source: aider.chat/docs/usage/commands, OWASP Top 10 for LLMs 2025 -->

#### Scenario: Natural language input (primary)
- **GIVEN** the REPL is running and awaiting input
- **WHEN** user enters text not starting with `/`
- **THEN** input is sent to AI agent for intent parsing
- **AND** AI determines appropriate tool call

#### Scenario: Slash command input (escape hatch)
- **GIVEN** the REPL is running and awaiting input
- **WHEN** user enters text starting with `/`
- **THEN** input is parsed as a slash command
- **AND** corresponding handler is invoked directly (no AI)
- **AND** response is instant (no AI latency)

#### Scenario: Both paths use same handlers
- **GIVEN** the system has handlers for entity operations
- **WHEN** either natural language or slash command triggers an action
- **THEN** the same underlying handler is invoked
- **AND** the same validation and business logic applies

#### Supported Slash Commands
- `/commit [text]` - Create commitment with optional description
- `/list [type]` - List entities (commitments, goals, tasks)
- `/complete [id]` - Mark entity complete
- `/help` - Show available commands

## Requirements (Retained)

### Requirement: Slash Command Parsing
**Original reason for removal**: All interaction was to be via natural language.
**Research finding**: Hybrid approach is industry best practice; deterministic fallback reduces risk.
**New status**: RETAINED with reduced scope. Basic CRUD commands available as power-user shortcuts.

### Requirement: Command Type Enumeration
**Status**: Reduced in scope but not removed.
**Rationale**: Limited set of common commands; AI handles complex/ambiguous requests.
