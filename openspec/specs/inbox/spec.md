# inbox Specification

## Purpose
Define the inbox and triage system for capturing quick thoughts and processing them into structured entities.
## Requirements
### Requirement: CLI Capture Command

The system SHALL provide a CLI command to capture raw text for later triage.

#### Scenario: Capture text from command line
- **WHEN** user runs `jdo capture "finish the quarterly report"`
- **THEN** a Draft is created with `entity_type=UNKNOWN` and `partial_data={"raw_text": "finish the quarterly report"}`
- **AND** the command prints "Captured for triage" and exits with code 0

#### Scenario: Capture empty text rejected
- **WHEN** user runs `jdo capture ""`
- **THEN** the command prints an error message and exits with code 1
- **AND** no Draft is created

#### Scenario: Capture with special characters
- **WHEN** user runs `jdo capture "meeting with Sarah @ 3pm re: budget"`
- **THEN** the text is stored exactly as provided, preserving special characters

#### Scenario: Multiple captures create separate items
- **WHEN** user runs `jdo capture "item 1"` then `jdo capture "item 2"`
- **THEN** two separate Draft records are created with sequential timestamps

### Requirement: Triage Command

The system SHALL provide a `/triage` command to process inbox items.

#### Scenario: Start triage with items
- **WHEN** user types `/triage` and there are items needing triage
- **THEN** the system displays the first item with AI analysis and action options

#### Scenario: Start triage with no items
- **WHEN** user types `/triage` and there are no items needing triage
- **THEN** the system responds "No items to triage. Your inbox is empty."

#### Scenario: Triage available from REPL
- **WHEN** user is in the REPL and says "let's triage" or types `/triage`
- **THEN** triage mode starts in the conversation

### Requirement: AI Classification

The system SHALL use AI to analyze and classify triage items.

#### Scenario: AI suggests object type
- **WHEN** a triage item is displayed
- **THEN** the AI analyzes the text and suggests: object type, confidence level, and detected entities (stakeholders, dates, potential links)

#### Scenario: High confidence suggestion
- **WHEN** AI confidence is high (>= 0.7)
- **THEN** the AI presents its suggestion directly: "This looks like a Commitment to Sarah, due Friday."

#### Scenario: Low confidence clarification
- **WHEN** AI confidence is low (< 0.7)
- **THEN** the AI asks a simple clarifying question: "Is this something you need to do, or a goal you want to achieve?"

#### Scenario: Entity detection
- **WHEN** AI analyzes "finish report for Sarah by Friday"
- **THEN** it detects: stakeholder "Sarah" (matches existing if present), due date "Friday", and suggests linking opportunities

### Requirement: Triage Actions

The system SHALL support user actions during triage.

#### Scenario: Accept suggestion
- **WHEN** user selects "Accept" (or presses 1)
- **THEN** the Draft's `entity_type` is updated to the suggested type
- **AND** the normal creation flow begins with pre-filled fields from AI extraction

#### Scenario: Change type
- **WHEN** user selects "Change type" (or presses 2)
- **THEN** the system prompts: "What type? [c]ommitment, [g]oal, [t]ask, [v]ision, [m]ilestone"
- **AND** user selection updates the Draft and proceeds to creation flow

#### Scenario: Delete item
- **WHEN** user selects "Delete" (or presses 3)
- **THEN** the Draft is permanently deleted
- **AND** the system proceeds to the next triage item

#### Scenario: Skip item
- **WHEN** user selects "Skip" (or presses 4)
- **THEN** the system proceeds to the next item
- **AND** the skipped item remains at the front of the queue for next triage session

### Requirement: Triage Queue Management

The system SHALL manage the triage queue with FIFO ordering.

#### Scenario: FIFO ordering
- **WHEN** multiple items need triage
- **THEN** they are presented in order of capture (oldest first)

#### Scenario: Queue persists across sessions
- **WHEN** user exits triage before completing all items
- **THEN** remaining items stay in the queue for the next session

#### Scenario: Partial progress saved
- **WHEN** user accepts a type but exits before completing creation
- **THEN** the item becomes a normal Draft with the confirmed `entity_type`
- **AND** it is removed from the triage queue (no longer UNKNOWN)

#### Scenario: Triage completion
- **WHEN** user processes the last item in the queue
- **THEN** the system displays "Triage complete! All items processed."

### Requirement: Vague Chat Input Detection

The system SHALL detect vague input in chat and offer triage.

#### Scenario: Unclassifiable input creates triage item
- **WHEN** user enters "remember to call mom" in chat (no command, unclear type)
- **AND** AI cannot determine object type with confidence
- **THEN** a Draft with `entity_type=UNKNOWN` is created
- **AND** AI responds: "I'm not sure what type of item this should be. I've added it to your triage queue. Would you like to triage it now?"

#### Scenario: User accepts immediate triage
- **WHEN** user responds "yes" to the triage offer
- **THEN** the system starts triage mode with the new item first

#### Scenario: User defers triage
- **WHEN** user responds "no" or continues with other input
- **THEN** the item remains in the triage queue
- **AND** the conversation continues normally

#### Scenario: Clear intent proceeds normally
- **WHEN** user enters text with clear intent (e.g., "I need to send the report to Sarah by Friday")
- **THEN** AI proceeds with normal creation flow (e.g., suggests `/commit`)
- **AND** no triage item is created

### Requirement: Triage Notifications

The system SHALL notify users of pending triage items.

#### Scenario: Triage reminder on startup
- **WHEN** user starts the REPL and items need triage
- **THEN** a message shows the triage count (e.g., "You have 3 items to triage")

