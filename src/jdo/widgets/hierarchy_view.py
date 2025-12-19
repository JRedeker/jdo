"""Hierarchy view widget showing Vision > Goal > Milestone > Commitment tree.

Displays the MPI hierarchy in an expandable tree structure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from textual.binding import Binding, BindingType

if TYPE_CHECKING:
    from uuid import UUID
from textual.message import Message
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from jdo.models import Commitment, Goal, Milestone, Vision

# Type alias for hierarchy items
HierarchyItem = Vision | Goal | Milestone | Commitment


class HierarchyView(Tree[HierarchyItem | None]):
    """Tree widget displaying the Vision > Goal > Milestone > Commitment hierarchy.

    The tree structure is:
    - Vision nodes at root level
    - Goal nodes as children of Visions (or orphan section)
    - Milestone nodes as children of Goals
    - Commitment nodes as children of Milestones (or orphan section)
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("enter", "select_cursor", "Select", show=True),
        Binding("right", "expand_cursor", "Expand"),
        Binding("left", "collapse_cursor", "Collapse"),
        Binding("j", "cursor_down", "Down"),
        Binding("k", "cursor_up", "Up"),
    ]

    class ItemSelected(Message):
        """Posted when a leaf item is selected."""

        def __init__(self, item: Vision | Goal | Milestone | Commitment) -> None:
            """Initialize the message.

            Args:
                item: The selected domain object.
            """
            self.item = item
            super().__init__()

    def __init__(
        self,
        label: str = "Hierarchy",
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Initialize the hierarchy view.

        Args:
            label: Root label for the tree.
            name: Widget name.
            id: Widget ID.
            classes: CSS classes.
            disabled: Whether widget is disabled.
        """
        super().__init__(
            label,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        # Track nodes by entity ID for lookups
        self._vision_nodes: dict[UUID, TreeNode[HierarchyItem | None]] = {}
        self._goal_nodes: dict[UUID, TreeNode[HierarchyItem | None]] = {}
        self._milestone_nodes: dict[UUID, TreeNode[HierarchyItem | None]] = {}
        self._orphan_goals_node: TreeNode[HierarchyItem | None] | None = None
        self._orphan_commitments_node: TreeNode[HierarchyItem | None] | None = None

    def _get_or_create_orphan_goals_node(self) -> TreeNode[HierarchyItem | None]:
        """Get or create the 'Orphan Goals' section."""
        if self._orphan_goals_node is None:
            self._orphan_goals_node = self.root.add("📁 Orphan Goals", expand=True)
        return self._orphan_goals_node

    def _get_or_create_orphan_commitments_node(self) -> TreeNode[HierarchyItem | None]:
        """Get or create the 'Orphan Commitments' section."""
        if self._orphan_commitments_node is None:
            self._orphan_commitments_node = self.root.add("📁 Orphan Commitments", expand=True)
        return self._orphan_commitments_node

    def add_vision(self, vision: Vision) -> TreeNode[HierarchyItem | None]:
        """Add a vision as a root-level node.

        Args:
            vision: The vision to add.

        Returns:
            The created tree node.
        """
        icon = "🔭" if vision.status.value == "active" else "✅"
        label = f"{icon} {vision.title}"
        node = self.root.add(label, data=vision, expand=True)
        self._vision_nodes[vision.id] = node
        return node

    def add_goal(self, goal: Goal) -> TreeNode[HierarchyItem | None]:
        """Add a goal as a child of its parent vision or orphan section.

        Args:
            goal: The goal to add.

        Returns:
            The created tree node.
        """
        icon = "🎯" if goal.status.value == "active" else "✅"
        label = f"{icon} {goal.title}"

        if goal.vision_id and goal.vision_id in self._vision_nodes:
            parent = self._vision_nodes[goal.vision_id]
        else:
            parent = self._get_or_create_orphan_goals_node()

        node = parent.add(label, data=goal, expand=True)
        self._goal_nodes[goal.id] = node
        return node

    def add_milestone(self, milestone: Milestone) -> TreeNode[HierarchyItem | None]:
        """Add a milestone as a child of its parent goal.

        Args:
            milestone: The milestone to add.

        Returns:
            The created tree node.
        """
        status_icons = {
            "pending": "⏳",
            "in_progress": "🔄",
            "completed": "✅",
            "missed": "❌",
        }
        icon = status_icons.get(milestone.status.value, "⏳")
        title = milestone.title or "(untitled)"
        label = f"{icon} {title}"

        if milestone.goal_id in self._goal_nodes:
            parent = self._goal_nodes[milestone.goal_id]
        else:
            # Milestone without a goal node - add to orphan goals section
            parent = self._get_or_create_orphan_goals_node()

        node = parent.add(label, data=milestone, expand=True)
        self._milestone_nodes[milestone.id] = node
        return node

    # Status icons for commitments (shared by add_commitment and add_orphan_commitment)
    _COMMITMENT_STATUS_ICONS: ClassVar[dict[str, str]] = {
        "pending": "⏳",
        "in_progress": "🔄",
        "at_risk": "⚠️",
        "completed": "✅",
        "abandoned": "✗",
    }

    def add_commitment(self, commitment: Commitment) -> TreeNode[HierarchyItem | None]:
        """Add a commitment as a child of its parent milestone.

        Args:
            commitment: The commitment to add.

        Returns:
            The created tree node.
        """
        icon = self._COMMITMENT_STATUS_ICONS.get(commitment.status.value, "⏳")
        deliverable = commitment.deliverable or "(no deliverable)"
        label = f"{icon} {deliverable}"

        if commitment.milestone_id and commitment.milestone_id in self._milestone_nodes:
            parent = self._milestone_nodes[commitment.milestone_id]
        else:
            parent = self._get_or_create_orphan_commitments_node()

        return parent.add(label, data=commitment)

    def add_orphan_commitment(self, commitment: Commitment) -> TreeNode[HierarchyItem | None]:
        """Add a commitment to the orphan commitments section.

        Args:
            commitment: The commitment to add.

        Returns:
            The created tree node.
        """
        icon = self._COMMITMENT_STATUS_ICONS.get(commitment.status.value, "⏳")
        deliverable = commitment.deliverable or "(no deliverable)"
        label = f"{icon} {deliverable}"

        parent = self._get_or_create_orphan_commitments_node()
        return parent.add(label, data=commitment)

    def action_expand_cursor(self) -> None:
        """Expand the currently selected node."""
        if self.cursor_node and self.cursor_node.allow_expand:
            self.cursor_node.expand()

    def action_collapse_cursor(self) -> None:
        """Collapse the currently selected node."""
        if self.cursor_node and self.cursor_node.allow_expand:
            self.cursor_node.collapse()

    def action_select_cursor(self) -> None:
        """Select the current node - expand/collapse or post selection event."""
        node = self.cursor_node
        if node is None:
            return

        # Check if this is a leaf node (no children and has data)
        has_children = len(list(node.children)) > 0

        if has_children:
            # Branch node - toggle expansion
            if node.is_expanded:
                node.collapse()
            else:
                node.expand()
        elif node.data is not None:
            # Leaf node with data - post selection event
            self.post_message(self.ItemSelected(node.data))
