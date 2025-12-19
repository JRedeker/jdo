"""UI State Observer for capturing Textual app state.

Provides utilities to capture the current state of the Textual app
in a structured format that can be consumed by an AI agent.
"""

from __future__ import annotations

from datetime import UTC, datetime, timezone
from typing import TYPE_CHECKING, Any, cast

from textual.app import App
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Static

if TYPE_CHECKING:
    from jdo.screens.chat import ChatScreen
    from jdo.screens.home import HomeScreen

from tests.uat.models import (
    BindingInfo,
    ChatMessageInfo,
    DataPanelInfo,
    UIState,
    WidgetInfo,
)


class UIStateObserver:
    """Captures current UI state from a Textual app.

    This class inspects the running Textual app and creates a structured
    UIState object that can be passed to an AI agent for decision-making.
    """

    def __init__(self, app: App[Any]) -> None:
        """Initialize the observer with a Textual app.

        Args:
            app: The running Textual app to observe.
        """
        self.app = app

    def capture(self) -> UIState:
        """Capture the current UI state.

        Returns:
            A UIState object representing the current state of the app.
        """
        screen = self.app.screen
        screen_type = type(screen).__name__

        # Get screen title if available
        screen_title = getattr(screen, "title", None)

        # Get focused widget
        focused = self.app.focused
        focused_widget = focused.id if focused and focused.id else None

        # Get bindings from the screen
        bindings = self._capture_bindings(screen)

        # Initialize state
        state = UIState(
            screen_type=screen_type,
            screen_title=screen_title,
            focused_widget=focused_widget,
            bindings=bindings,
            visible_widgets=[],
            chat_messages=[],
            data_panel=None,
            prompt_content=None,
            triage_count=0,
            integrity_grade=None,
        )

        # Capture screen-specific state
        if screen_type == "HomeScreen":
            self._capture_home_screen_state(screen, state)
        elif screen_type == "ChatScreen":
            self._capture_chat_screen_state(screen, state)
        elif screen_type == "SettingsScreen":
            self._capture_settings_screen_state(screen, state)

        # Capture key visible widgets
        state.visible_widgets = self._capture_visible_widgets()

        return state

    def _capture_bindings(self, screen: Widget) -> list[BindingInfo]:
        """Capture available keybindings from the screen.

        Args:
            screen: The current screen widget.

        Returns:
            List of binding information.
        """
        bindings: list[BindingInfo] = []

        # Get bindings from the screen's BINDINGS class variable
        screen_bindings = getattr(screen, "BINDINGS", [])
        for binding in screen_bindings:
            if isinstance(binding, Binding):
                if binding.show:  # Only include visible bindings
                    bindings.append(
                        BindingInfo(
                            key=binding.key,
                            action=binding.action,
                            description=binding.description,
                        )
                    )
            elif isinstance(binding, tuple) and len(binding) >= 3:
                # Handle tuple format: (key, action, description)
                bindings.append(
                    BindingInfo(
                        key=str(binding[0]),
                        action=str(binding[1]),
                        description=str(binding[2]),
                    )
                )

        return bindings

    def _capture_visible_widgets(self) -> list[WidgetInfo]:
        """Capture information about key visible widgets.

        Returns:
            List of widget information for important widgets.
        """
        widgets: list[WidgetInfo] = []

        # Find widgets with IDs (these are typically the important ones)
        for widget in self.app.query("*"):
            if widget.id and widget.display:
                content = None
                if isinstance(widget, Static):
                    # Get the render result as string
                    render_result = widget.render()
                    content = str(render_result)[:200]

                widgets.append(
                    WidgetInfo(
                        widget_id=widget.id,
                        widget_type=type(widget).__name__,
                        content=content,
                        has_focus=widget.has_focus,
                        is_enabled=not getattr(widget, "disabled", False),
                    )
                )

        return widgets[:20]  # Limit to avoid overwhelming the AI

    def _capture_home_screen_state(self, screen: Widget, state: UIState) -> None:
        """Capture HomeScreen-specific state.

        Args:
            screen: The HomeScreen instance.
            state: The UIState to update.
        """
        # Get triage count
        state.triage_count = getattr(screen, "triage_count", 0)

        # Get integrity grade
        state.integrity_grade = getattr(screen, "integrity_grade", None)

    def _capture_chat_screen_state(self, screen: Widget, state: UIState) -> None:
        """Capture ChatScreen-specific state.

        Args:
            screen: The ChatScreen instance.
            state: The UIState to update.
        """
        # Capture prompt content - silently ignore if widget not found
        try:
            prompt_input = screen.query_one("PromptInput")
            text_attr = getattr(prompt_input, "text", None)
            if text_attr is not None:
                state.prompt_content = str(text_attr)
        except (LookupError, AttributeError):
            # Widget not found or doesn't have expected attributes
            pass

        # Capture chat messages
        state.chat_messages = self._capture_chat_messages(screen)

        # Capture data panel state
        state.data_panel = self._capture_data_panel(screen)

    def _capture_settings_screen_state(self, screen: Widget, state: UIState) -> None:
        """Capture SettingsScreen-specific state.

        Args:
            screen: The SettingsScreen instance.
            state: The UIState to update.
        """
        # Settings screen doesn't have much special state

    def _capture_chat_messages(self, screen: Widget) -> list[ChatMessageInfo]:
        """Capture recent chat messages from the screen.

        Args:
            screen: The ChatScreen instance.

        Returns:
            List of recent chat messages.
        """
        messages: list[ChatMessageInfo] = []

        try:
            # Try to get chat container
            chat_container = screen.query_one("ChatContainer")
            if chat_container is None:
                return messages

            # Query for ChatMessage widgets
            chat_messages = chat_container.query("ChatMessage")

            for msg in chat_messages:
                role_attr: Any = getattr(msg, "role", "unknown")
                content_attr = getattr(msg, "content", "")

                # Handle role enum - check if it has a value attribute
                role_value: str = (
                    str(role_attr.value) if hasattr(role_attr, "value") else str(role_attr)
                )

                messages.append(
                    ChatMessageInfo(
                        role=str(role_value),
                        content=str(content_attr)[:500],  # Truncate long messages
                        timestamp=datetime.now(UTC),
                    )
                )
        except (LookupError, AttributeError):
            # Chat container or messages not found
            pass

        return messages[-10:]  # Return last 10 messages

    def _capture_data_panel(self, screen: Widget) -> DataPanelInfo | None:
        """Capture data panel state from ChatScreen.

        Args:
            screen: The ChatScreen instance.

        Returns:
            DataPanelInfo if data panel exists, None otherwise.
        """
        try:
            data_panel = screen.query_one("DataPanel")
            if data_panel is None:
                return None

            # Get panel mode
            mode_attr: Any = getattr(data_panel, "_mode", "empty")
            mode_value: str = (
                str(mode_attr.value) if hasattr(mode_attr, "value") else str(mode_attr)
            )

            # Get entity type
            entity_type_attr: Any = getattr(data_panel, "_entity_type", None)
            entity_type_value: str | None = None
            if entity_type_attr is not None:
                entity_type_value = (
                    str(entity_type_attr.value)
                    if hasattr(entity_type_attr, "value")
                    else str(entity_type_attr)
                )

            # Get content summary based on mode
            content_summary = None
            list_data: list[Any] | None = None
            if mode_value == "draft":
                draft_data = getattr(data_panel, "_draft_data", None)
                if draft_data:
                    content_summary = f"Draft with {len(draft_data)} fields"
            elif mode_value == "list":
                list_data = getattr(data_panel, "_list_data", None)
                if list_data:
                    content_summary = f"{len(list_data)} items"

            return DataPanelInfo(
                mode=str(mode_value),
                entity_type=entity_type_value,
                item_count=len(list_data) if mode_value == "list" and list_data else None,
                content_summary=content_summary,
            )
        except (LookupError, AttributeError):
            # Data panel not found or doesn't have expected structure
            return None
