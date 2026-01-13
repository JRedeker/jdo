"""Command parser for recognizing and routing TUI commands.

Commands start with '/' and trigger specific actions like creating
commitments, goals, or tasks.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from jdo.exceptions import JDOError


class CommandType(str, Enum):
    """Type of command recognized by the parser."""

    COMMIT = "commit"
    GOAL = "goal"
    TASK = "task"
    VISION = "vision"
    MILESTONE = "milestone"
    RECURRING = "recurring"
    TRIAGE = "triage"
    SHOW = "show"
    LIST = "list"  # List entities (commitments, goals, visions)
    VIEW = "view"
    EDIT = "edit"
    TYPE = "type"
    COMPLETE = "complete"
    CANCEL = "cancel"
    HELP = "help"
    REVIEW = "review"  # Review visions due for quarterly review
    ATRISK = "atrisk"  # Mark commitment as at-risk
    CLEANUP = "cleanup"  # View/update cleanup plan
    INTEGRITY = "integrity"  # Show integrity dashboard
    ABANDON = "abandon"  # Mark commitment as abandoned
    HOURS = "hours"  # Set available hours for time coaching
    RECOVER = "recover"  # Recover at-risk commitment to in_progress
    MESSAGE = "message"  # Not a command, just a regular message


class ParseError(JDOError):
    """Error raised when command parsing fails."""


@dataclass
class ParsedCommand:
    """Result of parsing a user input.

    Attributes:
        command_type: The type of command or MESSAGE for regular text.
        args: Arguments passed to the command.
        raw_text: The original input text.
    """

    command_type: CommandType
    args: list[str]
    raw_text: str

    def is_command(self) -> bool:
        """Check if this is a command (not a regular message).

        Returns:
            True if this is a command, False if it's a regular message.
        """
        return self.command_type != CommandType.MESSAGE


# Map command names to CommandType
_COMMAND_MAP: dict[str, CommandType] = {
    "commit": CommandType.COMMIT,
    "goal": CommandType.GOAL,
    "task": CommandType.TASK,
    "vision": CommandType.VISION,
    "milestone": CommandType.MILESTONE,
    "recurring": CommandType.RECURRING,
    "triage": CommandType.TRIAGE,
    "show": CommandType.SHOW,
    "list": CommandType.LIST,
    "view": CommandType.VIEW,
    "edit": CommandType.EDIT,
    "type": CommandType.TYPE,
    "complete": CommandType.COMPLETE,
    "cancel": CommandType.CANCEL,
    "help": CommandType.HELP,
    "review": CommandType.REVIEW,
    "atrisk": CommandType.ATRISK,
    "cleanup": CommandType.CLEANUP,
    "integrity": CommandType.INTEGRITY,
    "abandon": CommandType.ABANDON,
    "hours": CommandType.HOURS,
    "recover": CommandType.RECOVER,
}

# Aliases that expand to other commands with args
# Format: alias -> (command, args_to_prepend)
_COMMAND_ALIASES: dict[str, tuple[str, list[str]]] = {
    # Shortcut numbers /1 through /5 -> /view <n>
    "1": ("view", ["1"]),
    "2": ("view", ["2"]),
    "3": ("view", ["3"]),
    "4": ("view", ["4"]),
    "5": ("view", ["5"]),
    # Command abbreviations
    "c": ("commit", []),
    "l": ("list", []),
    "v": ("view", []),
    "h": ("help", []),
}


def parse_command(text: str) -> ParsedCommand:
    """Parse user input into a command or message.

    Supports command aliases like /1 -> /view 1, /c -> /commit, etc.

    Args:
        text: The user's input text.

    Returns:
        ParsedCommand with command_type, args, and raw_text.

    Raises:
        ParseError: If input starts with '/' but command is not recognized.
    """
    text = text.strip()

    # Empty or non-command text
    if not text or not text.startswith("/"):
        return ParsedCommand(
            command_type=CommandType.MESSAGE,
            args=[],
            raw_text=text,
        )

    # Parse command
    parts = text[1:].split()
    if not parts:
        msg = "Unknown command: /"
        raise ParseError(msg)

    command_name = parts[0].lower()
    args = parts[1:]

    # Check for aliases first
    if command_name in _COMMAND_ALIASES:
        actual_command, prepend_args = _COMMAND_ALIASES[command_name]
        command_name = actual_command
        args = prepend_args + args

    if command_name not in _COMMAND_MAP:
        msg = f"Unknown command: /{command_name}"
        raise ParseError(msg)

    return ParsedCommand(
        command_type=_COMMAND_MAP[command_name],
        args=args,
        raw_text=text,
    )
