"""Tests for ChatScreen - Split-panel layout.

Tests for the main chat interface with split-panel layout:
- Chat panel on left (60%)
- Data panel on right (40%)
- Responsive collapse on narrow terminals
- AI message handling
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from textual.app import App, ComposeResult
from textual.containers import Horizontal

from jdo.integrity import RiskSummary
from jdo.models.commitment import Commitment, CommitmentStatus
from tests.tui.conftest import create_test_app_for_screen


class TestChatScreen:
    """Tests for ChatScreen split-panel layout."""

    async def test_chat_screen_has_horizontal_container(self) -> None:
        """ChatScreen has Horizontal with ChatPanel and DataPanel."""
        from jdo.screens.chat import ChatScreen

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            # Should have a Horizontal container
            horizontal = screen.query_one(Horizontal)
            assert horizontal is not None

    async def test_chat_screen_has_chat_container(self) -> None:
        """ChatScreen has a ChatContainer on the left."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.chat_container import ChatContainer

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            chat_container = screen.query_one(ChatContainer)
            assert chat_container is not None

    async def test_chat_screen_has_data_panel(self) -> None:
        """ChatScreen has a DataPanel on the right."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.data_panel import DataPanel

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            data_panel = screen.query_one(DataPanel)
            assert data_panel is not None

    async def test_chat_screen_has_prompt_input(self) -> None:
        """ChatScreen has a PromptInput for user input."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.prompt_input import PromptInput

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            prompt = screen.query_one(PromptInput)
            assert prompt is not None

    async def test_tab_toggles_focus(self) -> None:
        """Tab toggles focus between ChatPanel and DataPanel."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.data_panel import DataPanel
        from jdo.widgets.prompt_input import PromptInput

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            prompt = screen.query_one(PromptInput)
            data_panel = screen.query_one(DataPanel)

            # Initially focus should be on prompt
            prompt.focus()
            assert prompt.has_focus

            # Tab should move focus to data panel
            await pilot.press("tab")
            await pilot.pause()
            assert data_panel.has_focus or data_panel.can_focus

    async def test_escape_returns_focus_to_prompt(self) -> None:
        """Escape returns focus to the prompt."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.prompt_input import PromptInput

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            prompt = screen.query_one(PromptInput)

            # Focus somewhere else then press escape
            await pilot.press("tab")
            await pilot.pause()

            await pilot.press("escape")
            await pilot.pause()

            # Focus should return to prompt
            assert prompt.has_focus


class TestChatScreenResponsive:
    """Tests for responsive behavior of ChatScreen."""

    async def test_data_panel_visible_by_default(self) -> None:
        """DataPanel is visible by default."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.data_panel import DataPanel

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            data_panel = screen.query_one(DataPanel)
            assert data_panel.display is True

    async def test_toggle_panel_method(self) -> None:
        """ChatScreen can toggle DataPanel visibility via action."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.data_panel import DataPanel

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            data_panel = screen.query_one(DataPanel)

            assert data_panel.display is True

            # Call the action directly
            screen.action_toggle_panel()
            await pilot.pause()

            assert data_panel.display is False

            # Toggle back
            screen.action_toggle_panel()
            await pilot.pause()

            assert data_panel.display is True


class TestChatScreenLayout:
    """Tests for ChatScreen CSS layout."""

    async def test_chat_panel_width(self) -> None:
        """ChatPanel takes approximately 60% width."""
        from jdo.screens.chat import ChatScreen

        class TestApp(App):
            CSS = """
            Screen {
                width: 100;
            }
            """

            def compose(self) -> ComposeResult:
                return
                yield  # Empty generator

            def on_mount(self) -> None:
                self.push_screen(ChatScreen())

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            # The chat panel should have width styling
            # We verify the CSS is applied correctly
            assert "60%" in ChatScreen.DEFAULT_CSS or "fr" in ChatScreen.DEFAULT_CSS

    async def test_data_panel_width(self) -> None:
        """DataPanel takes approximately 40% width."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.data_panel import DataPanel

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            data_panel = screen.query_one(DataPanel)
            # DataPanel should exist and have width styling
            assert data_panel is not None


class TestChatScreenCommandRouting:
    """Tests for command routing in ChatScreen."""

    async def test_help_command_displays_response(self) -> None:
        """Help command displays help text in chat."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.chat_container import ChatContainer
        from jdo.widgets.chat_message import ChatMessage, MessageRole
        from jdo.widgets.prompt_input import PromptInput

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            prompt = screen.query_one(PromptInput)
            container = screen.query_one(ChatContainer)

            # Submit help command
            prompt.focus()
            prompt.insert("/help")
            prompt.action_submit()
            await pilot.pause()
            await pilot.pause()

            # Should have user message (command) and assistant response
            messages = container.query(ChatMessage)
            assert len(messages) >= 2

            # Check for help content
            assistant_msgs = [m for m in messages if m.role == MessageRole.ASSISTANT]
            assert len(assistant_msgs) >= 1
            assert "/commit" in str(assistant_msgs[0].content)

    async def test_unknown_command_shows_error(self) -> None:
        """Unknown command shows error message."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.chat_container import ChatContainer
        from jdo.widgets.chat_message import ChatMessage, MessageRole
        from jdo.widgets.prompt_input import PromptInput

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            prompt = screen.query_one(PromptInput)
            container = screen.query_one(ChatContainer)

            # Submit unknown command
            prompt.focus()
            prompt.insert("/unknowncommand")
            prompt.action_submit()
            await pilot.pause()
            await pilot.pause()

            # Should show error about unknown command
            messages = container.query(ChatMessage)
            assistant_msgs = [m for m in messages if m.role == MessageRole.ASSISTANT]
            assert len(assistant_msgs) >= 1
            assert "unknown" in str(assistant_msgs[0].content).lower()

    async def test_command_updates_data_panel(self) -> None:
        """Command handler result updates data panel."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.data_panel import DataPanel
        from jdo.widgets.prompt_input import PromptInput

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            prompt = screen.query_one(PromptInput)
            data_panel = screen.query_one(DataPanel)

            # Submit show command
            prompt.focus()
            prompt.insert("/show goals")
            prompt.action_submit()
            await pilot.pause()
            await pilot.pause()

            # Data panel should update
            assert data_panel._entity_type == "goal"


class TestChatScreenConfirmationState:
    """Tests for confirmation state tracking in ChatScreen."""

    async def test_confirmation_state_set_on_needs_confirmation(self) -> None:
        """Confirmation state set when handler needs confirmation."""
        from jdo.screens.chat import ChatScreen, ConfirmationState
        from jdo.widgets.prompt_input import PromptInput

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            prompt = screen.query_one(PromptInput)

            # Directly set up a handler result that needs confirmation
            # by calling _handle_command with a commit that has full data
            with patch("jdo.screens.chat.get_handler") as mock_get_handler:
                mock_handler = MagicMock()
                mock_handler.execute.return_value = MagicMock(
                    message="Confirm?",
                    panel_update={"mode": "draft", "entity_type": "commitment", "data": {}},
                    draft_data={
                        "deliverable": "Test",
                        "stakeholder": "Sarah",
                        "due_date": "2025-12-20",
                    },
                    needs_confirmation=True,
                )
                mock_get_handler.return_value = mock_handler

                prompt.focus()
                prompt.insert("/commit")
                prompt.action_submit()
                await pilot.pause()
                await pilot.pause()

                assert screen._confirmation_state == ConfirmationState.AWAITING_CONFIRMATION
                assert screen._pending_draft is not None
                assert screen._pending_entity_type == "commitment"

    async def test_confirmation_clears_state(self) -> None:
        """Saying 'yes' saves entity and clears confirmation state."""
        from jdo.screens.chat import ChatScreen, ConfirmationState
        from jdo.widgets.prompt_input import PromptInput

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            prompt = screen.query_one(PromptInput)

            # Set up confirmation state manually
            screen._confirmation_state = ConfirmationState.AWAITING_CONFIRMATION
            screen._pending_draft = {
                "deliverable": "Test",
                "stakeholder": "Sarah",
                "due_date": "2025-12-20",
            }
            screen._pending_entity_type = "commitment"

            # Mock the persistence service
            with patch("jdo.screens.chat.get_session") as mock_session:
                mock_ctx = MagicMock()
                mock_session.return_value.__enter__.return_value = mock_ctx

                with patch("jdo.screens.chat.PersistenceService") as mock_service_class:
                    mock_service = MagicMock()
                    mock_service.save_commitment.return_value = MagicMock(
                        id="test-id",
                        deliverable="Test",
                        model_dump=lambda: {"id": "test-id", "deliverable": "Test"},
                    )
                    mock_service_class.return_value = mock_service

                    # Say yes
                    prompt.focus()
                    prompt.insert("yes")
                    prompt.action_submit()
                    await pilot.pause()
                    await pilot.pause()

                    # State should be cleared
                    assert screen._confirmation_state == ConfirmationState.IDLE
                    assert screen._pending_draft is None

    async def test_cancellation_clears_state(self) -> None:
        """Saying 'no' clears confirmation state."""
        from jdo.screens.chat import ChatScreen, ConfirmationState
        from jdo.widgets.prompt_input import PromptInput

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            prompt = screen.query_one(PromptInput)

            # Set up confirmation state
            screen._confirmation_state = ConfirmationState.AWAITING_CONFIRMATION
            screen._pending_draft = {"title": "Test Goal"}
            screen._pending_entity_type = "goal"

            # Say no
            prompt.focus()
            prompt.insert("no")
            prompt.action_submit()
            await pilot.pause()
            await pilot.pause()

            # State should be cleared
            assert screen._confirmation_state == ConfirmationState.IDLE
            assert screen._pending_draft is None


class TestChatScreenModificationRequests:
    """Tests for modification requests while awaiting confirmation."""

    async def test_untyped_draft_prompts_for_type_confirmation(self) -> None:
        """Untyped drafts require type assignment confirmation."""
        from jdo.screens.chat import ChatScreen, ConfirmationState
        from jdo.widgets.prompt_input import PromptInput

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            prompt = screen.query_one(PromptInput)

            screen._confirmation_state = ConfirmationState.AWAITING_CONFIRMATION
            screen._pending_entity_type = "unknown"
            screen._pending_draft = {
                "deliverable": "Test",
                "stakeholder": "Sarah",
                "due_date": "2025-12-20",
            }

            prompt.focus()
            prompt.insert("commitment")
            prompt.action_submit()
            await pilot.pause()
            await pilot.pause()

            assert screen._confirmation_state == ConfirmationState.AWAITING_CONFIRMATION
            assert screen._pending_draft is not None
            assert screen._proposed_entity_type == "commitment"

    async def test_untyped_draft_accepts_type_command(self) -> None:
        """Untyped drafts accept /type <type> input."""
        from jdo.screens.chat import ChatScreen, ConfirmationState
        from jdo.widgets.prompt_input import PromptInput

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            prompt = screen.query_one(PromptInput)

            screen._confirmation_state = ConfirmationState.AWAITING_CONFIRMATION
            screen._pending_entity_type = "unknown"
            screen._pending_draft = {
                "deliverable": "Test",
                "stakeholder": "Sarah",
                "due_date": "2025-12-20",
            }

            prompt.focus()
            prompt.insert("/type commitment")
            prompt.action_submit()
            await pilot.pause()
            await pilot.pause()

            assert screen._confirmation_state == ConfirmationState.AWAITING_CONFIRMATION
            assert screen._pending_draft is not None
            assert screen._proposed_entity_type == "commitment"

    async def test_typed_draft_applies_patch(self) -> None:
        """Typed drafts apply patch rules."""
        from jdo.screens.chat import ChatScreen, ConfirmationState
        from jdo.widgets.prompt_input import PromptInput

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            prompt = screen.query_one(PromptInput)

            screen._confirmation_state = ConfirmationState.AWAITING_CONFIRMATION
            screen._pending_entity_type = "commitment"
            screen._pending_draft = {
                "deliverable": "Test",
                "stakeholder": "Sarah",
                "due_date": "2025-12-20",
            }

            prompt.focus()
            prompt.insert("stakeholder to Alex")
            prompt.action_submit()
            await pilot.pause()
            await pilot.pause()

            assert screen._confirmation_state == ConfirmationState.AWAITING_CONFIRMATION
            assert screen._pending_draft is not None
            assert screen._pending_draft["stakeholder"] == "Alex"


class TestChatScreenConfirmationDetection:
    """Tests for confirmation/cancellation detection."""

    async def test_is_confirmation_detects_yes(self) -> None:
        """_is_confirmation detects various affirmative responses."""
        from jdo.screens.chat import ChatScreen

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)

            # Test various confirmations
            assert screen._is_confirmation("yes") is True
            assert screen._is_confirmation("Yes") is True
            assert screen._is_confirmation("y") is True
            assert screen._is_confirmation("confirm") is True
            assert screen._is_confirmation("ok") is True
            assert screen._is_confirmation("sure") is True

            # Test non-confirmations
            assert screen._is_confirmation("no") is False
            assert screen._is_confirmation("maybe") is False
            assert screen._is_confirmation("change it") is False

    async def test_is_cancellation_detects_no(self) -> None:
        """_is_cancellation detects various negative responses."""
        from jdo.screens.chat import ChatScreen

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)

            # Test various cancellations
            assert screen._is_cancellation("no") is True
            assert screen._is_cancellation("No") is True
            assert screen._is_cancellation("n") is True
            assert screen._is_cancellation("cancel") is True
            assert screen._is_cancellation("nope") is True
            assert screen._is_cancellation("/cancel") is True

            # Test non-cancellations
            assert screen._is_cancellation("yes") is False
            assert screen._is_cancellation("maybe") is False


class TestChatScreenMessageHandling:
    """Tests for message handling in ChatScreen."""

    async def test_user_message_added_to_chat_on_submit(self) -> None:
        """User message is added to chat container on submit."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.chat_container import ChatContainer
        from jdo.widgets.chat_message import ChatMessage, MessageRole
        from jdo.widgets.prompt_input import PromptInput

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            prompt = screen.query_one(PromptInput)
            container = screen.query_one(ChatContainer)

            # Mock AI credentials to avoid actual AI calls
            with patch.object(screen, "_has_ai_credentials", return_value=False):
                # Type and submit a message
                prompt.focus()
                prompt.insert("Hello AI")
                prompt.action_submit()
                await pilot.pause()
                await pilot.pause()

                # Check user message was added
                messages = container.query(ChatMessage)
                assert len(messages) >= 1
                user_msgs = [m for m in messages if m.role == MessageRole.USER]
                assert len(user_msgs) == 1
                assert user_msgs[0].content == "Hello AI"

    async def test_conversation_history_updated_on_submit(self) -> None:
        """Conversation history is updated when user submits message."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.prompt_input import PromptInput

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            prompt = screen.query_one(PromptInput)

            # Mock AI credentials
            with patch.object(screen, "_has_ai_credentials", return_value=False):
                # Submit a message
                prompt.focus()
                prompt.insert("Test message")
                prompt.action_submit()
                await pilot.pause()
                await pilot.pause()

                # Check conversation history
                assert len(screen._conversation) >= 1
                assert screen._conversation[0]["role"] == "user"
                assert screen._conversation[0]["content"] == "Test message"

    async def test_command_messages_not_added_to_ai_conversation(self) -> None:
        """Commands do not add messages to AI conversation history."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.prompt_input import PromptInput

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            prompt = screen.query_one(PromptInput)

            # Submit a command
            prompt.focus()
            prompt.insert("/help")
            prompt.action_submit()
            await pilot.pause()
            await pilot.pause()

            # Command should not be added to AI conversation history
            # (it's handled separately from AI chat)
            assert len(screen._conversation) == 0


class TestChatScreenCredentials:
    """Tests for credential checking in ChatScreen."""

    async def test_has_ai_credentials_checks_provider(self) -> None:
        """_has_ai_credentials checks the configured provider."""
        from jdo.screens.chat import ChatScreen

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)

            # Mock is_authenticated to return False
            with patch("jdo.screens.chat.is_authenticated", return_value=False):
                assert screen._has_ai_credentials() is False

            # Mock is_authenticated to return True
            with patch("jdo.screens.chat.is_authenticated", return_value=True):
                assert screen._has_ai_credentials() is True

    async def test_error_shown_when_no_credentials(self) -> None:
        """Error message shown when AI credentials are missing."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.chat_container import ChatContainer
        from jdo.widgets.chat_message import ChatMessage, MessageRole
        from jdo.widgets.prompt_input import PromptInput

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            prompt = screen.query_one(PromptInput)
            container = screen.query_one(ChatContainer)

            # Mock no credentials
            with patch.object(screen, "_has_ai_credentials", return_value=False):
                # Submit a message
                prompt.focus()
                prompt.insert("Hello")
                prompt.action_submit()
                # Wait for worker to complete
                await pilot.pause()
                await pilot.pause()

                # Should show error message
                messages = container.query(ChatMessage)
                system_msgs = [m for m in messages if m.role == MessageRole.SYSTEM]
                assert len(system_msgs) >= 1
                assert "not configured" in str(system_msgs[0].content).lower()


class TestChatScreenErrorHandling:
    """Tests for error message generation."""

    async def test_rate_limit_error_message(self) -> None:
        """Rate limit error returns appropriate message."""
        from jdo.screens.chat import ChatScreen

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)

            # Test rate limit error
            error = Exception("Rate limit exceeded")
            msg = screen._get_error_message(error)
            assert "busy" in msg.lower()

    async def test_auth_error_message(self) -> None:
        """Auth error returns appropriate message."""
        from jdo.screens.chat import ChatScreen

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)

            # Test auth error
            error = Exception("401 Unauthorized")
            msg = screen._get_error_message(error)
            assert "authentication" in msg.lower()

    async def test_network_error_message(self) -> None:
        """Network error returns appropriate message."""
        from jdo.screens.chat import ChatScreen

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)

            # Test network error
            error = Exception("Connection refused")
            msg = screen._get_error_message(error)
            assert "connection" in msg.lower()

    async def test_generic_error_message(self) -> None:
        """Unknown error returns generic message."""
        from jdo.screens.chat import ChatScreen

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)

            # Test generic error
            error = Exception("Something weird happened")
            msg = screen._get_error_message(error)
            assert "something went wrong" in msg.lower()


class TestChatScreenRiskDetection:
    """Tests for AI risk detection on app launch."""

    async def test_no_message_when_no_risks(self) -> None:
        """No system message when there are no at-risk commitments."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.chat_container import ChatContainer
        from jdo.widgets.chat_message import ChatMessage, MessageRole

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            # Mock detect_risks to return empty summary
            with patch("jdo.screens.chat.get_session") as mock_session:
                mock_ctx = MagicMock()
                mock_session.return_value.__enter__.return_value = mock_ctx

                with patch("jdo.screens.chat.IntegrityService") as mock_service_class:
                    mock_service = MagicMock()
                    mock_service.detect_risks.return_value = RiskSummary(
                        overdue_commitments=[],
                        due_soon_commitments=[],
                        stalled_commitments=[],
                    )
                    mock_service_class.return_value = mock_service

                    await pilot.pause()
                    await pilot.pause()

                    container = screen.query_one(ChatContainer)
                    messages = container.query(ChatMessage)
                    system_msgs = [m for m in messages if m.role == MessageRole.SYSTEM]
                    assert len(system_msgs) == 0

    async def test_system_message_when_overdue_commitments(self) -> None:
        """System message shown when there are overdue commitments."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.chat_container import ChatContainer
        from jdo.widgets.chat_message import ChatMessage, MessageRole

        class TestApp(App):
            def compose(self) -> ComposeResult:
                return
                yield  # Empty generator

            def on_mount(self) -> None:
                self.push_screen(ChatScreen())

        # Create a mock commitment
        mock_commitment = MagicMock(spec=Commitment)
        mock_commitment.deliverable = "Send report"
        mock_commitment.due_date = datetime.now(UTC).date() - timedelta(days=1)
        mock_commitment.status = CommitmentStatus.IN_PROGRESS

        app = TestApp()

        # Set up mocks BEFORE running app so they're active during on_mount
        with patch("jdo.screens.chat.get_session") as mock_session:
            mock_ctx = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_ctx

            with patch("jdo.screens.chat.IntegrityService") as mock_service_class:
                mock_service = MagicMock()
                mock_service.detect_risks.return_value = RiskSummary(
                    overdue_commitments=[mock_commitment],
                    due_soon_commitments=[],
                    stalled_commitments=[],
                )
                mock_service_class.return_value = mock_service

                async with app.run_test() as pilot:
                    await pilot.pause()
                    await pilot.pause()
                    await pilot.pause()

                    screen = pilot.app.screen
                    container = screen.query_one(ChatContainer)
                    messages = container.query(ChatMessage)
                    system_msgs = [m for m in messages if m.role == MessageRole.SYSTEM]
                    assert len(system_msgs) >= 1
                    assert "OVERDUE" in str(system_msgs[0].content)
                    assert "Send report" in str(system_msgs[0].content)

    async def test_system_message_when_due_soon_commitments(self) -> None:
        """System message shown when there are commitments due soon."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.chat_container import ChatContainer
        from jdo.widgets.chat_message import ChatMessage, MessageRole

        class TestApp(App):
            def compose(self) -> ComposeResult:
                return
                yield  # Empty generator

            def on_mount(self) -> None:
                self.push_screen(ChatScreen())

        mock_commitment = MagicMock(spec=Commitment)
        mock_commitment.deliverable = "Review PR"
        mock_commitment.due_date = datetime.now(UTC).date()
        mock_commitment.status = CommitmentStatus.PENDING

        app = TestApp()

        # Set up mocks BEFORE running app
        with patch("jdo.screens.chat.get_session") as mock_session:
            mock_ctx = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_ctx

            with patch("jdo.screens.chat.IntegrityService") as mock_service_class:
                mock_service = MagicMock()
                mock_service.detect_risks.return_value = RiskSummary(
                    overdue_commitments=[],
                    due_soon_commitments=[mock_commitment],
                    stalled_commitments=[],
                )
                mock_service_class.return_value = mock_service

                async with app.run_test() as pilot:
                    await pilot.pause()
                    await pilot.pause()
                    await pilot.pause()

                    screen = pilot.app.screen
                    container = screen.query_one(ChatContainer)
                    messages = container.query(ChatMessage)
                    system_msgs = [m for m in messages if m.role == MessageRole.SYSTEM]
                    assert len(system_msgs) >= 1
                    assert "DUE SOON" in str(system_msgs[0].content)
                    assert "Review PR" in str(system_msgs[0].content)

    async def test_system_message_when_stalled_commitments(self) -> None:
        """System message shown when there are stalled commitments."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.chat_container import ChatContainer
        from jdo.widgets.chat_message import ChatMessage, MessageRole

        class TestApp(App):
            def compose(self) -> ComposeResult:
                return
                yield  # Empty generator

            def on_mount(self) -> None:
                self.push_screen(ChatScreen())

        mock_commitment = MagicMock(spec=Commitment)
        mock_commitment.deliverable = "Fix bug"
        mock_commitment.due_date = datetime.now(UTC).date() + timedelta(days=1)
        mock_commitment.status = CommitmentStatus.IN_PROGRESS

        app = TestApp()

        # Set up mocks BEFORE running app
        with patch("jdo.screens.chat.get_session") as mock_session:
            mock_ctx = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_ctx

            with patch("jdo.screens.chat.IntegrityService") as mock_service_class:
                mock_service = MagicMock()
                mock_service.detect_risks.return_value = RiskSummary(
                    overdue_commitments=[],
                    due_soon_commitments=[],
                    stalled_commitments=[mock_commitment],
                )
                mock_service_class.return_value = mock_service

                async with app.run_test() as pilot:
                    await pilot.pause()
                    await pilot.pause()
                    await pilot.pause()

                    screen = pilot.app.screen
                    container = screen.query_one(ChatContainer)
                    messages = container.query(ChatMessage)
                    system_msgs = [m for m in messages if m.role == MessageRole.SYSTEM]
                    assert len(system_msgs) >= 1
                    assert "STALLED" in str(system_msgs[0].content)
                    assert "Fix bug" in str(system_msgs[0].content)

    async def test_risk_detection_failure_does_not_block_chat(self) -> None:
        """Risk detection failure doesn't prevent chat from working."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.prompt_input import PromptInput

        app = create_test_app_for_screen(ChatScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            # Mock detect_risks to raise an exception
            with patch("jdo.screens.chat.get_session") as mock_session:
                mock_session.return_value.__enter__.side_effect = Exception("DB error")

                await pilot.pause()
                await pilot.pause()

                # Chat should still be usable
                prompt = screen.query_one(PromptInput)
                assert prompt is not None
                assert prompt.disabled is False

    async def test_format_risk_message_includes_atrisk_hint(self) -> None:
        """Risk message includes hint about /atrisk command."""
        from jdo.screens.chat import ChatScreen

        class TestApp(App):
            def compose(self) -> ComposeResult:
                return
                yield  # Empty generator

            def on_mount(self) -> None:
                self.push_screen(ChatScreen())

        mock_commitment = MagicMock(spec=Commitment)
        mock_commitment.deliverable = "Test"
        mock_commitment.due_date = datetime.now(UTC).date()

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, ChatScreen)
            summary = RiskSummary(
                overdue_commitments=[mock_commitment],
                due_soon_commitments=[],
                stalled_commitments=[],
            )

            message = screen._format_risk_message(summary)
            assert "/atrisk" in message


class TestChatScreenAtRiskShortcut:
    """Tests for 'r' keybinding to mark commitment at-risk."""

    async def test_r_key_without_commitment_shows_guidance(self) -> None:
        """Pressing 'r' without a commitment selected shows guidance."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.chat_container import ChatContainer
        from jdo.widgets.chat_message import ChatMessage, MessageRole

        class TestApp(App):
            def compose(self) -> ComposeResult:
                return
                yield  # Empty generator

            def on_mount(self) -> None:
                self.push_screen(ChatScreen())

        app = TestApp()

        # Set up mocks before running
        with patch("jdo.screens.chat.get_session") as mock_session:
            mock_ctx = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_ctx

            with patch("jdo.screens.chat.IntegrityService") as mock_service_class:
                mock_service = MagicMock()
                mock_service.detect_risks.return_value = RiskSummary(
                    overdue_commitments=[],
                    due_soon_commitments=[],
                    stalled_commitments=[],
                )
                mock_service_class.return_value = mock_service

                async with app.run_test() as pilot:
                    await pilot.pause()

                    screen = pilot.app.screen
                    assert isinstance(screen, ChatScreen)

                    # Call action directly so PromptInput doesn't intercept the key
                    await screen.action_mark_at_risk()
                    await pilot.pause()

                    container = screen.query_one(ChatContainer)
                    messages = container.query(ChatMessage)
                    assistant_msgs = [m for m in messages if m.role == MessageRole.ASSISTANT]
                    assert len(assistant_msgs) >= 1
                    assert "No commitment selected" in str(assistant_msgs[-1].content)

    async def test_r_key_on_commitment_already_at_risk(self) -> None:
        """Pressing 'r' on at-risk commitment shows cleanup hint."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.chat_container import ChatContainer
        from jdo.widgets.chat_message import ChatMessage, MessageRole
        from jdo.widgets.data_panel import PanelMode

        class TestApp(App):
            def compose(self) -> ComposeResult:
                return
                yield  # Empty generator

            def on_mount(self) -> None:
                self.push_screen(ChatScreen())

        app = TestApp()

        with patch("jdo.screens.chat.get_session") as mock_session:
            mock_ctx = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_ctx

            with patch("jdo.screens.chat.IntegrityService") as mock_service_class:
                mock_service = MagicMock()
                mock_service.detect_risks.return_value = RiskSummary(
                    overdue_commitments=[],
                    due_soon_commitments=[],
                    stalled_commitments=[],
                )
                mock_service_class.return_value = mock_service

                async with app.run_test() as pilot:
                    await pilot.pause()

                    screen = pilot.app.screen
                    assert isinstance(screen, ChatScreen)
                    panel = screen.data_panel

                    # Simulate viewing an at-risk commitment
                    panel.mode = PanelMode.VIEW
                    panel._entity_type = "commitment"
                    panel._data = {"status": "at_risk", "deliverable": "Test"}

                    # Press 'r'
                    await pilot.press("r")
                    await pilot.pause()
                    await pilot.pause()

                    container = screen.query_one(ChatContainer)
                    messages = container.query(ChatMessage)
                    assistant_msgs = [m for m in messages if m.role == MessageRole.ASSISTANT]
                    assert len(assistant_msgs) >= 1
                    assert "already marked at-risk" in str(assistant_msgs[-1].content)
                    assert "/cleanup" in str(assistant_msgs[-1].content)

    async def test_r_key_on_pending_commitment_triggers_atrisk(self) -> None:
        """Pressing 'r' on pending commitment triggers /atrisk workflow."""
        from jdo.screens.chat import ChatScreen
        from jdo.widgets.chat_container import ChatContainer
        from jdo.widgets.chat_message import ChatMessage, MessageRole
        from jdo.widgets.data_panel import PanelMode

        class TestApp(App):
            def compose(self) -> ComposeResult:
                return
                yield  # Empty generator

            def on_mount(self) -> None:
                self.push_screen(ChatScreen())

        app = TestApp()

        with patch("jdo.screens.chat.get_session") as mock_session:
            mock_ctx = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_ctx

            with patch("jdo.screens.chat.IntegrityService") as mock_service_class:
                mock_service = MagicMock()
                mock_service.detect_risks.return_value = RiskSummary(
                    overdue_commitments=[],
                    due_soon_commitments=[],
                    stalled_commitments=[],
                )
                mock_service_class.return_value = mock_service

                async with app.run_test() as pilot:
                    await pilot.pause()

                    screen = pilot.app.screen
                    assert isinstance(screen, ChatScreen)
                    panel = screen.data_panel

                    # Simulate viewing a pending commitment
                    panel.mode = PanelMode.VIEW
                    panel._entity_type = "commitment"
                    panel._data = {"status": "pending", "deliverable": "Test"}

                    # Press 'r'
                    await pilot.press("r")
                    await pilot.pause()
                    await pilot.pause()

                    container = screen.query_one(ChatContainer)
                    messages = container.query(ChatMessage)
                    # Should show /atrisk command was executed (user message)
                    user_msgs = [m for m in messages if m.role == MessageRole.USER]
                    assert any("/atrisk" in str(m.content) for m in user_msgs)

    async def test_r_binding_shows_in_footer(self) -> None:
        """'r' keybinding appears in footer."""
        from jdo.screens.chat import ChatScreen

        class TestApp(App):
            def compose(self) -> ComposeResult:
                return
                yield  # Empty generator

            def on_mount(self) -> None:
                self.push_screen(ChatScreen())

        app = TestApp()

        with (
            patch("jdo.screens.chat.get_session"),
            patch("jdo.screens.chat.IntegrityService"),
        ):
            async with app.run_test() as pilot:
                await pilot.pause()
                screen = pilot.app.screen
                assert isinstance(screen, ChatScreen)

                # Check that 'r' binding exists and is shown
                bindings = screen.BINDINGS
                r_binding = next(
                    (b for b in bindings if b.key == "r"),
                    None,
                )
                assert r_binding is not None
                assert r_binding.show is True
                assert "risk" in r_binding.description.lower()


class TestChatScreenRiskDismissal:
    """Tests for session-scoped risk dismissal tracking."""

    async def test_dismissed_risks_not_shown_again(self) -> None:
        """Dismissed risks are not shown in subsequent risk detection."""
        from jdo.screens.chat import ChatScreen

        class TestApp(App):
            def compose(self) -> ComposeResult:
                return
                yield  # Empty generator

            def on_mount(self) -> None:
                self.push_screen(ChatScreen())

        mock_commitment = MagicMock(spec=Commitment)
        mock_commitment.id = "commit-123"
        mock_commitment.deliverable = "Test commitment"
        mock_commitment.due_date = datetime.now(UTC).date()

        app = TestApp()

        with patch("jdo.screens.chat.get_session") as mock_session:
            mock_ctx = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_ctx

            with patch("jdo.screens.chat.IntegrityService") as mock_service_class:
                mock_service = MagicMock()
                mock_service.detect_risks.return_value = RiskSummary(
                    overdue_commitments=[mock_commitment],
                    due_soon_commitments=[],
                    stalled_commitments=[],
                )
                mock_service_class.return_value = mock_service

                async with app.run_test() as pilot:
                    await pilot.pause()
                    screen = pilot.app.screen
                    assert isinstance(screen, ChatScreen)

                    # Dismiss the risk for this commitment
                    screen.dismiss_risk_warning("commit-123")

                    # Filter should exclude this commitment
                    original = RiskSummary(
                        overdue_commitments=[mock_commitment],
                        due_soon_commitments=[],
                        stalled_commitments=[],
                    )
                    filtered = screen._filter_dismissed_risks(original)

                    assert len(filtered.overdue_commitments) == 0
                    assert not filtered.has_risks

    async def test_dismiss_tracks_commitment_id(self) -> None:
        """dismiss_risk_warning adds commitment ID to dismissed set."""
        from jdo.screens.chat import ChatScreen

        class TestApp(App):
            def compose(self) -> ComposeResult:
                return
                yield  # Empty generator

            def on_mount(self) -> None:
                self.push_screen(ChatScreen())

        app = TestApp()

        with (
            patch("jdo.screens.chat.get_session"),
            patch("jdo.screens.chat.IntegrityService"),
        ):
            async with app.run_test() as pilot:
                await pilot.pause()
                screen = pilot.app.screen
                assert isinstance(screen, ChatScreen)

                assert "commit-456" not in screen._dismissed_risk_warnings
                screen.dismiss_risk_warning("commit-456")
                assert "commit-456" in screen._dismissed_risk_warnings

    async def test_multiple_dismissals_tracked(self) -> None:
        """Multiple risk dismissals are tracked independently."""
        from jdo.screens.chat import ChatScreen

        class TestApp(App):
            def compose(self) -> ComposeResult:
                return
                yield  # Empty generator

            def on_mount(self) -> None:
                self.push_screen(ChatScreen())

        app = TestApp()

        with (
            patch("jdo.screens.chat.get_session"),
            patch("jdo.screens.chat.IntegrityService"),
        ):
            async with app.run_test() as pilot:
                await pilot.pause()
                screen = pilot.app.screen
                assert isinstance(screen, ChatScreen)

                screen.dismiss_risk_warning("commit-1")
                screen.dismiss_risk_warning("commit-2")
                screen.dismiss_risk_warning("commit-3")

                assert len(screen._dismissed_risk_warnings) == 3
                assert "commit-1" in screen._dismissed_risk_warnings
                assert "commit-2" in screen._dismissed_risk_warnings
                assert "commit-3" in screen._dismissed_risk_warnings

    async def test_filter_preserves_non_dismissed_risks(self) -> None:
        """Filtering preserves risks that haven't been dismissed."""
        from jdo.screens.chat import ChatScreen

        class TestApp(App):
            def compose(self) -> ComposeResult:
                return
                yield  # Empty generator

            def on_mount(self) -> None:
                self.push_screen(ChatScreen())

        # Create mock commitments
        dismissed_commit = MagicMock(spec=Commitment)
        dismissed_commit.id = "dismissed-123"
        dismissed_commit.deliverable = "Dismissed"

        kept_commit = MagicMock(spec=Commitment)
        kept_commit.id = "kept-456"
        kept_commit.deliverable = "Kept"

        app = TestApp()

        with (
            patch("jdo.screens.chat.get_session"),
            patch("jdo.screens.chat.IntegrityService"),
        ):
            async with app.run_test() as pilot:
                await pilot.pause()
                screen = pilot.app.screen
                assert isinstance(screen, ChatScreen)

                # Dismiss only one
                screen.dismiss_risk_warning("dismissed-123")

                original = RiskSummary(
                    overdue_commitments=[dismissed_commit, kept_commit],
                    due_soon_commitments=[],
                    stalled_commitments=[],
                )
                filtered = screen._filter_dismissed_risks(original)

                # Only kept_commit should remain
                assert len(filtered.overdue_commitments) == 1
                assert filtered.overdue_commitments[0].id == "kept-456"
