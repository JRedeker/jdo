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

from jdo.recurrence.formatter import DAY_NAMES, MONTH_NAMES

# Validation constants for day of week
MIN_DAY_OF_WEEK = 0
MAX_DAY_OF_WEEK = 6

# Validation constants for month
MIN_MONTH = 1
MAX_MONTH = 12

# Week of month values representing "last week"
LAST_WEEK_VALUES = {5, -1}

# Ordinal suffix constants
ORDINAL_TEEN_MIN = 11
ORDINAL_TEEN_MAX = 13

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
    "recurring_commitment": (
        "No recurring commitments yet.\n\n"
        "Create your first recurring commitment by typing:\n"
        "  /recurring new\n\n"
        "Example: Weekly status report every Monday"
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
        # Use specialized rendering for recurring_commitment
        if self._entity_type == "recurring_commitment":
            self._render_recurring_commitment_view()
            return

        text = Text()
        entity_name = self._entity_type.upper()
        text.append(f"{entity_name}\n", style="bold")
        text.append("-" * 30 + "\n\n")

        for key, value in self._data.items():
            label = key.replace("_", " ").title()
            text.append(f"{label}:\n", style="dim")
            text.append(f"  {value}\n\n")

        self._content.update(text)

    def _render_recurring_commitment_view(self) -> None:
        """Render specialized view for recurring commitments."""
        text = Text()
        text.append("RECURRING COMMITMENT\n", style="bold")
        text.append("-" * 30 + "\n\n")

        # Deliverable template
        if "deliverable_template" in self._data:
            text.append("Deliverable:\n", style="dim")
            text.append(f"  {self._data['deliverable_template']}\n\n")

        # Try to format pattern summary if we have the model
        pattern = self._format_recurrence_pattern()
        if pattern:
            text.append("Schedule:\n", style="dim")
            text.append(f"  {pattern}\n\n")

        # Status
        if "status" in self._data:
            text.append("Status:\n", style="dim")
            status = self._data["status"]
            if hasattr(status, "value"):
                status = status.value
            text.append(f"  {status}\n\n")

        # Instance count
        if "instances_generated" in self._data:
            text.append("Instances Generated:\n", style="dim")
            text.append(f"  {self._data['instances_generated']}\n\n")

        self._content.update(text)

    def _format_recurrence_pattern(self) -> str:
        """Format recurrence pattern from data dict.

        Returns:
            Human-readable pattern string, or empty string if not enough data.
        """
        recurrence_type = self._data.get("recurrence_type")
        if not recurrence_type:
            return ""

        # Convert enum to string if needed
        if hasattr(recurrence_type, "value"):
            recurrence_type = recurrence_type.value

        formatters = {
            "daily": self._format_daily_pattern,
            "weekly": self._format_weekly_pattern,
            "monthly": self._format_monthly_pattern,
            "yearly": self._format_yearly_pattern,
        }
        formatter = formatters.get(recurrence_type)
        return formatter() if formatter else ""

    def _format_daily_pattern(self) -> str:
        """Format daily recurrence pattern."""
        interval = self._data.get("interval", 1)
        return "Daily" if interval == 1 else f"Every {interval} days"

    def _format_weekly_pattern(self) -> str:
        """Format weekly recurrence pattern."""
        interval = self._data.get("interval", 1)
        days = self._data.get("days_of_week", [])
        days_str = self._format_days_of_week(days)
        if interval == 1:
            return f"Weekly on {days_str}"
        return f"Every {interval} weeks on {days_str}"

    def _format_monthly_pattern(self) -> str:
        """Format monthly recurrence pattern."""
        interval = self._data.get("interval", 1)
        day_part = self._get_monthly_day_part()
        if interval == 1:
            return f"Monthly on {day_part}"
        return f"Every {interval} months on {day_part}"

    def _get_monthly_day_part(self) -> str:
        """Get the day specification for monthly pattern."""
        day_of_month = self._data.get("day_of_month")
        if day_of_month:
            return f"the {self._ordinal(day_of_month)}"

        week_of_month = self._data.get("week_of_month")
        days = self._data.get("days_of_week", [])
        if week_of_month is not None and days:
            day_name = DAY_NAMES[days[0]] if days else ""
            if week_of_month in LAST_WEEK_VALUES:
                return f"the last {day_name}"
            return f"the {self._ordinal(week_of_month)} {day_name}"
        return ""

    def _format_yearly_pattern(self) -> str:
        """Format yearly recurrence pattern."""
        interval = self._data.get("interval", 1)
        month = self._data.get("month_of_year", 1)
        month_name = MONTH_NAMES[month] if MIN_MONTH <= month <= MAX_MONTH else ""
        if interval == 1:
            return f"Yearly in {month_name}"
        return f"Every {interval} years in {month_name}"

    def _format_days_of_week(self, days: list[int]) -> str:
        """Format days of week list as readable string.

        Args:
            days: List of day indices (0=Monday to 6=Sunday).

        Returns:
            Formatted string like "Mon, Wed, Fri".
        """
        if not days:
            return ""
        sorted_days = sorted(days)
        return ", ".join(
            DAY_NAMES[d] for d in sorted_days if MIN_DAY_OF_WEEK <= d <= MAX_DAY_OF_WEEK
        )

    def _ordinal(self, n: int) -> str:
        """Get ordinal string for a number (1st, 2nd, 3rd, etc.)."""
        if ORDINAL_TEEN_MIN <= n % 100 <= ORDINAL_TEEN_MAX:
            return f"{n}th"
        suffixes = {1: "st", 2: "nd", 3: "rd"}
        return f"{n}{suffixes.get(n % 10, 'th')}"

    def _render_draft(self) -> None:
        """Render draft mode content."""
        # Use specialized rendering for recurring_commitment
        if self._entity_type == "recurring_commitment":
            self._render_recurring_commitment_draft()
            return

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

    def _render_recurring_commitment_draft(self) -> None:
        """Render specialized draft view for recurring commitments."""
        text = Text()
        text.append("RECURRING COMMITMENT (draft)\n", style="bold yellow")
        text.append("-" * 30 + "\n\n")

        # Deliverable template
        text.append("Deliverable:\n", style="dim")
        deliverable = self._data.get("deliverable_template", "")
        if deliverable:
            text.append(f"  {deliverable}\n\n")
        else:
            text.append("  (not set)\n\n", style="dim italic")

        # Stakeholder
        text.append("Stakeholder:\n", style="dim")
        stakeholder = self._data.get("stakeholder_name", "")
        if stakeholder:
            text.append(f"  {stakeholder}\n\n")
        else:
            text.append("  (not set)\n\n", style="dim italic")

        # Schedule pattern
        pattern = self._format_recurrence_pattern()
        text.append("Schedule:\n", style="dim")
        if pattern:
            text.append(f"  {pattern}\n\n")
        else:
            text.append("  (not set)\n\n", style="dim italic")

        # Due time
        due_time = self._data.get("due_time")
        if due_time:
            text.append("Due Time:\n", style="dim")
            text.append(f"  {due_time}\n\n")

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

    def show_recurring_commitment_draft(self, data: dict[str, Any]) -> None:
        """Show a recurring commitment draft in the panel."""
        self._entity_type = "recurring_commitment"
        self._data = data
        self.mode = PanelMode.DRAFT

    def show_recurring_commitment_view(self, data: dict[str, Any]) -> None:
        """Show a recurring commitment view in the panel."""
        self._entity_type = "recurring_commitment"
        self._data = data
        self.mode = PanelMode.VIEW

    def show_list(self, entity_type: str, items: list[dict[str, Any]]) -> None:
        """Show a list of items in the panel."""
        self._entity_type = entity_type
        self._list_items = items
        self.mode = PanelMode.LIST
