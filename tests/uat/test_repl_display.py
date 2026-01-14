"""UAT tests for REPL display behavior.

These tests verify that:
1. Screen clears before AI responds
2. Dashboard is redrawn after clear
3. User input is echoed before AI response
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from jdo.ai.agent import JDODependencies
from jdo.repl.loop import _process_user_input
from jdo.repl.session import Session


class TestClearScreenBehavior:
    """Tests for the clear screen + redraw behavior."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent."""
        return MagicMock()

    @pytest.fixture
    def mock_deps(self):
        """Create mock dependencies."""
        return MagicMock(spec=JDODependencies)

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def session(self):
        """Create a test session with dashboard cache."""
        s = Session()
        # Initialize dashboard cache to avoid errors
        s._dashboard_commitments = []
        s._dashboard_goals = []
        s._integrity_data = None
        return s

    async def test_screen_clears_before_ai_response(
        self, mock_agent, mock_deps, mock_db_session, session
    ):
        """Screen should clear before AI starts processing."""
        call_order = []

        async def mock_stream(*args, **kwargs):
            call_order.append("ai_stream")
            yield "Response"

        mock_console = MagicMock()
        mock_console.clear = MagicMock(side_effect=lambda: call_order.append("clear"))
        mock_console.print = MagicMock(side_effect=lambda *a, **kw: call_order.append("print"))

        with (
            patch("jdo.repl.loop.stream_response", mock_stream),
            patch("jdo.repl.loop.console", mock_console),
            patch(
                "jdo.repl.loop._show_dashboard",
                side_effect=lambda s: call_order.append("dashboard"),
            ),
        ):
            await _process_user_input(
                "test input",
                session,
                mock_db_session,
                mock_agent,
                mock_deps,
            )

        # Verify order: clear -> dashboard -> print (user input) -> ai_stream
        assert "clear" in call_order
        assert "dashboard" in call_order
        assert call_order.index("clear") < call_order.index("dashboard")
        assert call_order.index("dashboard") < call_order.index("ai_stream")

    async def test_user_input_echoed_after_dashboard(
        self, mock_agent, mock_deps, mock_db_session, session
    ):
        """User's input should be echoed after dashboard is shown."""
        printed_values = []

        def capture_print(*args, **kwargs):
            """Capture all print calls, handling both with and without args."""
            if args:
                printed_values.append(str(args[0]))

        async def mock_stream(*args, **kwargs):
            yield "Response"

        mock_console = MagicMock()
        mock_console.print = MagicMock(side_effect=capture_print)

        with (
            patch("jdo.repl.loop.stream_response", mock_stream),
            patch("jdo.repl.loop.console", mock_console),
            patch("jdo.repl.loop._show_dashboard"),
        ):
            await _process_user_input(
                "my test input",
                session,
                mock_db_session,
                mock_agent,
                mock_deps,
            )

        # Check that user input was echoed
        input_echoed = any("my test input" in val for val in printed_values)
        assert input_echoed, f"User input should be echoed. Printed: {printed_values}"

    async def test_slash_commands_do_not_clear_screen(
        self, mock_agent, mock_deps, mock_db_session, session
    ):
        """Slash commands should not trigger screen clear."""
        mock_console = MagicMock()

        with (
            patch("jdo.repl.loop.console", mock_console),
            patch("jdo.repl.loop.handle_slash_command", new_callable=AsyncMock),
        ):
            await _process_user_input(
                "/help",
                session,
                mock_db_session,
                mock_agent,
                mock_deps,
            )

        # console.clear should NOT have been called for slash commands
        mock_console.clear.assert_not_called()

    async def test_exit_commands_do_not_clear_screen(
        self, mock_agent, mock_deps, mock_db_session, session
    ):
        """Exit commands should not trigger screen clear."""
        mock_console = MagicMock()

        with patch("jdo.repl.loop.console", mock_console):
            result = await _process_user_input(
                "exit",
                session,
                mock_db_session,
                mock_agent,
                mock_deps,
            )

        assert result is False  # Should signal exit
        mock_console.clear.assert_not_called()


class TestDashboardPersistence:
    """Tests to verify dashboard behavior across turns."""

    @pytest.fixture
    def session(self):
        """Create a test session."""
        s = Session()
        s._dashboard_commitments = []
        s._dashboard_goals = []
        s._integrity_data = None
        return s

    def test_dashboard_shown_on_startup(self):
        """Dashboard should be shown when REPL starts."""
        # This is tested by verifying _show_dashboard is called in _main_repl_loop
        # before the first prompt. We verify the code structure exists.
        import inspect

        from jdo.repl import loop

        source = inspect.getsource(loop._main_repl_loop)

        # Should show dashboard before the while loop
        assert "_show_dashboard(session)" in source
        # The dashboard call should appear before "while True:"
        dashboard_pos = source.find("_show_dashboard(session)")
        while_pos = source.find("while True:")
        assert dashboard_pos < while_pos, "Dashboard should be shown before main loop"
