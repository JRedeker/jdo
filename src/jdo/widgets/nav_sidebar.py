"""Navigation sidebar widget for JDO TUI.

Provides persistent, collapsible navigation for the application.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import OptionList
from textual.widgets._option_list import Option


@dataclass
class NavItem:
    """Navigation item definition.

    Attributes:
        id: Unique identifier for the nav item.
        label: Display label for the item.
        shortcut: Single-letter keyboard shortcut.
    """

    id: str
    label: str
    shortcut: str


NAV_ITEMS: list[NavItem | None] = [
    NavItem(id="chat", label="Chat", shortcut="n"),
    None,  # Separator
    NavItem(id="goals", label="Goals", shortcut="g"),
    NavItem(id="commitments", label="Commitments", shortcut="c"),
    NavItem(id="visions", label="Visions", shortcut="v"),
    NavItem(id="milestones", label="Milestones", shortcut="m"),
    None,  # Separator
    NavItem(id="hierarchy", label="Hierarchy", shortcut="h"),
    NavItem(id="integrity", label="Integrity", shortcut="i"),
    NavItem(id="orphans", label="Orphans", shortcut="o"),
    None,  # Separator
    NavItem(id="triage", label="Triage", shortcut="t"),
    NavItem(id="settings", label="Settings", shortcut="s"),
]


class NavSidebar(Widget):
    """Persistent navigation sidebar widget.

    Provides discoverable navigation with:
    - Keyboard shortcuts (1-9 for quick nav)
    - Collapse/expand functionality
    - Visual highlighting of active item
    - Triage badge for pending items

    Messages:
        Selected: Posted when a navigation item is selected.
    """

    DEFAULT_CSS = """
    NavSidebar {
        width: 22;
        height: 100%;
        dock: left;
        border-right: solid $primary;
        padding: 0 1;
    }

    NavSidebar.-collapsed {
        width: 5;
    }

    NavSidebar OptionList {
        width: 100%;
        height: 100%;
        background: transparent;
        border: none;
    }

    NavSidebar OptionList:focus {
        border: none;
    }

    NavSidebar OptionList > .option-list--option-highlighted {
        background: $accent 30%;
    }

    NavSidebar OptionList > .option-list--option-hover {
        background: $surface-darken-1;
    }

    NavSidebar.-collapsed OptionList {
        width: 3;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("[", "toggle_collapse", "Toggle Sidebar", show=False),
        Binding("1", "select_item_1", "Chat", show=False),
        Binding("2", "select_item_2", "Goals", show=False),
        Binding("3", "select_item_3", "Commitments", show=False),
        Binding("4", "select_item_4", "Visions", show=False),
        Binding("5", "select_item_5", "Milestones", show=False),
        Binding("6", "select_item_6", "Hierarchy", show=False),
        Binding("7", "select_item_7", "Integrity", show=False),
        Binding("8", "select_item_8", "Orphans", show=False),
        Binding("9", "select_item_9", "Settings", show=False),
    ]

    collapsed: reactive[bool] = reactive(default=False)
    active_item: reactive[str] = reactive(default="chat")
    triage_count: reactive[int] = reactive(default=0)

    class Selected(Message):
        """Message posted when a navigation item is selected.

        Attributes:
            item_id: ID of the selected navigation item.
        """

        def __init__(self, item_id: str) -> None:
            """Initialize the Selected message.

            Args:
                item_id: ID of the selected navigation item.
            """
            self.item_id = item_id
            super().__init__()

    def __init__(
        self,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the navigation sidebar.

        Args:
            name: Widget name.
            id: Widget ID.
            classes: CSS classes.
        """
        super().__init__(name=name, id=id, classes=classes)
        self._option_list: OptionList | None = None
        self._nav_items = [item for item in NAV_ITEMS if item is not None]

    def compose(self) -> ComposeResult:
        """Compose the sidebar layout."""
        self._option_list = OptionList()
        # Add initial options
        item_index = 0
        for nav_item in NAV_ITEMS:
            if nav_item is None:
                self._option_list.add_option(None)  # None creates a separator
            else:
                item_index += 1
                label = self._format_label(nav_item, item_index)
                self._option_list.add_option(Option(label, id=nav_item.id))
        yield self._option_list

    def _refresh_options(self) -> None:
        """Refresh the OptionList labels (called when display state changes)."""
        if self._option_list is None or not self._option_list.is_mounted:
            return

        # Store current highlighted option
        current_highlighted = self._option_list.highlighted

        self._option_list.clear_options()
        item_index = 0

        for nav_item in NAV_ITEMS:
            if nav_item is None:
                self._option_list.add_option(None)  # None creates a separator
            else:
                item_index += 1
                label = self._format_label(nav_item, item_index)
                self._option_list.add_option(Option(label, id=nav_item.id))

        # Restore highlighted index
        if current_highlighted is not None:
            self._option_list.highlighted = current_highlighted

    def _format_label(self, item: NavItem, index: int) -> Text:
        """Format a navigation item label.

        Args:
            item: Navigation item to format.
            index: 1-based index for number shortcut display.

        Returns:
            Formatted Rich Text object.
        """
        text = Text()

        if self.collapsed:
            # Collapsed: just show shortcut letter
            text.append(item.shortcut.upper(), style="bold")
        else:
            # Expanded: show number, label, and badge if needed
            text.append(f"{index} ", style="dim")
            text.append(item.label)

            # Add triage badge if this is the triage item
            if item.id == "triage" and self.triage_count > 0:
                text.append(f" ({self.triage_count})", style="bold yellow")

        return text

    def get_nav_items(self) -> list[NavItem]:
        """Get the list of navigation items (excluding separators).

        Returns:
            List of NavItem objects.
        """
        return self._nav_items

    def toggle_collapse(self) -> None:
        """Toggle the collapsed state of the sidebar."""
        self.collapsed = not self.collapsed

    def action_toggle_collapse(self) -> None:
        """Action handler for toggle collapse binding."""
        self.toggle_collapse()

    def watch_collapsed(self, collapsed: bool) -> None:
        """React to collapsed state changes.

        Args:
            collapsed: New collapsed state.
        """
        if collapsed:
            self.add_class("-collapsed")
        else:
            self.remove_class("-collapsed")

        # Re-render labels
        self._refresh_options()

    def set_active_item(self, item_id: str) -> None:
        """Set the active (highlighted) navigation item.

        Args:
            item_id: ID of the item to make active.
        """
        self.active_item = item_id

        # Find and highlight the option
        if self._option_list is not None:
            for i, item in enumerate(self._nav_items):
                if item.id == item_id:
                    self._option_list.highlighted = i
                    break

    def set_triage_count(self, count: int) -> None:
        """Set the triage badge count.

        Args:
            count: Number of items needing triage.
        """
        self.triage_count = count
        # Re-render to update badge
        self._refresh_options()

    def _select_by_index(self, index: int) -> None:
        """Select a navigation item by its 1-based index.

        Args:
            index: 1-based index of the item to select.
        """
        # Get non-separator items
        if 0 < index <= len(self._nav_items):
            item = self._nav_items[index - 1]
            self.active_item = item.id
            self.post_message(self.Selected(item.id))

    def action_select_item_1(self) -> None:
        """Select item at position 1."""
        self._select_by_index(1)

    def action_select_item_2(self) -> None:
        """Select item at position 2."""
        self._select_by_index(2)

    def action_select_item_3(self) -> None:
        """Select item at position 3."""
        self._select_by_index(3)

    def action_select_item_4(self) -> None:
        """Select item at position 4."""
        self._select_by_index(4)

    def action_select_item_5(self) -> None:
        """Select item at position 5."""
        self._select_by_index(5)

    def action_select_item_6(self) -> None:
        """Select item at position 6."""
        self._select_by_index(6)

    def action_select_item_7(self) -> None:
        """Select item at position 7."""
        self._select_by_index(7)

    def action_select_item_8(self) -> None:
        """Select item at position 8."""
        self._select_by_index(8)

    def action_select_item_9(self) -> None:
        """Select item at position 9."""
        self._select_by_index(9)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle selection from the OptionList.

        Args:
            event: The option selection event.
        """
        if event.option.id is not None:
            self.active_item = event.option.id
            self.post_message(self.Selected(event.option.id))
