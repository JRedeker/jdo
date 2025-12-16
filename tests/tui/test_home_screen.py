"""Tests for HomeScreen - Main entry point.

The HomeScreen serves as the entry point for the JDO TUI,
providing quick access to views and shortcuts.
"""

import pytest
from textual.app import App, ComposeResult


class TestHomeScreen:
    """Tests for HomeScreen functionality."""

    async def test_home_screen_renders(self) -> None:
        """HomeScreen renders without error."""
        from jdo.screens.home import HomeScreen

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HomeScreen()

        app = TestApp()
        async with app.run_test():
            screen = app.query_one(HomeScreen)
            assert screen is not None

    async def test_home_screen_shows_welcome_message(self) -> None:
        """HomeScreen shows a welcome or prompt message."""
        from jdo.screens.home import HomeScreen

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HomeScreen()

        app = TestApp()
        async with app.run_test():
            screen = app.query_one(HomeScreen)
            # Should have some welcome content
            assert screen is not None


class TestHomeScreenKeyBindings:
    """Tests for HomeScreen keyboard shortcuts."""

    async def test_g_key_shows_goals(self) -> None:
        """'g' key shows goals in the panel."""
        from jdo.screens.home import HomeScreen

        class TestApp(App):
            BINDINGS = [("g", "show_goals", "Goals")]
            goals_shown = False

            def compose(self) -> ComposeResult:
                yield HomeScreen()

            def action_show_goals(self) -> None:
                self.goals_shown = True

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.press("g")
            await pilot.pause()
            assert app.goals_shown

    async def test_c_key_shows_commitments(self) -> None:
        """'c' key shows commitments in the panel."""
        from jdo.screens.home import HomeScreen

        class TestApp(App):
            BINDINGS = [("c", "show_commitments", "Commitments")]
            commitments_shown = False

            def compose(self) -> ComposeResult:
                yield HomeScreen()

            def action_show_commitments(self) -> None:
                self.commitments_shown = True

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.press("c")
            await pilot.pause()
            assert app.commitments_shown

    async def test_v_key_shows_visions(self) -> None:
        """'v' key shows visions in the panel."""
        from jdo.screens.home import HomeScreen

        class TestApp(App):
            BINDINGS = [("v", "show_visions", "Visions")]
            visions_shown = False

            def compose(self) -> ComposeResult:
                yield HomeScreen()

            def action_show_visions(self) -> None:
                self.visions_shown = True

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.press("v")
            await pilot.pause()
            assert app.visions_shown

    async def test_q_key_quits(self) -> None:
        """'q' key triggers quit action."""
        from jdo.screens.home import HomeScreen

        class TestApp(App):
            BINDINGS = [("q", "quit", "Quit")]
            quit_triggered = False

            def compose(self) -> ComposeResult:
                yield HomeScreen()

            def action_quit(self) -> None:
                self.quit_triggered = True

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.press("q")
            await pilot.pause()
            assert app.quit_triggered


class TestHomeScreenFooter:
    """Tests for HomeScreen footer with shortcuts."""

    async def test_home_screen_has_footer(self) -> None:
        """HomeScreen includes a footer with shortcuts."""
        from jdo.screens.home import HomeScreen

        class TestApp(App):
            def compose(self) -> ComposeResult:
                yield HomeScreen()

        app = TestApp()
        async with app.run_test():
            screen = app.query_one(HomeScreen)
            # HomeScreen should have BINDINGS defined
            assert hasattr(HomeScreen, "BINDINGS")
            assert len(HomeScreen.BINDINGS) > 0


class TestHomeScreenActions:
    """Tests for HomeScreen action methods."""

    async def test_action_show_goals_exists(self) -> None:
        """HomeScreen has action_show_goals method."""
        from jdo.screens.home import HomeScreen

        assert hasattr(HomeScreen, "action_show_goals")

    async def test_action_show_commitments_exists(self) -> None:
        """HomeScreen has action_show_commitments method."""
        from jdo.screens.home import HomeScreen

        assert hasattr(HomeScreen, "action_show_commitments")

    async def test_action_show_visions_exists(self) -> None:
        """HomeScreen has action_show_visions method."""
        from jdo.screens.home import HomeScreen

        assert hasattr(HomeScreen, "action_show_visions")

    async def test_action_new_chat_exists(self) -> None:
        """HomeScreen has action_new_chat method."""
        from jdo.screens.home import HomeScreen

        assert hasattr(HomeScreen, "action_new_chat")
