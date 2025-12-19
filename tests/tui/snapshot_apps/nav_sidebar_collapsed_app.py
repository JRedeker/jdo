"""Snapshot app for NavSidebar in collapsed state."""

from __future__ import annotations

from textual.app import App, ComposeResult

from jdo.widgets.nav_sidebar import NavSidebar


class NavSidebarCollapsedApp(App):
    """App showing NavSidebar in collapsed state with single letters."""

    CSS = """
    NavSidebar {
        height: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        sidebar = NavSidebar()
        sidebar.collapsed = True
        yield sidebar


if __name__ == "__main__":
    NavSidebarCollapsedApp().run()
