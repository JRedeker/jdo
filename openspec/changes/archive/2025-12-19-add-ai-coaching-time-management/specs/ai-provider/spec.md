# Capability: AI Provider (Delta)

## ADDED Requirements

### Requirement: AI Coaching System Prompt

The system SHALL use an enhanced system prompt that instructs the AI to act as a commitment integrity coach with proactive pushback behaviors.

#### Scenario: Coaching prompt loaded
- **WHEN** agent is created
- **THEN** the system prompt includes coaching behaviors for time management, integrity-based guidance, and estimation coaching

#### Scenario: Time-based pushback behavior
- **WHEN** system prompt is active
- **THEN** AI is instructed to ask "How many hours do you have remaining today?" and compare against task estimates
- **AND** AI understands this means hours remaining right now, not total workday hours

#### Scenario: Integrity-based coaching behavior
- **WHEN** system prompt is active
- **THEN** AI is instructed to reference user's letter grade and history when discussing new commitments

#### Scenario: Estimation coaching behavior
- **WHEN** system prompt is active
- **THEN** AI is instructed to request time estimates for every task and reference historical accuracy patterns

### Requirement: User Time Context Tool

The system SHALL provide an AI tool for querying user's daily time availability and allocation.

#### Scenario: Query time context
- **WHEN** AI calls query_user_time_context tool
- **THEN** it returns: available_hours_today, hours_allocated (sum of today's task estimates), remaining_capacity, and list of scheduled tasks

#### Scenario: No available hours set
- **WHEN** AI queries time context and user hasn't set available_hours_today
- **THEN** response indicates: "Available hours not set. Ask user: 'How many hours do you have available today?'"

#### Scenario: Over-allocated warning
- **WHEN** hours_allocated exceeds available_hours_today
- **THEN** response includes warning: "Over-committed by X hours. User has Y hours available but Z hours of tasks."

### Requirement: AI Pushback on Over-Commitment

The system SHALL enable AI to push back with suggestions (not blocking) when users attempt to take on more work than available time allows.

#### Scenario: Warn on task creation exceeding capacity
- **WHEN** user requests new task creation
- **AND** adding the task would exceed available_hours_today
- **THEN** AI warns: "This would put you at X hours for today but you only have Y hours remaining. Consider deferring something or extending the deadline."
- **AND** AI does NOT block task creation (suggestive, not blocking)

#### Scenario: Warn on commitment creation exceeding capacity
- **WHEN** user requests new commitment
- **AND** AI estimates total effort would exceed available capacity before due date
- **THEN** AI warns: "This commitment would require X hours but you have Y hours available before the due date. Is this realistic?"
- **AND** AI does NOT block commitment creation (suggestive, not blocking)

#### Scenario: Suggest deferral options
- **WHEN** AI detects over-commitment
- **THEN** AI suggests specific items that could be deferred or renegotiated
- **AND** suggestions are helpful, not demanding

#### Scenario: Reference integrity on pushback
- **WHEN** AI pushes back on over-commitment
- **AND** user's integrity grade is below B
- **THEN** AI includes: "Your current integrity grade is X. Taking on more work you can't complete will lower it further."

### Requirement: AI Estimation Coaching

The system SHALL enable AI to help users improve their time estimation skills.

#### Scenario: Request estimate for new task
- **WHEN** user creates a task via AI
- **THEN** AI asks: "How long do you think this will take?" before confirming creation

#### Scenario: Reference historical accuracy
- **WHEN** user provides an estimate
- **AND** task history shows poor estimation accuracy
- **THEN** AI responds: "Your recent estimates have been off by about X%. For similar tasks, you estimated Y hours but they took Z hours. Do you want to adjust?"
- **AND** similarity is inferred by AI from user's own task history only (title keywords, same commitment)
- **AND** AI does NOT compare across different users' data

#### Scenario: Suggest confidence level
- **WHEN** user provides an estimate for unfamiliar task type
- **THEN** AI asks: "How confident are you in that estimate? (high/medium/low)"

#### Scenario: Celebrate accurate estimation
- **WHEN** user completes a task and selects "On Target" for actual hours category
- **THEN** AI acknowledges: "Nice! Your estimate was spot on."

### Requirement: AI Session Initialization

The system SHALL prompt for available hours at the start of each chat session.

#### Scenario: First message prompts for hours
- **WHEN** user starts a new chat session
- **AND** available_hours_remaining is not set
- **THEN** AI's first response includes: "Before we dive in, how many hours do you have remaining for work today?"

#### Scenario: Remember hours within session
- **WHEN** user provides available_hours_remaining
- **THEN** the value is stored for the session and AI references it in subsequent responses

#### Scenario: Allow hours update mid-session
- **WHEN** user says "I now have X hours left" or similar
- **THEN** available_hours_remaining is updated and AI acknowledges the change
- **AND** AI does NOT proactively re-ask (user-initiated updates only)
