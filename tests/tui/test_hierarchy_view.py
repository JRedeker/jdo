"""Tests for Hierarchy View widget.

Phase 12: Tree view showing Vision > Goal > Milestone > Commitment.
"""

from typing import ClassVar
from uuid import uuid4

import pytest
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widgets import Tree

from jdo.models import Commitment, Goal, Milestone, Stakeholder, Vision
from jdo.models.commitment import CommitmentStatus
from jdo.models.goal import GoalStatus
from jdo.models.milestone import MilestoneStatus
from jdo.models.vision import VisionStatus


class TestHierarchyViewWidget:
    """Tests for the HierarchyView widget."""

    def test_hierarchy_view_is_tree_subclass(self) -> None:
        """HierarchyView is a Tree subclass."""
        from jdo.widgets.hierarchy_view import HierarchyView

        assert issubclass(HierarchyView, Tree)

    def test_hierarchy_view_has_bindings(self) -> None:
        """HierarchyView has navigation key bindings."""
        from jdo.widgets.hierarchy_view import HierarchyView

        binding_keys = [b.key for b in HierarchyView.BINDINGS]

        # Arrow keys for expand/collapse
        assert "right" in binding_keys or "enter" in binding_keys
        assert "left" in binding_keys


class TestHierarchyViewStructure:
    """Tests for hierarchy tree structure."""

    def test_visions_are_root_nodes(self) -> None:
        """Visions appear as root nodes in the tree."""
        from jdo.widgets.hierarchy_view import HierarchyView

        view = HierarchyView()

        vision = Vision(
            id=uuid4(),
            title="World-class engineering",
            narrative="A team that delivers excellence",
            status=VisionStatus.ACTIVE,
        )

        view.add_vision(vision)

        # Root should have the vision
        root = view.root
        assert len(root.children) == 1
        assert "World-class engineering" in str(root.children[0].label)

    def test_goals_are_children_of_visions(self) -> None:
        """Goals appear as children of their parent vision."""
        from jdo.widgets.hierarchy_view import HierarchyView

        view = HierarchyView()

        vision = Vision(
            id=uuid4(),
            title="World-class engineering",
            narrative="Excellence",
            status=VisionStatus.ACTIVE,
        )
        goal = Goal(
            id=uuid4(),
            vision_id=vision.id,
            title="Improve deployment speed",
            problem_statement="Deploys take too long",
            solution_vision="Fast deploys",
            status=GoalStatus.ACTIVE,
        )

        view.add_vision(vision)
        view.add_goal(goal)

        # Vision should have goal as child
        vision_node = view.root.children[0]
        assert len(vision_node.children) == 1
        assert goal.title in str(vision_node.children[0].label)

    def test_milestones_are_children_of_goals(self) -> None:
        """Milestones appear as children of their parent goal."""
        from datetime import date

        from jdo.widgets.hierarchy_view import HierarchyView

        view = HierarchyView()

        vision = Vision(
            id=uuid4(),
            title="World-class engineering",
            narrative="Excellence",
            status=VisionStatus.ACTIVE,
        )
        goal = Goal(
            id=uuid4(),
            vision_id=vision.id,
            title="Improve deployment speed",
            problem_statement="Deploys take too long",
            solution_vision="Fast deploys",
            status=GoalStatus.ACTIVE,
        )
        milestone = Milestone(
            id=uuid4(),
            goal_id=goal.id,
            title="Setup CI pipeline",
            target_date=date(2025, 3, 1),
            status=MilestoneStatus.PENDING,
        )

        view.add_vision(vision)
        view.add_goal(goal)
        view.add_milestone(milestone)

        # Goal should have milestone as child
        vision_node = view.root.children[0]
        goal_node = vision_node.children[0]
        assert len(goal_node.children) == 1
        assert milestone.title in str(goal_node.children[0].label)

    def test_commitments_are_children_of_milestones(self) -> None:
        """Commitments appear as children of their parent milestone."""
        from datetime import date, datetime

        from jdo.widgets.hierarchy_view import HierarchyView

        view = HierarchyView()

        vision = Vision(
            id=uuid4(),
            title="World-class engineering",
            narrative="Excellence",
            status=VisionStatus.ACTIVE,
        )
        goal = Goal(
            id=uuid4(),
            vision_id=vision.id,
            title="Improve deployment speed",
            problem_statement="Deploys take too long",
            solution_vision="Fast deploys",
            status=GoalStatus.ACTIVE,
        )
        milestone = Milestone(
            id=uuid4(),
            goal_id=goal.id,
            title="Setup CI pipeline",
            target_date=date(2025, 3, 1),
            status=MilestoneStatus.PENDING,
        )
        stakeholder = Stakeholder(id=uuid4(), name="DevOps Team")
        commitment = Commitment(
            id=uuid4(),
            milestone_id=milestone.id,
            stakeholder_id=stakeholder.id,
            deliverable="Configure GitHub Actions",
            due_date=datetime(2025, 2, 15),
            status=CommitmentStatus.PENDING,
        )

        view.add_vision(vision)
        view.add_goal(goal)
        view.add_milestone(milestone)
        view.add_commitment(commitment)

        # Milestone should have commitment as child
        vision_node = view.root.children[0]
        goal_node = vision_node.children[0]
        milestone_node = goal_node.children[0]
        assert len(milestone_node.children) == 1
        assert commitment.deliverable in str(milestone_node.children[0].label)

    def test_orphan_goals_under_orphans_section(self) -> None:
        """Goals without a vision appear under 'Orphan Goals' section."""
        from jdo.widgets.hierarchy_view import HierarchyView

        view = HierarchyView()

        goal = Goal(
            id=uuid4(),
            vision_id=None,
            title="Random goal",
            problem_statement="Something",
            solution_vision="Something else",
            status=GoalStatus.ACTIVE,
        )

        view.add_goal(goal)

        # Should have orphan section
        orphan_node = None
        for child in view.root.children:
            if "Orphan" in str(child.label):
                orphan_node = child
                break

        assert orphan_node is not None
        assert len(orphan_node.children) == 1


class TestHierarchyViewNavigation:
    """Tests for hierarchy tree navigation."""

    @pytest.fixture
    def hierarchy_app(self) -> type[App]:
        """Create a test app with HierarchyView."""
        from jdo.widgets.hierarchy_view import HierarchyView

        class HierarchyApp(App):
            BINDINGS: ClassVar[list[Binding]] = [
                Binding("q", "quit", "Quit"),
            ]

            def compose(self) -> ComposeResult:
                yield HierarchyView()

        return HierarchyApp

    async def test_enter_expands_node(self, hierarchy_app: type[App]) -> None:
        """Enter key expands a collapsed node."""
        from jdo.widgets.hierarchy_view import HierarchyView

        async with hierarchy_app().run_test() as pilot:
            view = pilot.app.query_one(HierarchyView)

            vision = Vision(
                id=uuid4(),
                title="Test Vision",
                narrative="Test",
                status=VisionStatus.ACTIVE,
            )
            view.add_vision(vision)

            # Focus the tree
            view.focus()

            # Get the vision node and collapse it first
            vision_node = view.root.children[0]
            vision_node.collapse()
            assert not vision_node.is_expanded

            # Select the node
            view.select_node(vision_node)

            # Press enter to expand
            await pilot.press("enter")

            assert vision_node.is_expanded

    async def test_right_arrow_expands_node(self, hierarchy_app: type[App]) -> None:
        """Right arrow expands a collapsed node."""
        from jdo.widgets.hierarchy_view import HierarchyView

        async with hierarchy_app().run_test() as pilot:
            view = pilot.app.query_one(HierarchyView)

            vision = Vision(
                id=uuid4(),
                title="Test Vision",
                narrative="Test",
                status=VisionStatus.ACTIVE,
            )
            view.add_vision(vision)

            view.focus()

            vision_node = view.root.children[0]
            vision_node.collapse()
            view.select_node(vision_node)

            await pilot.press("right")

            assert vision_node.is_expanded

    async def test_left_arrow_collapses_node(self, hierarchy_app: type[App]) -> None:
        """Left arrow collapses an expanded node."""
        from jdo.widgets.hierarchy_view import HierarchyView

        async with hierarchy_app().run_test() as pilot:
            view = pilot.app.query_one(HierarchyView)

            vision = Vision(
                id=uuid4(),
                title="Test Vision",
                narrative="Test",
                status=VisionStatus.ACTIVE,
            )
            view.add_vision(vision)

            view.focus()

            vision_node = view.root.children[0]
            vision_node.expand()
            assert vision_node.is_expanded

            view.select_node(vision_node)

            await pilot.press("left")

            assert not vision_node.is_expanded


class TestHierarchyViewSelection:
    """Tests for hierarchy selection events."""

    def test_item_selected_message_has_item(self) -> None:
        """ItemSelected message contains the selected item."""
        from datetime import datetime

        from jdo.widgets.hierarchy_view import HierarchyView

        stakeholder = Stakeholder(id=uuid4(), name="Team")
        commitment = Commitment(
            id=uuid4(),
            stakeholder_id=stakeholder.id,
            deliverable="Do the thing",
            due_date=datetime(2025, 12, 20),
            status=CommitmentStatus.PENDING,
        )

        message = HierarchyView.ItemSelected(commitment)

        assert message.item == commitment
        assert message.item.id == commitment.id

    def test_hierarchy_view_has_item_selected_message(self) -> None:
        """HierarchyView defines ItemSelected message class."""
        from jdo.widgets.hierarchy_view import HierarchyView

        assert hasattr(HierarchyView, "ItemSelected")
        assert issubclass(HierarchyView.ItemSelected, Message)
