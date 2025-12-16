"""Snapshot app for HomeScreen empty state."""

from textual.app import App, ComposeResult

from jdo.screens.home import HomeScreen


class HomeScreenApp(App):
    """App for testing HomeScreen snapshot."""

    def compose(self) -> ComposeResult:
        yield HomeScreen()


if __name__ == "__main__":
    HomeScreenApp().run()
