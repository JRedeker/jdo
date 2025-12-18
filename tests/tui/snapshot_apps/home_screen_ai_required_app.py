"""Snapshot app for HomeScreen AI-required modal."""

from __future__ import annotations

from textual.app import App, ComposeResult

from jdo.screens.ai_required import AiRequiredScreen
from jdo.screens.home import HomeScreen


class HomeScreenAiRequiredApp(App):
    """App for testing AI-required modal on HomeScreen."""

    def compose(self) -> ComposeResult:
        yield HomeScreen()

    async def on_mount(self) -> None:
        self.push_screen(AiRequiredScreen())


if __name__ == "__main__":
    HomeScreenAiRequiredApp().run()
