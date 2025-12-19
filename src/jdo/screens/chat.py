"""Chat screen with split-panel layout.

The main chat interface with:
- Chat panel on left (60%) - messages and prompt
- Data panel on right (40%) - structured data display
- Responsive collapse on narrow terminals
- AI agent integration with streaming responses
- Command routing and confirmation flow
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
from jdo.auth.api import is_authenticated
from jdo.commands.draft_patch import apply_patch, parse_entity_type
from jdo.commands.handlers import HandlerResult, get_handler
from jdo.commands.parser import CommandType, ParseError, parse_command
from jdo.config import get_settings
from jdo.db.persistence import PersistenceError, PersistenceService
from jdo.db.session import get_session
from jdo.integrity import IntegrityService, RiskSummary
from jdo.models.draft import EntityType
from jdo.widgets.chat_container import ChatContainer
from jdo.widgets.chat_message import MessageRole, create_error_message
from jdo.widgets.data_panel import DataPanel, PanelMode
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
class ChatScreenConfig:
    """Configuration for ChatScreen initialization.

    Groups related initialization parameters for cleaner API.
    """

    draft_id: UUID | None = None
    triage_mode: bool = False
    initial_mode: str | None = None
    initial_entity_type: str | None = None
    initial_data: list[dict[str, Any]] | dict[str, Any] | None = None


class ChatScreen(Screen[None]):
    """Main chat interface with split-panel layout.

    Layout:
    - Left panel (60%): Chat messages and prompt input
    - Right panel (40%): Data panel for drafts/views/lists

    Keyboard shortcuts:
    - Tab: Toggle focus between chat and data panel
    - Escape: Return to home (or focus prompt first if not focused)
    - p: Toggle data panel visibility
    """

    DEFAULT_CSS = """
    ChatScreen {
        width: 100%;
        height: 100%;
    }

    ChatScreen Horizontal {
        width: 100%;
        height: 100%;
    }

    ChatScreen #chat-panel {
        width: 60%;
        height: 100%;
    }

    ChatScreen #chat-panel.expanded {
        width: 100%;
    }

    ChatScreen ChatContainer {
        height: 1fr;
        border: solid $primary;
    }

    ChatScreen PromptInput {
        height: auto;
        max-height: 10;
        border: solid $accent;
        margin-top: 1;
    }

    ChatScreen DataPanel {
        width: 40%;
    }

    ChatScreen DataPanel.hidden {
        display: none;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("tab", "toggle_focus", "Switch panel", show=False),
        Binding("escape", "back", "Back", show=False),
        Binding("p", "toggle_panel", "Toggle panel"),
        Binding("r", "mark_at_risk", "At-risk", show=True),
    ]

    def __init__(
        self,
        config: ChatScreenConfig | None = None,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        """Initialize the chat screen.

        Args:
            config: Configuration for screen initialization. Defaults to empty config.
            name: Widget name.
            id: Widget ID.
            classes: CSS classes.
        """
        super().__init__(name=name, id=id, classes=classes)
        config = config or ChatScreenConfig()
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

    def compose(self) -> ComposeResult:
        """Compose the chat screen layout."""
        with Horizontal():
            with Vertical(id="chat-panel"):
                yield ChatContainer(id="chat-container")
                yield PromptInput(id="prompt-input")
            yield DataPanel(id="data-panel")

    def on_mount(self) -> None:
        """Handle mount event."""
        # Focus the prompt input on mount
        prompt = self.query_one("#prompt-input", PromptInput)
        prompt.focus()

        # If initial data provided, display it in the panel
        if self._initial_mode and self._initial_entity_type is not None:
            self._display_initial_data()

        # Run risk detection asynchronously
        self.run_worker(self._detect_and_show_risks(), name="risk_detection")

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
        """Detect at-risk commitments and display alerts.

        Queries for:
        - Overdue commitments
        - Commitments due soon with no progress
        - Stalled commitments (in_progress but no recent activity)

        Filters out commitments that have been dismissed this session.
        """
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
        """Filter out risks that have been dismissed this session.

        Args:
            summary: The original risk summary.

        Returns:
            A new RiskSummary with dismissed commitments filtered out.
        """
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
        """Dismiss a risk warning for a commitment this session.

        The warning won't be shown again for this commitment during
        this chat session.

        Args:
            commitment_id: The ID of the commitment to dismiss warnings for.
        """
        self._dismissed_risk_warnings.add(commitment_id)

    def _format_risk_message(self, summary: RiskSummary) -> str:
        """Format a risk summary as a user-friendly message.

        Args:
            summary: The risk summary from IntegrityService.

        Returns:
            Formatted message string.
        """
        lines = ["⚠️ **Commitments need attention:**", ""]

        # Overdue commitments (most urgent)
        for c in summary.overdue_commitments:
            lines.append(f"• **OVERDUE**: {c.deliverable}")
            if c.due_date:
                lines.append(f"  Due: {c.due_date}")

        # Due soon with no progress
        for c in summary.due_soon_commitments:
            lines.append(f"• **DUE SOON**: {c.deliverable}")
            if c.due_date:
                lines.append(f"  Due: {c.due_date} (not started)")

        # Stalled commitments
        for c in summary.stalled_commitments:
            lines.append(f"• **STALLED**: {c.deliverable}")
            if c.due_date:
                lines.append(f"  Due: {c.due_date} (no recent activity)")

        lines.append("")
        lines.append("Would you like to mark any as at-risk? Use `/atrisk` to start.")

        return "\n".join(lines)

    def action_toggle_focus(self) -> None:
        """Toggle focus between chat panel and data panel."""
        data_panel = self.query_one("#data-panel", DataPanel)
        prompt = self.query_one("#prompt-input", PromptInput)

        if prompt.has_focus:
            data_panel.focus()
        else:
            prompt.focus()

    def action_focus_prompt(self) -> None:
        """Return focus to the prompt input."""
        prompt = self.query_one("#prompt-input", PromptInput)
        prompt.focus()

    def action_back(self) -> None:
        """Go back to home screen.

        If prompt doesn't have focus, focus it first.
        If prompt has focus and is empty, go back to home.
        """
        prompt = self.query_one("#prompt-input", PromptInput)
        if not prompt.has_focus:
            prompt.focus()
        elif not prompt.text.strip():
            # Prompt is focused and empty, go back
            self.post_message(ChatScreen.Back())
        else:
            # Prompt has content, just focus it (no-op since already focused)
            pass

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

    async def action_mark_at_risk(self) -> None:
        """Mark the currently viewed commitment as at-risk.

        If a commitment is being viewed in the data panel, this triggers
        the /atrisk command workflow. Otherwise, shows a guidance message.
        """
        panel = self.data_panel

        # Check if we're viewing a commitment
        if panel.mode == PanelMode.VIEW and panel.entity_type == "commitment":
            # Check if commitment is already at_risk
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

            # Trigger the /atrisk command workflow
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

    def _has_ai_credentials(self) -> bool:
        """Check if AI credentials are configured.

        Returns:
            True if API key or OAuth token exists for the provider.
        """
        settings = get_settings()
        return is_authenticated(settings.ai_provider)

    async def on_prompt_input_submitted(self, event: PromptInput.Submitted) -> None:
        """Handle user message submission.

        Message flow:
        1. Check confirmation state - if awaiting, handle yes/no first
        2. Check for commands (starting with /)
        3. Otherwise, send to AI

        Args:
            event: The submitted message event.
        """
        text = event.text.strip()
        if not text:
            return

        # If we're currently saving, ignore new input.
        if self._confirmation_state == ConfirmationState.SAVING:
            await self.chat_container.add_message(
                MessageRole.ASSISTANT,
                "Saving… please wait a moment.",
            )
            return

        # Check confirmation state FIRST (before any other processing)
        if self._confirmation_state == ConfirmationState.AWAITING_CONFIRMATION:
            await self._handle_confirmation_response(text)
            return

        # Check for commands (starting with /)
        if text.startswith("/"):
            await self._handle_command(text)
            return

        # Add user message to chat and history
        await self.chat_container.add_message(MessageRole.USER, text)
        self._conversation.append({"role": "user", "content": text})

        # Send to AI
        self._send_to_ai(text)

    async def _handle_command(self, text: str) -> None:
        """Handle a slash command.

        Parses the command, routes to the appropriate handler,
        displays the result, and sets confirmation state if needed.

        Args:
            text: The command text (starting with /).
        """
        # Show the command in chat
        await self.chat_container.add_message(MessageRole.USER, text)

        try:
            parsed = parse_command(text)
        except ParseError as e:
            # Unknown command
            await self.chat_container.add_message(
                MessageRole.ASSISTANT,
                f"Unknown command. {e}\n\nType /help to see available commands.",
            )
            return

        # Get the handler for this command type
        handler = get_handler(parsed.command_type)

        if handler is None:
            # MESSAGE type - shouldn't happen since we check for /
            logger.warning(f"No handler for command type: {parsed.command_type}")
            return

        # Build context for the handler
        context = self._build_handler_context()

        # Execute the handler
        result = handler.execute(parsed, context)

        # Display the result
        await self._display_handler_result(result)

        # Set confirmation state if needed
        if result.needs_confirmation and result.draft_data:
            self._confirmation_state = ConfirmationState.AWAITING_CONFIRMATION
            self._pending_draft = result.draft_data
            # Get entity type from panel_update
            if result.panel_update:
                self._pending_entity_type = result.panel_update.get("entity_type")

            # If handler didn't set a concrete type, gate with UNKNOWN.
            if not self._pending_entity_type:
                self._pending_entity_type = EntityType.UNKNOWN.value

            logger.debug(
                f"Awaiting confirmation for {self._pending_entity_type}: {self._pending_draft}"
            )

    async def _handle_type_assignment_request(self, text: str) -> None:
        """Handle a type assignment request for an untyped draft.

        The user may provide a type explicitly (plain text), otherwise we require
        the user to use /type.

        Args:
            text: User input.
        """
        entity_type = parse_entity_type(text)

        # Support explicit /type command as well as plain text.
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

        # Require confirmation for all type assignments.
        if not self._pending_draft:
            msg = "No draft available to type"
            raise RuntimeError(msg)
        self._proposed_entity_type = entity_type.value
        await self.chat_container.add_message(
            MessageRole.ASSISTANT,
            f"Set draft type to '{entity_type.value}'? (y/n)",
        )

    async def _apply_modification_request(self, text: str) -> None:
        """Apply a modification request while awaiting confirmation.

        This implementation enforces typed drafts:
        - If the draft has no true type yet, the message is treated as a request
          to assign a type (commitment/goal/task/vision/milestone).
        - Once typed, the message is treated as a rules-based patch request.
        - The confirmation state remains active so the user can confirm after edits.

        Args:
            text: The user's free-form modification request.
        """
        if not self._pending_draft or not self._pending_entity_type:
            await self.chat_container.add_message(
                MessageRole.ASSISTANT,
                "No draft is currently pending confirmation.",
            )
            self._clear_confirmation_state()
            return

        # Enforce true typing before refinement.
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

    def _build_handler_context(self) -> dict[str, Any]:
        """Build context dict for command handlers.

        Returns:
            Context dict with conversation history and other data.
        """
        context: dict[str, Any] = {
            "conversation": self._conversation,
            # These would be populated from database queries in a full implementation
            "available_visions": [],
            "available_commitments": [],
            "goals": [],
            "commitments": [],
            # Time coaching context
            "available_hours_remaining": self._available_hours_remaining,
            "allocated_hours": 0.0,  # TODO: Calculate from active tasks
        }

        # Add current commitment context if viewing one
        panel = self.data_panel
        if panel.mode == PanelMode.VIEW and panel.entity_type == "commitment":
            context["current_commitment"] = panel.current_data
            context["current_commitment_id"] = panel.current_data.get("id")

        return context

    async def _display_handler_result(self, result: HandlerResult) -> None:
        """Display the result of a command handler.

        Args:
            result: The handler result to display.
        """
        # Show message in chat
        if result.message:
            await self.chat_container.add_message(MessageRole.ASSISTANT, result.message)

        # Update data panel
        if result.panel_update:
            self._update_data_panel(result.panel_update)

    def _update_data_panel(self, panel_update: dict[str, Any]) -> None:
        """Update the data panel based on handler result.

        Args:
            panel_update: Dict with mode, entity_type, and data/items.
        """
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
            # Update available hours in session state
            hours = panel_update.get("hours")
            if hours is not None:
                self._available_hours_remaining = float(hours)
        elif mode == "hours":
            # Just display, no state change
            pass

    def _show_draft_in_panel(self, entity_type: str, data: dict[str, Any]) -> None:
        """Show a draft in the data panel.

        Args:
            entity_type: Type of entity being drafted.
            data: Draft data to display.
        """
        panel = self.data_panel
        method_name = f"show_{entity_type}_draft"

        if hasattr(panel, method_name):
            getattr(panel, method_name)(data)
        else:
            # Use generic show_draft method
            panel.show_draft(entity_type, data)

    def _show_view_in_panel(self, entity_type: str, data: dict[str, Any]) -> None:
        """Show an entity view in the data panel.

        Args:
            entity_type: Type of entity being viewed.
            data: Entity data to display.
        """
        panel = self.data_panel
        method_name = f"show_{entity_type}_view"

        if hasattr(panel, method_name):
            getattr(panel, method_name)(data)
        else:
            # Use generic show_view method
            panel.show_view(entity_type, data)

    def _is_confirmation(self, text: str) -> bool:
        """Check if text is a confirmation response.

        Args:
            text: The user's input text.

        Returns:
            True if the text indicates confirmation.
        """
        normalized = text.lower().strip()
        return normalized in _CONFIRMATION_WORDS

    def _is_cancellation(self, text: str) -> bool:
        """Check if text is a cancellation response.

        Args:
            text: The user's input text.

        Returns:
            True if the text indicates cancellation.
        """
        normalized = text.lower().strip()
        # Also check for /cancel command
        if normalized == "/cancel":
            return True
        return normalized in _CANCELLATION_WORDS

    async def _handle_confirmation_response(self, text: str) -> None:
        """Handle user response when awaiting confirmation.

        Args:
            text: The user's response text.
        """
        # Show the response in chat
        await self.chat_container.add_message(MessageRole.USER, text)

        if self._is_confirmation(text):
            # If we are confirming a proposed draft type, apply it first.
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

            # User confirmed - save the entity
            await self._save_pending_entity()
        elif self._is_cancellation(text):
            # User cancelled - clear the draft
            await self._cancel_pending_draft()
        else:
            # Neither yes nor no: treat as a modification request.
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
                    # Show success message
                    entity_name = self._pending_entity_type.replace("_", " ")
                    await self.chat_container.add_message(
                        MessageRole.ASSISTANT,
                        f"Done! Your {entity_name} has been saved.",
                    )

                    # Update panel to view mode with saved entity
                    entity_data = self._entity_to_dict(saved_entity)
                    self._show_view_in_panel(self._pending_entity_type, entity_data)

        except PersistenceError as e:
            logger.error(f"Failed to save entity: {e}")
            await self.chat_container.add_message(
                MessageRole.ASSISTANT,
                f"Couldn't save: {e}\n\nPlease try again or type 'no' to cancel.",
            )
            # Stay in awaiting confirmation state so user can retry
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
        """Save the pending entity using the persistence service.

        Args:
            service: The persistence service to use.

        Returns:
            The saved entity, or None if entity type is unknown.
        """
        entity_type = self._pending_entity_type
        draft = self._pending_draft

        if not entity_type or not draft:
            return None

        # Map entity types to save methods
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
        """Convert a SQLModel entity to a dict for display.

        Args:
            entity: The entity to convert.

        Returns:
            Dict representation of the entity.
        """
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

        # Clear the panel
        self.data_panel.show_list("commitment", [])

        self._clear_confirmation_state()

    def _clear_confirmation_state(self) -> None:
        """Clear all confirmation state."""
        self._confirmation_state = ConfirmationState.IDLE
        self._pending_draft = None
        self._pending_entity_type = None

    def _send_to_ai(self, prompt: str) -> None:
        """Send a message to the AI agent and stream the response.

        This method uses a Textual worker to run the async AI call
        without blocking the UI. The worker is exclusive, meaning
        sending a new message cancels any in-progress response.

        Args:
            prompt: The user's message to send.
        """
        self.run_worker(
            self._do_ai_streaming(prompt),
            exclusive=True,
            name="ai_streaming",
        )

    async def _do_ai_streaming(self, prompt: str) -> None:
        """Execute the AI streaming call.

        Args:
            prompt: The user's message.
        """
        worker = get_current_worker()

        # Check credentials first
        if not self._has_ai_credentials():
            error_msg = create_error_message(
                "AI not configured. Please add your API key in settings "
                "(press 's' to open settings).",
                recoverable=True,
            )
            await self.chat_container.mount(error_msg)
            self.chat_container.scroll_end(animate=False)
            return

        # Create placeholder assistant message
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

            # Finalize the message
            assistant_msg.set_thinking(False)

            if accumulated_text:
                # Add to conversation history
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
        """Get a user-friendly error message for AI errors.

        Args:
            error: The exception that occurred.

        Returns:
            A user-friendly error message string.
        """
        error_str = str(error).lower()

        # Rate limit errors
        if "rate" in error_str or "429" in error_str:
            return "AI is busy. Please wait a moment and try again."

        # Authentication errors
        if "auth" in error_str or "401" in error_str or "403" in error_str:
            return "AI authentication failed. Check your API key in settings."

        # Network errors
        if "connect" in error_str or "network" in error_str or "timeout" in error_str:
            return "Couldn't reach AI provider. Check your connection."

        # Generic fallback
        return "Something went wrong. Your message was not processed."

    # Custom messages for parent app to handle
    class Back(Message):
        """Message to go back to home screen."""
