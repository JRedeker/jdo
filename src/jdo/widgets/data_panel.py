"""Data panel widget for displaying structured domain objects.

The data panel shows drafts, views, or lists of domain objects
on the right side of the split-panel chat interface.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.content import Content
from textual.reactive import reactive
from textual.selection import Selection
from textual.widgets import Static

from jdo.ai.time_parsing import format_hours
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


class _SelectableStatic(Static):
    """Static widget with safe selection handling.

    Works around a Textual bug where selection coordinates may be
    screen-relative rather than widget-relative, causing IndexError.
    """

    def get_selection(self, selection: Selection) -> tuple[str, str] | None:
        """Get the text under the selection safely.

        Args:
            selection: Selection information.

        Returns:
            Tuple of extracted text and ending, or None if extraction fails.
        """
        visual = self._render()
        if isinstance(visual, (Text, Content)):
            text = str(visual)
        else:
            return None

        try:
            extracted = selection.extract(text)
        except IndexError:
            # Selection coordinates out of range for this widget's text
            return None
        else:
            return extracted, "\n"


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
    if not entity_type:
        return "No items yet.\n\nUse /help to see available commands."
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
    INTEGRITY = "integrity"
    CLEANUP = "cleanup"
    ATRISK_WORKFLOW = "atrisk_workflow"


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

    DataPanel .status-in_progress {
        color: $primary;
    }

    DataPanel .status-at_risk {
        color: $warning;
        text-style: bold;
    }

    DataPanel .status-abandoned {
        color: $error;
    }

    DataPanel .notification-task {
        color: $warning;
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
        self._content = _SelectableStatic("")
        self._entity_type: str = ""
        self._data: dict[str, Any] = {}
        self._list_items: list[dict[str, Any]] = []

    @property
    def entity_type(self) -> str:
        """Get the current entity type being displayed.

        Returns:
            The entity type string (e.g., 'commitment', 'goal').
        """
        return self._entity_type

    @property
    def current_data(self) -> dict[str, Any]:
        """Get the current data being displayed.

        Returns:
            The data dictionary for the current view/draft.
        """
        return self._data

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
        elif self.mode == PanelMode.INTEGRITY:
            self._render_integrity()
        elif self.mode == PanelMode.CLEANUP:
            self._render_cleanup()
        elif self.mode == PanelMode.ATRISK_WORKFLOW:
            self._render_atrisk_workflow()

    def _render_list(self) -> None:
        """Render list mode content."""
        text = Text()
        title = self._entity_type.upper() if self._entity_type else "ITEMS"
        text.append(f"{title} LIST\n", style="bold")
        text.append("-" * 30 + "\n\n")

        if not self._list_items:
            # Use empty state guidance message
            empty_msg = get_empty_state_message(self._entity_type)
            text.append(empty_msg, style="dim")
        else:
            # Sort items by status priority for commitments/tasks
            sorted_items = self._sort_items_by_priority(self._list_items)
            for item in sorted_items:
                self._render_list_item(text, item)

        self._content.update(text)

    def _sort_items_by_priority(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Sort items by status priority (overdue/at-risk first).

        Args:
            items: List of items to sort.

        Returns:
            Sorted list with highest priority items first.
        """
        # Status priority for sorting (lower number = higher priority)
        status_priority = {
            "at_risk": 1,
            "in_progress": 2,
            "pending": 3,
            "completed": 4,
            "abandoned": 5,
            "skipped": 5,
        }

        def get_priority(item: dict[str, Any]) -> int:
            status = item.get("status", "")
            if hasattr(status, "value"):
                status = status.value
            return status_priority.get(str(status).lower(), 10)

        return sorted(items, key=get_priority)

    def _render_list_item(self, text: Text, item: dict[str, Any]) -> None:
        """Render a single list item with status indicator.

        Args:
            text: Rich Text object to append to.
            item: Item data dictionary.
        """
        # Get summary text
        summary = item.get("deliverable") or item.get("title") or str(item.get("id", ""))

        # Get status for styling
        status = item.get("status", "")
        if hasattr(status, "value"):
            status = status.value
        status = str(status).lower()

        # Determine icon and style based on status
        status_icons = {
            "pending": "○",
            "in_progress": "◐",
            "at_risk": "⚠",
            "completed": "✓",
            "abandoned": "✗",
            "skipped": "⊘",
        }

        status_styles = {
            "pending": "dim",
            "in_progress": "blue",
            "at_risk": "bold yellow",
            "completed": "green",
            "abandoned": "red",
            "skipped": "dim",
        }

        # Check if this is a notification task
        is_notification = item.get("is_notification_task", False)
        if is_notification:
            icon = "🔔"
            style = "yellow"
        else:
            icon = status_icons.get(status, "○")
            style = status_styles.get(status, "")

        # Render the item
        text.append(f"  {icon} ", style=style)
        text.append(f"{summary}", style=style if status == "at_risk" else "")

        # Add estimated hours for tasks if available
        estimated_hours = item.get("estimated_hours")
        if estimated_hours is not None:
            text.append(f" ({format_hours(estimated_hours)})", style="dim")

        text.append("\n")

    def _render_view(self) -> None:
        """Render view mode content."""
        # Use specialized rendering for recurring_commitment
        if self._entity_type == "recurring_commitment":
            self._render_recurring_commitment_view()
            return

        # Use specialized rendering for commitment with time rollup
        if self._entity_type == "commitment":
            self._render_commitment_view()
            return

        text = Text()
        entity_name = self._entity_type.upper() if self._entity_type else "ITEM"
        text.append(f"{entity_name}\n", style="bold")
        text.append("-" * 30 + "\n\n")

        for key, value in self._data.items():
            label = key.replace("_", " ").title()
            text.append(f"{label}:\n", style="dim")
            text.append(f"  {value}\n\n")

        self._content.update(text)

    def _render_commitment_view(self) -> None:
        """Render specialized view for commitments with time rollup."""
        text = Text()
        text.append("COMMITMENT\n", style="bold")
        text.append("-" * 30 + "\n\n")

        # Deliverable
        deliverable = self._data.get("deliverable", "")
        if deliverable:
            text.append("Deliverable:\n", style="dim")
            text.append(f"  {deliverable}\n\n")

        # Stakeholder
        stakeholder = self._data.get("stakeholder_name", self._data.get("stakeholder", ""))
        if stakeholder:
            text.append("Stakeholder:\n", style="dim")
            text.append(f"  {stakeholder}\n\n")

        # Due date and time
        due_date = self._data.get("due_date", "")
        due_time = self._data.get("due_time", "")
        if due_date:
            text.append("Due:\n", style="dim")
            due_str = str(due_date)
            if due_time:
                due_str += f" {due_time}"
            text.append(f"  {due_str}\n\n")

        # Status
        status = self._data.get("status", "")
        if hasattr(status, "value"):
            status = status.value
        if status:
            status_style = self._get_status_style(str(status))
            text.append("Status:\n", style="dim")
            text.append(f"  {status}\n\n", style=status_style)

        # Time rollup (if available)
        time_rollup = self._data.get("time_rollup")
        if time_rollup:
            self._render_time_rollup(text, time_rollup)

        self._content.update(text)

    def _render_time_rollup(self, text: Text, rollup: dict[str, Any]) -> None:
        """Render time rollup section for a commitment.

        Args:
            text: Rich Text object to append to.
            rollup: Time rollup data dict.
        """
        text.append("TIME ESTIMATE\n", style="bold")
        text.append("-" * 20 + "\n")

        total = rollup.get("total_estimated_hours", 0.0)
        remaining = rollup.get("remaining_estimated_hours", 0.0)
        completed = rollup.get("completed_estimated_hours", 0.0)
        task_count = rollup.get("task_count", 0)
        tasks_with_estimates = rollup.get("tasks_with_estimates", 0)

        if total > 0:
            text.append(f"  Total:     {format_hours(total)}\n")
            text.append(f"  Completed: {format_hours(completed)}\n")
            text.append(f"  Remaining: {format_hours(remaining)}\n")
            if task_count > 0:
                coverage_pct = (tasks_with_estimates / task_count) * 100
                coverage_str = f"{tasks_with_estimates}/{task_count} ({coverage_pct:.0f}%)"
                text.append(f"  Coverage:  {coverage_str}\n")
        else:
            text.append("  No time estimates yet\n", style="dim italic")

        text.append("\n")

    def _get_status_style(self, status: str) -> str:
        """Get Rich style for a status value.

        Args:
            status: Status string (pending, in_progress, etc.)

        Returns:
            Rich style string.
        """
        status_styles = {
            "pending": "dim",
            "in_progress": "blue",
            "at_risk": "bold yellow",
            "completed": "green",
            "abandoned": "red",
        }
        return status_styles.get(status.lower(), "")

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

        # Use specialized rendering for task
        if self._entity_type == "task":
            self._render_task_draft()
            return

        text = Text()
        entity_name = self._entity_type.upper() if self._entity_type else "ITEM"
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

    def _render_task_draft(self) -> None:
        """Render specialized draft view for tasks with time estimates."""
        text = Text()
        text.append("TASK (draft)\n", style="bold yellow")
        text.append("-" * 30 + "\n\n")

        # Title
        text.append("Title:\n", style="dim")
        title = self._data.get("title", "")
        if title:
            text.append(f"  {title}\n\n")
        else:
            text.append("  (not set)\n\n", style="dim italic")

        # Scope
        text.append("Scope:\n", style="dim")
        scope = self._data.get("scope", "")
        if scope:
            text.append(f"  {scope}\n\n")
        else:
            text.append("  (not set)\n\n", style="dim italic")

        # Estimated Hours
        text.append("Estimated Time:\n", style="dim")
        estimated_hours = self._data.get("estimated_hours")
        if estimated_hours is not None:
            text.append(f"  {format_hours(estimated_hours)}\n\n")
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

    def show_draft(self, entity_type: str, data: dict[str, Any]) -> None:
        """Show a draft of any entity type in the panel.

        Args:
            entity_type: Type of entity being drafted.
            data: Draft data to display.
        """
        self._entity_type = entity_type
        self._data = data
        self.mode = PanelMode.DRAFT

    def show_view(self, entity_type: str, data: dict[str, Any]) -> None:
        """Show a view of any entity type in the panel.

        Args:
            entity_type: Type of entity being viewed.
            data: Entity data to display.
        """
        self._entity_type = entity_type
        self._data = data
        self.mode = PanelMode.VIEW

    def show_integrity_dashboard(self, data: dict[str, Any]) -> None:
        """Show the integrity metrics dashboard.

        Args:
            data: Integrity metrics data including grade, scores, etc.
        """
        self._entity_type = "integrity"
        self._data = data
        self.mode = PanelMode.INTEGRITY

    def show_cleanup_plan(self, data: dict[str, Any]) -> None:
        """Show a cleanup plan view.

        Args:
            data: CleanupPlan data including impact, actions, status.
        """
        self._entity_type = "cleanup_plan"
        self._data = data
        self.mode = PanelMode.CLEANUP

    def show_atrisk_workflow(self, data: dict[str, Any], workflow_step: str = "reason") -> None:
        """Show the at-risk workflow panel.

        Args:
            data: Current commitment and workflow data.
            workflow_step: Current step (reason, impact, resolution).
        """
        self._entity_type = "commitment"
        self._data = {**data, "_workflow_step": workflow_step}
        self.mode = PanelMode.ATRISK_WORKFLOW

    def _render_integrity(self) -> None:
        """Render integrity dashboard content."""
        text = Text()
        text.append("INTEGRITY DASHBOARD\n", style="bold")
        text.append("=" * 30 + "\n\n")

        self._render_integrity_grade(text)
        self._render_integrity_metrics(text)
        self._render_integrity_history(text)
        self._render_affecting_commitments(text)

        self._content.update(text)

    def _render_integrity_grade(self, text: Text) -> None:
        """Render letter grade section with trend indicator."""
        grade = self._data.get("letter_grade") or "A+"
        grade_style = self._get_grade_style(grade)
        overall_trend = self._data.get("overall_trend")
        trend_indicator = self._get_trend_indicator(overall_trend)

        text.append("Overall Grade: ", style="dim")
        text.append(f"{grade}", style=f"bold {grade_style}")
        if trend_indicator:
            trend_style = self._get_trend_style(overall_trend)
            text.append(f" {trend_indicator}", style=trend_style)
        text.append("\n\n")

        score = self._data.get("composite_score", 100.0)
        text.append(f"Score: {score:.1f}%\n\n", style="dim")

    def _render_integrity_metrics(self, text: Text) -> None:
        """Render individual metrics with trends."""
        text.append("METRICS\n", style="bold")
        text.append("-" * 20 + "\n")

        on_time = self._data.get("on_time_rate", 1.0) * 100
        self._append_metric_with_trend(
            text, "On-time rate:", on_time, self._data.get("on_time_trend")
        )

        notification = self._data.get("notification_timeliness", 1.0) * 100
        self._append_metric_with_trend(
            text, "Notification:", notification, self._data.get("notification_trend")
        )

        cleanup = self._data.get("cleanup_completion_rate", 1.0) * 100
        self._append_metric_with_trend(
            text, "Cleanup rate:", cleanup, self._data.get("cleanup_trend")
        )

        estimation = self._data.get("estimation_accuracy")
        if estimation is not None:
            text.append(f"Estimation acc:    {estimation * 100:.0f}%\n")

        streak = self._data.get("current_streak_weeks", 0)
        text.append(f"Current streak:    {streak} week{'s' if streak != 1 else ''}\n\n")

    def _render_integrity_history(self, text: Text) -> None:
        """Render history statistics."""
        text.append("HISTORY\n", style="bold")
        text.append("-" * 20 + "\n")

        text.append(f"Completed:         {self._data.get('total_completed', 0)}\n")
        text.append(f"On-time:           {self._data.get('total_on_time', 0)}\n")
        text.append(f"Marked at-risk:    {self._data.get('total_at_risk', 0)}\n")
        text.append(f"Abandoned:         {self._data.get('total_abandoned', 0)}\n\n")

    def _render_affecting_commitments(self, text: Text) -> None:
        """Render list of commitments that hurt the score."""
        affecting = self._data.get("affecting_commitments", [])
        if not affecting:
            return

        text.append("AFFECTING SCORE\n", style="bold")
        text.append("-" * 20 + "\n")
        for item in affecting:
            deliverable = item.get("deliverable", "Untitled")[:35]
            reason = item.get("reason", "unknown")
            style = "red" if reason == "abandoned" else "yellow"
            text.append(f"  • {deliverable}\n", style=style)
            text.append(f"    ({reason})\n", style="dim")

    def _append_metric_with_trend(
        self, text: Text, label: str, value: float, trend: str | None
    ) -> None:
        """Append a metric line with optional trend indicator.

        Args:
            text: Rich Text object to append to.
            label: Metric label (e.g., "On-time rate:").
            value: Metric value as percentage.
            trend: Trend direction string or None.
        """
        # Pad label to 17 chars for alignment
        padded_label = f"{label:<17}"
        text.append(padded_label)
        text.append(f"{value:.0f}%")
        if trend:
            indicator = self._get_trend_indicator(trend)
            style = self._get_trend_style(trend)
            text.append(f" {indicator}", style=style)
        text.append("\n")

    def _get_trend_indicator(self, trend: str | None) -> str:
        """Get display indicator for a trend direction.

        Args:
            trend: Trend direction string (up/down/stable) or None.

        Returns:
            Arrow symbol: ↑ for up, ↓ for down, → for stable, empty for None.
        """
        if not trend:
            return ""
        indicators = {
            "up": "↑",
            "down": "↓",
            "stable": "→",
        }
        return indicators.get(trend, "")

    def _get_trend_style(self, trend: str | None) -> str:
        """Get Rich style for a trend indicator.

        Args:
            trend: Trend direction string.

        Returns:
            Rich style string (green for up, red for down, dim for stable).
        """
        if not trend:
            return ""
        styles = {
            "up": "green",
            "down": "red",
            "stable": "dim",
        }
        return styles.get(trend, "")

    def _get_grade_style(self, grade: str) -> str:
        """Get Rich style for a letter grade.

        Args:
            grade: Letter grade (A+, A, A-, B+, etc.)

        Returns:
            Rich style string.
        """
        if grade.startswith("A"):
            return "green"
        if grade.startswith("B"):
            return "blue"
        if grade.startswith("C"):
            return "yellow"
        return "red"

    def _render_cleanup(self) -> None:
        """Render cleanup plan content."""
        text = Text()
        text.append("CLEANUP PLAN\n", style="bold")
        text.append("=" * 30 + "\n\n")

        # Status
        status = self._data.get("status") or "planned"
        status_style = {
            "planned": "yellow",
            "in_progress": "blue",
            "completed": "green",
            "skipped": "red",
            "cancelled": "dim",
        }.get(status, "dim")
        text.append("Status: ", style="dim")
        text.append(f"{status.upper()}\n\n", style=f"bold {status_style}")

        # Commitment reference
        commitment = self._data.get("commitment_deliverable", "")
        if commitment:
            text.append("For commitment:\n", style="dim")
            text.append(f"  {commitment}\n\n")

        # Impact description
        impact = self._data.get("impact_description")
        text.append("IMPACT\n", style="bold")
        text.append("-" * 20 + "\n")
        if impact:
            text.append(f"{impact}\n\n")
        else:
            text.append("(Not yet described)\n\n", style="dim italic")

        # Mitigation actions
        actions = self._data.get("mitigation_actions", [])
        text.append("MITIGATION ACTIONS\n", style="bold")
        text.append("-" * 20 + "\n")
        if actions:
            for i, action in enumerate(actions, 1):
                text.append(f"  {i}. {action}\n")
            text.append("\n")
        else:
            text.append("(No actions defined yet)\n\n", style="dim italic")

        # Notification task status
        notification_complete = self._data.get("notification_task_complete", False)
        text.append("NOTIFICATION\n", style="bold")
        text.append("-" * 20 + "\n")
        if notification_complete:
            text.append("✓ Stakeholder notified\n", style="green")
        else:
            text.append("○ Pending notification\n", style="yellow")

        self._content.update(text)

    def _render_atrisk_workflow(self) -> None:
        """Render at-risk workflow panel."""
        text = Text()
        text.append("AT-RISK WORKFLOW\n", style="bold yellow")
        text.append("=" * 30 + "\n\n")

        # Show commitment being marked at-risk
        deliverable = self._data.get("deliverable", "")
        stakeholder = self._data.get("stakeholder_name", "")

        text.append("Commitment:\n", style="dim")
        text.append(f"  {deliverable}\n\n")

        if stakeholder:
            text.append("Stakeholder:\n", style="dim")
            text.append(f"  {stakeholder}\n\n")

        # Show workflow progress
        step = self._data.get("_workflow_step", "reason")
        steps = [
            ("reason", "Why might you miss this?"),
            ("impact", "What impact will this have?"),
            ("resolution", "What's your proposed resolution?"),
            ("confirm", "Review and confirm"),
        ]

        text.append("WORKFLOW STEPS\n", style="bold")
        text.append("-" * 20 + "\n")
        step_order = ["reason", "impact", "resolution", "confirm"]
        current_idx = step_order.index(step) if step in step_order else 0

        for i, (_step_id, step_desc) in enumerate(steps):
            if i < current_idx:
                text.append(f"  ✓ {step_desc}\n", style="green")
            elif i == current_idx:
                text.append(f"  → {step_desc}\n", style="bold yellow")
            else:
                text.append(f"  ○ {step_desc}\n", style="dim")

        self._content.update(text)
