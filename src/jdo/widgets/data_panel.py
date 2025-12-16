"""Data panel widget for displaying structured domain objects.

The data panel shows drafts, views, or lists of domain objects
on the right side of the split-panel chat interface.
"""

from enum import Enum
from typing import Any

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widgets import Static

# Empty state messages for each entity type
_EMPTY_STATE_MESSAGES: dict[str, str] = {
    "commitment": (
        "No commitments yet.\n\n"
        "Create your first commitment by typing:\n"
        "  /commit <what you'll deliver>\n\n"
        "Example: /commit finish the quarterly report by Friday"
    ),
    "goal": (
        "No goals yet.\n\n"
        "Create your first goal by typing:\n"
        "  /goal <what you want to achieve>\n\n"
        "Example: /goal improve team productivity by 20%"
    ),
    "vision": (
        "No visions yet.\n\n"
        "Create your first vision by typing:\n"
        "  /vision <your long-term aspiration>\n\n"
        "Example: /vision become a market leader in sustainable tech"
    ),
    "task": (
        "No tasks yet.\n\n"
        "Create your first task by typing:\n"
        "  /task <what needs to be done>\n\n"
        "Example: /task review pull requests"
    ),
    "milestone": (
        "No milestones yet.\n\n"
        "Create your first milestone by typing:\n"
        "  /milestone <a measurable checkpoint>\n\n"
        "Example: /milestone launch beta version by Q2"
    ),
}


def get_empty_state_message(entity_type: str) -> str:
    """Get guidance message for an empty list of entities.

    Args:
        entity_type: Type of entity (commitment, goal, vision, task, milestone).

    Returns:
        Guidance message with instructions on how to create the first item.
    """
    return _EMPTY_STATE_MESSAGES.get(
        entity_type.lower(),
        f"No {entity_type}s yet.\n\nUse /{entity_type} to create one.",
    )


def get_onboarding_message() -> str:
    """Get welcome message for first-time users.

    Returns:
        Onboarding message with key commands and getting started guidance.
    """
    return (
        "Welcome to JDO!\n\n"
        "Get started by creating your first commitment:\n"
        "  /commit <what you'll deliver>\n\n"
        "Other commands to explore:\n"
        "  /goal   - Set a goal to work toward\n"
        "  /vision - Define your long-term vision\n"
        "  /task   - Add a quick task\n"
        "  /help   - See all available commands\n\n"
        "Just start typing to chat with the AI assistant!"
    )


def get_quick_stats_message(stats: dict[str, Any]) -> str:
    """Get quick stats display message.

    Args:
        stats: Dictionary with stats like 'due_soon', 'overdue', etc.

    Returns:
        Formatted stats message.
    """
    lines = []

    due_soon = stats.get("due_soon", 0)
    overdue = stats.get("overdue", 0)

    if overdue > 0:
        lines.append(f"Overdue: {overdue} item{'s' if overdue != 1 else ''}")

    if due_soon > 0:
        lines.append(f"Due soon: {due_soon} item{'s' if due_soon != 1 else ''}")

    if not lines:
        lines.append("All caught up!")

    return "\n".join(lines)


def create_validation_error(field_name: str, message: str) -> str:
    """Create a validation error message for a field.

    Args:
        field_name: Name of the field with the error.
        message: The validation error message.

    Returns:
        Formatted validation error string.
    """
    field_label = field_name.replace("_", " ").title()
    return f"{field_label}: {message}"


class PanelMode(str, Enum):
    """Display mode for the data panel."""

    LIST = "list"
    VIEW = "view"
    DRAFT = "draft"


class DataPanel(VerticalScroll):
    """Panel for displaying structured domain object data.

    Features:
    - Switches between list, view, and draft modes
    - Displays entity templates with field labels
    - Supports reactive updates when data changes
    """

    DEFAULT_CSS = """
    DataPanel {
        width: 40%;
        height: 100%;
        border: solid $primary;
        padding: 1;
    }

    DataPanel .panel-title {
        text-style: bold;
        margin-bottom: 1;
    }

    DataPanel .field-label {
        color: $text-muted;
    }

    DataPanel .field-value {
        color: $text;
    }

    DataPanel .status-draft {
        color: $warning;
    }

    DataPanel .status-pending {
        color: $text-muted;
    }

    DataPanel .status-active {
        color: $success;
    }

    DataPanel .status-completed {
        color: $success;
    }
    """

    mode: reactive[PanelMode] = reactive(PanelMode.LIST)

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the data panel.

        Args:
            name: Widget name.
            id: Widget ID.
            classes: CSS classes.
        """
        super().__init__(name=name, id=id, classes=classes)
        self._content = Static("")
        self._entity_type: str = ""
        self._data: dict[str, Any] = {}
        self._list_items: list[dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        """Compose the panel content."""
        yield self._content

    def watch_mode(self, _new_mode: PanelMode) -> None:
        """React to mode changes by updating content."""
        self._update_content()

    def _update_content(self) -> None:
        """Update the displayed content based on current mode and data."""
        if self.mode == PanelMode.LIST:
            self._render_list()
        elif self.mode == PanelMode.VIEW:
            self._render_view()
        elif self.mode == PanelMode.DRAFT:
            self._render_draft()

    def _render_list(self) -> None:
        """Render list mode content."""
        text = Text()
        text.append(f"{self._entity_type.upper()} LIST\n", style="bold")
        text.append("-" * 30 + "\n\n")

        if not self._list_items:
            # Use empty state guidance message
            empty_msg = get_empty_state_message(self._entity_type)
            text.append(empty_msg, style="dim")
        else:
            for item in self._list_items:
                # Show a summary line for each item
                summary = item.get("deliverable") or item.get("title") or str(item.get("id", ""))
                text.append(f"  - {summary}\n")

        self._content.update(text)

    def _render_view(self) -> None:
        """Render view mode content."""
        text = Text()
        entity_name = self._entity_type.upper()
        text.append(f"{entity_name}\n", style="bold")
        text.append("-" * 30 + "\n\n")

        for key, value in self._data.items():
            label = key.replace("_", " ").title()
            text.append(f"{label}:\n", style="dim")
            text.append(f"  {value}\n\n")

        self._content.update(text)

    def _render_draft(self) -> None:
        """Render draft mode content."""
        text = Text()
        entity_name = self._entity_type.upper()
        text.append(f"{entity_name} (draft)\n", style="bold yellow")
        text.append("-" * 30 + "\n\n")

        for key, value in self._data.items():
            label = key.replace("_", " ").title()
            text.append(f"{label}:\n", style="dim")
            if value:
                text.append(f"  {value}\n\n")
            else:
                text.append("  (not set)\n\n", style="dim italic")

        self._content.update(text)

    # Convenience methods for showing different entity types

    def show_commitment_draft(self, data: dict[str, Any]) -> None:
        """Show a commitment draft in the panel."""
        self._entity_type = "commitment"
        self._data = data
        self.mode = PanelMode.DRAFT

    def show_goal_draft(self, data: dict[str, Any]) -> None:
        """Show a goal draft in the panel."""
        self._entity_type = "goal"
        self._data = data
        self.mode = PanelMode.DRAFT

    def show_task_draft(self, data: dict[str, Any]) -> None:
        """Show a task draft in the panel."""
        self._entity_type = "task"
        self._data = data
        self.mode = PanelMode.DRAFT

    def show_vision_draft(self, data: dict[str, Any]) -> None:
        """Show a vision draft in the panel."""
        self._entity_type = "vision"
        self._data = data
        self.mode = PanelMode.DRAFT

    def show_milestone_draft(self, data: dict[str, Any]) -> None:
        """Show a milestone draft in the panel."""
        self._entity_type = "milestone"
        self._data = data
        self.mode = PanelMode.DRAFT

    def show_commitment_view(self, data: dict[str, Any]) -> None:
        """Show a commitment view in the panel."""
        self._entity_type = "commitment"
        self._data = data
        self.mode = PanelMode.VIEW

    def show_goal_view(self, data: dict[str, Any]) -> None:
        """Show a goal view in the panel."""
        self._entity_type = "goal"
        self._data = data
        self.mode = PanelMode.VIEW

    def show_vision_view(self, data: dict[str, Any]) -> None:
        """Show a vision view in the panel."""
        self._entity_type = "vision"
        self._data = data
        self.mode = PanelMode.VIEW

    def show_milestone_view(self, data: dict[str, Any]) -> None:
        """Show a milestone view in the panel."""
        self._entity_type = "milestone"
        self._data = data
        self.mode = PanelMode.VIEW

    def show_list(self, entity_type: str, items: list[dict[str, Any]]) -> None:
        """Show a list of items in the panel."""
        self._entity_type = entity_type
        self._list_items = items
        self.mode = PanelMode.LIST
