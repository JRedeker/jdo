# tui-nav Specification Delta

## ADDED Requirements

### Requirement: Navigation Sidebar Widget

The system SHALL provide a NavSidebar widget that displays navigation options in a persistent, collapsible sidebar.

#### Scenario: Sidebar displays navigation items
- **GIVEN** the application is running
- **WHEN** the main screen is displayed
- **THEN** the NavSidebar shows navigation items: Chat, Goals, Commitments, Visions, Milestones, Hierarchy, Integrity, Orphans, Settings

#### Scenario: Sidebar items are keyboard navigable
- **WHEN** the sidebar has focus
- **AND** the user presses up/down arrow keys
- **THEN** the highlighted item changes accordingly

#### Scenario: Sidebar item selection posts message
- **WHEN** the user presses Enter on a highlighted item
- **THEN** the sidebar posts a `NavSidebar.Selected` message with the item ID

#### Scenario: Sidebar supports number key shortcuts
- **WHEN** the user presses a number key (1-9)
- **THEN** the corresponding navigation item is selected directly

#### Scenario: Sidebar collapse toggle
- **WHEN** the user presses `[` key
- **THEN** the sidebar toggles between expanded and collapsed states

#### Scenario: Collapsed sidebar shows abbreviations
- **GIVEN** the sidebar is in collapsed state
- **WHEN** the sidebar is rendered
- **THEN** only single-character abbreviations are shown (e.g., "C" for Chat, "G" for Goals)

#### Scenario: Expanded sidebar shows full labels
- **GIVEN** the sidebar is in expanded state
- **WHEN** the sidebar is rendered
- **THEN** full labels are shown with shortcut hints (e.g., "1 Chat", "2 Goals")

### Requirement: Navigation Item Selection

The system SHALL handle navigation item selection by updating the content area appropriately.

#### Scenario: Chat selection shows chat-only view
- **WHEN** user selects "Chat" from sidebar
- **THEN** the content area shows ChatContainer and PromptInput
- **AND** the DataPanel is hidden or minimized

#### Scenario: Goals selection shows goals list
- **WHEN** user selects "Goals" from sidebar
- **THEN** the DataPanel shows the goals list view
- **AND** the chat area remains visible

#### Scenario: Commitments selection shows commitments list
- **WHEN** user selects "Commitments" from sidebar
- **THEN** the DataPanel shows the commitments list view
- **AND** commitments are sorted with at_risk first, then by due date

#### Scenario: Visions selection shows visions list
- **WHEN** user selects "Visions" from sidebar
- **THEN** the DataPanel shows the visions list view

#### Scenario: Milestones selection shows milestones list
- **WHEN** user selects "Milestones" from sidebar
- **THEN** the DataPanel shows the milestones list view

#### Scenario: Hierarchy selection shows tree view
- **WHEN** user selects "Hierarchy" from sidebar
- **THEN** the DataPanel shows the full hierarchy tree (Vision > Goal > Milestone > Commitment)

#### Scenario: Integrity selection shows dashboard
- **WHEN** user selects "Integrity" from sidebar
- **THEN** the DataPanel shows the integrity metrics dashboard

#### Scenario: Orphans selection shows orphan commitments
- **WHEN** user selects "Orphans" from sidebar
- **THEN** the DataPanel shows commitments without goal/milestone linkage

#### Scenario: Settings selection opens settings screen
- **WHEN** user selects "Settings" from sidebar
- **THEN** the SettingsScreen is pushed onto the screen stack

### Requirement: Navigation Focus Management

The system SHALL manage focus between sidebar and content area consistently.

#### Scenario: Tab cycles focus
- **WHEN** the user presses Tab
- **THEN** focus cycles: NavSidebar -> PromptInput -> DataPanel -> NavSidebar

#### Scenario: Sidebar retains selection on focus loss
- **GIVEN** the sidebar has an item selected
- **WHEN** focus moves to another widget
- **THEN** the selected item remains highlighted

#### Scenario: Focus returns to prompt after navigation
- **WHEN** user selects a navigation item (except Settings)
- **THEN** focus moves to the PromptInput after content updates

### Requirement: Triage Badge

The system SHALL display a badge on the Triage navigation item when items need attention.

#### Scenario: Badge shows count when items exist
- **GIVEN** there are N items in the triage queue (N > 0)
- **WHEN** the sidebar is rendered
- **THEN** the Triage item shows a badge with count N

#### Scenario: Badge hidden when queue empty
- **GIVEN** there are no items in the triage queue
- **WHEN** the sidebar is rendered
- **THEN** no badge is shown on the Triage item

#### Scenario: Badge updates on return
- **WHEN** user processes triage items and returns to main view
- **THEN** the badge count is refreshed

### Requirement: Sidebar Persistence

The system SHALL remember sidebar state within a session.

#### Scenario: Collapse state persists in session
- **GIVEN** user collapses the sidebar
- **WHEN** user navigates to Settings and back
- **THEN** the sidebar remains collapsed

#### Scenario: Selection persists across modals
- **GIVEN** user has "Goals" selected in sidebar
- **WHEN** a modal dialog opens and closes
- **THEN** "Goals" remains selected in sidebar
