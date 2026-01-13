## MODIFIED Requirements

### Requirement: Commitment Summary Panel (Enhanced)

The system SHALL provide a multi-line commitment panel showing up to 5 upcoming commitments with status indicators.

#### Scenario: Display commitments panel with multiple items
- **GIVEN** user has active commitments
- **WHEN** dashboard is rendered
- **THEN** panel shows up to 5 commitments ordered by due date (soonest first)
- **AND** panel has fixed width of 100 characters
- **AND** panel title shows "📋 Commitments (N active, M at-risk)" format

#### Scenario: Commitment row formatting with fixed columns
- **GIVEN** a commitment is displayed in the panel
- **WHEN** row is rendered
- **THEN** row uses fixed-width columns for consistent alignment:
  - Column 1: Status emoji (4 chars) - 🔴 overdue, 🟡 at-risk, 🔵 in-progress, ⚪ pending
  - Column 2: Deliverable (40 chars, left-aligned, truncate with ...)
  - Column 3: Stakeholder (20 chars, left-aligned)
  - Column 4: Due date/time (20 chars, right-aligned)
- **AND** columns are separated by consistent spacing (4 chars, 8 chars)

#### Scenario: Overdue commitment highlighting
- **GIVEN** a commitment is past its due date
- **WHEN** displayed in panel
- **THEN** status icon is 🔴
- **AND** due column shows "OVERDUE (Xd)" in red styling

#### Scenario: At-risk commitment highlighting
- **GIVEN** a commitment has at_risk status
- **WHEN** displayed in panel
- **THEN** status icon is 🟡
- **AND** row uses yellow styling for emphasis

## ADDED Requirements

### Requirement: Goals Progress Panel

The system SHALL provide a goals panel showing active goals with visual progress indicators.

#### Scenario: Display goals panel
- **GIVEN** user has active goals
- **WHEN** dashboard is rendered in full mode
- **THEN** panel shows active goals with progress bars
- **AND** panel has fixed width of 100 characters
- **AND** panel title shows "🎯 Goals (N active)" format

#### Scenario: Goal row with fixed columns
- **GIVEN** a goal is displayed in the panel
- **WHEN** row is rendered
- **THEN** row uses fixed-width columns for consistent alignment:
  - Column 1: Title (40 chars, left-aligned, truncate with ...)
  - Column 2: Progress bar (20 chars, using █ and ░ characters)
  - Column 3: Percentage (6 chars, right-aligned, e.g., "  80%")
  - Column 4: Status (18 chars, right-aligned, e.g., "3/4 done", "review ⚠")
- **AND** columns are separated by consistent spacing

#### Scenario: Progress bar coloring
- **GIVEN** goal progress is being rendered
- **WHEN** progress bar is displayed
- **THEN** bar uses green style for >= 80% progress
- **AND** bar uses yellow style for 50-79% progress
- **AND** bar uses red style for < 50% progress

#### Scenario: Goal needing review indicator
- **GIVEN** a goal is due for review
- **WHEN** displayed in panel
- **THEN** status text shows "review due" instead of completion fraction

### Requirement: Status Bar Panel

The system SHALL provide a compact status bar showing integrity, streak, and triage information.

#### Scenario: Display status bar with fixed columns
- **GIVEN** dashboard is being rendered
- **WHEN** status bar is displayed
- **THEN** bar uses 3 fixed-width sections of 32 chars each separated by │:
  - Section 1: Integrity with grade, score, trend arrow (📊)
  - Section 2: Streak in weeks (🔥)
  - Section 3: Triage count (📥)
- **AND** bar has fixed width of 100 characters
- **AND** sections are evenly spaced within the 96-char content area

#### Scenario: Integrity grade coloring
- **GIVEN** integrity grade is displayed
- **WHEN** grade is rendered
- **THEN** A grades use green styling
- **AND** B grades use blue styling
- **AND** C grades use yellow styling
- **AND** D and F grades use red styling

#### Scenario: Trend arrow display
- **GIVEN** integrity trend is available
- **WHEN** displayed in status bar
- **THEN** improving trend shows ↑ in green
- **AND** declining trend shows ↓ in red
- **AND** stable trend shows → in dim

### Requirement: Dashboard Assembly

The system SHALL assemble panels into a cohesive dashboard based on display level.

#### Scenario: Full display mode
- **GIVEN** user has 3+ commitments AND 1+ active goals
- **WHEN** dashboard is rendered
- **THEN** shows commitments panel, goals panel, and status bar stacked vertically

#### Scenario: Standard display mode
- **GIVEN** user has 3+ commitments but no active goals
- **WHEN** dashboard is rendered
- **THEN** shows commitments panel and status bar only

#### Scenario: Compact display mode
- **GIVEN** user has 1-2 commitments
- **WHEN** dashboard is rendered
- **THEN** shows merged panel with commitments and status bar separated by horizontal rule

#### Scenario: Minimal display mode
- **GIVEN** user has no active commitments or goals
- **WHEN** dashboard is rendered
- **THEN** shows status bar only

### Requirement: Column Alignment Utilities

The system SHALL provide alignment functions for consistent column formatting.

#### Scenario: Left-align text within column
- **GIVEN** text shorter than column width
- **WHEN** `_align_left(text, width)` is called
- **THEN** returns text padded with spaces on the right

#### Scenario: Left-align with truncation
- **GIVEN** text longer than column width
- **WHEN** `_align_left(text, width)` is called
- **THEN** returns text truncated to (width - 3) chars plus "..."

#### Scenario: Right-align text within column
- **GIVEN** text shorter than column width
- **WHEN** `_align_right(text, width)` is called
- **THEN** returns text padded with spaces on the left

#### Scenario: Right-align with truncation
- **GIVEN** text longer than column width
- **WHEN** `_align_right(text, width)` is called
- **THEN** returns "..." plus last (width - 3) chars of text

### Requirement: Consistent Right-Edge Alignment

The system SHALL pad all content lines to exact width for consistent right-edge alignment.

#### Scenario: Pad short line to full width
- **GIVEN** a content line shorter than CONTENT_WIDTH (96 chars)
- **WHEN** `_pad_line(content)` is called
- **THEN** returns content padded with spaces to exactly 96 chars

#### Scenario: Truncate long line to full width
- **GIVEN** a content line longer than CONTENT_WIDTH
- **WHEN** `_pad_line(content)` is called
- **THEN** returns content truncated to exactly 96 chars

#### Scenario: All panel rows have consistent width
- **GIVEN** a panel is being rendered with multiple rows
- **WHEN** rows are assembled
- **THEN** every row is padded to exactly CONTENT_WIDTH
- **AND** all right borders align vertically

### Requirement: Progress Bar Formatting

The system SHALL format progress as a visual bar using Unicode block characters.

#### Scenario: Full progress bar
- **GIVEN** progress is 100%
- **WHEN** bar is rendered with width 16
- **THEN** returns "████████████████" (16 full blocks)

#### Scenario: Partial progress bar
- **GIVEN** progress is 50%
- **WHEN** bar is rendered with width 16
- **THEN** returns "████████░░░░░░░░" (8 full, 8 empty)

#### Scenario: Empty progress bar
- **GIVEN** progress is 0%
- **WHEN** bar is rendered with width 16
- **THEN** returns "░░░░░░░░░░░░░░░░" (16 empty blocks)
