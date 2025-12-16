# Capability: TUI Chat Interface (Integrity Protocol Extension)

This spec extends the TUI chat interface from `add-conversational-tui` to add integrity commands, home screen integrity display, and AI risk detection.

**Cross-reference**: See `add-conversational-tui/specs/tui-chat` for the base TUI specification.

**Implementation Notes** (Textual-specific):
- Integrity grade in header: Extend `Header` or add custom widget docked to top-right
- At-risk styling: Use Textual CSS with warning color class (e.g., `.at-risk { color: $warning; }`)
- AI risk detection: Check on `on_mount()` of main screen, display via system message in chat
- 'i' and 'r' bindings: Add to appropriate widget BINDINGS with `show=True` for footer display

## ADDED Requirements

### Requirement: Command - Mark At-Risk

The system SHALL support the `/atrisk` command to mark a commitment as at-risk and start the notification workflow.

#### Scenario: Mark commitment at-risk
- **WHEN** user types `/atrisk` while viewing a commitment
- **THEN** AI prompts for reason: "Why might you miss this commitment?"

#### Scenario: Gather at-risk details
- **WHEN** user provides reason for at-risk
- **THEN** AI prompts: "What impact will missing this have on [stakeholder]?" and "Can you propose a new deadline or alternative?"

#### Scenario: Create notification task with draft
- **WHEN** user completes at-risk workflow
- **THEN** system creates notification task at position 0 with AI-drafted message containing:
  - Stakeholder name and contact info (if available)
  - Commitment deliverable and original due date
  - User's reason for risk
  - Impact description
  - Proposed resolution
- **AND** AI says: "I've created a task to notify [stakeholder]. Please send the notification and mark the task complete."

#### Scenario: At-risk without commitment context
- **WHEN** user types `/atrisk` without an active commitment
- **THEN** AI prompts: "Which commitment is at risk?" and shows list of active commitments

#### Scenario: Already at-risk commitment
- **WHEN** user types `/atrisk` on a commitment that is already at_risk
- **THEN** AI responds: "This commitment is already marked at-risk. Would you like to view the cleanup plan?"

### Requirement: Command - Cleanup Plan

The system SHALL support the `/cleanup` command to view or update a commitment's cleanup plan.

#### Scenario: View cleanup plan
- **WHEN** user types `/cleanup` while viewing an at-risk or abandoned commitment
- **THEN** the data panel shows CleanupPlan details: impact, mitigation actions, notification status, plan status

#### Scenario: Update cleanup plan
- **WHEN** user types `/cleanup` and provides updates in conversation
- **THEN** AI extracts updates to impact_description or mitigation_actions and updates the CleanupPlan

#### Scenario: No cleanup plan exists
- **WHEN** user types `/cleanup` on a commitment without a CleanupPlan
- **THEN** AI responds: "This commitment doesn't have a cleanup plan. Would you like to mark it as at-risk?"

#### Scenario: Add mitigation action
- **WHEN** user describes a mitigation action during cleanup conversation
- **THEN** AI adds it to the mitigation_actions list and confirms

### Requirement: Command - Integrity Dashboard

The system SHALL support the `/integrity` command to show the integrity dashboard.

#### Scenario: Show integrity dashboard
- **WHEN** user types `/integrity`
- **THEN** the data panel displays:
  - Overall letter grade (large, prominent)
  - On-time delivery rate with percentage
  - Notification timeliness rating
  - Cleanup completion rate with percentage
  - Current reliability streak
  - Recent events affecting score

#### Scenario: Integrity dashboard breakdown
- **WHEN** viewing integrity dashboard
- **THEN** user can see how each metric contributes to the overall grade

#### Scenario: Empty integrity history
- **WHEN** user types `/integrity` with no commitment history
- **THEN** the dashboard shows "A+" with message: "You're starting with a clean slate. Keep your commitments to maintain your integrity score."

### Requirement: Home Screen Integrity Display

The system SHALL display the integrity grade on the home screen.

#### Scenario: Display integrity grade on home
- **WHEN** user views the home screen
- **THEN** the integrity letter grade is displayed in the header area (e.g., "Integrity: A-")

#### Scenario: Integrity grade styling
- **WHEN** displaying integrity grade
- **THEN** grade is color-coded: A grades (green), B grades (blue), C grades (yellow), D/F grades (red)

#### Scenario: Tap integrity for details
- **WHEN** user presses 'i' on home screen
- **THEN** the integrity dashboard is shown in the data panel

### Requirement: AI Risk Detection on Launch

The system SHALL proactively check for at-risk commitments when the application launches.

#### Scenario: Detect overdue commitments
- **WHEN** application launches and there are commitments with due_date < today and status in (pending, in_progress)
- **THEN** AI alerts: "You have [N] overdue commitment(s). Would you like to address them?"

#### Scenario: Detect commitments due soon with no progress
- **WHEN** application launches and there are commitments due within 24 hours with status="pending"
- **THEN** AI alerts: "[Commitment] is due in [hours] hours and hasn't been started. Are you on track?"

#### Scenario: Detect stalled commitments
- **WHEN** application launches and there are commitments due within 48 hours with status="in_progress" and no task activity in 24 hours
- **THEN** AI asks: "[Commitment] is due soon. How is progress going?"

#### Scenario: Multiple risks detected
- **WHEN** multiple commitments are detected as at-risk on launch
- **THEN** AI summarizes: "[N] commitments need attention" and lists them with due dates

#### Scenario: Dismiss risk warning
- **WHEN** user responds "I'm on track" or dismisses the warning
- **THEN** AI acknowledges and doesn't repeat the warning for that commitment during the session

#### Scenario: Accept risk suggestion
- **WHEN** user responds "no" or indicates they may miss the commitment
- **THEN** AI offers: "Would you like to mark it as at-risk and notify [stakeholder]?"

### Requirement: At-Risk Visual Indicators

The system SHALL provide clear visual distinction for at-risk commitments.

#### Scenario: At-risk status indicator
- **WHEN** displaying a commitment with status="at_risk"
- **THEN** the status shows with warning styling (e.g., yellow/orange color, warning icon)

#### Scenario: At-risk in commitment list
- **WHEN** listing commitments
- **THEN** at-risk commitments are visually distinct and sorted after overdue but before pending

#### Scenario: Notification task indicator
- **WHEN** displaying a notification task (is_notification_task=True)
- **THEN** the task has distinct styling (e.g., bell icon) indicating it's a notification

### Requirement: Keyboard Navigation (Extended)

The system SHALL add keyboard shortcuts for integrity features.

#### Scenario: Quick access integrity
- **WHEN** user presses 'i' on home screen
- **THEN** the integrity dashboard is displayed in the data panel

#### Scenario: Mark at-risk shortcut
- **WHEN** user presses 'r' while viewing a commitment
- **THEN** the at-risk workflow begins (equivalent to `/atrisk`)

### Requirement: Footer Shortcuts (Extended)

The system SHALL update the footer to show new shortcuts.

#### Scenario: Home screen footer includes integrity
- **WHEN** viewing home screen
- **THEN** footer includes: i:integrity alongside existing shortcuts

#### Scenario: Commitment view footer includes at-risk
- **WHEN** viewing a commitment that is not already at_risk
- **THEN** footer includes: r:at-risk alongside existing shortcuts
