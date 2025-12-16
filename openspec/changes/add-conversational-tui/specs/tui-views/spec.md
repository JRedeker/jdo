# Capability: TUI Views

## REMOVED Requirements

### Requirement: TUI Design Principles

**Reason**: Replaced by conversational AI-driven interface in `tui-chat` capability.

**Migration**: All TUI functionality is superseded by the `tui-chat` capability which provides an Elia-style conversational interface with split-panel layout. The visual design principles (alignment, monospace-friendly, keyboard navigation, status symbols) are preserved in `tui-chat`.

### Requirement: Home Screen

**Reason**: Replaced by conversation-based home screen in `tui-chat` capability.

**Migration**: The new home screen shows recent conversations instead of commitments due soon. Quick access to domain objects is available via keyboard shortcuts (g for goals, c for commitments).

### Requirement: Commitment List Screen

**Reason**: Replaced by data panel list mode in `tui-chat` capability.

**Migration**: Use `/show commitments` command to display commitment list in the data panel.

### Requirement: Commitment Detail Screen

**Reason**: Replaced by data panel view mode in `tui-chat` capability.

**Migration**: Use `/view <id>` command or select from list to view commitment details in data panel.

### Requirement: Commitment Creation Flow

**Reason**: Replaced by conversational creation via `/commit` command in `tui-chat` capability.

**Migration**: Users describe commitments in natural conversation; `/commit` command extracts and creates structured data.

### Requirement: Goal List Screen

**Reason**: Replaced by data panel list mode in `tui-chat` capability.

**Migration**: Use `/show goals` command to display goal list in the data panel.

### Requirement: Goal Detail Screen

**Reason**: Replaced by data panel view mode in `tui-chat` capability.

**Migration**: Use `/view <id>` command or select from list to view goal details in data panel.

### Requirement: Goal Creation Flow

**Reason**: Replaced by conversational creation via `/goal` command in `tui-chat` capability.

**Migration**: Users describe goals in natural conversation; `/goal` command extracts and creates structured data.

### Requirement: Stakeholder List Screen

**Reason**: Replaced by data panel list mode in `tui-chat` capability.

**Migration**: Stakeholder management available through `/show stakeholders` command and conversational creation.

### Requirement: Task Detail View

**Reason**: Replaced by data panel view mode in `tui-chat` capability.

**Migration**: Tasks displayed inline within commitment view in data panel.

### Requirement: Task Creation Flow

**Reason**: Replaced by conversational creation via `/task` command in `tui-chat` capability.

**Migration**: Users describe tasks in natural conversation; `/task` command extracts and creates structured data.
