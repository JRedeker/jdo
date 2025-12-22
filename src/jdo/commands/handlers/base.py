"""Base classes for command handlers.

Provides the abstract CommandHandler interface and HandlerResult
for all command handler implementations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from jdo.commands.parser import ParsedCommand


@dataclass
class HandlerResult:
    """Result from executing a command handler.

    Attributes:
        message: Response message to display in chat.
        panel_update: Optional dict with panel mode and data.
        draft_data: Optional draft data being created/updated.
        needs_confirmation: Whether user confirmation is needed.
    """

    message: str
    panel_update: dict[str, Any] | None = None
    draft_data: dict[str, Any] | None = None
    needs_confirmation: bool = False


class CommandHandler(ABC):
    """Base class for command handlers."""

    @abstractmethod
    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute the command and return a result.

        Args:
            cmd: The parsed command to execute.
            context: Context data including conversation history and extracted fields.

        Returns:
            HandlerResult with message and optional panel updates.
        """
