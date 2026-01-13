"""REPL Test Harness for UAT.

Provides programmatic access to the JDO REPL for testing.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from io import StringIO
from unittest.mock import patch

from pydantic_ai import Agent
from rich.console import Console
from sqlmodel import Session

from jdo.ai.agent import JDODependencies, create_agent
from jdo.repl.session import Session as REPLSession


@dataclass
class REPLOutput:
    """Captured output from a REPL interaction."""

    text: str
    continue_loop: bool
    error: Exception | None = None


@dataclass
class REPLTestHarness:
    """Harness for programmatic REPL UAT testing.

    Allows sending inputs to the REPL and capturing outputs without
    running the full interactive loop.

    Example:
        ```python
        from jdo.db.session import get_session
        from jdo.uat import REPLTestHarness

        with get_session() as db:
            harness = REPLTestHarness(db)
            output = await harness.send("/help")
            print(output.text)
        ```
    """

    db_session: Session
    repl_session: REPLSession = field(default_factory=REPLSession)
    _agent: Agent[JDODependencies, str] | None = field(default=None)
    _deps: JDODependencies | None = field(default=None)
    _output_buffer: StringIO = field(default_factory=StringIO)
    _console: Console | None = field(default=None)
    _start_time: datetime = field(default_factory=datetime.now)
    _inputs_sent: list[str] = field(default_factory=list)
    _outputs_received: list[REPLOutput] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize the harness components."""
        if self._agent is None:
            self._agent = create_agent()
        if self._deps is None:
            self._deps = JDODependencies(session=self.db_session)
        self._console = Console(
            file=self._output_buffer,
            force_terminal=True,
            width=100,
        )

    @property
    def start_time(self) -> datetime:
        """Return the time this harness was created (for cleanup)."""
        return self._start_time

    @property
    def has_pending_draft(self) -> bool:
        """Check if there's a pending draft awaiting confirmation."""
        return self.repl_session.has_pending_draft

    @property
    def pending_draft_type(self) -> str | None:
        """Get the type of pending draft, if any."""
        if self.repl_session.pending_draft:
            return self.repl_session.pending_draft.entity_type
        return None

    @property
    def message_history(self) -> list[dict[str, str]]:
        """Get the conversation history."""
        return self.repl_session.message_history

    @property
    def inputs_sent(self) -> list[str]:
        """Get all inputs sent during this session."""
        return self._inputs_sent.copy()

    @property
    def outputs_received(self) -> list[REPLOutput]:
        """Get all outputs received during this session."""
        return self._outputs_received.copy()

    async def send(self, user_input: str) -> REPLOutput:
        """Send input to the REPL and capture output.

        Args:
            user_input: The text to send as if the user typed it.

        Returns:
            REPLOutput with captured text and metadata.
        """
        # Import here to avoid circular imports
        from jdo.repl.loop import _process_user_input

        # Clear the output buffer
        self._output_buffer.truncate(0)
        self._output_buffer.seek(0)

        self._inputs_sent.append(user_input)

        # These should always be set by __post_init__
        assert self._agent is not None, "Agent not initialized"
        assert self._deps is not None, "Dependencies not initialized"

        try:
            # Patch the console to capture output
            with patch("jdo.repl.loop.console", self._console):
                continue_loop = await _process_user_input(
                    user_input,
                    self.repl_session,
                    self.db_session,
                    self._agent,
                    self._deps,
                )

            output = REPLOutput(
                text=self._output_buffer.getvalue(),
                continue_loop=continue_loop,
            )
        except Exception as e:
            output = REPLOutput(
                text=self._output_buffer.getvalue(),
                continue_loop=True,
                error=e,
            )

        self._outputs_received.append(output)
        return output

    async def send_sequence(self, inputs: list[str]) -> list[REPLOutput]:
        """Send a sequence of inputs to the REPL.

        Args:
            inputs: List of inputs to send in order.

        Returns:
            List of outputs in corresponding order.
        """
        outputs = []
        for user_input in inputs:
            output = await self.send(user_input)
            outputs.append(output)
            if not output.continue_loop:
                break
        return outputs

    def reset_session(self) -> None:
        """Reset the REPL session state (but keep DB connection)."""
        self.repl_session = REPLSession()
        self._inputs_sent.clear()
        self._outputs_received.clear()
        self._output_buffer.truncate(0)
        self._output_buffer.seek(0)


def run_sync(harness: REPLTestHarness, user_input: str) -> REPLOutput:
    """Synchronous wrapper for harness.send().

    Args:
        harness: The test harness to use.
        user_input: The input to send.

    Returns:
        REPLOutput with captured text and metadata.
    """
    return asyncio.run(harness.send(user_input))
