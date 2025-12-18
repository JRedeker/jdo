# tui-chat Specification

## Purpose
Define the conversational AI interface for JDO, including slash commands for managing visions, milestones, and hierarchy views, along with data panel displays and keyboard navigation extensions.
## Requirements
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

### Requirement: Command - Review Goal

The system SHALL support the `/goal review` command for periodic goal reflection.

#### Scenario: List goals due for review
- **WHEN** user types `/goal review`
- **THEN** the data panel shows active goals where next_review_date <= today

#### Scenario: Review specific goal
- **WHEN** user types `/goal review <id>` or selects a goal from the review list
- **THEN** the data panel shows a goal review interface with motivation, commitment progress, and reflection prompts

#### Scenario: Goal review interface
- **WHEN** viewing a goal in review mode
- **THEN** the panel shows:
  - Goal title and problem/solution vision
  - "Why This Matters" section with motivation (if set)
  - Commitment progress: "✓ X completed, ● Y in progress, ○ Z pending"
  - Reflection prompts: "Are you still moving toward this vision?", "What commitments should you make next?"
  - Action options: [c]ontinue, [h]old, [a]chieve, [b]andon, [e]dit

#### Scenario: Complete goal review - continue
- **WHEN** user presses 'c' to continue during review
- **THEN** last_reviewed_at is set to now, next_review_date is calculated from review_interval_days (if set), and status remains active

#### Scenario: Complete goal review - hold
- **WHEN** user presses 'h' to hold during review
- **THEN** status changes to on_hold, last_reviewed_at is set, and AI confirms: "Goal paused. You can reactivate it anytime with /goal activate <id>"

#### Scenario: Complete goal review - achieve
- **WHEN** user presses 'a' to mark achieved during review
- **THEN** AI prompts: "Marking a goal as achieved is significant. Are you sure this vision has been realized?" and requires confirmation

#### Scenario: Complete goal review - abandon
- **WHEN** user presses 'b' to abandon during review
- **THEN** AI prompts for reason and confirms: "Goals evolve. Abandoning isn't failure—it's honest reprioritization."

#### Scenario: No goals due for review
- **WHEN** user types `/goal review` and no goals are due
- **THEN** AI responds: "No goals due for review. Your next review is for '[goal title]' on [date]." or "No goals have review dates set."

### Requirement: Command - Create Goal (Extended)

The system SHALL prompt for motivation and review interval during goal creation.

#### Scenario: Motivation prompt during creation
- **WHEN** AI creates a goal draft from conversation
- **THEN** AI asks: "Why does this goal matter to you?" and includes response in motivation field

#### Scenario: Motivation is optional
- **WHEN** user skips or provides empty motivation
- **THEN** goal is created with motivation=None (allowed)

#### Scenario: Review interval suggestion
- **WHEN** goal creation is near completion
- **THEN** AI suggests: "How often would you like to review this goal? Weekly, Monthly, or Quarterly?" with default of Monthly (30 days)

#### Scenario: Review interval display
- **WHEN** showing interval options
- **THEN** options display as "Weekly (7 days)", "Monthly (30 days)", "Quarterly (90 days)", or "No recurring review"

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

### Requirement: Command - Triage

The system SHALL support the `/triage` command to process inbox items.

#### Scenario: Triage command recognized
- **WHEN** user types `/triage`
- **THEN** the command is parsed as CommandType.TRIAGE

#### Scenario: Triage with items starts workflow
- **WHEN** user types `/triage` and triage items exist
- **THEN** the triage workflow begins with the first item displayed

#### Scenario: Triage without items shows message
- **WHEN** user types `/triage` and no triage items exist
- **THEN** the system responds "No items to triage. Your inbox is empty."

#### Scenario: Triage in help output
- **WHEN** user types `/help`
- **THEN** the help text includes "/triage - Process items in your inbox"

### Requirement: Chat Message Handling

The system SHALL handle non-command messages in the chat.

#### Scenario: Message submitted in chat
- **WHEN** user submits text without a `/` prefix in chat
- **THEN** the message is processed by the AI for intent detection

#### Scenario: Clear intent proceeds to creation
- **WHEN** user submits "I need to send the report to Sarah by Friday"
- **AND** AI detects clear commitment intent
- **THEN** AI responds with creation guidance or suggests `/commit`

#### Scenario: Vague intent creates triage item
- **WHEN** user submits "remember to call mom"
- **AND** AI cannot determine object type with confidence
- **THEN** a triage item is created and AI offers immediate triage

#### Scenario: User accepts immediate triage
- **WHEN** AI offers triage and user responds affirmatively
- **THEN** triage mode starts with the new item

#### Scenario: User declines immediate triage
- **WHEN** AI offers triage and user declines or continues chatting
- **THEN** the item remains in triage queue and conversation continues

### Requirement: Triage Workflow Display

The system SHALL display triage items with AI analysis in the chat.

#### Scenario: Triage item display format
- **WHEN** a triage item is shown in the workflow
- **THEN** the display includes: item number, total count, raw text, AI analysis, and action options

#### Scenario: AI analysis display
- **WHEN** AI analyzes a triage item
- **THEN** the analysis shows: suggested type, confidence indicator, detected entities, and potential links

#### Scenario: Action options display
- **WHEN** triage item is displayed
- **THEN** options show: "[1] Accept [2] Change type [3] Delete [4] Skip"

#### Scenario: Low confidence clarification
- **WHEN** AI confidence is low
- **THEN** a simple clarifying question is shown instead of a type suggestion

