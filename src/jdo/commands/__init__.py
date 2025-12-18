"""Command parsing and handling for JDO TUI."""

from __future__ import annotations

from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult
from jdo.commands.handlers import (
    AtRiskHandler,
    CancelHandler,
    CleanupHandler,
    CommandHandler,
    CommitHandler,
    CompleteHandler,
    EditHandler,
    GoalHandler,
    HandlerResult,
    HelpHandler,
    IntegrityHandler,
    MilestoneHandler,
    ShowHandler,
    TaskHandler,
    ViewHandler,
    VisionHandler,
    get_handler,
)
from jdo.commands.parser import (
    CommandType,
    ParsedCommand,
    ParseError,
    parse_command,
)

__all__ = [
    "AtRiskHandler",
    "CancelHandler",
    "CleanupHandler",
    "CommandHandler",
    "CommandType",
    "CommitHandler",
    "CompleteHandler",
    "ConfirmationMatcher",
    "ConfirmationResult",
    "EditHandler",
    "GoalHandler",
    "HandlerResult",
    "HelpHandler",
    "IntegrityHandler",
    "MilestoneHandler",
    "ParseError",
    "ParsedCommand",
    "ShowHandler",
    "TaskHandler",
    "ViewHandler",
    "VisionHandler",
    "get_handler",
    "parse_command",
]
