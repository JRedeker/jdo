# tui-chat Specification

## Purpose
Define the conversational AI interface for JDO, including slash commands for managing visions, milestones, and hierarchy views, along with data panel displays and keyboard navigation extensions.
## Requirements
### Requirement: Typed Draft Gate

The system SHALL require a draft to have a true entity type before applying refinements.

#### Scenario: Untyped draft prompts for type
- **GIVEN** a draft is awaiting confirmation
- **AND** the draft has no true type assigned
- **WHEN** the user enters any refinement text
- **THEN** the system prompts the user to assign a type
- **AND** the system accepts either a type name (plain text) or `/type <type>`

#### Scenario: Type assignment requires confirmation
- **GIVEN** the user has proposed a type for an untyped draft
- **WHEN** the user confirms with `y` or `yes`
- **THEN** the draft type is set
- **AND** the user may continue refining the typed draft

#### Scenario: Refine typed commitment draft with rules
- **GIVEN** a commitment draft is awaiting confirmation
- **WHEN** the user enters "stakeholder to Alex"
- **THEN** the draft stakeholder is updated
- **AND** the updated draft is re-rendered

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

The system SHALL support keyboard shortcuts for Vision and Milestone navigation via NavSidebar.

#### Scenario: Quick access visions
- **WHEN** user presses '4' (Visions nav item) or selects from sidebar
- **THEN** the data panel shows visions list

#### Scenario: Quick access milestones
- **WHEN** user presses '5' (Milestones nav item) or selects from sidebar
- **THEN** the data panel shows milestones list (filtered to current goal if in goal context)

#### Scenario: Quick access hierarchy
- **WHEN** user presses '6' (Hierarchy nav item) or selects from sidebar
- **THEN** the data panel shows the full planning hierarchy tree

### Requirement: Home Screen (Extended)

The system SHALL integrate Vision and Milestone access into the NavSidebar.

#### Scenario: Sidebar shows navigation shortcuts
- **WHEN** viewing the main layout
- **THEN** NavSidebar includes: Visions, Milestones, Hierarchy alongside existing items

#### Scenario: Vision review notification
- **WHEN** user opens the app and visions are due for review
- **THEN** a subtle notification appears in chat: "1 vision due for quarterly review"

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
- **THEN** the message is displayed in chat and sent to AI for processing

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

The system SHALL display integrity grade prominently in the NavSidebar header.

#### Scenario: Integrity grade in sidebar
- **WHEN** user views the main layout
- **THEN** current integrity letter grade is displayed in NavSidebar header (e.g., "Integrity: A-")

#### Scenario: Integrity grade color coding
- **WHEN** integrity grade is displayed
- **THEN** grade is color-coded: A-range = green, B-range = blue, C-range = yellow, D/F = red

### Requirement: Time-Aware Risk Warning

The system SHALL enhance risk warnings with time-based analysis.

#### Scenario: Daily capacity warning
- **WHEN** user's allocated hours exceed available hours
- **THEN** a warning message appears in chat: "Over-committed today: X hours allocated, Y hours available"

### Requirement: Commitment Guardrail Warnings

The system SHALL display velocity-based coaching warnings when users create commitments faster than they complete them.

#### Scenario: Velocity warning for overcommitting
- **WHEN** user confirms a commitment draft
- **AND** commitments created > commitments completed in the past 7 days
- **THEN** a coaching note is displayed: "You've created X commitments this week but only completed Y. Are you overcommitting?"

#### Scenario: No velocity warning when balanced
- **WHEN** user confirms a commitment draft
- **AND** commitments created <= commitments completed in the past 7 days
- **THEN** no velocity warning is displayed

#### Scenario: User can proceed despite warning
- **WHEN** velocity warning is displayed
- **THEN** the confirmation flow continues normally (no hard block)
- **AND** user can confirm to create the commitment

#### Scenario: Graceful degradation if database unavailable
- **WHEN** velocity query fails
- **THEN** no warning is displayed
- **AND** commitment creation proceeds normally

### Requirement: AI Message Handling

The system SHALL invoke the AI agent for non-command chat messages.

#### Scenario: User sends non-command message
- **WHEN** user submits text without a `/` prefix in chat
- **THEN** the message is displayed in the chat container
- **AND** the message is sent to the AI agent for processing

#### Scenario: AI response streams into chat
- **WHEN** AI agent begins responding to a message
- **THEN** an assistant message appears with "Thinking..." indicator
- **AND** the message content updates as text chunks arrive
- **AND** the chat auto-scrolls to show new content

#### Scenario: AI response completes
- **WHEN** AI agent finishes streaming a response
- **THEN** the final message is displayed in full
- **AND** the conversation history is updated with the complete response

#### Scenario: New message cancels previous AI request
- **WHEN** user submits a new message while AI is still responding
- **THEN** the previous AI request is cancelled
- **AND** the new message is processed instead

### Requirement: Conversation History

The system SHALL maintain conversation history within a chat session.

#### Scenario: History accumulates during session
- **WHEN** user and AI exchange multiple messages
- **THEN** conversation history includes all messages with role and content
- **AND** history is available for AI context on subsequent messages

#### Scenario: History truncation
- **WHEN** conversation exceeds 50 messages
- **THEN** oldest messages are removed to maintain context window
- **AND** system prompt is always included

### Requirement: AI Error Display

The system SHALL display user-friendly error messages for AI failures.

#### Scenario: Rate limit error
- **WHEN** AI provider returns rate limit error
- **THEN** chat displays "AI is busy. Please wait a moment and try again."

#### Scenario: Authentication error
- **WHEN** AI provider returns authentication error
- **THEN** chat displays "AI authentication failed. Check your API key in settings."
- **AND** user is guided to settings screen

#### Scenario: Network error
- **WHEN** network connection to AI provider fails
- **THEN** chat displays "Couldn't reach AI provider. Check your connection."

#### Scenario: Unknown error
- **WHEN** an unexpected error occurs during AI processing
- **THEN** chat displays "Something went wrong. Your message was not processed."
- **AND** the error is logged for debugging

### Requirement: AI Credentials Check

The system SHALL verify AI credentials before sending messages.

#### Scenario: No credentials configured
- **WHEN** user sends a message and no API key is configured
- **THEN** chat displays "AI not configured. Set up your API key in settings."
- **AND** user is guided to settings screen

#### Scenario: Credentials available
- **WHEN** user sends a message and credentials are configured
- **THEN** the message is sent to the AI agent

### Requirement: Input State During AI Processing

The system SHALL manage input state while AI is processing.

#### Scenario: Input disabled during streaming
- **WHEN** AI agent is processing a response
- **THEN** the prompt input is disabled to prevent duplicate submissions

#### Scenario: Input re-enabled after completion
- **WHEN** AI response completes or errors
- **THEN** the prompt input is re-enabled for new input

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

### Requirement: Integrity Display via NavSidebar

The system SHALL display the integrity grade in the NavSidebar header area.

**Note**: This requirement is implemented via `add-navigation-sidebar/specs/tui-nav` "Sidebar Header Display" requirement. The integrity grade is shown in the NavSidebar header when expanded.

#### Scenario: Display integrity grade in sidebar header
- **WHEN** user views the main layout with NavSidebar expanded
- **THEN** the integrity letter grade is displayed in the NavSidebar header (e.g., "Integrity: A-")

#### Scenario: Integrity grade styling
- **WHEN** displaying integrity grade
- **THEN** grade is color-coded: A grades (green), B grades (blue), C grades (yellow), D/F grades (red)

#### Scenario: Access integrity dashboard via sidebar
- **WHEN** user selects "Integrity" from NavSidebar (item 7) or presses number key '7'
- **THEN** the integrity dashboard is displayed in the DataPanel

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

### Requirement: Integrity Navigation via Sidebar

The system SHALL provide access to integrity features through NavSidebar.

#### Scenario: Integrity item in sidebar
- **WHEN** viewing the NavSidebar
- **THEN** "Integrity" appears as navigation item (position 7)

#### Scenario: Quick access integrity via number key
- **WHEN** user presses '7' (Integrity nav item)
- **THEN** the integrity dashboard is displayed in the DataPanel

#### Scenario: Mark at-risk from commitment view
- **WHEN** user is viewing a commitment in DataPanel and types `/atrisk`
- **THEN** the at-risk workflow begins for that commitment

### Requirement: Conversation History Management

The system SHALL manage conversation history to prevent unbounded memory growth.

#### Scenario: Prune conversation after user message
- **WHEN** a user message is added to conversation history
- **AND** conversation length exceeds MAX_CONVERSATION_HISTORY (default 50)
- **THEN** the oldest messages are removed to maintain the limit
- **AND** only the most recent MAX_CONVERSATION_HISTORY messages are retained

#### Scenario: Prune conversation after AI response
- **WHEN** an AI response is added to conversation history
- **AND** conversation length exceeds MAX_CONVERSATION_HISTORY
- **THEN** the oldest messages are removed to maintain the limit

#### Scenario: Preserve recent context
- **WHEN** conversation is pruned
- **THEN** the most recent messages are preserved
- **AND** AI retains sufficient context for coherent responses

#### Scenario: No pruning when under limit
- **WHEN** conversation length is at or below MAX_CONVERSATION_HISTORY
- **THEN** no messages are removed

