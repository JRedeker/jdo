# Capability: TUI Chat Interface (Vision & Milestone Extension)

This spec extends the TUI chat interface from `add-conversational-tui` to add Vision and Milestone commands and views.

**Cross-reference**: See `add-conversational-tui/specs/tui-chat` for the base TUI specification.

**Implementation Notes** (Textual-specific):
- Hierarchy tree view: Use Textual's `Tree` widget or custom nested `ListView`
- 'v', 'm', 'h' bindings: Add to HomeScreen and PromptInput BINDINGS with `show=True`
- Vision review notification: Display as system message on `on_mount()` or subtle indicator in Header

## ADDED Requirements

### Requirement: Command - Create Vision

The system SHALL support the `/vision` command to create and manage visions.

#### Scenario: List visions
- **WHEN** user types `/vision` or `/vision list`
- **THEN** the data panel shows a list of visions with title, timeframe, and status

#### Scenario: Create vision from context
- **WHEN** user types `/vision new` after discussing aspirations
- **THEN** AI extracts title, narrative, and metrics from conversation and updates draft panel

#### Scenario: Vision draft template
- **WHEN** AI proposes a vision from conversation
- **THEN** the data panel shows: Title, Timeframe, Narrative, Metrics, Why It Matters, Status (Draft)

#### Scenario: Confirm vision creation
- **WHEN** user confirms the proposed vision
- **THEN** the vision is saved to the database with next_review_date set to 90 days from now

#### Scenario: Vision creation guidance
- **WHEN** user types `/vision new` without prior context
- **THEN** AI guides: "Let's create a vivid picture of your future. Describe what life looks like when this vision is realized..."

### Requirement: Command - Review Vision

The system SHALL support vision review workflow.

#### Scenario: List visions due for review
- **WHEN** user types `/vision review`
- **THEN** the data panel shows visions where next_review_date <= today

#### Scenario: Review vision prompt
- **WHEN** user selects a vision for review
- **THEN** AI displays the vision and asks: "Is this vision still inspiring? Has anything changed?"

#### Scenario: Complete review
- **WHEN** user completes a vision review (affirms or updates)
- **THEN** last_reviewed_at is set to now and next_review_date is set to 90 days from now

#### Scenario: Evolve vision
- **WHEN** user indicates the vision has evolved during review
- **THEN** AI helps create a new vision and offers to mark the old one as "evolved"

### Requirement: Command - Create Milestone

The system SHALL support the `/milestone` command to create and manage milestones.

#### Scenario: List milestones
- **WHEN** user types `/milestone` or `/milestone list`
- **THEN** the data panel shows milestones for the current goal context (or all milestones if no goal selected)

#### Scenario: Create milestone from context
- **WHEN** user types `/milestone new` while viewing a goal
- **THEN** AI extracts title, description, and target_date from conversation and updates draft panel

#### Scenario: Milestone draft template
- **WHEN** AI proposes a milestone from conversation
- **THEN** the data panel shows: Title, Description, Target Date, Goal, Status (Draft)

#### Scenario: Confirm milestone creation
- **WHEN** user confirms the proposed milestone
- **THEN** the milestone is saved to the database linked to the current goal

#### Scenario: Require goal context
- **WHEN** user types `/milestone new` without an active goal context
- **THEN** AI prompts: "Which goal is this milestone for?" and shows available goals

#### Scenario: Target date requirement
- **WHEN** AI creates a milestone draft without a target_date
- **THEN** AI asks: "When should this milestone be completed? Milestones need a specific date."

### Requirement: Command - View Hierarchy

The system SHALL support viewing the full planning hierarchy.

#### Scenario: Show vision hierarchy
- **WHEN** user types `/show hierarchy` or presses 'h' on home screen
- **THEN** the data panel shows a tree view: Visions > Goals > Milestones > Commitments

#### Scenario: Expand hierarchy node
- **WHEN** user navigates to a hierarchy item and presses Enter or right arrow
- **THEN** the node expands to show its children

#### Scenario: Collapse hierarchy node
- **WHEN** user presses left arrow on an expanded node
- **THEN** the node collapses

#### Scenario: Navigate to item from hierarchy
- **WHEN** user presses Enter on a leaf node (Goal, Milestone, or Commitment)
- **THEN** the data panel switches to view mode for that item

### Requirement: Data Panel - Vision View

The system SHALL display vision details in the data panel.

#### Scenario: View vision
- **WHEN** user views a vision via command or selection
- **THEN** the panel shows: Title, Timeframe, Narrative, Metrics (bulleted list), Why It Matters, Status, Next Review Date, and linked Goals count

#### Scenario: Vision metrics display
- **WHEN** viewing a vision with metrics
- **THEN** metrics are displayed as a bulleted list under a "Success Metrics" heading

#### Scenario: Vision goals summary
- **WHEN** viewing a vision
- **THEN** the panel shows: "Goals: X active, Y achieved, Z total" with option to list them

### Requirement: Data Panel - Milestone View

The system SHALL display milestone details in the data panel.

#### Scenario: View milestone
- **WHEN** user views a milestone via command or selection
- **THEN** the panel shows: Title, Description, Target Date, Goal (linked), Status, Progress (X of Y commitments), and linked Commitments list

#### Scenario: Milestone status indicator
- **WHEN** viewing a milestone
- **THEN** status is shown with visual indicator: (pending), (in_progress), (completed), (missed - warning color)

#### Scenario: Milestone progress bar
- **WHEN** viewing a milestone with commitments
- **THEN** a visual progress indicator shows commitment completion percentage

### Requirement: Data Panel - Goal View (Extended)

The system SHALL extend goal view to show Vision and Milestone context.

#### Scenario: Goal with vision shows link
- **WHEN** viewing a goal that has a vision_id
- **THEN** the panel shows "Vision: [vision title]" with option to navigate to vision

#### Scenario: Goal shows milestone progress
- **WHEN** viewing a goal that has milestones
- **THEN** the panel shows "Milestones: X of Y completed" with option to list them

#### Scenario: Goal shows orphan indicator
- **WHEN** viewing a goal without a vision_id
- **THEN** the panel may show a subtle indicator that it's not linked to a vision

### Requirement: Data Panel - Commitment View (Extended)

The system SHALL extend commitment view to show Milestone context.

#### Scenario: Commitment with milestone shows link
- **WHEN** viewing a commitment that has a milestone_id
- **THEN** the panel shows "Milestone: [milestone title]" with option to navigate to milestone

#### Scenario: Commitment shows full hierarchy
- **WHEN** viewing a commitment linked to a milestone
- **THEN** the panel shows breadcrumb: "Vision > Goal > Milestone > This Commitment"

### Requirement: Keyboard Navigation (Extended)

The system SHALL add keyboard shortcuts for Vision and Milestone navigation.

#### Scenario: Quick access visions
- **WHEN** user presses 'v' on home screen or with prompt focused
- **THEN** the data panel shows visions list

#### Scenario: Quick access milestones
- **WHEN** user presses 'm' on home screen or with prompt focused
- **THEN** the data panel shows milestones list (filtered to current goal if in goal context)

#### Scenario: Quick access hierarchy
- **WHEN** user presses 'h' on home screen
- **THEN** the data panel shows the full planning hierarchy tree

### Requirement: Home Screen (Extended)

The system SHALL extend the home screen for Vision and Milestone access.

#### Scenario: Footer shows new shortcuts
- **WHEN** viewing home screen
- **THEN** footer includes: v:visions, m:milestones, h:hierarchy alongside existing shortcuts

#### Scenario: Vision review notification
- **WHEN** user opens the app and visions are due for review
- **THEN** a subtle notification appears: "1 vision due for quarterly review"

### Requirement: Empty State Guidance (Extended)

The system SHALL provide guidance for Vision and Milestone empty states.

#### Scenario: Empty visions list
- **WHEN** user views visions and none exist
- **THEN** the data panel shows: "No visions yet. Visions are your north star. Type '/vision new' to create one."

#### Scenario: Empty milestones for goal
- **WHEN** user views milestones for a goal and none exist
- **THEN** the data panel shows: "No milestones for this goal. Type '/milestone new' to break it into achievable chunks."

#### Scenario: First vision onboarding
- **WHEN** user has commitments and goals but no visions
- **THEN** AI may suggest: "You have goals but no guiding vision. Would you like to create a vision that ties them together?"
