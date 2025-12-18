"""Tests for Command Parser - TDD Red phase.

The command parser recognizes commands starting with '/' and routes them.
"""

import pytest

from jdo.commands.parser import CommandType, ParsedCommand, ParseError, parse_command


class TestParseCommand:
    """Tests for parse_command function."""

    def test_recognize_commit_command(self) -> None:
        """/commit is recognized as a command."""
        result = parse_command("/commit")

        assert result.command_type == CommandType.COMMIT
        assert result.args == []

    def test_recognize_goal_command(self) -> None:
        """/goal is recognized as a command."""
        result = parse_command("/goal")

        assert result.command_type == CommandType.GOAL
        assert result.args == []

    def test_recognize_task_command(self) -> None:
        """/task is recognized as a command."""
        result = parse_command("/task")

        assert result.command_type == CommandType.TASK
        assert result.args == []

    def test_recognize_vision_command(self) -> None:
        """/vision is recognized as a command."""
        result = parse_command("/vision")

        assert result.command_type == CommandType.VISION
        assert result.args == []

    def test_recognize_milestone_command(self) -> None:
        """/milestone is recognized as a command."""
        result = parse_command("/milestone")

        assert result.command_type == CommandType.MILESTONE
        assert result.args == []

    def test_recognize_triage_command(self) -> None:
        """/triage is recognized as a command."""
        result = parse_command("/triage")

        assert result.command_type == CommandType.TRIAGE
        assert result.args == []

    def test_recognize_show_command_with_argument(self) -> None:
        """/show goals parses command with argument."""
        result = parse_command("/show goals")

        assert result.command_type == CommandType.SHOW
        assert result.args == ["goals"]

    def test_recognize_help_command_with_argument(self) -> None:
        """/help commit parses command with argument."""
        result = parse_command("/help commit")

        assert result.command_type == CommandType.HELP
        assert result.args == ["commit"]


class TestNonCommandMessages:
    """Tests for messages that are not commands."""

    def test_message_without_slash_is_not_command(self) -> None:
        """Message without '/' is not a command."""
        result = parse_command("Hello, how are you?")

        assert result.command_type == CommandType.MESSAGE
        assert result.raw_text == "Hello, how are you?"

    def test_slash_in_middle_is_not_command(self) -> None:
        """Message with '/' in middle is not a command."""
        result = parse_command("Can you help me with /commit?")

        assert result.command_type == CommandType.MESSAGE

    def test_empty_message_is_not_command(self) -> None:
        """Empty message is not a command."""
        result = parse_command("")

        assert result.command_type == CommandType.MESSAGE


class TestUnknownCommand:
    """Tests for unknown commands."""

    def test_unknown_command_returns_error(self) -> None:
        """Unknown command returns error."""
        with pytest.raises(ParseError, match="Unknown command"):
            parse_command("/foobar")

    def test_slash_alone_returns_error(self) -> None:
        """Just '/' returns error."""
        with pytest.raises(ParseError, match="Unknown command"):
            parse_command("/")


class TestCommandType:
    """Tests for CommandType enum."""

    def test_has_all_command_types(self) -> None:
        """CommandType has all required values."""
        assert CommandType.COMMIT.value == "commit"
        assert CommandType.GOAL.value == "goal"
        assert CommandType.TASK.value == "task"
        assert CommandType.VISION.value == "vision"
        assert CommandType.MILESTONE.value == "milestone"
        assert CommandType.TRIAGE.value == "triage"
        assert CommandType.SHOW.value == "show"
        assert CommandType.VIEW.value == "view"
        assert CommandType.EDIT.value == "edit"
        assert CommandType.COMPLETE.value == "complete"
        assert CommandType.CANCEL.value == "cancel"
        assert CommandType.HELP.value == "help"
        assert CommandType.MESSAGE.value == "message"


class TestParsedCommand:
    """Tests for ParsedCommand dataclass."""

    def test_parsed_command_has_fields(self) -> None:
        """ParsedCommand has command_type, args, raw_text."""
        cmd = ParsedCommand(
            command_type=CommandType.COMMIT,
            args=["arg1", "arg2"],
            raw_text="/commit arg1 arg2",
        )

        assert cmd.command_type == CommandType.COMMIT
        assert cmd.args == ["arg1", "arg2"]
        assert cmd.raw_text == "/commit arg1 arg2"

    def test_is_command_method(self) -> None:
        """is_command returns True for commands, False for messages."""
        cmd = ParsedCommand(command_type=CommandType.COMMIT, args=[], raw_text="/commit")
        msg = ParsedCommand(command_type=CommandType.MESSAGE, args=[], raw_text="hello")

        assert cmd.is_command() is True
        assert msg.is_command() is False
