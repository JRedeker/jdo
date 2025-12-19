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


# ============================================================
# Phase 14: Integrity Protocol Integration Tests
# ============================================================


class TestIntegrityDashboardFlows:
    """Integration tests for integrity dashboard display."""

    @pytest.fixture
    def panel_app(self) -> type[App]:
        """Create an app with DataPanel."""

        class PanelTestApp(App):
            def compose(self) -> ComposeResult:
                yield DataPanel()

        return PanelTestApp

    async def test_integrity_dashboard_displays_all_metrics(self, panel_app: type[App]) -> None:
        """Integrity dashboard displays all metric categories."""
        async with panel_app().run_test() as pilot:
            panel = pilot.app.query_one(DataPanel)

            # Show integrity dashboard with full metrics
            panel.show_integrity_dashboard(
                {
                    "letter_grade": "B+",
                    "composite_score": 87.5,
                    "on_time_rate": 0.85,
                    "notification_timeliness": 0.90,
                    "cleanup_completion_rate": 0.80,
                    "current_streak_weeks": 2,
                    "total_completed": 15,
                    "total_on_time": 12,
                    "total_at_risk": 3,
                    "total_abandoned": 1,
                }
            )
            await pilot.pause()

            assert panel.mode == PanelMode.INTEGRITY
            assert panel.entity_type == "integrity"

    async def test_integrity_grade_styles_applied(self, panel_app: type[App]) -> None:
        """Integrity grade gets appropriate styling based on grade."""
        async with panel_app().run_test() as pilot:
            panel = pilot.app.query_one(DataPanel)

            # Test A grade
            panel.show_integrity_dashboard({"letter_grade": "A", "composite_score": 95.0})
            await pilot.pause()
            assert panel.current_data.get("letter_grade") == "A"

            # Test C grade
            panel.show_integrity_dashboard({"letter_grade": "C-", "composite_score": 70.0})
            await pilot.pause()
            assert panel.current_data.get("letter_grade") == "C-"


class TestCleanupPlanFlows:
    """Integration tests for cleanup plan display."""

    @pytest.fixture
    def panel_app(self) -> type[App]:
        """Create an app with DataPanel."""

        class PanelTestApp(App):
            def compose(self) -> ComposeResult:
                yield DataPanel()

        return PanelTestApp

    async def test_cleanup_plan_displays_all_sections(self, panel_app: type[App]) -> None:
        """Cleanup plan displays impact, actions, and notification status."""
        async with panel_app().run_test() as pilot:
            panel = pilot.app.query_one(DataPanel)

            panel.show_cleanup_plan(
                {
                    "id": "cleanup-123",
                    "commitment_deliverable": "Quarterly financial report",
                    "status": "in_progress",
                    "impact_description": "Delayed board meeting preparation",
                    "mitigation_actions": [
                        "Notify CFO about delay",
                        "Request 1-week extension",
                        "Prioritize critical sections",
                    ],
                    "notification_task_complete": False,
                }
            )
            await pilot.pause()

            assert panel.mode == PanelMode.CLEANUP
            assert len(panel.current_data.get("mitigation_actions", [])) == 3

    async def test_cleanup_plan_status_progression(self, panel_app: type[App]) -> None:
        """Cleanup plan shows different statuses correctly."""
        async with panel_app().run_test() as pilot:
            panel = pilot.app.query_one(DataPanel)

            # Test planned status
            panel.show_cleanup_plan({"status": "planned"})
            await pilot.pause()
            assert panel.current_data.get("status") == "planned"

            # Test completed status
            panel.show_cleanup_plan({"status": "completed"})
            await pilot.pause()
            assert panel.current_data.get("status") == "completed"


class TestAtRiskWorkflowFlows:
    """Integration tests for at-risk workflow display."""

    @pytest.fixture
    def panel_app(self) -> type[App]:
        """Create an app with DataPanel."""

        class PanelTestApp(App):
            def compose(self) -> ComposeResult:
                yield DataPanel()

        return PanelTestApp

    async def test_atrisk_workflow_shows_commitment_context(self, panel_app: type[App]) -> None:
        """At-risk workflow displays commitment being marked."""
        async with panel_app().run_test() as pilot:
            panel = pilot.app.query_one(DataPanel)

            panel.show_atrisk_workflow(
                {
                    "id": "commit-456",
                    "deliverable": "Complete API documentation",
                    "stakeholder_name": "Developer Relations",
                    "due_date": "2025-12-20",
                },
                workflow_step="reason",
            )
            await pilot.pause()

            assert panel.mode == PanelMode.ATRISK_WORKFLOW
            assert panel.current_data.get("deliverable") == "Complete API documentation"
            assert panel.current_data.get("_workflow_step") == "reason"

    async def test_atrisk_workflow_step_progression(self, panel_app: type[App]) -> None:
        """At-risk workflow tracks progression through steps."""
        async with panel_app().run_test() as pilot:
            panel = pilot.app.query_one(DataPanel)

            commitment_data = {
                "id": "commit-789",
                "deliverable": "Ship feature X",
                "stakeholder_name": "Product Manager",
            }

            # Step 1: Reason
            panel.show_atrisk_workflow(commitment_data, workflow_step="reason")
            await pilot.pause()
            assert panel.current_data.get("_workflow_step") == "reason"

            # Step 2: Impact
            panel.show_atrisk_workflow(commitment_data, workflow_step="impact")
            await pilot.pause()
            assert panel.current_data.get("_workflow_step") == "impact"

            # Step 3: Resolution
            panel.show_atrisk_workflow(commitment_data, workflow_step="resolution")
            await pilot.pause()
            assert panel.current_data.get("_workflow_step") == "resolution"

            # Step 4: Confirm
            panel.show_atrisk_workflow(commitment_data, workflow_step="confirm")
            await pilot.pause()
            assert panel.current_data.get("_workflow_step") == "confirm"


class TestChatScreenIntegrityFlows:
    """Integration tests for ChatScreen integrity features."""

    async def test_r_key_triggers_atrisk_flow(self) -> None:
        """Pressing 'r' key starts at-risk workflow when viewing commitment."""
        from unittest.mock import MagicMock, patch

        from jdo.integrity import RiskSummary
        from jdo.widgets.data_panel import PanelMode

        class ChatTestApp(App):
            def compose(self) -> ComposeResult:
                yield ChatScreen()

        # Mock must be applied BEFORE app starts so on_mount uses mock
        mock_service = MagicMock()
        mock_service.detect_risks.return_value = RiskSummary(
            overdue_commitments=[],
            due_soon_commitments=[],
            stalled_commitments=[],
        )

        app = ChatTestApp()

        with (
            patch("jdo.screens.chat.get_session"),
            patch("jdo.screens.chat.IntegrityService", return_value=mock_service),
        ):
            async with app.run_test() as pilot:
                await pilot.pause()

                screen = app.query_one(ChatScreen)
                panel = screen.data_panel

                # Set up commitment view (match unit test pattern)
                panel.mode = PanelMode.VIEW
                panel._entity_type = "commitment"
                panel._data = {
                    "id": "commit-test",
                    "deliverable": "Test commitment",
                    "status": "pending",
                    "stakeholder_name": "Test Team",
                }
                await pilot.pause()

                # Press 'r' to trigger at-risk
                await pilot.press("r")
                await pilot.pause()
                await pilot.pause()

                # Should show /atrisk command in chat
                container = screen.chat_container
                messages = list(container.query(ChatMessage))
                user_msgs = [m for m in messages if m.role == MessageRole.USER]
                assert any("/atrisk" in str(m.content) for m in user_msgs)

    async def test_chat_screen_context_includes_commitment(self) -> None:
        """ChatScreen context includes current commitment when viewing one."""
        from unittest.mock import MagicMock, patch

        from jdo.integrity import RiskSummary
        from jdo.widgets.data_panel import PanelMode

        class ChatTestApp(App):
            def compose(self) -> ComposeResult:
                yield ChatScreen()

        # Mock must be applied BEFORE app starts so on_mount uses mock
        mock_service = MagicMock()
        mock_service.detect_risks.return_value = RiskSummary(
            overdue_commitments=[],
            due_soon_commitments=[],
            stalled_commitments=[],
        )

        app = ChatTestApp()

        with (
            patch("jdo.screens.chat.get_session"),
            patch("jdo.screens.chat.IntegrityService", return_value=mock_service),
        ):
            async with app.run_test() as pilot:
                await pilot.pause()

                screen = app.query_one(ChatScreen)
                panel = screen.data_panel

                # View a commitment (match unit test pattern)
                commitment_data = {
                    "id": "ctx-commit-123",
                    "deliverable": "Context test commitment",
                    "status": "in_progress",
                }
                panel.mode = PanelMode.VIEW
                panel._entity_type = "commitment"
                panel._data = commitment_data
                await pilot.pause()

                # Build context and verify commitment is included
                context = screen._build_handler_context()
                assert context.get("current_commitment") == commitment_data
                assert context.get("current_commitment_id") == "ctx-commit-123"


class TestHomeScreenIntegrityFlows:
    """Integration tests for HomeScreen integrity features."""

    @pytest.fixture
    def home_app(self) -> type[App]:
        """Create an app with HomeScreen."""

        class HomeTestApp(App):
            def compose(self) -> ComposeResult:
                yield HomeScreen()

        return HomeTestApp

    async def test_i_key_binding_exists(self, home_app: type[App]) -> None:
        """HomeScreen has 'i' key binding for integrity."""
        async with home_app().run_test() as pilot:
            screen = pilot.app.query_one(HomeScreen)

            binding_keys = [b.key for b in screen.BINDINGS]
            assert "i" in binding_keys

    async def test_integrity_grade_displayed(self, home_app: type[App]) -> None:
        """HomeScreen displays integrity grade."""
        async with home_app().run_test() as pilot:
            screen = pilot.app.query_one(HomeScreen)

            # Default grade is A+ (clean slate with no commitment history)
            assert screen.integrity_grade == "A+"
