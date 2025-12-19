"""Snapshot app for NavSidebar in expanded state."""

from __future__ import annotations

from textual.app import App, ComposeResult

from jdo.widgets.nav_sidebar import NavSidebar


class NavSidebarExpandedApp(App):
    """App showing NavSidebar in expanded state with all items."""

    CSS = """
    NavSidebar {
        height: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield NavSidebar()

    def on_mount(self) -> None:
        sidebar = self.query_one(NavSidebar)
        # Set triage count to show badge
        sidebar.set_triage_count(3)


if __name__ == "__main__":
    NavSidebarExpandedApp().run()
