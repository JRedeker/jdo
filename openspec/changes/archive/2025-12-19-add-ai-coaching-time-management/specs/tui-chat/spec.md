# Capability: TUI Chat (Delta)

## ADDED Requirements

### Requirement: Time Estimation Prompt Flow

The system SHALL prompt users for time estimates when creating tasks through the chat interface.

#### Scenario: Prompt for estimate during task creation
- **WHEN** AI proposes a task creation draft
- **THEN** the draft includes an estimate field with prompt: "Estimated time (hours):"

#### Scenario: Accept estimate in natural language
- **WHEN** user says "about 2 hours" or "30 minutes" or "half a day"
- **THEN** the system parses and converts to 15-minute increments (2.0, 0.5, 4.0 respectively)
- **AND** ambiguous values are rounded up (e.g., "20 minutes" → 0.5 hours)

#### Scenario: Allow skip estimate
- **WHEN** user declines to provide estimate (says "skip" or "not sure")
- **THEN** task is created with estimated_hours=None and AI notes: "No estimate provided. Consider adding one later for better workload planning."

#### Scenario: Show estimate in task draft panel
- **WHEN** task draft is displayed in data panel
- **THEN** estimated hours and confidence are shown if provided

### Requirement: Actual Hours Recording Flow

The system SHALL prompt for actual hours category when completing tasks that have estimates, using a 5-point picker.

#### Scenario: Prompt on task completion with 5-point picker
- **WHEN** user marks a task as completed
- **AND** task has estimated_hours set
- **THEN** system displays 5-point picker: "[Much Shorter] [Shorter] [On Target] [Longer] [Much Longer]"
- **AND** picker shows estimate for context: "(estimated: X hours)"

#### Scenario: 5-point picker thresholds displayed
- **WHEN** 5-point picker is shown
- **THEN** labels correspond to variance ranges:
  - Much Shorter = took <50% of estimate
  - Shorter = took 50-85% of estimate
  - On Target = took 85-115% of estimate
  - Longer = took 115-150% of estimate
  - Much Longer = took >150% of estimate

#### Scenario: Skip actual hours recording
- **WHEN** user presses Escape or skip action on 5-point picker
- **THEN** task is completed with actual_hours_category=None

#### Scenario: Keyboard navigation for picker
- **WHEN** 5-point picker is displayed
- **THEN** user can select with arrow keys and Enter, or press 1-5 for quick selection

### Requirement: Available Hours Command

The system SHALL support setting remaining available hours through chat.

#### Scenario: Set hours via command
- **WHEN** user types "/hours 6" or "/available 6"
- **THEN** available_hours_remaining is set to 6.0 and AI confirms: "Got it, you have 6 hours remaining today."

#### Scenario: Set hours via natural language
- **WHEN** user says "I have 4 hours left" or "I can work 5 more hours"
- **THEN** AI parses and sets available_hours_remaining accordingly

#### Scenario: Query current hours
- **WHEN** user types "/hours" with no argument
- **THEN** system displays current available_hours_remaining and hours_allocated

#### Scenario: Update hours mid-session
- **WHEN** user provides new hours value during session
- **THEN** available_hours_remaining is updated (not cumulative, replaces previous value)
- **AND** AI does NOT proactively re-ask for hours updates

### Requirement: Workload Summary Display

The system SHALL display workload summary in the data panel when viewing commitments.

#### Scenario: Show time rollup in commitment view
- **WHEN** viewing a commitment in the data panel
- **THEN** display includes: "Time: X hours estimated (Y remaining)"

#### Scenario: Show task estimates in list
- **WHEN** viewing task list for a commitment
- **THEN** each task shows its estimated_hours if set

#### Scenario: Color code overdue time math
- **WHEN** commitment remaining_hours / days_until_due exceeds available_hours_today
- **THEN** time display is shown in warning color

### Requirement: Integrity Command Enhancement

The system SHALL enhance the /integrity command to show estimation accuracy.

#### Scenario: Show estimation accuracy in integrity view
- **WHEN** user types "/integrity"
- **THEN** display includes: "Estimation Accuracy: X%" alongside other metrics

#### Scenario: Show estimation trend
- **WHEN** viewing integrity metrics
- **AND** user has task history
- **THEN** display includes trend: "Tends to underestimate by X%" or "Accurate estimator"

### Requirement: Integrity Always Visible

The system SHALL display integrity grade prominently on the home screen.

#### Scenario: Integrity grade on home screen
- **WHEN** user views the home screen
- **THEN** current integrity letter grade is displayed prominently (e.g., "Integrity: A-")

#### Scenario: Integrity grade color coding
- **WHEN** integrity grade is displayed
- **THEN** grade is color-coded: A-range = green, B-range = blue, C-range = yellow, D/F = red

### Requirement: Time-Aware Risk Warning

The system SHALL enhance risk warnings with time-based analysis.

#### Scenario: Time-based risk in startup warning
- **WHEN** app detects risks on startup
- **AND** a commitment has remaining hours exceeding available time
- **THEN** warning includes: "Commitment X needs Y hours but only Z hours remain before due date"

#### Scenario: Daily capacity warning
- **WHEN** user's allocated hours exceed available hours
- **THEN** home screen shows warning: "Over-committed today: X hours allocated, Y hours available"
