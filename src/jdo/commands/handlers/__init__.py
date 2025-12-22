"""Command handlers package with lazy-loaded registry."""

from __future__ import annotations

from jdo.commands.handlers.base import CommandHandler, HandlerResult
from jdo.commands.parser import CommandType

_HANDLERS: dict[CommandType, type[CommandHandler]] = {}
_handler_instances: dict[CommandType, CommandHandler] = {}


def _register_handlers() -> None:
    """Populate the handler registry once."""
    if _HANDLERS:
        return

    from jdo.commands.handlers.milestone_handlers import MilestoneHandler

    _HANDLERS.update(
        {
            CommandType.MILESTONE: MilestoneHandler,
        }
    )


def get_handler(command_type: CommandType) -> CommandHandler | None:
    """Return a handler instance for the requested command type."""
    if command_type == CommandType.MESSAGE:
        return None

    _register_handlers()
    if command_type not in _handler_instances:
        handler_class = _HANDLERS.get(command_type)
        if handler_class:
            _handler_instances[command_type] = handler_class()
    return _handler_instances.get(command_type)


__all__ = ["get_handler", "CommandHandler", "HandlerResult"]
