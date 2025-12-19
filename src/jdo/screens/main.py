"""Main screen with navigation sidebar and chat interface.

The MainScreen is the primary interface that combines:
- NavSidebar for navigation
- Chat panel for AI interaction
- Data panel for viewing/editing entities

This replaces the previous HomeScreen → ChatScreen navigation flow.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar
from uuid import UUID

from loguru import logger
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.worker import get_current_worker

from jdo.ai.agent import JDODependencies, create_agent
from jdo.ai.context import stream_response
from jdo.ai.time_context import calculate_allocated_hours
from jdo.auth.api import is_authenticated
from jdo.commands.draft_patch import apply_patch, parse_entity_type
from jdo.commands.handlers import HandlerResult, get_handler
from jdo.commands.parser import CommandType, ParseError, parse_command
from jdo.config import get_settings
from jdo.db.persistence import PersistenceError, PersistenceService
from jdo.db.session import get_session, get_triage_count
from jdo.integrity import IntegrityService, RiskSummary
from jdo.models.draft import EntityType
from jdo.widgets.chat_container import ChatContainer
from jdo.widgets.chat_message import MessageRole, create_error_message
from jdo.widgets.data_panel import DataPanel, PanelMode
from jdo.widgets.nav_sidebar import NavSidebar
from jdo.widgets.prompt_input import PromptInput


class ConfirmationState(str, Enum):
    """State for tracking confirmation flow.

    States:
    - IDLE: Normal chat mode
    - AWAITING_CONFIRMATION: Draft shown, waiting for yes/no
    - SAVING: Persistence in progress
    """

    IDLE = "idle"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    SAVING = "saving"


# Words that indicate confirmation
_CONFIRMATION_WORDS = frozenset(
    {"yes", "y", "confirm", "ok", "sure", "yep", "yeah", "yup", "affirmative"}
)

# Words that indicate cancellation
_CANCELLATION_WORDS = frozenset(
    {"no", "n", "cancel", "nope", "nah", "nevermind", "never mind", "abort"}
)


@dataclass
class MainScreenConfig:
    """Configuration for MainScreen initialization.

    Groups related initialization parameters for cleaner API.
    """

    draft_id: UUID | None = None
    triage_mode: bool = False
    initial_mode: str | None = None
    initial_entity_type: str | None = None
    initial_data: list[dict[str, Any]] | dict[str, Any] | None = None


class MainScreen(Screen[None]):
    """Main interface with navigation sidebar and chat.

    Layout:
    - NavSidebar (docked left, collapsible)
    - Content area:
      - Chat panel (60%): Chat messages and prompt input
      - Data panel (40%): Structured data display

    Keyboard shortcuts:
    - Tab: Cycle focus: sidebar → prompt → panel
    - Escape: Context-aware (clear input, unfocus, or quit confirmation)
    - p: Toggle data panel visibility
    - [: Toggle sidebar collapse
    - 1-9: Quick nav to sidebar items
    """

    DEFAULT_CSS = """
    MainScreen {
        width: 100%;
        height: 100%;
    }

    MainScreen #main-content {
        width: 100%;
        height: 100%;
    }

    MainScreen #content-area {
        width: 1fr;
        height: 100%;
    }

    MainScreen #chat-panel {
        width: 60%;
        height: 100%;
    }

    MainScreen #chat-panel.expanded {
        width: 100%;
    }

    MainScreen ChatContainer {
        height: 1fr;
        border: solid $primary;
    }

    MainScreen PromptInput {
        height: auto;
        max-height: 10;
        border: solid $accent;
        margin-top: 1;
    }

    MainScreen DataPanel {
        width: 40%;
    }

    MainScreen DataPanel.hidden {
        display: none;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("tab", "cycle_focus", "Switch panel", show=False),
        Binding("escape", "handle_escape", "Back", show=False),
        Binding("p", "toggle_panel", "Toggle panel"),
        Binding("r", "mark_at_risk", "At-risk", show=True),
        Binding("[", "toggle_sidebar", "Toggle sidebar", show=False),
    ]

    def __init__(
        self,
        config: MainScreenConfig | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the main screen.

        Args:
            config: Configuration for screen initialization. Defaults to empty config.
            name: Widget name.
            id: Widget ID.
            classes: CSS classes.
        """
        super().__init__(name=name, id=id, classes=classes)
        config = config or MainScreenConfig()
        self._panel_visible = True
        self._draft_id = config.draft_id
        self._triage_mode = config.triage_mode
        self._initial_mode = config.initial_mode
        self._initial_entity_type = config.initial_entity_type
        self._initial_data = config.initial_data
        # Conversation history for AI context
        self._conversation: list[dict[str, str]] = []
        # Track if AI is currently streaming
        self._ai_streaming = False
        # Confirmation state tracking
        self._confirmation_state = ConfirmationState.IDLE
        self._pending_draft: dict[str, Any] | None = None
        self._pending_entity_type: str | None = None
        self._proposed_entity_type: str | None = None
        # Session-scoped set of dismissed risk warning commitment IDs
        self._dismissed_risk_warnings: set[str] = set()
        # Available hours remaining for time coaching
        self._available_hours_remaining: float | None = None

    def set_draft_id(self, draft_id: UUID) -> None:
        """Set the draft ID for restore.

        Args:
            draft_id: ID of the draft to restore.
        """
        self._draft_id = draft_id

    def set_triage_mode(self, enabled: bool) -> None:
        """Enable or disable triage mode.

        Args:
            enabled: Whether triage mode should be enabled.
        """
        self._triage_mode = enabled

    def compose(self) -> ComposeResult:
        """Compose the main screen layout."""
        with Horizontal(id="main-content"):
            yield NavSidebar(id="nav-sidebar")
            with Horizontal(id="content-area"):
                with Vertical(id="chat-panel"):
                    yield ChatContainer(id="chat-container")
                    yield PromptInput(id="prompt-input")
                yield DataPanel(id="data-panel")

    def on_mount(self) -> None:
        """Handle mount event."""
        # Focus the prompt input on mount
        prompt = self.query_one("#prompt-input", PromptInput)
        prompt.focus()

        # Update triage badge
        self._update_triage_badge()

        # If initial data provided, display it in the panel
        if self._initial_mode and self._initial_entity_type:
            self._display_initial_data()

        # Run risk detection asynchronously
        self.run_worker(self._detect_and_show_risks(), name="risk_detection")

    def _update_triage_badge(self) -> None:
        """Update the triage badge count in the sidebar."""
        try:
            with get_session() as session:
                count = get_triage_count(session)
                sidebar = self.query_one("#nav-sidebar", NavSidebar)
                sidebar.set_triage_count(count)
        except Exception:
            # Database may not be initialized (e.g., in tests)
            logger.debug("Could not update triage badge - database may not be initialized")

    def _display_initial_data(self) -> None:
        """Display initial data in the panel if provided."""
        if not self._initial_mode:
            return

        panel_update: dict[str, Any] = {
            "mode": self._initial_mode,
            "entity_type": self._initial_entity_type or "",
        }

        if isinstance(self._initial_data, list):
            panel_update["items"] = self._initial_data
        else:
            panel_update["data"] = self._initial_data or {}

        self._update_data_panel(panel_update)

    async def _detect_and_show_risks(self) -> None:
        """Detect at-risk commitments and display alerts."""
        try:
            with get_session() as session:
                service = IntegrityService()
                summary = service.detect_risks(session)

                # Filter out dismissed commitments
                filtered_summary = self._filter_dismissed_risks(summary)

                if filtered_summary.has_risks:
                    message = self._format_risk_message(filtered_summary)
                    await self.chat_container.add_message(MessageRole.SYSTEM, message)

        except Exception as e:
            # Don't block chat startup if risk detection fails
            logger.warning(f"Risk detection failed: {e}")

    def _filter_dismissed_risks(self, summary: RiskSummary) -> RiskSummary:
        """Filter out risks that have been dismissed this session."""
        return RiskSummary(
            overdue_commitments=[
                c
                for c in summary.overdue_commitments
                if str(c.id) not in self._dismissed_risk_warnings
            ],
            due_soon_commitments=[
                c
                for c in summary.due_soon_commitments
                if str(c.id) not in self._dismissed_risk_warnings
            ],
            stalled_commitments=[
                c
                for c in summary.stalled_commitments
                if str(c.id) not in self._dismissed_risk_warnings
            ],
        )

    def dismiss_risk_warning(self, commitment_id: str) -> None:
        """Dismiss a risk warning for a commitment this session."""
        self._dismissed_risk_warnings.add(commitment_id)

    def _format_risk_message(self, summary: RiskSummary) -> str:
        """Format a risk summary as a user-friendly message."""
        lines = ["⚠️ **Commitments need attention:**", ""]

        for c in summary.overdue_commitments:
            lines.append(f"• **OVERDUE**: {c.deliverable}")
            if c.due_date:
                lines.append(f"  Due: {c.due_date}")

        for c in summary.due_soon_commitments:
            lines.append(f"• **DUE SOON**: {c.deliverable}")
            if c.due_date:
                lines.append(f"  Due: {c.due_date} (not started)")

        for c in summary.stalled_commitments:
            lines.append(f"• **STALLED**: {c.deliverable}")
            if c.due_date:
                lines.append(f"  Due: {c.due_date} (no recent activity)")

        lines.append("")
        lines.append("Would you like to mark any as at-risk? Use `/atrisk` to start.")

        return "\n".join(lines)

    def action_cycle_focus(self) -> None:
        """Cycle focus between sidebar, prompt, and data panel."""
        sidebar = self.query_one("#nav-sidebar", NavSidebar)
        prompt = self.query_one("#prompt-input", PromptInput)
        data_panel = self.query_one("#data-panel", DataPanel)

        if sidebar.has_focus:
            prompt.focus()
        elif prompt.has_focus:
            if self._panel_visible:
                data_panel.focus()
            else:
                sidebar.focus()
        else:
            sidebar.focus()

    def action_handle_escape(self) -> None:
        """Handle escape key with context-aware behavior."""
        prompt = self.query_one("#prompt-input", PromptInput)

        if not prompt.has_focus:
            # Move focus to prompt
            prompt.focus()
        elif prompt.text.strip():
            # Clear the prompt if it has content
            prompt.clear()
        else:
            # Prompt is focused and empty - post quit request
            self.post_message(self.QuitRequested())

    def action_toggle_panel(self) -> None:
        """Toggle data panel visibility."""
        data_panel = self.query_one("#data-panel", DataPanel)
        chat_panel = self.query_one("#chat-panel", Vertical)

        self._panel_visible = not self._panel_visible

        if self._panel_visible:
            data_panel.display = True
            data_panel.remove_class("hidden")
            chat_panel.remove_class("expanded")
        else:
            data_panel.display = False
            data_panel.add_class("hidden")
            chat_panel.add_class("expanded")

    def action_toggle_sidebar(self) -> None:
        """Toggle sidebar collapse state."""
        sidebar = self.query_one("#nav-sidebar", NavSidebar)
        sidebar.toggle_collapse()

    async def action_mark_at_risk(self) -> None:
        """Mark the currently viewed commitment as at-risk."""
        panel = self.data_panel

        if panel.mode == PanelMode.VIEW and panel.entity_type == "commitment":
            status = panel.current_data.get("status")
            if hasattr(status, "value"):
                status = status.value

            if status == "at_risk":
                await self.chat_container.add_message(
                    MessageRole.ASSISTANT,
                    "This commitment is already marked at-risk. "
                    "Use /cleanup to view or update the cleanup plan.",
                )
                return

            await self._handle_command("/atrisk")
        else:
            await self.chat_container.add_message(
                MessageRole.ASSISTANT,
                "No commitment selected. View a commitment first, then press 'r' "
                "to mark it at-risk, or use /atrisk to select one.",
            )

    @property
    def chat_container(self) -> ChatContainer:
        """Get the chat container widget."""
        return self.query_one("#chat-container", ChatContainer)

    @property
    def prompt_input(self) -> PromptInput:
        """Get the prompt input widget."""
        return self.query_one("#prompt-input", PromptInput)

    @property
    def data_panel(self) -> DataPanel:
        """Get the data panel widget."""
        return self.query_one("#data-panel", DataPanel)

    @property
    def nav_sidebar(self) -> NavSidebar:
        """Get the navigation sidebar widget."""
        return self.query_one("#nav-sidebar", NavSidebar)

    def _has_ai_credentials(self) -> bool:
        """Check if AI credentials are configured."""
        settings = get_settings()
        return is_authenticated(settings.ai_provider)

    async def on_prompt_input_submitted(self, event: PromptInput.Submitted) -> None:
        """Handle user message submission."""
        text = event.text.strip()
        if not text:
            return

        if self._confirmation_state == ConfirmationState.SAVING:
            await self.chat_container.add_message(
                MessageRole.ASSISTANT,
                "Saving… please wait a moment.",
            )
            return

        if self._confirmation_state == ConfirmationState.AWAITING_CONFIRMATION:
            await self._handle_confirmation_response(text)
            return

        if text.startswith("/"):
            await self._handle_command(text)
            return

        await self.chat_container.add_message(MessageRole.USER, text)
        self._conversation.append({"role": "user", "content": text})

        self._send_to_ai(text)

    async def _handle_command(self, text: str) -> None:
        """Handle a slash command."""
        await self.chat_container.add_message(MessageRole.USER, text)

        try:
            parsed = parse_command(text)
        except ParseError as e:
            await self.chat_container.add_message(
                MessageRole.ASSISTANT,
                f"Unknown command. {e}\n\nType /help to see available commands.",
            )
            return

        handler = get_handler(parsed.command_type)

        if handler is None:
            logger.warning(f"No handler for command type: {parsed.command_type}")
            return

        context = self._build_handler_context()
        result = handler.execute(parsed, context)

        await self._display_handler_result(result)

        if result.needs_confirmation and result.draft_data:
            self._confirmation_state = ConfirmationState.AWAITING_CONFIRMATION
            self._pending_draft = result.draft_data
            if result.panel_update:
                self._pending_entity_type = result.panel_update.get("entity_type")

            if not self._pending_entity_type:
                self._pending_entity_type = EntityType.UNKNOWN.value

            logger.debug(
                f"Awaiting confirmation for {self._pending_entity_type}: {self._pending_draft}"
            )

    async def _handle_type_assignment_request(self, text: str) -> None:
        """Handle a type assignment request for an untyped draft."""
        entity_type = parse_entity_type(text)

        if entity_type is None and text.startswith("/type"):
            try:
                parsed = parse_command(text)
            except ParseError:
                parsed = None

            if parsed and parsed.command_type == CommandType.TYPE and parsed.args:
                entity_type = parse_entity_type(parsed.args[0])

        if entity_type is None:
            await self.chat_container.add_message(
                MessageRole.ASSISTANT,
                "Please assign a type first: commitment, goal, task, vision, or milestone. "
                "You can reply with the type name or use /type <type>.",
            )
            return

        if not self._pending_draft:
            msg = "No draft available to type"
            raise RuntimeError(msg)
        self._proposed_entity_type = entity_type.value
        await self.chat_container.add_message(
            MessageRole.ASSISTANT,
            f"Set draft type to '{entity_type.value}'? (y/n)",
        )

    async def _apply_modification_request(self, text: str) -> None:
        """Apply a modification request while awaiting confirmation."""
        if not self._pending_draft or not self._pending_entity_type:
            await self.chat_container.add_message(
                MessageRole.ASSISTANT,
                "No draft is currently pending confirmation.",
            )
            self._clear_confirmation_state()
            return

        if self._pending_entity_type == EntityType.UNKNOWN.value:
            await self._handle_type_assignment_request(text)
            return

        entity_type = (
            parse_entity_type(self._pending_entity_type) if self._pending_entity_type else None
        )
        if entity_type is None:
            await self.chat_container.add_message(
                MessageRole.ASSISTANT,
                "I couldn't determine the draft type. Please set it with /type <type>.",
            )
            return

        patch_result = apply_patch(entity_type, self._pending_draft, text)
        if not patch_result.applied:
            await self.chat_container.add_message(
                MessageRole.ASSISTANT,
                patch_result.error or "I couldn't apply that change.",
            )
            return

        self._pending_draft = patch_result.updated
        self._update_data_panel(
            {
                "mode": "draft",
                "entity_type": self._pending_entity_type,
                "data": self._pending_draft,
            }
        )

        if patch_result.summary:
            await self.chat_container.add_message(MessageRole.ASSISTANT, patch_result.summary)

        await self.chat_container.add_message(
            MessageRole.ASSISTANT,
            "Confirm the updated draft? (y/n)",
        )

    def _get_allocated_hours(self) -> float:
        """Calculate total allocated hours from active tasks."""
        try:
            with get_session() as session:
                allocated, _task_count, _without_estimates = calculate_allocated_hours(session)
                return allocated
        except Exception as e:
            logger.warning(f"Failed to calculate allocated hours: {e}")
            return 0.0

    def _build_handler_context(self) -> dict[str, Any]:
        """Build context dict for command handlers."""
        context: dict[str, Any] = {
            "conversation": self._conversation,
            "available_visions": [],
            "available_commitments": [],
            "goals": [],
            "commitments": [],
            "available_hours_remaining": self._available_hours_remaining,
            "allocated_hours": self._get_allocated_hours(),
        }

        panel = self.data_panel
        if panel.mode == PanelMode.VIEW and panel.entity_type == "commitment":
            context["current_commitment"] = panel.current_data
            context["current_commitment_id"] = panel.current_data.get("id")

        return context

    async def _display_handler_result(self, result: HandlerResult) -> None:
        """Display the result of a command handler."""
        if result.message:
            await self.chat_container.add_message(MessageRole.ASSISTANT, result.message)

        if result.panel_update:
            self._update_data_panel(result.panel_update)

    def _update_data_panel(self, panel_update: dict[str, Any]) -> None:
        """Update the data panel based on handler result."""
        mode = panel_update.get("mode", "list")
        entity_type = panel_update.get("entity_type", "")

        if mode == "list":
            items = panel_update.get("items", [])
            self.data_panel.show_list(entity_type, items)
        elif mode == "draft":
            data = panel_update.get("data", {})
            self._show_draft_in_panel(entity_type, data)
        elif mode == "view":
            data = panel_update.get("data", {})
            self._show_view_in_panel(entity_type, data)
        elif mode == "integrity":
            data = panel_update.get("data", {})
            self.data_panel.show_integrity_dashboard(data)
        elif mode == "cleanup":
            data = panel_update.get("data", {})
            self.data_panel.show_cleanup_plan(data)
        elif mode == "atrisk_workflow":
            data = panel_update.get("data", {})
            workflow_step = panel_update.get("workflow_step", "reason")
            self.data_panel.show_atrisk_workflow(data, workflow_step)
        elif mode == "hours_set":
            hours = panel_update.get("hours")
            if hours is not None:
                self._available_hours_remaining = float(hours)
        elif mode == "hours":
            pass

    def _show_draft_in_panel(self, entity_type: str, data: dict[str, Any]) -> None:
        """Show a draft in the data panel."""
        panel = self.data_panel
        method_name = f"show_{entity_type}_draft"

        if hasattr(panel, method_name):
            getattr(panel, method_name)(data)
        else:
            panel.show_draft(entity_type, data)

    def _show_view_in_panel(self, entity_type: str, data: dict[str, Any]) -> None:
        """Show an entity view in the data panel."""
        panel = self.data_panel
        method_name = f"show_{entity_type}_view"

        if hasattr(panel, method_name):
            getattr(panel, method_name)(data)
        else:
            panel.show_view(entity_type, data)

    def _is_confirmation(self, text: str) -> bool:
        """Check if text is a confirmation response."""
        normalized = text.lower().strip()
        return normalized in _CONFIRMATION_WORDS

    def _is_cancellation(self, text: str) -> bool:
        """Check if text is a cancellation response."""
        normalized = text.lower().strip()
        if normalized == "/cancel":
            return True
        return normalized in _CANCELLATION_WORDS

    async def _handle_confirmation_response(self, text: str) -> None:
        """Handle user response when awaiting confirmation."""
        await self.chat_container.add_message(MessageRole.USER, text)

        if self._is_confirmation(text):
            if self._pending_draft and self._proposed_entity_type:
                self._pending_entity_type = self._proposed_entity_type
                self._proposed_entity_type = None
                self._update_data_panel(
                    {
                        "mode": "draft",
                        "entity_type": self._pending_entity_type,
                        "data": self._pending_draft,
                    }
                )
                await self.chat_container.add_message(
                    MessageRole.ASSISTANT,
                    f"Type set to '{self._pending_entity_type}'. What would you like to change?",
                )
                return

            await self._save_pending_entity()
        elif self._is_cancellation(text):
            await self._cancel_pending_draft()
        else:
            await self._apply_modification_request(text)

    async def _save_pending_entity(self) -> None:
        """Save the pending entity to the database."""
        if not self._pending_draft or not self._pending_entity_type:
            logger.warning("No pending draft to save")
            self._clear_confirmation_state()
            return

        self._confirmation_state = ConfirmationState.SAVING
        self.prompt_input.disabled = True

        try:
            with get_session() as session:
                service = PersistenceService(session)
                saved_entity = self._save_entity(service)

                if saved_entity:
                    entity_name = self._pending_entity_type.replace("_", " ")
                    await self.chat_container.add_message(
                        MessageRole.ASSISTANT,
                        f"Done! Your {entity_name} has been saved.",
                    )

                    entity_data = self._entity_to_dict(saved_entity)
                    self._show_view_in_panel(self._pending_entity_type, entity_data)

        except PersistenceError as e:
            logger.error(f"Failed to save entity: {e}")
            await self.chat_container.add_message(
                MessageRole.ASSISTANT,
                f"Couldn't save: {e}\n\nPlease try again or type 'no' to cancel.",
            )
            self._confirmation_state = ConfirmationState.AWAITING_CONFIRMATION
            return

        except Exception:
            logger.exception("Unexpected error saving entity")
            await self.chat_container.add_message(
                MessageRole.ASSISTANT,
                "Something went wrong while saving. Please try again.",
            )
            self._confirmation_state = ConfirmationState.AWAITING_CONFIRMATION
            return

        finally:
            self.prompt_input.disabled = False
            self.prompt_input.focus()

        self._clear_confirmation_state()

    def _save_entity(self, service: PersistenceService) -> Any:  # noqa: ANN401
        """Save the pending entity using the persistence service."""
        entity_type = self._pending_entity_type
        draft = self._pending_draft

        if not entity_type or not draft:
            return None

        save_methods = {
            "commitment": service.save_commitment,
            "goal": service.save_goal,
            "task": service.save_task,
            "milestone": service.save_milestone,
            "vision": service.save_vision,
            "recurring_commitment": service.save_recurring_commitment,
        }

        save_method = save_methods.get(entity_type)
        if save_method:
            return save_method(draft)

        logger.warning(f"Unknown entity type for persistence: {entity_type}")
        return None

    def _entity_to_dict(self, entity: Any) -> dict[str, Any]:  # noqa: ANN401
        """Convert a SQLModel entity to a dict for display."""
        if hasattr(entity, "model_dump"):
            return entity.model_dump()
        if hasattr(entity, "dict"):
            return entity.dict()
        return {"id": getattr(entity, "id", None)}

    async def _cancel_pending_draft(self) -> None:
        """Cancel the pending draft and clear confirmation state."""
        entity_name = (self._pending_entity_type or "draft").replace("_", " ")

        await self.chat_container.add_message(
            MessageRole.ASSISTANT,
            f"Cancelled {entity_name}. What would you like to do next?",
        )

        self.data_panel.show_list("commitment", [])

        self._clear_confirmation_state()

    def _clear_confirmation_state(self) -> None:
        """Clear all confirmation state."""
        self._confirmation_state = ConfirmationState.IDLE
        self._pending_draft = None
        self._pending_entity_type = None

    def _send_to_ai(self, prompt: str) -> None:
        """Send a message to the AI agent and stream the response."""
        self.run_worker(
            self._do_ai_streaming(prompt),
            exclusive=True,
            name="ai_streaming",
        )

    async def _do_ai_streaming(self, prompt: str) -> None:
        """Execute the AI streaming call."""
        worker = get_current_worker()

        if not self._has_ai_credentials():
            error_msg = create_error_message(
                "AI not configured. Please add your API key in settings.",
                recoverable=True,
            )
            await self.chat_container.mount(error_msg)
            self.chat_container.scroll_end(animate=False)
            return

        assistant_msg = await self.chat_container.add_message(MessageRole.ASSISTANT, "Thinking...")
        assistant_msg.set_thinking(True)
        self._ai_streaming = True
        self.prompt_input.disabled = True

        accumulated_text = ""

        try:
            with get_session() as session:
                settings = get_settings()
                deps = JDODependencies(session=session, timezone=settings.timezone)
                agent = create_agent()

                async for chunk in stream_response(agent, prompt, deps, self._conversation):
                    if worker.is_cancelled:
                        logger.debug("AI streaming cancelled by user")
                        break

                    accumulated_text += chunk
                    assistant_msg.update_content(accumulated_text)

            assistant_msg.set_thinking(False)

            if accumulated_text:
                self._conversation.append({"role": "assistant", "content": accumulated_text})

        except Exception as e:
            logger.exception("AI streaming error")
            error_text = self._get_error_message(e)
            assistant_msg.update_content(f"Error: {error_text}")
            assistant_msg.set_thinking(False)
            assistant_msg.add_class("-system")

        finally:
            self._ai_streaming = False
            self.prompt_input.disabled = False
            self.prompt_input.focus()

    def _get_error_message(self, error: Exception) -> str:
        """Get a user-friendly error message for AI errors."""
        error_str = str(error).lower()

        if "rate" in error_str or "429" in error_str:
            return "AI is busy. Please wait a moment and try again."

        if "auth" in error_str or "401" in error_str or "403" in error_str:
            return "AI authentication failed. Check your API key in settings."

        if "connect" in error_str or "network" in error_str or "timeout" in error_str:
            return "Couldn't reach AI provider. Check your connection."

        return "Something went wrong. Your message was not processed."

    # Handle sidebar navigation
    def on_nav_sidebar_selected(self, message: NavSidebar.Selected) -> None:
        """Handle navigation selection from NavSidebar."""
        item_id = message.item_id
        logger.debug(f"NavSidebar selection: {item_id}")

        # Settings is special - it pushes a screen
        if item_id == "settings":
            self.post_message(self.OpenSettings())
            return

        # Other selections update the data panel
        self.post_message(self.NavigationSelected(item_id))

    # Custom messages for parent app to handle
    class QuitRequested(Message):
        """Message when user wants to quit (Escape on empty prompt)."""

    class OpenSettings(Message):
        """Message to open settings screen."""

    class NavigationSelected(Message):
        """Message when a navigation item is selected."""

        def __init__(self, item_id: str) -> None:
            """Initialize with the selected item ID."""
            self.item_id = item_id
            super().__init__()
