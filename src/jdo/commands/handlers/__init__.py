"""Command handlers package with domain-focused modules.

Handlers are organized by domain:
- commitment_handlers: Commitment lifecycle (commit, at-risk, cleanup, recover, abandon)
- goal_handlers: Goal creation and management
- task_handlers: Task creation and completion
- vision_handlers: Vision management
- milestone_handlers: Milestone management
- integrity_handlers: Integrity dashboard
- recurring_handlers: Recurring commitment management
- utility_handlers: Help, show, view, cancel, edit, type, hours, triage
"""

from __future__ import annotations

# Export base classes from new base module
from jdo.commands.handlers.base import CommandHandler, HandlerResult

# Override with migrated handlers from new package modules
from jdo.commands.handlers.commitment_handlers import (
    AbandonHandler,
    AtRiskHandler,
    CleanupHandler,
    CommitHandler,
    RecoverHandler,
)
from jdo.commands.handlers.goal_handlers import GoalHandler
from jdo.commands.handlers.integrity_handlers import IntegrityHandler
from jdo.commands.handlers.milestone_handlers import MilestoneHandler
from jdo.commands.handlers.recurring_handlers import RecurringHandler
from jdo.commands.handlers.task_handlers import CompleteHandler, TaskHandler
from jdo.commands.handlers.utility_handlers import (
    CancelHandler,
    EditHandler,
    HelpHandler,
    HoursHandler,
    ShowHandler,
    TriageHandler,
    TypeHandler,
    ViewHandler,
)
from jdo.commands.handlers.vision_handlers import VisionHandler
from jdo.commands.parser import CommandType

# Handler registry
_HANDLERS: dict[CommandType, type[CommandHandler]] = {}
_handler_instances: dict[CommandType, CommandHandler] = {}


def _register_handlers() -> None:
    """Populate the handler registry."""
    if _HANDLERS:
        return

    _HANDLERS.update(
        {
            CommandType.COMMIT: CommitHandler,
            CommandType.GOAL: GoalHandler,
            CommandType.TASK: TaskHandler,
            CommandType.VISION: VisionHandler,
            CommandType.MILESTONE: MilestoneHandler,
            CommandType.RECURRING: RecurringHandler,
            CommandType.TRIAGE: TriageHandler,
            CommandType.SHOW: ShowHandler,
            CommandType.HELP: HelpHandler,
            CommandType.VIEW: ViewHandler,
            CommandType.CANCEL: CancelHandler,
            CommandType.COMPLETE: CompleteHandler,
            CommandType.TYPE: TypeHandler,
            CommandType.EDIT: EditHandler,
            CommandType.ATRISK: AtRiskHandler,
            CommandType.CLEANUP: CleanupHandler,
            CommandType.INTEGRITY: IntegrityHandler,
            CommandType.ABANDON: AbandonHandler,
            CommandType.HOURS: HoursHandler,
            CommandType.RECOVER: RecoverHandler,
        }
    )


def get_handler(command_type: CommandType) -> CommandHandler | None:
    """Get the handler for a command type.

    Args:
        command_type: The type of command to get a handler for.

    Returns:
        Handler instance or None for MESSAGE type.
    """
    if command_type == CommandType.MESSAGE:
        return None

    _register_handlers()
    if command_type not in _handler_instances:
        handler_class = _HANDLERS.get(command_type)
        if handler_class:
            _handler_instances[command_type] = handler_class()

    return _handler_instances.get(command_type)


__all__ = [
    "AbandonHandler",
    "AtRiskHandler",
    "CancelHandler",
    "CleanupHandler",
    "CommandHandler",
    "CommitHandler",
    "CompleteHandler",
    "EditHandler",
    "GoalHandler",
    "HandlerResult",
    "HelpHandler",
    "HoursHandler",
    "IntegrityHandler",
    "MilestoneHandler",
    "RecoverHandler",
    "RecurringHandler",
    "ShowHandler",
    "TaskHandler",
    "TriageHandler",
    "TypeHandler",
    "ViewHandler",
    "VisionHandler",
    "get_handler",
]
