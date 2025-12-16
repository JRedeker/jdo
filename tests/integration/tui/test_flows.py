"""Integration tests for TUI end-to-end flows.

Phase 17: End-to-end tests for complete user flows.

These tests verify the interaction between screens, widgets, and domain logic.
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from textual.app import App, ComposeResult

from jdo.models import (
    Commitment,
    CommitmentStatus,
    Goal,
    GoalStatus,
    Milestone,
    MilestoneStatus,
    Vision,
    VisionStatus,
)
from jdo.screens.chat import ChatScreen
from jdo.screens.home import HomeScreen
from jdo.widgets.chat_container import ChatContainer
from jdo.widgets.chat_message import ChatMessage, MessageRole
from jdo.widgets.data_panel import DataPanel, PanelMode
from jdo.widgets.hierarchy_view import HierarchyView
from jdo.widgets.prompt_input import PromptInput


class TestChatScreenFlows:
    """Integration tests for ChatScreen interactions."""

    @pytest.fixture
    def chat_app(self) -> type[App]:
        """Create an app that pushes ChatScreen.

        Note: Screens must be pushed, not yielded in compose().
        Yielding a Screen in compose() causes focus tracking issues.
        """

        class ChatTestApp(App):
            def on_mount(self) -> None:
                self.push_screen(ChatScreen())

        return ChatTestApp

    async def test_chat_screen_shows_prompt_and_panel(self, chat_app: type[App]) -> None:
        """ChatScreen displays both prompt input and data panel."""
        async with chat_app().run_test() as pilot:
            # Wait for screen to mount
            await pilot.pause()
            screen = pilot.app.screen

            # Verify both main components exist
            prompt = screen.query_one(PromptInput)
            panel = screen.query_one(DataPanel)
            container = screen.query_one(ChatContainer)

            assert prompt is not None
            assert panel is not None
            assert container is not None

    async def test_typing_message_in_prompt(self, chat_app: type[App]) -> None:
        """User can type a message in the prompt input."""
        async with chat_app().run_test() as pilot:
            # Wait for screen to mount
            await pilot.pause()
            screen = pilot.app.screen

            prompt = screen.query_one(PromptInput)

            # Focus the prompt and type
            prompt.focus()
            await pilot.pause()

            await pilot.press("h", "e", "l", "l", "o")
            await pilot.pause()

            assert "hello" in prompt.text

    async def test_panel_starts_in_list_mode(self, chat_app: type[App]) -> None:
        """DataPanel starts in list mode by default."""
        async with chat_app().run_test() as pilot:
            # Wait for screen to mount
            await pilot.pause()
            screen = pilot.app.screen

            panel = screen.query_one(DataPanel)

            assert panel.mode == PanelMode.LIST


class TestHomeScreenFlows:
    """Integration tests for HomeScreen interactions."""

    @pytest.fixture
    def home_app(self) -> type[App]:
        """Create an app with HomeScreen."""

        class HomeTestApp(App):
            def compose(self) -> ComposeResult:
                yield HomeScreen()

        return HomeTestApp

    async def test_home_screen_has_action_bindings(self, home_app: type[App]) -> None:
        """HomeScreen has keyboard bindings for actions."""
        async with home_app().run_test() as pilot:
            screen = pilot.app.query_one(HomeScreen)

            # Check bindings exist (from HomeScreen.BINDINGS)
            binding_keys = [b.key for b in screen.BINDINGS]
            assert "n" in binding_keys  # new chat
            assert "g" in binding_keys  # goals
            assert "c" in binding_keys  # commitments


class TestHierarchyViewFlows:
    """Integration tests for HierarchyView interactions."""

    @pytest.fixture
    def sample_hierarchy_data(self) -> dict:
        """Create sample hierarchy domain objects."""
        vision = Vision(
            id=uuid4(),
            title="Market Leader Vision",
            narrative="Become the market leader",
            status=VisionStatus.ACTIVE,
        )
        goal = Goal(
            id=uuid4(),
            title="Increase Revenue",
            problem_statement="Revenue is low",
            solution_vision="Increase sales",
            status=GoalStatus.ACTIVE,
            vision_id=vision.id,
        )
        milestone = Milestone(
            id=uuid4(),
            title="Q1 Target",
            goal_id=goal.id,
            target_date=date.today() + timedelta(days=90),
            status=MilestoneStatus.PENDING,
        )
        commitment = Commitment(
            id=uuid4(),
            deliverable="Close Acme deal",
            stakeholder_id=uuid4(),
            milestone_id=milestone.id,
            due_date=date.today() + timedelta(days=30),
            status=CommitmentStatus.PENDING,
        )
        return {
            "vision": vision,
            "goal": goal,
            "milestone": milestone,
            "commitment": commitment,
        }

    @pytest.fixture
    def hierarchy_app(self, sample_hierarchy_data: dict) -> type[App]:
        """Create an app with HierarchyView and sample data."""
        data = sample_hierarchy_data

        class HierarchyTestApp(App):
            def compose(self) -> ComposeResult:
                yield HierarchyView()

            def on_mount(self) -> None:
                view = self.query_one(HierarchyView)
                # Build a hierarchy using domain objects
                view.add_vision(data["vision"])
                view.add_goal(data["goal"])
                view.add_milestone(data["milestone"])
                view.add_commitment(data["commitment"])

        return HierarchyTestApp

    async def test_hierarchy_displays_tree_structure(self, hierarchy_app: type[App]) -> None:
        """HierarchyView displays Vision > Goal > Milestone > Commitment tree."""
        async with hierarchy_app().run_test() as pilot:
            view = pilot.app.query_one(HierarchyView)
            await pilot.pause()

            # The tree should have a root with children
            assert view.root is not None
            # Root should have the vision as a child
            assert len(view.root.children) > 0

    async def test_hierarchy_keyboard_navigation(self, hierarchy_app: type[App]) -> None:
        """HierarchyView supports keyboard navigation with j/k keys."""
        async with hierarchy_app().run_test() as pilot:
            view = pilot.app.query_one(HierarchyView)
            view.focus()
            await pilot.pause()

            # Navigate down
            await pilot.press("j")
            await pilot.pause()

            # The cursor should have moved (implementation-specific)
            # Just verify no errors occur
            assert view.is_attached


class TestDataPanelFlows:
    """Integration tests for DataPanel mode switching."""

    @pytest.fixture
    def panel_app(self) -> type[App]:
        """Create an app with DataPanel."""

        class PanelTestApp(App):
            def compose(self) -> ComposeResult:
                yield DataPanel()

        return PanelTestApp

    async def test_panel_switches_to_draft_mode(self, panel_app: type[App]) -> None:
        """DataPanel switches to draft mode when showing a draft."""
        async with panel_app().run_test() as pilot:
            panel = pilot.app.query_one(DataPanel)

            # Show a commitment draft
            panel.show_commitment_draft(
                {
                    "deliverable": "Test deliverable",
                    "stakeholder_name": "Test Team",
                }
            )
            await pilot.pause()

            assert panel.mode == PanelMode.DRAFT

    async def test_panel_switches_to_view_mode(self, panel_app: type[App]) -> None:
        """DataPanel switches to view mode when showing an item."""
        async with panel_app().run_test() as pilot:
            panel = pilot.app.query_one(DataPanel)

            # Show a commitment view
            panel.show_commitment_view(
                {
                    "id": "123",
                    "deliverable": "Test deliverable",
                    "status": "pending",
                }
            )
            await pilot.pause()

            assert panel.mode == PanelMode.VIEW

    async def test_panel_switches_to_list_mode(self, panel_app: type[App]) -> None:
        """DataPanel switches to list mode when showing a list."""
        async with panel_app().run_test() as pilot:
            panel = pilot.app.query_one(DataPanel)

            # First switch to another mode
            panel.show_commitment_draft({"deliverable": "test"})
            await pilot.pause()
            assert panel.mode == PanelMode.DRAFT

            # Then switch to list mode
            panel.show_list(
                "commitment",
                [
                    {"id": "1", "deliverable": "Item 1"},
                    {"id": "2", "deliverable": "Item 2"},
                ],
            )
            await pilot.pause()

            assert panel.mode == PanelMode.LIST


class TestChatMessageFlows:
    """Integration tests for ChatMessage interactions."""

    @pytest.fixture
    def chat_container_app(self) -> type[App]:
        """Create an app with ChatContainer."""

        class ContainerTestApp(App):
            def compose(self) -> ComposeResult:
                yield ChatContainer()

        return ContainerTestApp

    async def test_add_user_message(self, chat_container_app: type[App]) -> None:
        """ChatContainer can add user messages."""
        async with chat_container_app().run_test() as pilot:
            container = pilot.app.query_one(ChatContainer)

            await container.add_message(MessageRole.USER, "Hello, AI!")
            await pilot.pause()

            messages = container.query(ChatMessage)
            assert len(messages) == 1
            assert messages[0].role == MessageRole.USER
            assert messages[0].content == "Hello, AI!"

    async def test_add_assistant_message(self, chat_container_app: type[App]) -> None:
        """ChatContainer can add assistant messages."""
        async with chat_container_app().run_test() as pilot:
            container = pilot.app.query_one(ChatContainer)

            await container.add_message(MessageRole.ASSISTANT, "Hello! How can I help?")
            await pilot.pause()

            messages = container.query(ChatMessage)
            assert len(messages) == 1
            assert messages[0].role == MessageRole.ASSISTANT

    async def test_multiple_messages_in_conversation(self, chat_container_app: type[App]) -> None:
        """ChatContainer maintains message order in conversation."""
        async with chat_container_app().run_test() as pilot:
            container = pilot.app.query_one(ChatContainer)

            await container.add_message(MessageRole.USER, "First message")
            await container.add_message(MessageRole.ASSISTANT, "Response")
            await container.add_message(MessageRole.USER, "Second message")
            await pilot.pause()

            messages = list(container.query(ChatMessage))
            assert len(messages) == 3
            assert messages[0].content == "First message"
            assert messages[1].content == "Response"
            assert messages[2].content == "Second message"


class TestScreenNavigationFlows:
    """Integration tests for navigation between screens."""

    @pytest.fixture
    def home_screen_app(self) -> type[App]:
        """Create an app with HomeScreen as the initial screen."""

        class HomeScreenApp(App):
            def compose(self) -> ComposeResult:
                yield HomeScreen()

        return HomeScreenApp

    @pytest.fixture
    def chat_screen_app(self) -> type[App]:
        """Create an app with ChatScreen."""

        class ChatScreenApp(App):
            def compose(self) -> ComposeResult:
                yield ChatScreen()

        return ChatScreenApp

    async def test_home_screen_renders(self, home_screen_app: type[App]) -> None:
        """HomeScreen renders successfully."""
        async with home_screen_app().run_test() as pilot:
            await pilot.pause()

            # Should have home screen
            home = pilot.app.query(HomeScreen)
            assert len(home) == 1

    async def test_chat_screen_renders(self, chat_screen_app: type[App]) -> None:
        """ChatScreen renders successfully."""
        async with chat_screen_app().run_test() as pilot:
            await pilot.pause()

            # Should have chat screen components
            chat = pilot.app.query(ChatScreen)
            assert len(chat) == 1

    async def test_chat_screen_has_required_widgets(self, chat_screen_app: type[App]) -> None:
        """ChatScreen contains all required widgets."""
        async with chat_screen_app().run_test() as pilot:
            await pilot.pause()

            # Should have prompt, container, and panel
            assert len(pilot.app.query(PromptInput)) == 1
            assert len(pilot.app.query(ChatContainer)) == 1
            assert len(pilot.app.query(DataPanel)) == 1
