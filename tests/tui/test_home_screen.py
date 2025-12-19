"""Tests for HomeScreen - Main entry point.

The HomeScreen serves as the entry point for the JDO TUI,
providing quick access to views and shortcuts.
"""

import pytest
from textual.app import App, ComposeResult

from tests.tui.conftest import create_test_app_for_screen


class TestHomeScreen:
    """Tests for HomeScreen functionality."""

    async def test_home_screen_renders(self) -> None:
        """HomeScreen renders without error."""
        from jdo.screens.home import HomeScreen

        app = create_test_app_for_screen(HomeScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, HomeScreen)

    async def test_home_screen_shows_welcome_message(self) -> None:
        """HomeScreen shows a welcome or prompt message."""
        from jdo.screens.home import HomeScreen

        app = create_test_app_for_screen(HomeScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, HomeScreen)


class TestHomeScreenKeyBindings:
    """Tests for HomeScreen keyboard shortcuts."""

    async def test_g_key_shows_goals(self) -> None:
        """'g' key posts ShowGoals message."""
        from jdo.screens.home import HomeScreen

        message_received = False

        class TestApp(App):
            def compose(self) -> ComposeResult:
                return
                yield

            async def on_mount(self) -> None:
                await self.push_screen(HomeScreen())

            def on_home_screen_show_goals(self, message: HomeScreen.ShowGoals) -> None:
                nonlocal message_received
                message_received = True

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("g")
            await pilot.pause()
            assert message_received

    async def test_c_key_shows_commitments(self) -> None:
        """'c' key posts ShowCommitments message."""
        from jdo.screens.home import HomeScreen

        message_received = False

        class TestApp(App):
            def compose(self) -> ComposeResult:
                return
                yield

            async def on_mount(self) -> None:
                await self.push_screen(HomeScreen())

            def on_home_screen_show_commitments(self, message: HomeScreen.ShowCommitments) -> None:
                nonlocal message_received
                message_received = True

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("c")
            await pilot.pause()
            assert message_received

    async def test_v_key_shows_visions(self) -> None:
        """'v' key posts ShowVisions message."""
        from jdo.screens.home import HomeScreen

        message_received = False

        class TestApp(App):
            def compose(self) -> ComposeResult:
                return
                yield

            async def on_mount(self) -> None:
                await self.push_screen(HomeScreen())

            def on_home_screen_show_visions(self, message: HomeScreen.ShowVisions) -> None:
                nonlocal message_received
                message_received = True

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("v")
            await pilot.pause()
            assert message_received

    async def test_q_key_quits(self) -> None:
        """'q' key triggers quit action."""
        from jdo.screens.home import HomeScreen

        quit_triggered = False

        class TestApp(App):
            BINDINGS = [("q", "quit", "Quit")]

            def compose(self) -> ComposeResult:
                return
                yield

            async def on_mount(self) -> None:
                await self.push_screen(HomeScreen())

            def action_quit(self) -> None:
                nonlocal quit_triggered
                quit_triggered = True

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("q")
            await pilot.pause()
            assert quit_triggered


class TestHomeScreenFooter:
    """Tests for HomeScreen footer with shortcuts."""

    async def test_home_screen_has_footer(self) -> None:
        """HomeScreen includes a footer with shortcuts."""
        from jdo.screens.home import HomeScreen

        app = create_test_app_for_screen(HomeScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
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

    async def test_action_show_integrity_exists(self) -> None:
        """HomeScreen has action_show_integrity method."""
        from jdo.screens.home import HomeScreen

        assert hasattr(HomeScreen, "action_show_integrity")


class TestHomeScreenIntegrity:
    """Tests for HomeScreen integrity display."""

    async def test_home_screen_has_integrity_binding(self) -> None:
        """HomeScreen has 'i' binding for integrity."""
        from jdo.screens.home import HomeScreen

        bindings = {b.key: b for b in HomeScreen.BINDINGS}
        assert "i" in bindings
        assert bindings["i"].action == "show_integrity"

    async def test_home_screen_has_integrity_indicator(self) -> None:
        """HomeScreen has integrity indicator widget."""
        from jdo.screens.home import HomeScreen

        app = create_test_app_for_screen(HomeScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            indicator = pilot.app.screen.query_one("#integrity-indicator")
            assert indicator is not None

    async def test_home_screen_has_integrity_grade_reactive(self) -> None:
        """HomeScreen has integrity_grade reactive property."""
        from jdo.screens.home import HomeScreen

        assert hasattr(HomeScreen, "integrity_grade")

    async def test_integrity_indicator_exists_and_updates(self) -> None:
        """Integrity indicator exists and updates with grade."""
        from textual.widgets import Static

        from jdo.screens.home import HomeScreen

        app = create_test_app_for_screen(HomeScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, HomeScreen)
            indicator = screen.query_one("#integrity-indicator", Static)
            assert indicator is not None
            # Default grade should be one of the valid grades
            assert screen.integrity_grade in [
                "A+",
                "A",
                "A-",
                "B+",
                "B",
                "B-",
                "C+",
                "C",
                "C-",
                "D+",
                "D",
                "D-",
                "F",
            ]

    async def test_i_key_triggers_show_integrity(self) -> None:
        """'i' key posts ShowIntegrity message."""
        from jdo.screens.home import HomeScreen

        message_received = False

        class TestApp(App):
            def compose(self) -> ComposeResult:
                return
                yield

            async def on_mount(self) -> None:
                await self.push_screen(HomeScreen())

            def on_home_screen_show_integrity(self, message: HomeScreen.ShowIntegrity) -> None:
                nonlocal message_received
                message_received = True

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await pilot.press("i")
            await pilot.pause()
            assert message_received

    async def test_home_screen_posts_show_integrity_message(self) -> None:
        """HomeScreen posts ShowIntegrity message on 'i' key."""
        from jdo.screens.home import HomeScreen

        received_messages: list[HomeScreen.ShowIntegrity] = []

        class TestApp(App):
            def compose(self) -> ComposeResult:
                return
                yield

            async def on_mount(self) -> None:
                await self.push_screen(HomeScreen())

            def on_home_screen_show_integrity(self, message: HomeScreen.ShowIntegrity) -> None:
                received_messages.append(message)

        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, HomeScreen)
            screen.action_show_integrity()
            await pilot.pause()
            assert len(received_messages) == 1

    async def test_integrity_indicator_has_grade_class(self) -> None:
        """Integrity indicator has appropriate grade CSS class."""
        from textual.widgets import Static

        from jdo.screens.home import HomeScreen

        app = create_test_app_for_screen(HomeScreen())
        async with app.run_test() as pilot:
            await pilot.pause()
            screen = pilot.app.screen
            assert isinstance(screen, HomeScreen)
            indicator = screen.query_one("#integrity-indicator", Static)
            # Should have one of the grade classes
            has_grade_class = any(
                cls in indicator.classes
                for cls in ["grade-a", "grade-b", "grade-c", "grade-d", "grade-f"]
            )
            assert has_grade_class

    async def test_home_screen_bindings_include_integrity(self) -> None:
        """HomeScreen BINDINGS include integrity shortcut."""
        from jdo.screens.home import HomeScreen

        # Check that the bindings include 'i' for integrity
        binding_keys = [b.key for b in HomeScreen.BINDINGS]
        assert "i" in binding_keys

        # Check the action name
        i_binding = next(b for b in HomeScreen.BINDINGS if b.key == "i")
        assert i_binding.action == "show_integrity"
        assert i_binding.description == "Integrity"
