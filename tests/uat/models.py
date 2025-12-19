"""Pydantic models for AI-driven UAT.

Defines structured types for:
- UI state observation
- AI action commands
- Scenario definitions
- Execution results
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Types of actions the AI can perform."""

    PRESS = "press"
    CLICK = "click"
    TYPE = "type"
    WAIT = "wait"
    ASSERT = "assert"
    DONE = "done"


class UATAction(BaseModel):
    """Structured action for AI-driven test execution.

    The AI returns this model to specify what action to take next.
    All actions include a reason for debugging and logging.
    """

    action_type: ActionType = Field(description="Type of action to perform")
    target: str | None = Field(
        default=None,
        description="Widget ID, CSS selector, or key sequence depending on action type",
    )
    value: str | None = Field(
        default=None,
        description="Text to type, assertion value, or delay in seconds for wait",
    )
    reason: str = Field(description="AI's explanation for choosing this action")


class WidgetInfo(BaseModel):
    """Information about a visible widget."""

    widget_id: str | None = Field(default=None, description="Widget ID if set")
    widget_type: str = Field(description="Widget class name")
    content: str | None = Field(default=None, description="Text content if applicable")
    has_focus: bool = Field(default=False, description="Whether widget has focus")
    is_enabled: bool = Field(default=True, description="Whether widget is enabled")


class BindingInfo(BaseModel):
    """Information about an available keybinding."""

    key: str = Field(description="Key or key combination")
    action: str = Field(description="Action name")
    description: str = Field(description="Human-readable description")


class ChatMessageInfo(BaseModel):
    """Information about a chat message."""

    role: str = Field(description="Message role: user, assistant, or system")
    content: str = Field(description="Message content (may be truncated)")
    timestamp: datetime | None = Field(default=None, description="Message timestamp")


class DataPanelInfo(BaseModel):
    """Information about the data panel state."""

    mode: str = Field(description="Panel mode: draft, list, view, or empty")
    entity_type: str | None = Field(default=None, description="Type of entity displayed")
    item_count: int | None = Field(default=None, description="Number of items in list mode")
    content_summary: str | None = Field(default=None, description="Brief summary of panel content")


class UIState(BaseModel):
    """Complete UI state snapshot for AI consumption.

    Captures all relevant information about the current state
    of the Textual app for the AI to make decisions.
    """

    screen_type: str = Field(description="Current screen class name")
    screen_title: str | None = Field(default=None, description="Screen title if set")
    focused_widget: str | None = Field(default=None, description="ID of currently focused widget")
    visible_widgets: list[WidgetInfo] = Field(
        default_factory=list, description="Key visible widgets"
    )
    bindings: list[BindingInfo] = Field(default_factory=list, description="Available keybindings")
    chat_messages: list[ChatMessageInfo] = Field(
        default_factory=list, description="Recent chat messages (if on chat screen)"
    )
    data_panel: DataPanelInfo | None = Field(
        default=None, description="Data panel state (if visible)"
    )
    prompt_content: str | None = Field(
        default=None, description="Current prompt input content (if on chat screen)"
    )
    triage_count: int = Field(default=0, description="Number of items needing triage")
    integrity_grade: str | None = Field(
        default=None, description="Current integrity grade if visible"
    )

    def _format_bindings(self) -> str | None:
        """Format bindings for prompt context."""
        if not self.bindings:
            return None
        binding_strs = [f"[{b.key}] {b.description}" for b in self.bindings[:10]]
        return f"Available Actions: {', '.join(binding_strs)}"

    def _format_chat_messages(self) -> list[str]:
        """Format chat messages for prompt context."""
        if not self.chat_messages:
            return []
        lines = [f"Chat Messages: {len(self.chat_messages)} messages"]
        for msg in self.chat_messages[-2:]:
            content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            lines.append(f"  [{msg.role}]: {content}")
        return lines

    def _format_data_panel(self) -> list[str]:
        """Format data panel info for prompt context."""
        if not self.data_panel:
            return []
        lines = [f"Data Panel: {self.data_panel.mode} mode"]
        if self.data_panel.entity_type:
            lines.append(f"  Entity Type: {self.data_panel.entity_type}")
        if self.data_panel.content_summary:
            lines.append(f"  Content: {self.data_panel.content_summary}")
        return lines

    def to_prompt_context(self) -> str:
        """Convert UI state to a text description for AI prompt.

        Returns:
            Human-readable description of the current UI state.
        """
        lines = [f"Current Screen: {self.screen_type}"]

        if self.screen_title:
            lines.append(f"Screen Title: {self.screen_title}")
        if self.focused_widget:
            lines.append(f"Focused Widget: {self.focused_widget}")
        if self.integrity_grade:
            lines.append(f"Integrity Grade: {self.integrity_grade}")
        if self.triage_count > 0:
            lines.append(f"Triage Items: {self.triage_count}")
        if bindings := self._format_bindings():
            lines.append(bindings)

        lines.extend(self._format_chat_messages())
        lines.extend(self._format_data_panel())

        if self.prompt_content:
            lines.append(f"Prompt Input: '{self.prompt_content}'")

        return "\n".join(lines)


class UATScenario(BaseModel):
    """Declarative scenario definition for UAT tests.

    Scenarios are loaded from YAML files and define:
    - What the test is trying to accomplish (goal)
    - Any setup needed (preconditions)
    - How to know when it's done (success_criteria)
    """

    name: str = Field(description="Unique scenario identifier")
    description: str = Field(description="Human-readable description of the scenario")
    goal: str = Field(description="Natural language goal for the AI to accomplish")
    preconditions: list[str] = Field(
        default_factory=list, description="Setup steps to run before AI takes over"
    )
    success_criteria: list[str] = Field(
        description="Conditions that must be true for the scenario to pass"
    )
    max_steps: int = Field(default=50, description="Maximum number of AI actions allowed")
    timeout_seconds: int = Field(default=120, description="Maximum time for scenario execution")
    tags: list[str] = Field(default_factory=list, description="Tags for filtering scenarios")


class StepResult(BaseModel):
    """Result of a single action step."""

    step_number: int = Field(description="Step number in the sequence")
    action: UATAction = Field(description="Action that was executed")
    success: bool = Field(description="Whether the action succeeded")
    error: str | None = Field(default=None, description="Error message if action failed")
    ui_state_before: UIState | None = Field(default=None, description="UI state before action")
    ui_state_after: UIState | None = Field(default=None, description="UI state after action")
    duration_ms: float = Field(description="Time taken to execute action in milliseconds")


class UATResult(BaseModel):
    """Complete result of a UAT scenario execution."""

    scenario_name: str = Field(description="Name of the executed scenario")
    success: bool = Field(description="Whether the scenario passed")
    steps: list[StepResult] = Field(default_factory=list, description="Results of each action step")
    total_steps: int = Field(description="Total number of steps executed")
    total_duration_ms: float = Field(description="Total execution time in milliseconds")
    error: str | None = Field(default=None, description="Error message if scenario failed")
    final_ui_state: UIState | None = Field(default=None, description="UI state at end of scenario")
    success_criteria_met: list[str] = Field(
        default_factory=list, description="Which success criteria were met"
    )
    success_criteria_failed: list[str] = Field(
        default_factory=list, description="Which success criteria were not met"
    )


class UATStepLimitError(Exception):
    """Raised when a scenario exceeds its maximum step limit."""

    def __init__(self, scenario_name: str, max_steps: int, steps_taken: int) -> None:
        self.scenario_name = scenario_name
        self.max_steps = max_steps
        self.steps_taken = steps_taken
        super().__init__(
            f"Scenario '{scenario_name}' exceeded step limit: {steps_taken}/{max_steps} steps"
        )


class UATTimeoutError(Exception):
    """Raised when a scenario exceeds its timeout."""

    def __init__(self, scenario_name: str, timeout_seconds: int, elapsed_seconds: float) -> None:
        self.scenario_name = scenario_name
        self.timeout_seconds = timeout_seconds
        self.elapsed_seconds = elapsed_seconds
        super().__init__(
            f"Scenario '{scenario_name}' timed out: {elapsed_seconds:.1f}s/{timeout_seconds}s"
        )
