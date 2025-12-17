"""Command parser for recognizing and routing TUI commands.

Commands start with '/' and trigger specific actions like creating
commitments, goals, or tasks.
"""

from dataclasses import dataclass
from enum import Enum


class CommandType(str, Enum):
    """Type of command recognized by the parser."""

    COMMIT = "commit"
    GOAL = "goal"
    TASK = "task"
    VISION = "vision"
    MILESTONE = "milestone"
    RECURRING = "recurring"
    SHOW = "show"
    VIEW = "view"
    EDIT = "edit"
    COMPLETE = "complete"
    CANCEL = "cancel"
    HELP = "help"
    MESSAGE = "message"  # Not a command, just a regular message


class ParseError(Exception):
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
    "show": CommandType.SHOW,
    "view": CommandType.VIEW,
    "edit": CommandType.EDIT,
    "complete": CommandType.COMPLETE,
    "cancel": CommandType.CANCEL,
    "help": CommandType.HELP,
}


def parse_command(text: str) -> ParsedCommand:
    """Parse user input into a command or message.

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

    if command_name not in _COMMAND_MAP:
        msg = f"Unknown command: /{command_name}"
        raise ParseError(msg)

    return ParsedCommand(
        command_type=_COMMAND_MAP[command_name],
        args=args,
        raw_text=text,
    )
